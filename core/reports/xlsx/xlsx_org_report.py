# python
import io

from datetime import date
from datetime import timedelta

# django
from django.conf import settings

# third party
import xlsxwriter

# project
from charges.constants import BASIC_SERVICE_ACCESS
from charges.constants import BASIC_SERVICE_CHOICES
from charges.constants import BASIC_SERVICE_MO
from core.utils import get_amount_ust
from phonecalls.constants import CALLTYPE_CHOICES
from phonecalls.constants import LOCAL, VC1, VC2, VC3, LDN, LDI
from phonecalls.constants import PABX_CHOICES
from phonecalls.constants import REPORT_CALLTYPE_MAP
from phonecalls.constants import SERVICE_CHOICES

BASIC_SERVICE_MAP = dict(BASIC_SERVICE_CHOICES)
CALLTYPE_MAP = dict(CALLTYPE_CHOICES)
PABX_MAP = dict(PABX_CHOICES)
SERVICE_MAP = dict(SERVICE_CHOICES)


class XLSXOrgReport(object):

    def __init__(self, date_start, date_stop, title, org):
        self.org = org
        self.date_start = date_start
        self.date_stop = date_stop
        self.today = date.today().strftime('%d/%m/%Y')
        self.title = title
        self.org_title = org.name.upper()
        self.org_logo = self.org.settings.logo.name if self.org.settings.logo else None

        # create an in-memory output file
        self.xls_file = io.BytesIO()
        self.workbook = xlsxwriter.Workbook(self.xls_file, {'constant_memory': True})

        # style
        bold = {'bold': True}
        center = {'align': 'center'}
        right = {'align': 'right'}
        bg_color = {'bg_color': '#cccccc'}
        self.bold = self.workbook.add_format(bold)
        self.center = self.workbook.add_format(center)
        self.bold_center = self.workbook.add_format({**bold, **center})
        self.bold_right = self.workbook.add_format({**bold, **right})
        self.header_style = self.workbook.add_format({**bold, **bg_color})
        self.header_center_style = self.workbook.add_format({**bold, **center, **bg_color})

        # format data
        self.date_format = self.workbook.add_format({'num_format': 'dd/mm/yy', **center})
        self.time_format = self.workbook.add_format({'num_format': '[hh]:mm:ss', **center})
        self.price_format = self.workbook.add_format({'num_format': '[$R$-416] #,##0.00', **right})
        self.num_ust_format = self.workbook.add_format({'num_format': '0.0000', **center})
        self.price_ust_format = self.workbook.add_format({'num_format': '[$R$-416] #,##0.0000', **right})

    def write_row(self, row_data=[]):
        for col, data in enumerate(row_data):
            if isinstance(data, tuple):
                data, data_format, *data_merge = data
                if isinstance(data_format, dict):
                    data_format = self.workbook.add_format(data_format)
                self.worksheet.write(self.row, col, data, data_format)
            else:
                self.worksheet.write(self.row, col, data)
        self.row += 1

    def write_header(self):
        if self.org_logo:
            for row in range(12):
                self.worksheet.merge_range(f'A{row}:E{row}', '')
            self.worksheet.insert_image(
                self.row, 0, f'{settings.MEDIA_ROOT}{self.org_logo}', {'y_offset': 5})
            self.row += 11

        # title
        self.row += 1
        self.worksheet.merge_range(f'A{self.row}:E{self.row}', self.title, self.bold_center)

        # company title
        self.row += 1
        self.worksheet.merge_range(f'A{self.row}:E{self.row}', self.org_title, self.bold)

        # report time
        self.row += 1
        self.worksheet.merge_range(
            f'A{self.row}:B{self.row}', f'Período: {self.date_start} - {self.date_stop}', self.bold)
        self.worksheet.merge_range(
            f'D{self.row}:E{self.row}', f'Emissão: {self.today}', self.bold_right)
        self.write_row()

    def write_table_detail(self, company, ramal, call_data):
        # header company - ramal
        self.worksheet.merge_range(
            f'A{self.row + 1}:C{self.row + 1}', f'Cliente: {company}', self.bold)
        self.worksheet.write(
            f'D{self.row + 1}:D{self.row + 1}', f'RAMAL: {ramal}', self.bold_right)
        self.row += 1

        # header columns
        row_data = [
            ('Ramal',           self.header_style),
            ('Número Discado',  self.header_style),
            ('Tipo de Chamada', self.header_style),
            ('Tipo de Serviço', self.header_style),
            ('Classificação',   self.header_style),
            ('Data Início',     self.header_center_style),
            ('Hora Início',     self.header_center_style),
            ('Data Fim',        self.header_center_style),
            ('Hora Fim',        self.header_center_style),
            ('Duração',         self.header_center_style),
            ('Valor',           self.header_center_style)]
        self.write_row(row_data)

        # calls
        row_begin = self.row + 1
        for call in call_data['phonecall_list']:
            self.write_row([
                ramal,
                call['dialednumber'],
                CALLTYPE_MAP[call['calltype']],
                SERVICE_MAP[call['service']] if call['service'] else '',
                PABX_MAP[call['pabx']] if call['pabx'] else '',
                (call['startdate'], self.date_format),
                (call['starttime'], self.time_format),
                (call['stopdate'], self.date_format),
                (call['stoptime'], self.time_format),
                (timedelta(seconds=call['duration']), self.time_format),
                (call['billedamount'], self.price_format)])
        row_end = self.row

        # total
        self.write_row([
            '', '', '', '', '', '', '',
            ('TOTAL:', {'bold': True, 'align': 'right'}),
            (f'=ROWS(A{row_begin}:A{row_end})', self.center),
            (f'=SUM(J{row_begin}:J{row_end})', self.time_format),
            (f'=SUM(K{row_begin}:K{row_end})', self.price_format)])
        self.write_row()

    def write_basic_service_resume(self, bs_data):
        # header
        self.worksheet.merge_range(
            f'A{self.row + 1}:E{self.row + 1}', 'TOTAL SERVIÇOS BÁSICOS', self.header_center_style)
        self.row += 1

        # header columns
        self.write_row([
            '', '', '',
            ('QUANTIDADE',    self.header_center_style),
            ('VALOR PERÍODO', self.header_center_style)])
        self.worksheet.merge_range(f'A{self.row}:C{self.row}', 'SERVIÇO', self.header_center_style)

        # basic service
        row_begin = self.row + 1
        for basic_service, bs_name in BASIC_SERVICE_MAP.items():
            if basic_service in bs_data:
                data = bs_data[basic_service]
                self.write_row([
                    '', '', '',
                    (data['amount'], self.center),
                    (data['cost'],   self.price_format)])
                self.worksheet.merge_range(f'A{self.row}:C{self.row}', bs_name)
        row_end = self.row

        # total
        self.write_row([
            '', '', '',
            (f'=SUM(D{row_begin}:D{row_end})', self.center),
            (f'=SUM(E{row_begin}:E{row_end})', self.price_format)])
        self.worksheet.merge_range(f'A{self.row}:C{self.row}', 'TOTAL DOS SERVIÇOS BÁSICOS', self.bold)
        self.write_row()

        return f'E{self.row - 1}'

    def write_communication_service_resume(self, cs_data):
        # header
        self.worksheet.merge_range(
            f'A{self.row + 1}:E{self.row + 1}', 'TOTAL SERVIÇOS DE COMUNICAÇÃO', self.header_center_style)
        self.row += 1

        # header columns
        self.write_row([
            '', '',
            ('CHAMADAS',       self.header_center_style),
            ('TEMPO FATURADO', self.header_center_style),
            ('VALOR PERÍODO',  self.header_center_style)])
        self.worksheet.merge_range(f'A{self.row}:B{self.row}', 'SERVIÇO', self.header_center_style)

        # local
        self.worksheet.merge_range(f'A{self.row + 1}:E{self.row + 1}', 'DISCAGEM LOCAL', self.bold_center)
        self.row += 1

        row_begin = self.row + 1
        for calltype in [LOCAL, VC1]:
            if calltype in cs_data:
                data = cs_data[calltype]
                self.write_row([
                    '', '',
                    (data['count'],                             self.center),
                    (timedelta(seconds=data['billedtime_sum']), self.time_format),
                    (data['cost_sum'],                          self.price_format)])
                self.worksheet.merge_range(f'A{self.row}:B{self.row}', REPORT_CALLTYPE_MAP[calltype])
            else:
                self.write_row(['', '', (0, self.center), (0, self.time_format), (0, self.price_format)])
                self.worksheet.merge_range(f'A{self.row}:B{self.row}', REPORT_CALLTYPE_MAP[calltype])
        row_end = self.row

        # total local
        self.write_row([
            '', '',
            (f'=SUM(C{row_begin}:C{row_end})', self.center),
            (f'=SUM(D{row_begin}:D{row_end})', self.time_format),
            (f'=SUM(E{row_begin}:E{row_end})', self.price_format)])
        self.worksheet.merge_range(f'A{self.row}:B{self.row}', 'Total Discagem Local', self.bold)

        rows_count = f'C{self.row}'
        rows_billedtime = f'D{self.row}'
        rows_cost = f'E{self.row}'

        # national
        self.worksheet.merge_range(
            f'A{self.row + 1}:E{self.row + 1}', 'LONGA DISTÂNCIA NACIONAL', self.bold_center)
        self.row += 1

        row_begin = self.row + 1
        for calltype in [VC2, VC3, LDN]:
            if calltype in cs_data:
                data = cs_data[calltype]
                self.write_row([
                    '', '',
                    (data['count'],                             self.center),
                    (timedelta(seconds=data['billedtime_sum']), self.time_format),
                    (data['cost_sum'],                          self.price_format)])
                self.worksheet.merge_range(f'A{self.row}:B{self.row}', REPORT_CALLTYPE_MAP[calltype])
            else:
                self.write_row(['', '', (0, self.center), (0, self.time_format), (0, self.price_format)])
                self.worksheet.merge_range(f'A{self.row}:B{self.row}', REPORT_CALLTYPE_MAP[calltype])
        row_end = self.row

        # total national
        self.write_row([
            '', '',
            (f'=SUM(C{row_begin}:C{row_end})', self.center),
            (f'=SUM(D{row_begin}:D{row_end})', self.time_format),
            (f'=SUM(E{row_begin}:E{row_end})', self.price_format)])
        self.worksheet.merge_range(f'A{self.row}:B{self.row}', 'Total de Longa Distancia Nacional', self.bold)

        rows_count = f'{rows_count};C{self.row}'
        rows_billedtime = f'{rows_billedtime};D{self.row}'
        rows_cost = f'{rows_cost};E{self.row}'

        # international
        self.worksheet.merge_range(
            f'A{self.row + 1}:E{self.row + 1}', 'LONGA DISTÂNCIA INTERNACIONAL', self.bold_center)
        self.row += 1

        row_begin = self.row + 1
        for calltype in [LDI]:
            if calltype in cs_data:
                data = cs_data[calltype]
                self.write_row([
                    '', '',
                    (data['count'],                             self.center),
                    (timedelta(seconds=data['billedtime_sum']), self.time_format),
                    (data['cost_sum'],                          self.price_format)])
                self.worksheet.merge_range(f'A{self.row}:B{self.row}', REPORT_CALLTYPE_MAP[calltype])
            else:
                self.write_row(['', '', (0, self.center), (0, self.time_format), (0, self.price_format)])
                self.worksheet.merge_range(f'A{self.row}:B{self.row}', REPORT_CALLTYPE_MAP[calltype])
        row_end = self.row

        # total international
        self.write_row([
            '', '',
            (f'=SUM(C{row_begin}:C{row_end})', self.center),
            (f'=SUM(D{row_begin}:D{row_end})', self.time_format),
            (f'=SUM(E{row_begin}:E{row_end})', self.price_format)])
        self.worksheet.merge_range(
            f'A{self.row}:B{self.row}', 'Total de Longa Distancia Internacional', self.bold)

        rows_count = f'{rows_count};C{self.row}'
        rows_billedtime = f'{rows_billedtime};D{self.row}'
        rows_cost = f'{rows_cost};E{self.row}'

        # total
        self.write_row([
            '', '',
            (f'=SUM({rows_count})',      self.center),
            (f'=SUM({rows_billedtime})', self.time_format),
            (f'=SUM({rows_cost})',       self.price_format)])
        self.worksheet.merge_range(
            f'A{self.row}:B{self.row}', 'TOTAL DOS SERVIÇOS DE COMUNICAÇÃO', self.bold)
        self.write_row()

        return f'E{self.row - 1}'

    def write_basic_service_table_resume(self, basic_service):
        if not basic_service:
            return

        # header
        self.worksheet.merge_range(
            f'A{self.row + 1}:E{self.row + 1}', 'SERVIÇOS BÁSICOS', self.header_center_style)
        self.row += 1

        # header columns
        row_data = [
            '', '',
            ('VALOR UNITÁRIO', self.header_center_style),
            ('QUANTIDADE',     self.header_center_style),
            ('VALOR',          self.header_center_style)]
        self.write_row(row_data)
        self.worksheet.merge_range(f'A{self.row}:B{self.row}', 'SERVIÇO', self.header_center_style)

        # basic service
        row_begin = self.row + 1
        for service, service_name in BASIC_SERVICE_MAP.items():
            if service in basic_service:
                self.write_row([
                    '', '',
                    (basic_service[service]['price'],  self.price_format),
                    (basic_service[service]['amount'], self.center),
                    (basic_service[service]['cost'],   self.price_format)])
                self.worksheet.merge_range(f'A{self.row}:B{self.row}', service_name)
        row_end = self.row

        # total
        self.write_row([
            '', '', '',
            (f'=SUM(D{row_begin}:D{row_end})', self.center),
            (f'=SUM(E{row_begin}:E{row_end})', self.price_format)])
        self.worksheet.merge_range(f'A{self.row}:C{self.row}', 'TOTAL DOS SERVIÇOS BÁSICOS:', self.bold)
        self.write_row()

        return f'E{self.row - 1}'

    def write_call_data_table_resume(self, call_data):
        # header
        self.worksheet.merge_range(
            f'A{self.row + 1}:E{self.row + 1}', 'SERVIÇOS DE COMUNICAÇÃO', self.header_center_style)
        self.row += 1

        # header columns
        row_data = [
            ('SERVIÇO',        self.header_center_style),
            ('VALOR UNITÁRIO', self.header_center_style),
            ('CHAMADAS',       self.header_center_style),
            ('TEMPO FATURADO', self.header_center_style),
            ('VALOR',          self.header_center_style)]
        self.write_row(row_data)

        rows_count = ''
        rows_billedtime = ''
        rows_cost = ''

        # local
        if [calltype for calltype in [LOCAL, VC1] if calltype in call_data]:
            self.worksheet.merge_range(
                f'A{self.row + 1}:E{self.row + 1}', 'DISCAGEM LOCAL', self.bold_center)
            self.row += 1

            row_begin = self.row + 1
            for calltype in [LOCAL, VC1]:
                if calltype in call_data:
                    data = call_data[calltype]
                    self.write_row([
                        REPORT_CALLTYPE_MAP[calltype],
                        (data['price'],                             self.price_format),
                        (data['count'],                             self.center),
                        (timedelta(seconds=data['billedtime_sum']), self.time_format),
                        (data['cost_sum'],                          self.price_format)])
            row_end = self.row

            # total local
            self.write_row([
                '', '',
                (f'=SUM(C{row_begin}:C{row_end})', self.center),
                (f'=SUM(D{row_begin}:D{row_end})', self.time_format),
                (f'=SUM(E{row_begin}:E{row_end})', self.price_format)])
            self.worksheet.merge_range(
                f'A{self.row}:B{self.row}', 'Total Discagem Local', self.bold)

            rows_count = f'C{self.row}'
            rows_billedtime = f'D{self.row}'
            rows_cost = f'E{self.row}'

        # national
        if [calltype for calltype in [VC2, VC3, LDN] if calltype in call_data]:
            self.worksheet.merge_range(
                f'A{self.row + 1}:E{self.row + 1}', 'LONGA DISTÂNCIA NACIONAL', self.bold_center)
            self.row += 1

            row_begin = self.row + 1
            for calltype in [VC2, VC3, LDN]:
                if calltype in call_data:
                    data = call_data[calltype]
                    self.write_row([
                        REPORT_CALLTYPE_MAP[calltype],
                        (data['price'],                             self.price_format),
                        (data['count'],                             self.center),
                        (timedelta(seconds=data['billedtime_sum']), self.time_format),
                        (data['cost_sum'],                          self.price_format)])
            row_end = self.row

            # total national
            self.write_row([
                '', '',
                (f'=SUM(C{row_begin}:C{row_end})', self.center),
                (f'=SUM(D{row_begin}:D{row_end})', self.time_format),
                (f'=SUM(E{row_begin}:E{row_end})', self.price_format)])
            self.worksheet.merge_range(
                f'A{self.row}:B{self.row}', 'Total de Longa Distancia Nacional', self.bold)

            rows_count = f'{rows_count};C{self.row}'
            rows_billedtime = f'{rows_billedtime};D{self.row}'
            rows_cost = f'{rows_cost};E{self.row}'

        # international
        if [calltype for calltype in [LDI] if calltype in call_data]:
            self.worksheet.merge_range(
                f'A{self.row + 1}:E{self.row + 1}', 'LONGA DISTÂNCIA INTERNACIONAL', self.bold_center)
            self.row += 1

            row_begin = self.row + 1
            for calltype in [LDI]:
                if calltype in call_data:
                    data = call_data[calltype]
                    self.write_row([
                        REPORT_CALLTYPE_MAP[calltype],
                        (data['price'],                             self.price_format),
                        (data['count'],                             self.center),
                        (timedelta(seconds=data['billedtime_sum']), self.time_format),
                        (data['cost_sum'],                          self.price_format)])
            row_end = self.row

            # total international
            self.write_row([
                '', ''
                (f'=SUM(C{row_begin}:C{row_end})', self.center),
                (f'=SUM(D{row_begin}:D{row_end})', self.time_format),
                (f'=SUM(E{row_begin}:E{row_end})', self.price_format)])
            self.worksheet.merge_range(
                f'A{self.row}:B{self.row}', 'Total de Longa Distancia Internacional', self.bold)

            rows_count = f'{rows_count};C{self.row}'
            rows_billedtime = f'{rows_billedtime};D{self.row}'
            rows_cost = f'{rows_cost};E{self.row}'

        # total
        self.write_row([
            '', '',
            (f'=SUM({rows_count})' if rows_count else 0,           self.center),
            (f'=SUM({rows_billedtime})' if rows_billedtime else 0, self.time_format),
            (f'=SUM({rows_cost})' if rows_cost else 0,             self.price_format)])
        self.worksheet.merge_range(
            f'A{self.row}:B{self.row}', 'TOTAL DOS SERVIÇOS DE COMUNICAÇÃO:', self.bold)
        self.write_row()
        return f'E{self.row - 1}'

    def write_basic_service_table_ust_resume(self, table_name, bs_data, bs_type):
        if not bs_data:
            return

        # header
        self.worksheet.merge_range(
            f'A{self.row + 1}:E{self.row + 1}', table_name, self.header_center_style)
        self.row += 1

        # header columns
        row_data = [
            ('SERVIÇO',              self.header_center_style),
            ('VALOR UNITÁRIO (UST)', self.header_center_style),
            ('QUANTIDADE (UST)',     self.header_center_style),
            ('VALOR MENSAL (UST)',   self.header_center_style),
            ('VALOR MENSAL (R$)',    self.header_center_style)]
        self.write_row(row_data)

        # basic service
        row_begin = self.row + 1
        for service, service_name in BASIC_SERVICE_MAP.items():
            if service not in bs_type:
                continue
            if service in bs_data:
                self.write_row([
                    service_name,
                    (bs_data[service]['price'],    self.num_ust_format),
                    (bs_data[service]['amount'],   self.num_ust_format),
                    (bs_data[service]['cost_ust'], self.num_ust_format),
                    (bs_data[service]['cost'],     self.price_ust_format)])
            else:
                self.write_row([
                    service_name,
                    (0, self.num_ust_format),
                    (0, self.num_ust_format),
                    (0, self.num_ust_format),
                    (0, self.price_ust_format)])
        row_end = self.row

        # total
        self.write_row([
            '', '',
            (f'=SUM(C{row_begin}:C{row_end})', self.num_ust_format),
            (f'=SUM(D{row_begin}:D{row_end})', self.num_ust_format),
            (f'=SUM(E{row_begin}:E{row_end})', self.price_ust_format)])
        self.worksheet.merge_range(
            f'A{self.row}:B{self.row}', 'TOTAL DOS SERVIÇOS:', self.bold_center)
        self.write_row()

        return self.row - 1

    def write_communication_service_table_ust_resume(self, table_name, cs_data):
        # header
        self.worksheet.merge_range(
            f'A{self.row + 1}:E{self.row + 1}', table_name, self.header_center_style)
        self.row += 1

        # header columns
        self.write_row([
            ('SERVIÇO',              self.header_center_style),
            ('VALOR UNITÁRIO (UST)', self.header_center_style),
            ('QUANTIDADE (UST)',     self.header_center_style),
            ('VALOR MENSAL (UST)',   self.header_center_style),
            ('VALOR MENSAL (R$)',    self.header_center_style)])

        # local
        self.worksheet.merge_range(
            f'A{self.row + 1}:E{self.row + 1}', 'DISCAGEM LOCAL', self.bold_center)
        self.row += 1

        row_begin = self.row + 1
        for calltype in [LOCAL, VC1]:
            if calltype in cs_data:
                data = cs_data[calltype]
                amount = get_amount_ust(data['price_ust'], data['cost_ust_sum'])
                self.write_row([
                    REPORT_CALLTYPE_MAP[calltype],
                    (data['price_ust'],            self.num_ust_format),
                    (amount,                       self.num_ust_format),
                    (data['cost_ust_sum'],         self.num_ust_format),
                    (data['cost_sum'],             self.price_ust_format)])
            else:
                self.write_row([
                    REPORT_CALLTYPE_MAP[calltype],
                    (0, self.num_ust_format),
                    (0, self.num_ust_format),
                    (0, self.num_ust_format),
                    (0, self.price_ust_format)])
        row_end = self.row

        # total local
        self.write_row([
            '', '',
            (f'=SUM(C{row_begin}:C{row_end})', self.num_ust_format),
            (f'=SUM(D{row_begin}:D{row_end})', self.num_ust_format),
            (f'=SUM(E{row_begin}:E{row_end})', self.price_ust_format)])
        self.worksheet.merge_range(
            f'A{self.row}:B{self.row}', 'TOTAL DISCAGEM LOCAL:', self.bold)

        rows_count = f'C{self.row}'
        rows_cost_ust = f'D{self.row}'
        rows_cost = f'E{self.row}'

        # national
        self.worksheet.merge_range(
            f'A{self.row + 1}:E{self.row + 1}', 'LONGA DISTÂNCIA NACIONAL', self.bold_center)
        self.row += 1

        row_begin = self.row + 1
        for calltype in [VC2, VC3, LDN]:
            if calltype in cs_data:
                data = cs_data[calltype]
                amount = get_amount_ust(data['price_ust'], data['cost_ust_sum'])
                self.write_row([
                    REPORT_CALLTYPE_MAP[calltype],
                    (data['price_ust'],            self.num_ust_format),
                    (amount,                       self.num_ust_format),
                    (data['cost_ust_sum'],         self.num_ust_format),
                    (data['cost_sum'],             self.price_ust_format)])
            else:
                self.write_row([
                    REPORT_CALLTYPE_MAP[calltype],
                    (0, self.num_ust_format),
                    (0, self.num_ust_format),
                    (0, self.num_ust_format),
                    (0, self.price_ust_format)])
        row_end = self.row

        # total national
        self.write_row([
            '', '',
            (f'=SUM(C{row_begin}:C{row_end})', self.num_ust_format),
            (f'=SUM(D{row_begin}:D{row_end})', self.num_ust_format),
            (f'=SUM(E{row_begin}:E{row_end})', self.price_ust_format)])
        self.worksheet.merge_range(
            f'A{self.row}:B{self.row}', 'TOTAL LONGA DISTÂNCIA NACIONAL:', self.bold)

        rows_count = f'{rows_count};C{self.row}'
        rows_cost_ust = f'{rows_cost_ust};D{self.row}'
        rows_cost = f'{rows_cost};E{self.row}'

        # international
        self.worksheet.merge_range(
            f'A{self.row + 1}:E{self.row + 1}', 'LONGA DISTÂNCIA INTERNACIONAL', self.bold_center)
        self.row += 1

        row_begin = self.row + 1
        for calltype in [LDI]:
            if calltype in cs_data:
                data = cs_data[calltype]
                amount = get_amount_ust(data['price_ust'], data['cost_ust_sum'])
                self.write_row([
                    REPORT_CALLTYPE_MAP[calltype],
                    (data['price_ust'],            self.num_ust_format),
                    (amount,                       self.num_ust_format),
                    (data['cost_ust_sum'],         self.num_ust_format),
                    (data['cost_sum'],             self.price_ust_format)])
            else:
                self.write_row([
                    REPORT_CALLTYPE_MAP[calltype],
                    (0, self.num_ust_format),
                    (0, self.num_ust_format),
                    (0, self.num_ust_format),
                    (0, self.price_ust_format)])
        row_end = self.row

        # total international
        self.write_row([
            '', '',
            (f'=SUM(C{row_begin}:C{row_end})', self.num_ust_format),
            (f'=SUM(D{row_begin}:D{row_end})', self.num_ust_format),
            (f'=SUM(E{row_begin}:E{row_end})', self.price_ust_format)])
        self.worksheet.merge_range(
            f'A{self.row}:B{self.row}', 'TOTAL LONGA DISTÂNCIA INTERNACIONAL:', self.bold)

        rows_count = f'{rows_count};C{self.row}'
        rows_cost_ust = f'{rows_cost_ust};D{self.row}'
        rows_cost = f'{rows_cost};E{self.row}'

        # total
        self.write_row([
            '', '',
            (f'=SUM({rows_count})',    self.num_ust_format),
            (f'=SUM({rows_cost_ust})', self.num_ust_format),
            (f'=SUM({rows_cost})',     self.price_ust_format)])
        self.worksheet.merge_range(
            f'A{self.row}:B{self.row}', 'TOTAL DOS SERVIÇOS:', self.bold_center)
        self.write_row()

        return self.row - 1

    def build_detail_report(self, context):
        self.worksheet = self.workbook.add_worksheet('Relatório Detalhado')
        self.worksheet.set_column('A:B', 20)
        self.worksheet.set_column('C:C', 40)
        self.worksheet.set_column('D:E', 30)
        self.worksheet.set_column('F:K', 12)
        self.row = 0

        self.write_header()
        for company, phonecall_data in context['phonecall_data'].items():
            for ramal, call_data in phonecall_data.items():
                self.write_table_detail(company, ramal, call_data)

    def build_resume_report(self, context):
        self.worksheet = self.workbook.add_worksheet('Relatório Resumido')
        self.worksheet.set_column('A:A', 65)
        self.worksheet.set_column('B:E', 20)
        self.row = 0

        self.write_header()
        for company, call_data in context['data']['company_data'].items():
            # header company
            self.worksheet.merge_range(
                f'A{self.row + 1}:E{self.row + 1}', company, self.bold_center)
            self.row += 1

            cells_company_total = []

            if 'basic_service' in call_data:
                cell_company_bs_total = self.write_basic_service_table_resume(call_data['basic_service'])
                if cell_company_bs_total:
                    cells_company_total.append(cell_company_bs_total)

            cell_company_cs_total = self.write_call_data_table_resume(call_data)
            if cell_company_cs_total:
                cells_company_total.append(cell_company_cs_total)

            cells_company_total = ';'.join(cells_company_total)

            self.worksheet.merge_range(f'A{self.row + 1}:E{self.row + 1}', 'TOTAL', self.header_center_style)
            self.row += 1

            cell_company_total = f'=SUM({cells_company_total})' if cells_company_total else 0
            self.worksheet.merge_range(f'A{self.row + 1}:D{self.row + 1}', 'TOTAL DOS SERVIÇOS', self.bold)
            self.worksheet.write(f'E{self.row + 1}:E{self.row + 1}', cell_company_total, self.price_format)
            self.write_row()
            self.write_row()

        cell_bs_total = self.write_basic_service_resume(context['data']['basic_service'])
        cell_cs_total = self.write_communication_service_resume(context['data']['communication_service'])

        # total
        self.worksheet.merge_range(f'A{self.row + 1}:E{self.row + 1}', 'TOTAL', self.header_center_style)
        self.row += 1

        cells_total = f'{cell_bs_total};{cell_cs_total}'

        self.worksheet.merge_range(f'A{self.row + 1}:D{self.row + 1}', 'TOTAL DOS SERVIÇOS', self.bold)
        self.worksheet.write(f'E{self.row + 1}:E{self.row + 1}', f'=SUM({cells_total})')

    def build_ust_resume_report(self, context):
        self.worksheet = self.workbook.add_worksheet('Relatório Resumido UST')
        self.worksheet.set_column('A:A', 65)
        self.worksheet.set_column('B:E', 25)
        self.row = 0

        self.write_header()

        row_bs_a_total = self.write_basic_service_table_ust_resume(
            'TABELA 1 – SERVIÇOS DE DISPONIBILIZAÇÃO DE ACESSO A COMUNICAÇÃO VOIP',
            context['basic_service'],
            BASIC_SERVICE_ACCESS)

        row_bs_mo_total = self.write_basic_service_table_ust_resume(
            'TABELA 2 –SERVIÇOS DE CONTACT CENTER',
            context['basic_service'],
            BASIC_SERVICE_MO)

        row_cs_total = self.write_communication_service_table_ust_resume(
            'TABELA 3 - SERVIÇOS MENSAL EXECUTADOS POR DEMANDA (MINUTAGEM)',
            context['communication_service'])

        self.write_row()

        # total
        self.row += 1
        self.worksheet.merge_range(f'A{self.row}:E{self.row}', 'TOTAL', self.header_center_style)

        cost_ust_total = f'=SUM(D{row_bs_a_total};D{row_bs_mo_total};D{row_cs_total})'
        self.row += 1
        self.worksheet.merge_range(f'A{self.row}:D{self.row}', 'Valor Mensal (UST) (t1+t2+t3+t4+t5):', self.bold)
        self.worksheet.write(f'E{self.row}:E{self.row}', cost_ust_total, self.num_ust_format)

        cost_total = f'=SUM(E{row_bs_a_total};E{row_bs_mo_total};E{row_cs_total})'
        self.row += 1
        self.worksheet.merge_range(f'A{self.row}:D{self.row}', 'Valor Mensal (R$) (t1+t2+t3+t4+t5):', self.bold)
        self.worksheet.write(f'E{self.row}:E{self.row}', cost_total, self.price_ust_format)

    def close(self):
        self.workbook.close()
        self.xls_file.seek(0)

    def get_file(self):
        self.close()
        return self.xls_file
