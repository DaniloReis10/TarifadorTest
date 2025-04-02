# python
import io
import os

# from cgi import escape
from datetime import datetime

# django
from django.conf import settings
from django.contrib.staticfiles import finders

# third party
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Table
from reportlab.platypus import TableStyle
from reportlab.rl_config import TTFSearchPath

# project
from centers.utils import make_price
from charges.constants import BASIC_SERVICE_MAP, BASIC_SERVICE_MAP_NEW, BASIC_SERVICE_MAP_PMF
from core.utils import time_format
from phonecalls.constants import CALLTYPE_CHOICES
from phonecalls.constants import VC1, VC2, VC3, LOCAL, LDN

# local
from .utils import get_tj_calltype_title
from phonecalls.constants import OLD_CONTRACT,  NEW_CONTRACT


from charges.constants import LEVEL_1_ACCESS_SERVICE
from charges.constants import LEVEL_2_ACCESS_SERVICE
from charges.constants import LEVEL_3_ACCESS_SERVICE
from charges.constants import LEVEL_4_ACCESS_SERVICE
from charges.constants import LEVEL_5_ACCESS_SERVICE
from charges.constants import LEVEL_6_ACCESS_SERVICE
from charges.constants import WIFI_ACCESS_SERVICE
from charges.constants import MO_AUTO_ANSWER_CHANNEL_AND_MESSAGES
from charges.constants import MO_BASIC_CONTACT_CENTER_PLATFORM
from charges.constants import MO_BASIC_RECORDING_PLATFORM
from charges.constants import MO_REAL_TIME_TRACKING
from charges.constants import MO_RECORDING_POSITION
from charges.constants import MO_RECORDING_SUPERVISOR
from charges.constants import MO_SERVICE_POSITION
from charges.constants import MO_SUPERVISOR
from charges.constants import SOFTWARE_ACCESS_SERVICE
from charges.constants import SOFTWARE_EXTENSION_SERVICE
from charges.constants import WIRELESS_ACCESS_SERVICE
from Equipments.models import ContractBasicServices

CALLTYPE_MAP = dict(CALLTYPE_CHOICES)

BASIC_SERVICE_MAP_MAPPING = {
    LEVEL_1_ACCESS_SERVICE: 'LEVEL_1_ACCESS_SERVICE',
    LEVEL_2_ACCESS_SERVICE: 'LEVEL_2_ACCESS_SERVICE',
    LEVEL_3_ACCESS_SERVICE: 'LEVEL_3_ACCESS_SERVICE',
    LEVEL_4_ACCESS_SERVICE: 'LEVEL_4_ACCESS_SERVICE',
    LEVEL_5_ACCESS_SERVICE: 'LEVEL_5_ACCESS_SERVICE',
    LEVEL_6_ACCESS_SERVICE: 'LEVEL_6_ACCESS_SERVICE',
    WIRELESS_ACCESS_SERVICE: 'WIRELESS_ACCESS_SERVICE',
    SOFTWARE_ACCESS_SERVICE: 'SOFTWARE_ACCESS_SERVICE',
    SOFTWARE_EXTENSION_SERVICE: 'SOFTWARE_EXTENSION_SERVICE',
    MO_BASIC_CONTACT_CENTER_PLATFORM: 'MO_BASIC_CONTACT_CENTER_PLATFORM',
    MO_BASIC_RECORDING_PLATFORM: 'MO_BASIC_RECORDING_PLATFORM',
    MO_SERVICE_POSITION: 'MO_SERVICE_POSITION',
    MO_SUPERVISOR: 'MO_SUPERVISOR',
    MO_REAL_TIME_TRACKING: 'MO_REAL_TIME_TRACKING',
    MO_AUTO_ANSWER_CHANNEL_AND_MESSAGES: 'MO_AUTO_ANSWER_CHANNEL_AND_MESSAGES',
    MO_RECORDING_POSITION: 'MO_RECORDING_POSITION',
    MO_RECORDING_SUPERVISOR: 'MO_RECORDING_SUPERVISOR',
    WIFI_ACCESS_SERVICE: 'WIFI_ACCESS_SERVICE'
}


def escape(data):
    return data


class SystemReport(object):

    def __init__(self, dateBegin, dateEnd, reportTitle, company, formatPage=1):
        self.org = company.organization
        self.company = company
        self._dateBegin = dateBegin
        self._dateEnd = dateEnd
        self._issueDate = datetime.now().strftime('%d/%m/%Y')
        self._reportTitle = reportTitle
        self._companyTitle = \
            f'{company.name.upper()} - {company.description}' \
            if company.description else company.name.upper()
        self._companyLogo = company.logo.name if company.logo else None
        self._orgLogo = self.org.settings.logo.name if self.org.settings.logo else None
        self._buffer = io.BytesIO()
        if formatPage == 1:
            self._doc = SimpleDocTemplate(
                self._buffer,
                rightMargin=35,
                leftMargin=35,
                topMargin=125,
                bottomMargin=56)
        else:
            self._doc = SimpleDocTemplate(
                self._buffer,
                rightMargin=35,
                leftMargin=35,
                topMargin=135,
                bottomMargin=56)

        TTFSearchPath.append(finders.find(os.path.join('fonts')))
        pdfmetrics.registerFont(TTFont('Sans',  "Microsoft Sans Serif.ttf"))
        self.style = ParagraphStyle(
            name='Sans',
            fontName='Sans',
            fontSize=9)
        self._width, self._height = self._doc.pagesize
        self._story = []

    def header(self, canvas, doc):
        header_list = []

        if self.org.id ==2:
            width = 250
        else:
            width = 550
        if self._orgLogo:
            header_list.append({
                'text': f'<img src="{settings.MEDIA_ROOT}{self._orgLogo}" width = "{width}"'
                        'height="80" valign="top"/>', #86
                'width': 20,
                'height': self._height - 20})
        header_list.append({
            'text': f'<font size=8><b>Período: { self._dateBegin }'
                    f' - { self._dateEnd }</b></font>',
            'width': 30,
            'height': self._height - 135})
        header_list.append({
            'text': f'<font size=8><b>Emissão: { self._issueDate }</b></font>',
            'width': self._width - 105,
            'height': self._height - 135})

        for header_data in header_list:
            insertParagraph = Paragraph(header_data['text'], style=self.style)
            insertParagraph.wrapOn(canvas, self._width, self._height)
            insertParagraph.drawOn(canvas, header_data['width'], header_data['height'])

    def header_resume(self, canvas, doc):
        header_list = []

        if self.org.id ==2:
            width = 250
        else:
            width = 550
        if self._orgLogo:
            header_list.append({
                'text': f'<img src="{settings.MEDIA_ROOT}{self._orgLogo}" width = "{width}"'
                        'height="66" valign="top"/>',
                'width': 20,
                'height': self._height-20})
        header_list.append({
            'text': f'<font size=10><b>Período: { self._dateBegin }'
                    f' - { self._dateEnd }</b></font>',
            'width': 30,
            'height': self._height-120})
        header_list.append({
            'text': f'<font size=10><b>Emissão: { self._issueDate }</b></font>',
            'width': self._width-125,
            'height': self._height-120})

        for header_data in header_list:
            insertParagraph = Paragraph(header_data['text'], style=self.style)
            insertParagraph.wrapOn(canvas, self._width, self._height)
            insertParagraph.drawOn(canvas, header_data['width'], header_data['height'])

    def title(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Sans', 12)
        canvas.drawCentredString(
            self._width / 2.0,
            self._height - 102,
            f"{escape(self._reportTitle)}")
        canvas.saveState()
        canvas.setFont('Sans', 10)
        canvas.drawString(
            30,
            self._height - 117,
            f"{escape(self._companyTitle)}")

    def title_resume(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Sans', 12)
        canvas.drawString(
            30,
            self._height - 101,
            escape(self._reportTitle + ': ' + self._companyTitle))

    def footer(self, canvas, doc):
        """
        Create a footer
        """

        title = [
            f'{self.org.settings.street}, {self.org.settings.street_number} - '
            f'{self.org.settings.neighborhood}, {self.org.settings.zip_code}',
            '',  # Telefone
            f'{self.org.settings.city.name if self.org.settings.city else ""} - '
            f'{self.org.settings.state.name if self.org.settings.state else ""}']
        canvas.saveState()
        canvas.setFont('Sans', 8)
        height_footer = 45
        for i in range(0, 3):
            canvas.drawCentredString(self._width / 2.0, height_footer, escape(title[i]))
            height_footer -= 10

    def create_header_and_footer(self, canvas, doc):
        """
        Add the header, title and footer to each page
        """
        self.header(canvas, doc)
        self.title(canvas, doc)
        self.footer(canvas, doc)

    def create_header_and_footer_resume(self, canvas, doc):
        """
        Add the header, title and footer to each page
        """
        self.header_resume(canvas, doc)
        self.title_resume(canvas, doc)
        self.footer(canvas, doc)

    def insert_title_table(self, title: str):
        """
        Add table title
        """
        p = Paragraph(f"<font size=9><b>{ escape(title) }</b></font><br/>", style=self.style)
        self._story.append(p)

    def space_between_tables(self):
        """
        Space between tables
        """
        p = Paragraph("<br/><br/>", style=self.style)
        self._story.append(p)

    def create_table(self, data):
        """
        Creating the table header
        """

        array_tblstyle = [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
            ('FONTSIZE', (0, 0), (-1, -1), 8),  # middle column
            ('FONTNAME', (0, 0), (-1, -1), 'Sans'),  # middle column
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#cccccc')),
            ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
        tblstyle = TableStyle(array_tblstyle)
        thead = [data['thead']]
        tbl = Table(
            thead,
            colWidths=data['len_col'],
            rowHeights=[20 for x in range(len(thead))])
        tbl.setStyle(tblstyle)
        self._story.append(tbl)

        # Inserting the data in the table
        cont = 0
        array_tblstyle = []
        for align in data['align']:
            array_tblstyle.append(('ALIGN', (cont, 0), (cont, -1), align))
            cont += 1

        array_tblstyle.append(('VALIGN', (0, 0), (-1, -1), 'MIDDLE'))
        array_tblstyle.append(('FONTSIZE', (0, 0), (-1, -1), 8))
        array_tblstyle.append(('FONTNAME', (0, 0), (-1, -1), 'Sans'))
        array_tblstyle.append(('BACKGROUND', (0, 0), (-1, -1), HexColor('#ffffff')))
        array_tblstyle.append(('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white))
        array_tblstyle.append(('BOX', (0, 0), (-1, -1), 0.50, colors.white))
        tblstyle = TableStyle(array_tblstyle)

        tbl = Table(
            data['values'],
            colWidths=data['len_col'],
            rowHeights=[22 for x in range(len(data['values']))])
        tbl.setStyle(tblstyle)
        self._story.append(tbl)

    def close(self):
        self._doc.build(
            self._story,
            onFirstPage=self.create_header_and_footer,
            onLaterPages=self.create_header_and_footer)
        value = self._buffer.getvalue()
        self._buffer.close()
        return value

    def close_resume(self):
        self._doc.build(
            self._story,
            onFirstPage=self.create_header_and_footer_resume,
            onLaterPages=self.create_header_and_footer_resume)
        value = self._buffer.getvalue()
        self._buffer.close()
        return value

    def get_value(self):
        self._buffer.getvalue()

    def make_phonecall_table(self, context):
        for ramal, phonecall_data in context['phonecall_data'].items():
            self.insert_title_table(title=f'RAMAL: {ramal}')
            size = (self._width - 50) / 7
            data = {
                'thead':   ['Ramal', 'Número Discado', 'Tipo de Chamada',
                            'Data/Hora Início', 'Data/Hora Fim', 'Duração', 'Valor'],
                'len_col': [size - 15, size - 15, size + 90, size, size, size - 30, size - 30],
                'align':   ['CENTER', 'CENTER', 'CENTER', 'CENTER', 'CENTER', 'CENTER', 'CENTER'],
                'values':  []}
            for phonecall in phonecall_data['phonecall_list']:
                calltype_title = CALLTYPE_MAP[phonecall['calltype']]
                if self.company.slug == 'tj' or self.company.slug == 'sema':
                    calltype_title = get_tj_calltype_title(phonecall['calltype'])

                data['values'].append([
                    ramal,
                    phonecall['dialednumber'],
                    calltype_title,
                    f"{phonecall['startdate'].strftime('%d/%m/%Y')} {phonecall['starttime'].strftime('%H:%M:%S')}",
                    f"{phonecall['stopdate'].strftime('%d/%m/%Y')} {phonecall['stoptime'].strftime('%H:%M:%S')}",
                    time_format(phonecall['duration']),
                    f"R$ {make_price(phonecall['billedamount'])}"])
            data['values'].append([
                '',
                '',
                '',
                'TOTAL:',
                phonecall_data['count'],
                time_format(phonecall_data['billedtime_sum']),
                f"R$ {make_price(phonecall_data['cost_sum'])}"])
            self.create_table(data)
            self.space_between_tables()
        return self.close()

    def make_phonecall_resume_table(self, context):
        service_amount = 0
        service_cost = 0
        if (context['basic_service'] and len(context['basic_service']) > 0) or \
            (context['prop'] and len(context['prop']) > 0):
            array_tblstyle = [
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#cccccc')),
                ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
            tblstyle = TableStyle(array_tblstyle)
            thead = [['SERVIÇOS BASICOS']]
            size = self._width - 50
            tbl = Table(
                thead,
                colWidths=[size],
                rowHeights=[20 for x in range(len(thead))])
            tbl.setStyle(tblstyle)
            self._story.append(tbl)

            array_tblstyle = [
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#cccccc')),
                ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
            tblstyle = TableStyle(array_tblstyle)
            thead = [['SERVIÇO', 'VALOR UNITÁRIO', 'QUANTIDADE', 'VALOR PERÍODO']]
            size = (self._width - 50) / 5
            tbl = Table(
                thead,
                colWidths=[size*2, size, size, size],
                rowHeights=[20 for x in range(len(thead))])
            tbl.setStyle(tblstyle)
            self._story.append(tbl)

            array_tblstyle = [
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                ('FONTSIZE', (0, 0), (0, -1), 7),  # middle column
                ('FONTSIZE', (1, 0), (-1, -1), 9),  # middle column
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#ffffff')),
                ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
            tblstyle = TableStyle(array_tblstyle)
            thead = []
            if self.org.id == 2:
                basic_map = BASIC_SERVICE_MAP_PMF
            else:
                if context['contract_version'] == NEW_CONTRACT:
                    basic_map = BASIC_SERVICE_MAP_NEW
                else:
                    basic_map = BASIC_SERVICE_MAP

    #---------------
            service_amount = 0
            service_cost = 0
            call_company_map = context['basic_service']
            call_prop_map = context['prop']
            #deal with legacy
            if self.org.id == 1 and context['contract_version'] == OLD_CONTRACT:
                for key, value in basic_map.items():
                            if key in context['basic_service']:
                                service_amount += context['basic_service'][key]['amount']
                                service_cost += context['basic_service'][key]['cost']
                                thead.append([
                                    value,
                                    f"R$ {make_price(context['basic_service'][key]['price'])}",
                                    str(context['basic_service'][key]['amount']),
                                    f"R$ {make_price(context['basic_service'][key]['cost'])}"])
            else:
                #Here I may need to consider not only company but also contract number
                contract_list = ContractBasicServices.objects.filter(organization=context['organization'])
                for contract in contract_list:
                    if contract.legacyID in call_company_map and call_company_map[contract.legacyID]['amount'] != 0:
                        service_amount += call_company_map[contract.legacyID]['amount']
                        service_cost += call_company_map[contract.legacyID]['cost']
                        value_mask = make_price(call_company_map[contract.legacyID]['cost'])
                        thead.append([
                            contract.description,
                            f"R$ {make_price(call_company_map[contract.legacyID]['price'])}",
                            str(call_company_map[contract.legacyID]['amount']),
                            f"R$ {value_mask}"])
                    if contract.legacyID in call_prop_map and call_prop_map[contract.legacyID]['amount'] != 0:
                        service_amount += call_prop_map[contract.legacyID]['amount']
                        service_cost += call_prop_map[contract.legacyID]['cost']
                        value_mask = make_price(call_prop_map[contract.legacyID]['cost'])
                        thead.append([
                            contract.description + '  PRORATA',
                            f"R$ {make_price(call_prop_map[contract.legacyID]['price'])}",
                            str(call_prop_map[contract.legacyID]['amount']),
                            f"R$ {value_mask}"])
#------------------------


#

            size = (self._width - 50) / 5
            tbl = Table(
                thead,
                colWidths=[size * 2, size, size, size],
                rowHeights=[20 for x in range(len(thead))])
            tbl.setStyle(tblstyle)
            self._story.append(tbl)

            array_tblstyle = [
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),   # 1 column
                ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#cccccc')),
                ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
            tblstyle = TableStyle(array_tblstyle)
            thead = [[
                'TOTAL DOS SERVIÇOS BASICOS',
                str(service_amount),
                f"R$ {make_price(service_cost)}"]]
            size = (self._width - 50) / 5
            tbl = Table(
                thead,
                colWidths=[size * 3, size, size],
                rowHeights=[20 for x in range(len(thead))])
            tbl.setStyle(tblstyle)
            self._story.append(tbl)
            self.space_between_tables()

        array_tblstyle = [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#cccccc')),
            ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
        tblstyle = TableStyle(array_tblstyle)
        thead = [['SERVIÇOS DE COMUNICAÇÃO']]
        size = self._width - 50
        tbl = Table(
            thead,
            colWidths=[size],
            rowHeights=[20 for x in range(len(thead))])
        tbl.setStyle(tblstyle)
        self._story.append(tbl)

        array_tblstyle = [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#cccccc')),
            ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
        tblstyle = TableStyle(array_tblstyle)
        thead = [['SERVIÇO', 'VALOR UNITÁRIO', 'QUANTIDADE', 'VALOR']]
        size = (self._width - 50) / 5
        tbl = Table(
            thead,
            colWidths=[size*2, size, size, size],
            rowHeights=[20 for x in range(len(thead))])
        tbl.setStyle(tblstyle)
        self._story.append(tbl)

        cost_vc1 = cost_vc2 = cost_vc3 = cost_local = cost_ldn = 0
        qnt_vc1 = qnt_vc2 = qnt_vc3 = qnt_local = qnt_ldn = 0
        price_vc1 = price_vc2 = price_vc3 = price_local = price_ldn = 0
        contract_version = OLD_CONTRACT
        for phonecall in context['phonecall_long_distance']:
            if phonecall['company__is_new_contract'] or phonecall['company__organization_id'] == 2:
                contract_version = NEW_CONTRACT
            if phonecall['calltype'] == LDN:
                cost_ldn = phonecall['cost_sum']
                qnt_ldn = phonecall['count']
                price_ldn = phonecall['price']
            elif phonecall['calltype'] == VC2:
                cost_vc2 = phonecall['cost_sum']
                qnt_vc2 = phonecall['count']
                price_vc2 = phonecall['price']
            elif phonecall['calltype'] == VC3:
                cost_vc3 = phonecall['cost_sum']
                qnt_vc3 = phonecall['count']
                price_vc3 = phonecall['price']
        for phonecall in context['phonecall_local']:
            if phonecall['company__is_new_contract'] or phonecall['company__organization_id'] == 2:
                contract_version = NEW_CONTRACT
            if phonecall['calltype'] == LOCAL:
                cost_local = phonecall['cost_sum']
                qnt_local = phonecall['count']
                price_local = phonecall['price']
            elif phonecall['calltype'] == VC1:
                cost_vc1 = phonecall['cost_sum']
                qnt_vc1 = phonecall['count']
                price_vc1 = phonecall['price']
        cost_total = context['cost_total']
        qnt_total = context['phonecall_total']

        array_tblstyle = [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#cccccc')),
            ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
        tblstyle = TableStyle(array_tblstyle)
        thead = [['DISCAGEM LOCAL']]
        size = (self._width - 50) / 5
        tbl = Table(
            thead,
            colWidths=[self._width - 50],
            rowHeights=[20 for x in range(len(thead))])
        tbl.setStyle(tblstyle)
        self._story.append(tbl)

        array_tblstyle = [
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
            ('FONTSIZE', (0, 0), (-1, -1), 8),  # middle column
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#ffffff')),
            ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
        tblstyle = TableStyle(array_tblstyle)
        if contract_version == NEW_CONTRACT:
            thead = [
                [
                    get_tj_calltype_title(LOCAL) if self.company.slug == 'tj'  else 'Local Fixo-Fixo Extragrupo',
                    f"R$ {make_price(price_local)}",
                    qnt_local,
                    f"R$ {make_price(cost_local)}"
                ],
                [
                    get_tj_calltype_title(VC1) if self.company.slug == 'tj' else 'Local Fixo-Móvel (VC1/VC2/VC3)',
                    f"R$ {make_price(price_vc1)}",
                    qnt_vc1,
                    f"R$ {make_price(cost_vc1)}"
                ]
            ]
        else:
            thead = [
                [
                    get_tj_calltype_title(LOCAL) if self.company.slug == 'tj' else 'Local Fixo-Fixo Extragrupo',
                    f"R$ {make_price(price_local)}",
                    qnt_local,
                    f"R$ {make_price(cost_local)}"
                ],
                [
                    get_tj_calltype_title(VC1) if self.company.slug == 'tj' else 'Local Fixo-Móvel (VC1)',
                    f"R$ {make_price(price_vc1)}",
                    qnt_vc1,
                    f"R$ {make_price(cost_vc1)}"
                ]
            ]
        size = (self._width - 50) / 5
        tbl = Table(
            thead,
            colWidths=[size * 2, size, size, size],
            rowHeights=[25 for x in range(len(thead))])
        tbl.setStyle(tblstyle)
        self._story.append(tbl)

        array_tblstyle = [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#cccccc')),
            ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
        tblstyle = TableStyle(array_tblstyle)
        thead = [['LONGA DISTÂNCIA NACIONAL']]
        size = (self._width - 50) / 5
        tbl = Table(
            thead,
            colWidths=[self._width - 50],
            rowHeights=[20 for x in range(len(thead))])
        tbl.setStyle(tblstyle)
        self._story.append(tbl)

        array_tblstyle = [
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
            ('FONTSIZE', (0, 0), (-1, -1), 8),  # middle column
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#ffffff')),
            ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
        tblstyle = TableStyle(array_tblstyle)
        if contract_version == NEW_CONTRACT:
            thead = [
                [
                    get_tj_calltype_title(LDN) if self.company.slug == 'tj' else 'LDN-fixo/fixo-D1/D2/D3/D4',
                    f"R$ {make_price(price_ldn)}",
                    qnt_ldn,
                    f"R$ {make_price(cost_ldn)}"
                ]
            ]
        else:
            thead = [
                [
                    get_tj_calltype_title(LDN) if self.company.slug == 'tj' else 'LDN-fixo/fixo-D1/D2/D3/D4',
                    f"R$ {make_price(price_ldn)}",
                    qnt_ldn,
                    f"R$ {make_price(cost_ldn)}"
                ],
                [
                    get_tj_calltype_title(VC2) if self.company.slug == 'tj' else 'LDN-VC2 Fixo-Móvel',
                    f"R$ {make_price(price_vc2)}",
                    qnt_vc2,
                    f"R$ {make_price(cost_vc2)}"
                ],
                [
                    get_tj_calltype_title(VC3) if self.company.slug == 'tj' else 'LDN-VC3 Fixo-Móvel',
                    f"R$ {make_price(price_vc3)}",
                    qnt_vc3,
                    f"R$ {make_price(cost_vc3)}"
                ]
            ]
        size = (self._width - 50) / 5
        tbl = Table(
            thead,
            colWidths=[size * 2, size, size, size],
            rowHeights=[25 for x in range(len(thead))])
        tbl.setStyle(tblstyle)
        self._story.append(tbl)

        array_tblstyle = [
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),   # 1 column
            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#cccccc')),
            ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
        tblstyle = TableStyle(array_tblstyle)
        #total_comunication = float(cost_total)-float(service_cost)
        total_comunication = float(cost_total)
        thead = [[
            'TOTAL DOS SERVIÇOS DE COMUNICAÇÃO',
            str(qnt_total),
            f"R$ {make_price(total_comunication)}"]]
        size = (self._width - 50) / 5
        tbl = Table(
            thead,
            colWidths=[size * 3, size, size],
            rowHeights=[20 for x in range(len(thead))])
        tbl.setStyle(tblstyle)
        self._story.append(tbl)
        self.space_between_tables()

        array_tblstyle = [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#cccccc')),
            ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
        tblstyle = TableStyle(array_tblstyle)
        thead = [['TOTAL']]
        size = (self._width - 50) / 5
        tbl = Table(
            thead,
            colWidths=[self._width - 50],
            rowHeights=[20 for x in range(len(thead))])
        tbl.setStyle(tblstyle)
        self._story.append(tbl)
        array_tblstyle = [
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#b8b8b8')),
            ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
        tblstyle = TableStyle(array_tblstyle)
        total_company = float(cost_total) + float(service_cost)
        thead = [
            ['Total dos Serviços', f"R$ {make_price(total_company)}"]
        ]
        size = (self._width - 50) / 5
        tbl = Table(
            thead,
            colWidths=[size * 4, size],
            rowHeights=[20 for x in range(len(thead))])
        tbl.setStyle(tblstyle)
        self._story.append(tbl)
        return self.close_resume()
