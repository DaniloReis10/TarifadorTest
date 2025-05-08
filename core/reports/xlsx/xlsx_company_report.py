# python
import io

from datetime import date
from datetime import timedelta

# django
from django.conf import settings

# third party
import xlsxwriter

# project
from charges.constants import BASIC_SERVICE_MAP
from phonecalls.constants import CALLTYPE_CHOICES
from phonecalls.constants import REPORT_CALLTYPE_MAP
from phonecalls.constants import VC1, VC2, VC3, LOCAL, LDN, LDI

CALLTYPE_MAP = dict(CALLTYPE_CHOICES)


class XLSXCompanyReport(object):

    def __init__(self, date_start, date_stop, title, company):
        self.org = company.organization
        self.company = company
        self.date_start = date_start
        self.date_stop = date_stop
        self.today = date.today().strftime('%d/%m/%Y')
        self.title = title
        self.company_title = \
            f'{company.name.upper()} - {company.description}' if company.description else company.name.upper()
        self.company_logo = company.logo.name if company.logo else None
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
        self.price_format = self.workbook.add_format({'num_format': '[$R$-416] #,##0.00', **right}) #changed format here

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
        self.worksheet.merge_range(f'A{self.row}:E{self.row}', self.company_title, self.bold)

        # report time
        self.row += 1
        self.worksheet.merge_range(
            f'A{self.row}:B{self.row}', f'Período: {self.date_start} - {self.date_stop}', self.bold)
        self.worksheet.merge_range(
            f'D{self.row}:E{self.row}', f'Emissão: {self.today}', self.bold_right)
        self.write_row()

    def write_table_detail(self, ramal, call_data):
        # header ramal
        self.worksheet.merge_range(
            f'A{self.row + 1}:B{self.row + 1}', f'RAMAL: {ramal}', self.bold)
        self.row += 1

        # header columns
        row_data = [
            ('Ramal',           self.header_style),
            ('Número Discado',  self.header_style),
            ('Tipo de Chamada', self.header_style),
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
                (call['startdate'], self.date_format),
                (call['starttime'], self.time_format),
                (call['stopdate'], self.date_format),
                (call['stoptime'], self.time_format),
                (timedelta(seconds=call['duration']), self.time_format),
                (call['billedamount'], self.price_format)])
        row_end = self.row

        # total
        self.write_row([
            '', '', '', '', '',
            ('TOTAL:', {'bold': True, 'align': 'right'}),
            (f'=ROWS(A{row_begin}:A{row_end})', self.center),
            (f'=SUM(H{row_begin}:H{row_end})', self.time_format),
            (f'=SUM(I{row_begin}:I{row_end})', self.price_format)])
        self.write_row()

    def write_table_resume_basic_service(self, basic_service):
        if not basic_service:
            return

        # header
        self.row += 1
        self.worksheet.merge_range(f'A{self.row}:E{self.row}', 'SERVIÇOS BASICOS', self.header_center_style)

        # header columns
        row_data = [
            '', '',
            ('VALOR UNITÁRIO', self.header_center_style),
            ('QUANTIDADE',     self.header_center_style),
            ('VALOR',  self.header_center_style)]
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

    def write_table_resume_call_service(self, cs_data):
        # header
        self.row += 1
        self.worksheet.merge_range(f'A{self.row}:E{self.row}', 'SERVIÇOS DE COMUNICAÇÃO', self.header_center_style)

        # header columns
        row_data = [
            ('SERVIÇO',        self.header_center_style),
            ('VALOR UNITÁRIO', self.header_center_style),
            ('CHAMADAS',       self.header_center_style),
            ('TEMPO FATURADO', self.header_center_style),
            ('VALOR',          self.header_center_style)]
        self.write_row(row_data)

        # local
        self.row += 1
        self.worksheet.merge_range(f'A{self.row}:E{self.row}', 'DISCAGEM LOCAL', self.bold_center)

        row_begin = self.row + 1
        for calltype in [LOCAL, VC1]:
            calltype_name = REPORT_CALLTYPE_MAP[calltype]
            if calltype in cs_data:
                data = cs_data[calltype]
                self.write_row([
                    calltype_name,
                    (data['price'],                             self.price_format),
                    (data['count'],                             self.center),
                    (timedelta(seconds=data['billedtime_sum']), self.time_format),
                    (data['cost_sum'],                          self.price_format)])
            else:
                self.write_row([
                    calltype_name,
                    (0, self.price_format), (0, self.center), (0, self.time_format), (0, self.price_format)])
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
        self.row += 1
        self.worksheet.merge_range(f'A{self.row}:E{self.row}', 'LONGA DISTÂNCIA NACIONAL', self.bold_center)

        row_begin = self.row + 1
        for calltype in [VC2, VC3, LDN]:
            if calltype in cs_data:
                data = cs_data[calltype]
                self.write_row([
                    REPORT_CALLTYPE_MAP[calltype],
                    (data['price'],                             self.price_format),
                    (data['count'],                             self.center),
                    (timedelta(seconds=data['billedtime_sum']), self.time_format),
                    (data['cost_sum'],                          self.price_format)])
            else:
                self.write_row([
                    REPORT_CALLTYPE_MAP[calltype],
                    (0, self.price_format), (0, self.center), (0, self.time_format), (0, self.price_format)])
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
        self.row += 1
        self.worksheet.merge_range(f'A{self.row}:E{self.row}', 'LONGA DISTÂNCIA INTERNACIONAL', self.bold_center)

        row_begin = self.row + 1
        for calltype in [LDI]:
            if calltype in cs_data:
                data = cs_data[calltype]
                self.write_row([
                    REPORT_CALLTYPE_MAP[calltype],
                    (data['price'],                             self.price_format),
                    (data['count'],                             self.center),
                    (timedelta(seconds=data['billedtime_sum']), self.time_format),
                    (data['cost_sum'],                          self.price_format)])
            else:
                self.write_row([
                    REPORT_CALLTYPE_MAP[calltype],
                    (0, self.price_format), (0, self.center), (0, self.time_format), (0, self.price_format)])
        row_end = self.row

        # total international
        self.write_row([
            '', '',
            (f'=SUM(C{row_begin}:C{row_end})', self.center),
            (f'=SUM(D{row_begin}:D{row_end})', self.time_format),
            (f'=SUM(E{row_begin}:E{row_end})', self.price_format)])
        self.worksheet.merge_range(f'A{self.row}:B{self.row}', 'Total de Longa Distancia Internacional', self.bold)

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

    def build_detail_report(self, context):
        self.worksheet = self.workbook.add_worksheet('Relatório Detalhado')
        self.worksheet.set_column('A:B', 20)
        self.worksheet.set_column('C:C', 40)
        self.worksheet.set_column('D:I', 12)
        self.row = 0

        self.write_header()
        for ramal, call_data in context['phonecall_data'].items():
            self.write_table_detail(ramal, call_data)

    def build_resume_report(self, context):
        self.worksheet = self.workbook.add_worksheet('Relatório Resumido')
        self.worksheet.set_column('A:E', 30)
        self.row = 0

        self.write_header()
        cell_bs_total = self.write_table_resume_basic_service(context['basic_service'])
        cell_cs_total = self.write_table_resume_call_service(context['communication_service'])

        # total
        self.row += 1
        self.worksheet.merge_range(f'A{self.row}:E{self.row}', 'TOTAL', self.header_center_style)

        self.row += 1
        self.worksheet.merge_range(f'A{self.row}:D{self.row}', 'TOTAL DOS SERVIÇOS:', self.bold)
        self.worksheet.write(f'E{self.row}:E{self.row}', f'=SUM({cell_bs_total};{cell_cs_total})')

    def close(self):
        self.workbook.close()
        self.xls_file.seek(0)

    def get_file(self):
        self.close()
        return self.xls_file
