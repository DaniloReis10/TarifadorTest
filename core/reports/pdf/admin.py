# python
import io
import os

from html import escape
from datetime import datetime

# django
from django.conf import settings
from django.contrib.staticfiles import finders
from django.templatetags.static import static

# third party
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak
from reportlab.platypus import Paragraph
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Table
from reportlab.platypus import TableStyle
from reportlab.rl_config import TTFSearchPath

# project
from centers.utils import make_price_adm
from charges.constants import BASIC_SERVICE_ACCESS_MAP, BASIC_SERVICE_ACCESS_MAP_NEW
from charges.constants import BASIC_SERVICE_MAP,  BASIC_SERVICE_MAP_NEW
from charges.constants import BASIC_SERVICE_MO_MAP
from core.utils import time_format
from phonecalls.constants import CALLTYPE_CHOICES
from phonecalls.constants import VC1, VC2, VC3, LOCAL, LDN, LDI
from phonecalls.constants import OLD_CONTRACT,  NEW_CONTRACT

CALLTYPE_MAP = dict(CALLTYPE_CHOICES)


class SystemReportAdministrador(object):

    def __init__(self, dateBegin, dateEnd, reportTitle, context, showCompanies=False, ust=False):
        self._dateBegin = dateBegin
        self._dateEnd = dateEnd
        self._issueDate = datetime.now().strftime('%d/%m/%Y')
        self._reportTitle = reportTitle
        self._orgLogo = static('img/Logo.jpg')
        self._buffer = io.BytesIO()
        self._doc = SimpleDocTemplate(
            self._buffer,
            rightMargin=35,
            leftMargin=35,
            topMargin=125,
            bottomMargin=56)
        self._ust = ust
        self._width, self._height = self._doc.pagesize
        self._story = []
        self.showCompanies = showCompanies

        TTFSearchPath.append(finders.find(os.path.join('fonts')))
        pdfmetrics.registerFont(TTFont('Sans',  "Microsoft Sans Serif.ttf"))
        self.style = ParagraphStyle(
            name='Sans',
            fontName='Sans',
            fontSize=8)

    def header(self, canvas, doc):
        header_list = []

        if self._orgLogo:
            header_list.append({
                'text': f'<img src="{settings.BASE_DIR}{self._orgLogo}"'
                        'width="150" height="66" valign="top"/>',
                'width': 20,
                'height': self._height - 20})
        header_list.append({
            'text': f'<font size=8><b>Período: {self._dateBegin}'
                    f' - {self._dateEnd}</b></font>',
            'width': 30,
            'height': self._height - 120})
        header_list.append({
            'text': f'<font size=8><b>Emissão: {self._issueDate}</b></font>',
            'width': self._width - 105,
            'height': self._height - 120})
        for header_data in header_list:
            insertParagraph = Paragraph(header_data['text'], style=self.style)
            insertParagraph.wrapOn(canvas, self._width, self._height)
            insertParagraph.drawOn(canvas, header_data['width'], header_data['height'])

    def title(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Sans', 12)
        canvas.drawString(30, self._height - 98, escape(self._reportTitle))

    def title_ust(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Sans', 11)
        canvas.drawCentredString(self._width / 2, self._height - 91, escape(self._reportTitle))
        canvas.setFont('Sans', 11)
        canvas.drawCentredString(
            self._width / 2, self._height - 103, 'Referente ao Contrato Nº XX/2023 – SEATIC')

    def create_header_and_footer(self, canvas, doc):
        """
        Add the header, title and footer to each page
        """

        if self._ust:
            self.header(canvas, doc)
            self.title_ust(canvas, doc)
        else:
            self.header(canvas, doc)
            self.title(canvas, doc)

    def insert_title_table(self, title: str):
        """
        Add table title
        """

        p = Paragraph(f"<font size=10><b>{escape(title)}</b></font><br/><br/>", style=self.style)
        self._story.append(p)

    def space_between_tables(self):
        """
        Space between tables
        """

        p = Paragraph("<br/>", style=self.style)
        self._story.append(p)

    def space_between_tables2(self):
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
            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
            ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#ffffff')),
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
        array_tblstyle.append(('FONTSIZE', (0, 0), (-1, -1), 9))
        array_tblstyle.append(('FONTNAME', (0, 0), (-1, -1), 'Sans'))
        array_tblstyle.append(('BACKGROUND', (0, 0), (-1, -1), HexColor('#ffffff')))
        array_tblstyle.append(('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white))
        array_tblstyle.append(('BOX', (0, 0), (-1, -1), 0.50, colors.white))
        tblstyle = TableStyle(array_tblstyle)

        tbl = Table(
            data['values'],
            colWidths=data['len_col'],
            rowHeights=[13 for x in range(len(data['values']))])
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

    def get_value(self):
        self._buffer.getvalue()

    def create_table_resume_services(self, context):
        value_service_basic_total = 0
        value_service_comunication_total = 0
        for organization, call_organization_map in context.items():
            if organization != 'Prefeitura Municipal de Fortaleza':
                continue
            service_amount = 0
            service_cost = 0
            if organization == 'SERVIÇOS DE COMUNICAÇÃO':
                self.insert_title_table(title=organization)
                value_service_comunication_total = call_organization_map['cost_sum']

                # ### Parte 1 - Título Serviços de Comunicação ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
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

                # ### Parte 2 - Cabeçalho da tabela ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [['SERVIÇO', 'CHAMADAS', 'TEMPO FATURADO', 'VALOR PERÍODO']]
                size = (self._width - 50) / 5
                tbl = Table(
                    thead,
                    colWidths=[size*2, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 3 - Título Discagem Local ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [['DISCAGEM LOCAL']]
                size = self._width - 50
                tbl = Table(
                    thead,
                    colWidths=[size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 4 - Chamadas de Discagem Local ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                local_list = [{
                        'type': LOCAL,  # LOCAL
                        'desc': 'Local Fixo-Fixo Extragrupo'
                    }, {
                        'type': VC1,  # VC1
                        'desc': 'Local Fixo-Móvel (VC1/VC2/VC3)'
                    }]

#                    {
#                        'type': VC2,  # VC2
#                        'desc': 'Local Fixo-Móvel (VC2)'
#                    }, {
#                        'type': VC3,  # VC3
#                        'desc': 'Local Fixo-Móvel (VC3)'
#                    }]"""
                thead = []
                for local in local_list:
                    if local['type'] in call_organization_map:
                        call_organization = call_organization_map[local['type']]
                        if type(call_organization) is not dict:
                            call_organization = call_organization._asdict()
                        minutes = call_organization['billedtime_sum']
                        thead.append([
                            local['desc'],
                            str(call_organization['count']),
                            time_format(minutes),
                            f"R$ {make_price_adm(call_organization['cost_sum'])}"])
                    else:
                        thead.append([local['desc'], '0', '00:00:00', 'R$ 0,00'])
                size = (self._width - 50) / 5
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 5 - Total de Discagem Local ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                if 'local' in call_organization_map:
                    minutes = call_organization_map['local']['billedtime_sum']
                    thead = [[
                        'Total de Discagem Local',
                        str(call_organization_map['local']['count']),
                        time_format(minutes),
                        f"R$ {make_price_adm(call_organization_map['local']['cost_sum'])}"]]
                else:
                    thead = [['Total de Discagem Local', '0', '00:00:00', 'R$ 0,00']]
                size = (self._width - 50) / 5
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 6 - Título Longa Distancia Nacional ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [['LONGA DISTÂNCIA NACIONAL']]
                size = self._width - 50
                tbl = Table(
                    thead,
                    colWidths=[size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 7 - Chamadas de Longa Distancia Nacional ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                if LDN in call_organization_map:
                    call_organization = call_organization_map[LDN]
                    if type(call_organization) is not dict:
                        call_organization = call_organization._asdict()
                    minutes = call_organization['billedtime_sum']
                    thead = [[
                        'LDN-fixo/fixo-D1/D2/D3/D4',
                        str(call_organization['count']),
                        time_format(minutes),
                        f"R$ {make_price_adm(call_organization['cost_sum'])}"]]
                else:
                    thead = [['LDN-fixo/fixo-D1/D2/D3/D4', '0', '00:00:00', 'R$ 0,00']]
                size = (self._width - 50) / 5
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 8 - Total de Longa Distancia Nacional ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                if 'national' in call_organization_map:
                    minutes = call_organization_map['national']['billedtime_sum']
                    thead = [[
                        'Total de Longa Distancia Nacional',
                        str(call_organization_map['national']['count']),
                        time_format(minutes),
                        f"R$ {make_price_adm(call_organization_map['national']['cost_sum'])}"]]
                else:
                    thead = [[
                        'Total de Longa Distancia Nacional',
                        '0',
                        '00:00:00',
                        'R$ 0,00']]
                size = (self._width - 50) / 5
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 9 - Título Longa Distância Internacional ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [['LONGA DISTÂNCIA INTERNACIONAL']]
                size = self._width - 50
                tbl = Table(
                    thead,
                    colWidths=[size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 10 - Chamadas de Longa Distância Internacional ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [['Longa Distância Internacional', '0', '00:00:00', 'R$ 2,00']]
                size = (self._width - 50) / 5
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 11 - Total de Longa Distancia Internacional ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                if 'international' in call_organization_map:
                    minutes = call_organization_map['international']['billedtime_sum']
                    thead = [[
                        'Total de Longa Distancia Internacional',
                        str(call_organization_map['international']['count']),
                        time_format(minutes),
                        f"R$ {make_price_adm(call_organization_map['international']['cost_sum'])}"]]
                else:
                    thead = [[
                        'Total de Longa Distancia Internacional',
                        '0',
                        '00:00:00',
                        'R$ 2,00']]
                size = (self._width - 50) / 5
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 12 - Total dos Serviços de Comunicação ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                minutes = call_organization_map['billedtime_sum']
                thead = [[
                    'TOTAL DOS SERVIÇOS DE COMUNICAÇÃO',
                    str(call_organization_map['count']),
                    time_format(minutes),
                    f"R$ {make_price_adm(call_organization_map['cost_sum'])}"]]
                size = (self._width - 50) / 5
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)

                self._story.append(tbl)
                self.space_between_tables()
                self.space_between_tables2()
            elif organization == 'SERVIÇOS BÁSICOS':
                self.insert_title_table(title=organization)

                # ### Parte 2 - Título Serviços de Comunicação ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
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

                # ### Parte 1 - Cabeçalho da tabela ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [['SERVIÇO', 'QUANTIDADE', 'VALOR PERÍODO']]
                size = (self._width - 50) / 5
                tbl = Table(
                    thead,
                    colWidths=[size*3, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 4 - Chamadas de Discagem Local ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (2, 0), (2, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = []

                service_amount = 0
                service_cost = 0

                for key, value in BASIC_SERVICE_MAP_NEW.items():
                    if key in call_organization_map:
                        service_amount += call_organization_map[key]['amount']
                        service_cost += call_organization_map[key]['cost']
                        value_mask = make_price_adm(call_organization_map[key]['cost'])
                        thead.append([
                            value,
                            str(call_organization_map[key]['amount']),
                            f"R$ {value_mask}"])

                size = (self._width - 50) / 5
                tbl = Table(
                    thead,
                    colWidths=[size * 3, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 12 - Total dos Serviços de Comunicação ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (2, 0), (2, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [[
                    'TOTAL DOS SERVIÇOS BASICOS',
                    str(service_amount),
                    f"R$ {make_price_adm(service_cost)}"]]
                size = (self._width - 50) / 5
                tbl = Table(
                    thead,
                    colWidths=[size * 3, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)
                self.space_between_tables2()
                value_service_basic_total = service_cost
                continue
            else:
                self.insert_title_table(title=f"Organização: {organization}")

                if 'service_basic' in call_organization_map:
                    # ### Parte 2 - Título Serviços de Comunicação ###
                    array_tblstyle = [
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                        ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                        ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
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

                    # ### Parte 1 - Cabeçalho da tabela ###
                    array_tblstyle = [
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                        ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                        ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
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

                    # ### Parte 4 - Chamadas de Discagem Local ###
                    array_tblstyle = [
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                        ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                        ('FONTSIZE', (0, 0), (0, -1), 7),  # middle column
                        ('FONTSIZE', (1, 0), (-1, -1), 9),  # middle column
                        ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                        ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                        ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                    tblstyle = TableStyle(array_tblstyle)
                    thead = []


                    for key, value in BASIC_SERVICE_MAP_NEW.items():
                        #if key != 'WIRELESS_ACCESS_SERVICE' and key in call_organization_map:
                        if key in call_organization_map:
                            service_amount += call_organization_map[key]['amount']
                            service_cost += call_organization_map[key]['cost']
                            thead.append([
                                value,
                                f"R$ {make_price_adm(call_organization_map[key]['price'])}",
                                str(call_organization_map[key]['amount']),
                                f"R$ {make_price_adm(call_organization_map[key]['cost'])}"])

                    size = (self._width - 50) / 5
                    tbl = Table(
                        thead,
                        colWidths=[size * 2, size, size, size],
                        rowHeights=[20 for x in range(len(thead))])
                    tbl.setStyle(tblstyle)
                    self._story.append(tbl)

                    # ### Parte 12 - Total dos Serviços de Comunicação ###
                    array_tblstyle = [
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                        ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),   # 1 column
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                        ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                        ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                        ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                        ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                    tblstyle = TableStyle(array_tblstyle)
                    thead = [[
                        'TOTAL DOS SERVIÇOS BASICOS',
                        str(service_amount),
                        f"R$ {make_price_adm(service_cost)}"]]
                    size = (self._width - 50) / 5
                    tbl = Table(
                        thead,
                        colWidths=[size * 3, size, size],
                        rowHeights=[20 for x in range(len(thead))])
                    tbl.setStyle(tblstyle)
                    self._story.append(tbl)
                    self.space_between_tables()

                # ### Parte 1 - Título Serviços de Comunicação ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
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

                # ### Parte 2 - Cabeçalho da tabela ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [['SERVIÇO', 'VALOR UNITÁRIO', 'CHAMADAS',
                          'TEMPO FATURADO', 'VALOR PERÍODO']]
                size = (self._width - 50) / 6
                tbl = Table(
                    thead,
                    colWidths=[size*2, size, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 3 - Título Discagem Local ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [['DISCAGEM LOCAL']]
                size = self._width - 50
                tbl = Table(
                    thead,
                    colWidths=[size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 4 - Chamadas de Discagem Local ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (3, 0), (3, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (4, 0), (4, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                #In this case I assume that the amount comes already coorected in VC1
                local_list = [{
                        'type': LOCAL,  # LOCAL
                        'desc': 'Local Fixo-Fixo Extragrupo'
                    }, {
                        'type': VC1,  # VC1
                        'desc': 'Local Fixo-Móvel (VC1/VC2/VC3)'
                    }] #, {
#                        'type': VC2,  # VC2
#                        'desc': 'Local Fixo-Móvel (VC2)'
#                    }, {
#                        'type': VC3,  # VC3
#                        'desc': 'Local Fixo-Móvel (VC3)'
#                    }]
                thead = []
                for local in local_list:
                    if local['type'] in call_organization_map:
                        call_organization = call_organization_map[local['type']]
                        if type(call_organization) is not dict:
                            call_organization = call_organization._asdict()
                        minutes = call_organization['billedtime_sum']
                        thead.append([
                            local['desc'],
                            f"R$ {make_price_adm(call_organization['org_price'])}",
                            str(call_organization['count']),
                            time_format(minutes),
                            f"R$ {make_price_adm(call_organization['cost_sum'])}"])
                    else:
                        thead.append([local['desc'], 'R$ 0,00', '0', '00:00:00', 'R$ 0,00'])
                size = (self._width - 50) / 6
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 5 - Total de Discagem Local ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                if 'local' in call_organization_map:
                    minutes = call_organization_map['local']['billedtime_sum']
                    thead = [[
                        'Total de Discagem Local',
                        str(call_organization_map['local']['count']),
                        time_format(minutes),
                        f"R$ {make_price_adm(call_organization_map['local']['cost_sum'])}"]]
                else:
                    thead = [['Total de Discagem Local', '0', '00:00:00', 'R$ 0,00']]
                size = (self._width - 50) / 6
                tbl = Table(
                    thead,
                    colWidths=[size * 3, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 6 - Título Longa Distancia Nacional ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [['LONGA DISTÂNCIA NACIONAL']]
                size = self._width - 50
                tbl = Table(
                    thead,
                    colWidths=[size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 7 - Chamadas de Longa Distancia Nacional ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (3, 0), (3, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (4, 0), (4, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                if LDN in call_organization_map:
                    call_organization = call_organization_map[LDN]
                    if type(call_organization) is not dict:
                        call_organization = call_organization._asdict()
                    minutes = call_organization['billedtime_sum']
                    thead = [[
                        'LDN-fixo/fixo-D1/D2/D3/D4',
                        f"R$ {make_price_adm(call_organization['org_price'])}",
                        str(call_organization['count']),
                        time_format(minutes),
                        f"R$ {make_price_adm(call_organization['cost_sum'])}"]]
                else:
                    thead = [['LDN-fixo/fixo-D1/D2/D3/D4', 'R$ 0,00', '0', '00:00:00', 'R$ 0,00']]
                size = (self._width - 50) / 6
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 8 - Total de Longa Distancia Nacional ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                if 'national' in call_organization_map:
                    minutes = call_organization_map['national']['billedtime_sum']
                    thead = [[
                        'Total de Longa Distancia Nacional',
                        str(call_organization_map['national']['count']),
                        time_format(minutes),
                        f"R$ {make_price_adm(call_organization_map['national']['cost_sum'])}"]]
                else:
                    thead = [[
                        'Total de Longa Distancia Nacional',
                        '0',
                        '00:00:00',
                        'R$ 0,00']]
                size = (self._width - 50) / 6
                tbl = Table(
                    thead,
                    colWidths=[size * 3, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 9 - Título Longa Distância Internacional ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [['LONGA DISTÂNCIA INTERNACIONAL']]
                size = self._width - 50
                tbl = Table(
                    thead,
                    colWidths=[size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 10 - Chamadas de Longa Distância Internacional ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (3, 0), (3, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (4, 0), (4, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                if LDI in call_organization_map:
                    call_organization = call_organization_map[LDI]
                    if type(call_organization) is not dict:
                        call_organization = call_organization._asdict()
                    minutes = call_organization['billedtime_sum']
                    thead = [[
                        'Longa Distância Internacional',
                        f"R$ {make_price_adm(call_organization['org_price'])}",
                        str(call_organization['count']),
                        time_format(minutes),
                        f"R$ {make_price_adm(call_organization['cost_sum'])}"]]
                else:
                    thead = [['Longa Distância Internacional', 'R$ 0,00', '0', '00:00:00', 'R$ 0,00']]
                size = (self._width - 50) / 6
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 11 - Total de Longa Distancia Internacional ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                if 'international' in call_organization_map:
                    minutes = call_organization_map['international']['billedtime_sum']
                    thead = [[
                        'Total de Longa Distancia Internacional',
                        str(call_organization_map['international']['count']),
                        time_format(minutes),
                        f"R$ {make_price_adm(call_organization_map['international']['cost_sum'])}"]]
                else:
                    thead = [[
                        'Total de Longa Distancia Internacional',
                        '0',
                        '00:00:00',
                        'R$ 2,00']]
                size = (self._width - 50) / 6
                tbl = Table(
                    thead,
                    colWidths=[size * 3, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 12 - Total dos Serviços de Comunicação ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                minutes = call_organization_map['billedtime_sum']
                thead = [[
                    'TOTAL DOS SERVIÇOS DE COMUNICAÇÃO',
                    str(call_organization_map['count']),
                    time_format(minutes),
                    f"R$ {make_price_adm(call_organization_map['cost_sum'])}"]]
                size = (self._width - 50) / 6
                tbl = Table(
                    thead,
                    colWidths=[size * 3, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)

                self._story.append(tbl)
                self.space_between_tables()

                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [['TOTAL']]
                size = self._width - 50
                tbl = Table(
                    thead,
                    colWidths=[size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                value_total = float(service_cost) + float(call_organization_map['cost_sum'])

                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                minutes = call_organization_map['billedtime_sum'] * 60
                thead = [[
                    'TOTAL DOS SERVIÇOS',
                    f"R$ {make_price_adm(value_total)}"]]
                size = (self._width - 50) / 6
                tbl = Table(
                    thead,
                    colWidths=[size * 5, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)
                self.space_between_tables()
                self.space_between_tables2()
                if self.showCompanies:
                    for company, call_company_map in call_organization_map['companies'].items():
                        try:
                            self.insert_title_table(
                                title=f"Organização: {organization} - Cliente: {company} - "
                                      f"{call_company_map['desc']}")
                        except KeyError:
                            self.insert_title_table(
                                title=f"Organização: {organization} - Cliente: {company}")

                        if 'services' in call_company_map:
                             # ### Parte 2 - Título Serviços de Comunicação ###
                            array_tblstyle = [
                                 ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                                 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                                 ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                                 ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                                 ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
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

                            # ### Parte 1 - Cabeçalho da tabela ###
                            array_tblstyle = [
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                                ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                                ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
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

                             # ### Parte 4 - Chamadas de Discagem Local ###
                            array_tblstyle = [
                                 ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                                 ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                                 ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                                 ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
                                 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                                 ('FONTSIZE', (0, 0), (0, -1), 7),  # middle column
                                 ('FONTSIZE', (1, 0), (-1, -1), 9),  # middle column
                                 ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                                 ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                                 ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                                 ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                            tblstyle = TableStyle(array_tblstyle)
                            thead = []
                            service_amount = 0
                            service_cost = 0
                            for key, value in BASIC_SERVICE_MAP_NEW.items():
                                if key in call_company_map['services']:
                                     service_amount += call_company_map['services'][key]['amount']
                                     service_cost += call_company_map['services'][key]['cost']
                                     thead.append([
                                         value,
                                         f"R$ {make_price_adm(call_company_map['services'][key]['price'])}",
                                         str(call_company_map['services'][key]['amount']),
                                         f"R$ {make_price_adm(call_company_map['services'][key]['cost'])}"])

                            size = (self._width - 50) / 5
                            tbl = Table(
                                 thead,
                                 colWidths=[size * 2, size, size, size],
                                 rowHeights=[20 for x in range(len(thead))])
                            tbl.setStyle(tblstyle)
                            self._story.append(tbl)

                             # ### Parte 12 - Total dos Serviços de Comunicação ###
                            array_tblstyle = [
                                 ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                                 ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                                 ('ALIGN', (2, 0), (2, -1), 'RIGHT'),   # 1 column
                                 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                                 ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                                 ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                                 ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                                 ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                                 ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                            tblstyle = TableStyle(array_tblstyle)
                            thead = [[
                                 'TOTAL DOS SERVIÇOS BASICOS',
                                 str(service_amount),
                                 f"R$ {make_price_adm(service_cost)}"]]
                            size = (self._width - 50) / 5
                            tbl = Table(
                                 thead,
                                 colWidths=[size * 3, size, size],
                                 rowHeights=[20 for x in range(len(thead))])
                            tbl.setStyle(tblstyle)
                            self._story.append(tbl)
                            self.space_between_tables()

                        # ### Parte 1 - Título Serviços de Comunicação ###
                        array_tblstyle = [
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                            ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
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

                        # ### Parte 2 - Cabeçalho da tabela ###
                        array_tblstyle = [
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                            ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
                            ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                        tblstyle = TableStyle(array_tblstyle)
                        thead = [['SERVIÇO', 'VALOR UNITÁRIO', 'CHAMADAS',
                                  'TEMPO FATURADO', 'VALOR PERÍODO']]
                        size = (self._width - 50) / 6
                        tbl = Table(
                            thead,
                            colWidths=[size*2, size, size, size, size],
                            rowHeights=[20 for x in range(len(thead))])
                        tbl.setStyle(tblstyle)
                        self._story.append(tbl)

                        # ### Parte 3 - Título Discagem Local ###
                        array_tblstyle = [
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                            ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                            ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                        tblstyle = TableStyle(array_tblstyle)
                        thead = [['DISCAGEM LOCAL']]
                        size = self._width - 50
                        tbl = Table(
                            thead,
                            colWidths=[size],
                            rowHeights=[20 for x in range(len(thead))])
                        tbl.setStyle(tblstyle)
                        self._story.append(tbl)

                        # ### Parte 4 - Chamadas de Discagem Local ###
                        array_tblstyle = [
                            ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                            ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                            ('ALIGN', (3, 0), (3, -1), 'CENTER'),   # 1 column
                            ('ALIGN', (4, 0), (4, -1), 'RIGHT'),   # 1 column
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                            ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                            ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                        tblstyle = TableStyle(array_tblstyle)
                        local_list = [{
                                'type': LOCAL,  # LOCAL
                                'desc': 'Local Fixo-Fixo Extragrupo'
                            }, {
                                'type': VC1,  # VC1
                                'desc': 'Local Fixo-Móvel (VC1/VC2/VC3)'
                            }] #, {
#                                'type': VC2,  # VC2
#                                'desc': 'Local Fixo-Móvel (VC2)'
#                            }, {
#                                'type': VC3,  # VC3
#                                'desc': 'Local Fixo-Móvel (VC3)'
#                            }]
                        thead = []
                        for local in local_list:
                            if local['type'] in call_company_map:
                                call_company = call_company_map[local['type']]
                                if type(call_company) is not dict:
                                    call_company = call_company._asdict()
                                minutes = call_company['billedtime_sum']
                                thead.append([
                                    local['desc'],
                                    f"R$ {make_price_adm(call_company['org_price'])}",
                                    str(call_company['count']),
                                    time_format(minutes),
                                    f"R$ {make_price_adm(call_company['cost_sum'])}"])
                            else:
                                thead.append([local['desc'], 'R$ 0,00', '0', '00:00:00', 'R$ 0,00'])
                        size = (self._width - 50) / 6
                        tbl = Table(
                            thead,
                            colWidths=[size * 2, size, size, size, size],
                            rowHeights=[20 for x in range(len(thead))])
                        tbl.setStyle(tblstyle)
                        self._story.append(tbl)

                        # ### Parte 5 - Total de Discagem Local ###
                        array_tblstyle = [
                            ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                            ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                            ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                            ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                            ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                        tblstyle = TableStyle(array_tblstyle)
                        if 'local' in call_company_map:
                            minutes = call_company_map['local']['billedtime_sum']
                            thead = [[
                                'Total de Discagem Local',
                                str(call_company_map['local']['count']),
                                time_format(minutes),
                                f"R$ {make_price_adm(call_company_map['local']['cost_sum'])}"]]
                        else:
                            thead = [['Total de Discagem Local', '0', '00:00:00', 'R$ 0,00']]
                        size = (self._width - 50) / 6
                        tbl = Table(
                            thead,
                            colWidths=[size * 3, size, size, size],
                            rowHeights=[20 for x in range(len(thead))])
                        tbl.setStyle(tblstyle)
                        self._story.append(tbl)

                        # ### Parte 6 - Título Longa Distancia Nacional ###
                        array_tblstyle = [
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                            ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                            ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                        tblstyle = TableStyle(array_tblstyle)
                        thead = [['LONGA DISTÂNCIA NACIONAL']]
                        size = self._width - 50
                        tbl = Table(
                            thead,
                            colWidths=[size],
                            rowHeights=[20 for x in range(len(thead))])
                        tbl.setStyle(tblstyle)
                        self._story.append(tbl)

                        # ### Parte 7 - Chamadas de Longa Distancia Nacional ###
                        array_tblstyle = [
                            ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                            ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                            ('ALIGN', (3, 0), (3, -1), 'CENTER'),   # 1 column
                            ('ALIGN', (4, 0), (4, -1), 'RIGHT'),   # 1 column
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                            ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                            ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                        tblstyle = TableStyle(array_tblstyle)
                        if LDN in call_company_map:
                            call_company = call_company_map[LDN]
                            if type(call_company) is not dict:
                                call_company = call_company._asdict()
                            minutes = call_company['billedtime_sum']
                            thead = [[
                                'LDN-fixo/fixo-D1/D2/D3/D4',
                                f"R$ {make_price_adm(call_company['org_price'])}",
                                str(call_company['count']),
                                time_format(minutes),
                                f"R$ {make_price_adm(call_company['cost_sum'])}"]]
                        else:
                            thead = [[
                                'LDN-fixo/fixo-D1/D2/D3/D4', 'R$ 0,00', '0', '00:00:00', 'R$ 0,00']]
                        size = (self._width - 50) / 6
                        tbl = Table(
                            thead,
                            colWidths=[size * 2, size, size, size, size],
                            rowHeights=[20 for x in range(len(thead))])
                        tbl.setStyle(tblstyle)
                        self._story.append(tbl)

                        # ### Parte 8 - Total de Longa Distancia Nacional ###
                        array_tblstyle = [
                            ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                            ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                            ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                            ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                            ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                        tblstyle = TableStyle(array_tblstyle)
                        if 'national' in call_company_map:
                            minutes = call_company_map['national']['billedtime_sum']
                            thead = [[
                                'Total de Longa Distancia Nacional',
                                str(call_company_map['national']['count']),
                                time_format(minutes),
                                f"R$ {make_price_adm(call_company_map['national']['cost_sum'])}"]]
                        else:
                            thead = [[
                                'Total de Longa Distancia Nacional',
                                '0',
                                '00:00:00',
                                'R$ 0,00']]
                        size = (self._width - 50) / 6
                        tbl = Table(
                            thead,
                            colWidths=[size * 3, size, size, size],
                            rowHeights=[20 for x in range(len(thead))])
                        tbl.setStyle(tblstyle)
                        self._story.append(tbl)

                        # ### Parte 9 - Título Longa Distância Internacional ###
                        array_tblstyle = [
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                            ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                            ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                        tblstyle = TableStyle(array_tblstyle)
                        thead = [['LONGA DISTÂNCIA INTERNACIONAL']]
                        size = self._width - 50
                        tbl = Table(
                            thead,
                            colWidths=[size],
                            rowHeights=[20 for x in range(len(thead))])
                        tbl.setStyle(tblstyle)
                        self._story.append(tbl)

                        # ### Parte 10 - Chamadas de Longa Distância Internacional ###
                        array_tblstyle = [
                            ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                            ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                            ('ALIGN', (3, 0), (3, -1), 'CENTER'),   # 1 column
                            ('ALIGN', (4, 0), (4, -1), 'RIGHT'),   # 1 column
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                            ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                            ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                        tblstyle = TableStyle(array_tblstyle)
                        if LDI in call_company_map:
                            call_company = call_company_map[LDI]
                            if type(call_company) is not dict:
                                call_company = call_company._asdict()
                            minutes = call_company['billedtime_sum']
                            thead = [[
                                'Longa Distância Internacional',
                                f"R$ {make_price_adm(call_company['org_price'])}",
                                str(call_company['count']),
                                time_format(minutes),
                                f"R$ {make_price_adm(call_company['cost_sum'])}"]]
                        else:
                            thead = [[
                                'Longa Distância Internacional', 'R$ 0,00', '0', '00:00:00', 'R$ 0,00']]
                        size = (self._width - 50) / 6
                        tbl = Table(
                            thead,
                            colWidths=[size * 2, size, size, size, size],
                            rowHeights=[20 for x in range(len(thead))])
                        tbl.setStyle(tblstyle)
                        self._story.append(tbl)

                        # ### Parte 11 - Total de Longa Distancia Internacional ###
                        array_tblstyle = [
                            ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                            ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                            ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                            ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                            ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                        tblstyle = TableStyle(array_tblstyle)
                        if 'international' in call_company_map:
                            minutes = call_company_map['international']['billedtime_sum']
                            cost = make_price_adm(call_company_map['international']['cost_sum'])
                            thead = [[
                                'Total de Longa Distancia Internacional',
                                str(call_company_map['international']['count']),
                                time_format(minutes),
                                f"R$ {cost}"]]
                        else:
                            thead = [[
                                'Total de Longa Distancia Internacional',
                                '0',
                                '00:00:00',
                                'R$ 2,00']]
                        size = (self._width - 50) / 6
                        tbl = Table(
                            thead,
                            colWidths=[size * 3, size, size, size],
                            rowHeights=[20 for x in range(len(thead))])
                        tbl.setStyle(tblstyle)
                        self._story.append(tbl)

                        # ### Parte 12 - Total dos Serviços de Comunicação ###
                        array_tblstyle = [
                            ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                            ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                            ('ALIGN', (2, 0), (2, -1), 'CENTER'),   # 1 column
                            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   # 1 column
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                            ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                            ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                        tblstyle = TableStyle(array_tblstyle)
                        minutes = call_company_map['billedtime_sum']
                        thead = [[
                            'TOTAL DOS SERVIÇOS DE COMUNICAÇÃO',
                            str(call_company_map['count']),
                            time_format(minutes),
                            f"R$ {make_price_adm(call_company_map['cost_sum'])}"]]
                        size = (self._width - 50) / 6
                        tbl = Table(
                            thead,
                            colWidths=[size * 3, size, size, size],
                            rowHeights=[20 for x in range(len(thead))])
                        tbl.setStyle(tblstyle)

                        self._story.append(tbl)
                        self.space_between_tables()
                        self.space_between_tables()
                        self.space_between_tables2()

        array_tblstyle = [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
            ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
            ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
        tblstyle = TableStyle(array_tblstyle)
        thead = [['TOTAL GERAL']]
        size = self._width - 50
        tbl = Table(
            thead,
            colWidths=[size],
            rowHeights=[20 for x in range(len(thead))])
        tbl.setStyle(tblstyle)
        self._story.append(tbl)

        value_total = float(value_service_basic_total) + float(value_service_comunication_total)

        array_tblstyle = [
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
            ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
            ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
        tblstyle = TableStyle(array_tblstyle)
        minutes = call_organization_map['billedtime_sum'] * 60
        thead = [[
            'TOTAL DOS SERVIÇOS',
            f"R$ {make_price_adm(value_total)}"]]
        size = (self._width - 50) / 6
        tbl = Table(
            thead,
            colWidths=[size * 5, size],
            rowHeights=[20 for x in range(len(thead))])
        tbl.setStyle(tblstyle)
        self._story.append(tbl)

        return self.close()

    def create_table_ust_services(self, context):
        # value_service_basic_total = 0  # TODO variáveis não utilizadas
        # value_service_basic_total_ust = 0
        # value_service_comunication_total = 0
        # value_service_comunication_total_ust = 0
        for organization, call_organization_map in context.items():
            service_amount = 0
            service_cost = 0
            service_cost_ust = 0.0
            if organization == 'SERVIÇOS DE COMUNICAÇÃO':
                pass
            elif organization == 'SERVIÇOS BÁSICOS':
                self.insert_title_table(title=organization)

                # ### Parte 2 - Título Serviços de Comunicação ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
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

                # ### Parte 1 - Cabeçalho da tabela ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 8),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [['SERVIÇO', 'QUANTIDADE', 'VALOR MENSAL(UST)', 'VALOR MENSAL(R$)']]
                size = (self._width - 50) / 6
                tbl = Table(
                    thead,
                    colWidths=[size*3, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 4 - Chamadas de Discagem Local ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (2, 0), (2, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = []

                service_amount = 0
                service_cost = 0
                service_cost_ust = 0
                for key, value in BASIC_SERVICE_MAP.items():
                    if key in call_organization_map:
                        service_amount += call_organization_map[key]['amount']
                        service_cost += call_organization_map[key]['cost']
                        service_cost_ust += call_organization_map[key]['cost_ust']
                        value_mask = make_price_adm(call_organization_map[key]['cost'])
                        value_mask_ust = make_price_adm(call_organization_map[key]['cost'])
                        thead.append([
                            value,
                            str(make_price_adm(call_organization_map[key]['amount'])),
                            f"{value_mask_ust}",
                            f"R$ {value_mask}"])

                size = (self._width - 50) / 6
                tbl = Table(
                    thead,
                    colWidths=[size * 3, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 12 - Total dos Serviços de Comunicação ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),   # 1 column
                    ('ALIGN', (2, 0), (2, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [[
                    'TOTAL DOS SERVIÇOS BASICOS',
                    str(make_price_adm(service_amount)),
                    f"{make_price_adm(service_cost_ust)}",
                    f"R$ {make_price_adm(service_cost)}"]]
                size = (self._width - 50) / 6
                tbl = Table(
                    thead,
                    colWidths=[size * 3, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)
                self.space_between_tables2()
                # value_service_basic_total = service_cost  # TODO variáveis não utilizadas
                # value_service_basic_total_ust = service_cost_ust
                continue
            else:
                # self.insert_title_table(title=f"Organização: {organization}")

                if 'service_basic' in call_organization_map:
                    # ### Parte 2 - Título Serviços de Comunicação ###
                    array_tblstyle = [
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                        ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                        ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
                        ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                        ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                    tblstyle = TableStyle(array_tblstyle)
                    thead = [[
                        'TABELA 1 – SERVIÇOS DE DISPONIBILIZAÇÃO DE ACESSO A COMUNICAÇÃO VOIP']]
                    size = self._width - 50
                    tbl = Table(
                        thead,
                        colWidths=[size],
                        rowHeights=[20 for x in range(len(thead))])
                    tbl.setStyle(tblstyle)
                    self._story.append(tbl)

                    # ### Parte 1 - Cabeçalho da tabela ###
                    array_tblstyle = [
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                        ('FONTSIZE', (0, 0), (-1, -1), 7),  # middle column
                        ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
                        ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                        ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                    tblstyle = TableStyle(array_tblstyle)
                    thead = [['SERVIÇO', 'VALOR MENSAL(R$)']]
                    size = (self._width - 50) / 3
                    tbl = Table(
                        thead,
                        colWidths=[size*2, size],
                        rowHeights=[20 for x in range(len(thead))])
                    tbl.setStyle(tblstyle)
                    self._story.append(tbl)

                    # ### Parte 4 - Chamadas de Discagem Local ###
                    array_tblstyle = [
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                        ('FONTSIZE', (0, 0), (0, -1), 7),  # middle column
                        ('FONTSIZE', (1, 0), (-1, -1), 9),  # middle column
                        ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                        ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                        ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                    tblstyle = TableStyle(array_tblstyle)
                    thead = []

                    service_amount = 0
                    service_cost = 0
                    service_cost_ust = 0.0
                    for key, value in BASIC_SERVICE_ACCESS_MAP_NEW.items():
                        if key in call_organization_map:
                            service_amount += call_organization_map[key]['amount']
                            service_cost += call_organization_map[key]['cost']
                            service_cost_ust += call_organization_map[key]['cost_ust']
                            thead.append([
                                value,
                                f"R$ {make_price_adm(call_organization_map[key]['cost'])}"])
                        else:
                            thead.append([
                                value,
                                "R$ 0,0000"])
                    size = (self._width - 50) / 3
                    tbl = Table(
                        thead,
                        colWidths=[size * 2, size ],
                        rowHeights=[20 for x in range(len(thead))])
                    tbl.setStyle(tblstyle)
                    self._story.append(tbl)

                    # ### Parte 12 - Total dos Serviços de Comunicação ###
                    array_tblstyle = [
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                        ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                        ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                        ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                        ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                    tblstyle = TableStyle(array_tblstyle)
                    thead = [[
                        'TOTAL',
                        f"R$ {make_price_adm(service_cost)}"]]
                    size = (self._width - 50) / 3
                    tbl = Table(
                        thead,
                        colWidths=[size * 2, size],
                        rowHeights=[20 for x in range(len(thead))])
                    tbl.setStyle(tblstyle)
                    self._story.append(tbl)
                    self._story.append(PageBreak())

                    value_service_cost = service_cost
                    value_service_cost_ust = service_cost_ust

                    # ### Parte 13 - Título Serviços de Comunicação ###
                    array_tblstyle = [
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                        ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                        ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
                        ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                        ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                    tblstyle = TableStyle(array_tblstyle)
                    thead = [['TABELA 2 –SERVIÇOS DE CONTACT CENTER']]
                    size = self._width - 50
                    tbl = Table(
                        thead,
                        colWidths=[size],
                        rowHeights=[20 for x in range(len(thead))])
                    tbl.setStyle(tblstyle)
                    self._story.append(tbl)

                    # ### Parte 14 - Cabeçalho da tabela ###
                    array_tblstyle = [
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                        ('FONTSIZE', (0, 0), (-1, -1), 7),  # middle column
                        ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
                        ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                        ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                    tblstyle = TableStyle(array_tblstyle)
                    thead = [['SERVIÇO', 'VALOR MENSAL(R$)']]
                    size = (self._width - 50) / 3
                    tbl = Table(
                        thead,
                        colWidths=[size*2, size],
                        rowHeights=[20 for x in range(len(thead))])
                    tbl.setStyle(tblstyle)
                    self._story.append(tbl)

                    # ### Parte 15 - Chamadas de Discagem Local ###
                    array_tblstyle = [
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                        ('FONTSIZE', (0, 0), (0, -1), 7),  # middle column
                        ('FONTSIZE', (1, 0), (-1, -1), 9),  # middle column
                        ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                        ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                        ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                    tblstyle = TableStyle(array_tblstyle)
                    thead = []

                    service_amount = 0
                    service_cost = 0
                    service_cost_ust = 0.0
                    for key, value in BASIC_SERVICE_MO_MAP.items():
                        if key in call_organization_map:
                            service_amount += call_organization_map[key]['amount']
                            service_cost += call_organization_map[key]['cost']
                            service_cost_ust += call_organization_map[key]['cost_ust']
                            thead.append([
                                value,
                                f"R$ {make_price_adm(call_organization_map[key]['cost'])}"])
                        else:
                            thead.append([
                                value,
                                "R$ 0,0000"])
                    size = (self._width - 50) / 3
                    tbl = Table(
                        thead,
                        colWidths=[size * 2, size],
                        rowHeights=[20 for x in range(len(thead))])
                    tbl.setStyle(tblstyle)
                    self._story.append(tbl)

                    # ### Parte 16 - Total dos Serviços de Comunicação ###
                    array_tblstyle = [
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                        ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                        ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                        ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                        ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                    tblstyle = TableStyle(array_tblstyle)
                    thead = [[
                        'TOTAL',
                        f"R$ {make_price_adm(service_cost)}"]]
                    size = (self._width - 50) / 3
                    tbl = Table(
                        thead,
                        colWidths=[size * 2, size],
                        rowHeights=[20 for x in range(len(thead))])
                    tbl.setStyle(tblstyle)
                    self._story.append(tbl)
                    self._story.append(PageBreak())

                    value_service_cost += service_cost
                    value_service_cost_ust += service_cost_ust

                # ### Parte 17 - Título Serviços de Comunicação ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [['TABELA 3 - SERVIÇOS MENSAL EXECUTADOS POR DEMANDA (MINUTAGEM)']]
                size = self._width - 50
                tbl = Table(
                    thead,
                    colWidths=[size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 18 - Cabeçalho da tabela ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 7),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [['SERVIÇO', 'VALOR MENSAL(R$)']]
                size = (self._width - 50) / 3
                tbl = Table(
                    thead,
                    colWidths=[size*2, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 19 - Título Discagem Local ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [['DISCAGEM LOCAL']]
                size = self._width - 50
                tbl = Table(
                    thead,
                    colWidths=[size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 20 - Chamadas de Discagem Local ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                local_list = [{
                        'type': LOCAL,  # LOCAL
                        'desc': 'Local Fixo-Fixo Extragrupo'
                    }, {
                        'type': VC1,  # VC1
                        'desc': 'Local Fixo-Móvel (VC1/VC2/VC3)'
                    }]
                thead = []
                # Valores referentes a quantidade total de cada tabela de serviços de comunicação
                # e quantidade geral de serviços de comunicação
                total_amount = 0
                partial_quantity = 0
                for local in local_list:
                    if local['type'] in call_organization_map:
                        call_organization = call_organization_map[local['type']]
                        if type(call_organization) is not dict:
                            call_organization = call_organization._asdict()
                        if call_organization['price_ust'] > 0:
                            cost_ust = round(float(call_organization['cost_ust_sum']), 4)
                            price_ust = round(float(call_organization['price_ust']), 4)
                            amount = round(cost_ust / price_ust, 4)
                            total_amount += amount
                            partial_quantity += amount
                        else:
                            amount = 0.0
                        thead.append([
                            local['desc'],
                            f"R$ {make_price_adm(call_organization['cost_sum'])}"])
                    else:
                        thead.append([local['desc'], 'R$ 0,0000'])
                size = (self._width - 50) / 3
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 21 - Total de Discagem Local ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                if 'local' in call_organization_map:
                    thead = [[
                        'Total de Discagem Local',
                        f"R$ {make_price_adm(call_organization_map['local']['cost_sum'])}"]]
                else:
                    thead = [['Total de Discagem Local', 'R$ 0,0000']]
                size = (self._width - 50) / 3
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 22 - Título Longa Distancia Nacional ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [['LONGA DISTÂNCIA NACIONAL']]
                size = self._width - 50
                tbl = Table(
                    thead,
                    colWidths=[size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 23 - Chamadas de Longa Distancia Nacional ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)

                # Valores referentes a quantidade total de cada tabela de serviços de comunicação
                partial_quantity = 0
                if LDN in call_organization_map:
                    call_organization = call_organization_map[LDN]
                    if type(call_organization) is not dict:
                        call_organization = call_organization._asdict()
                    if call_organization['price_ust'] > 0:
                        cost_ust = round(float(call_organization['cost_ust_sum']), 4)
                        prtice_ust = round(float(call_organization['price_ust']), 4)
                        amount = round(cost_ust / prtice_ust, 4)
                        total_amount += amount
                        partial_quantity += amount
                    else:
                        amount = 0.0
                    thead = [[
                        'LDN-fixo/fixo-D1/D2/D3/D4',
                        f"R$ {make_price_adm(call_organization['cost_sum'])}"]]
                else:
                    thead = [[
                        'LDN-fixo/fixo-D1/D2/D3/D4', 'R$ 0,0000']]
                size = (self._width - 50) / 3
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 24 - Total de Longa Distancia Nacional ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                if 'national' in call_organization_map:
                    thead = [[
                        'Total de Longa Distancia Nacional',
                        f"R$ {make_price_adm(call_organization_map['national']['cost_sum'])}"]]
                else:
                    thead = [[
                        'Total de Longa Distancia Nacional',
                        'R$ 0,0000']]
                size = (self._width - 50) / 3
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 25 - Título Longa Distância Internacional ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [['LONGA DISTÂNCIA INTERNACIONAL']]
                size = self._width - 50
                tbl = Table(
                    thead,
                    colWidths=[size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 26 - Chamadas de Longa Distância Internacional ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f1f1f1')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [[
                    'Longa Distância Internacional', 'R$ 0,0000']]
                size = (self._width - 50) / 3
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 27 - Total de Longa Distancia Internacional ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                if 'international' in call_organization_map:
                    thead = [[
                        'Total de Longa Distancia Internacional',
                        f"R$ {make_price_adm(call_organization_map['international']['cost_sum'])}"]]
                else:
                    thead = [[
                        'Total de Longa Distancia Internacional',
                        'R$ 0,0000']]
                size = (self._width - 50) / 3
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                # ### Parte 28 - Total dos Serviços de Comunicação ###
                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#dedede')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [[
                    'TOTAL DOS SERVIÇOS DE COMUNICAÇÃO',
                    f"R$ {make_price_adm(call_organization_map['cost_sum'])}"]]
                size = (self._width - 50) / 3
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)

                self._story.append(tbl)
                self.space_between_tables()
                self.space_between_tables()
                self.space_between_tables2()
                self.space_between_tables()
                self.space_between_tables2()

                array_tblstyle = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [['TOTAL']]
                size = self._width - 50
                tbl = Table(
                    thead,
                    colWidths=[size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)

                value_total = float(value_service_cost) + float(call_organization_map['cost_sum'])
                value_total_ust = \
                    float(value_service_cost_ust) + float(call_organization_map['cost_ust_sum'])

                array_tblstyle = [
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
                    ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
                    ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
                tblstyle = TableStyle(array_tblstyle)
                thead = [[
                    'Valor Mensal (R$) (t1+t2+t3+t4+t5):',
                    f"R$ {make_price_adm(value_total)}"]]
                size = (self._width - 50) / 3
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)
                self.space_between_tables()
                self.space_between_tables2()

        # array_tblstyle = [
        #     ('ALIGN', (0, 0), (-1, -1), 'CENTER'),   # 1 column
        #     ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
        #     ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
        #     ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
        #     ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
        #     ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
        #     ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
        # tblstyle = TableStyle(array_tblstyle)
        # thead = [['TOTAL GERAL']]
        # size = self._width - 50
        # tbl = Table(
        #     thead,
        #     colWidths=[size],
        #     rowHeights=[20 for x in range(len(thead))])
        # tbl.setStyle(tblstyle)
        # self._story.append(tbl)

        # value_total = float(value_service_basic_total) + float(value_service_comunication_total)
        # value_total_ust = \
        #     float(value_service_basic_total_ust) + float(value_service_comunication_total_ust)

        # array_tblstyle = [
        #     ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # 1 column
        #     ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # 1 column
        #     ('ALIGN', (2, 0), (2, -1), 'RIGHT'),   # 1 column
        #     ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # middle column
        #     ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
        #     ('FONTNAME', (0, 0), (-1, -1), 'Sans'),
        #     ('BACKGROUND', (0, 0), (-1, -1), HexColor('#c3c3c3')),
        #     ('INNERGRID', (0, 0), (-1, -1), 0.70, colors.white),
        #     ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
        # tblstyle = TableStyle(array_tblstyle)
        # thead = [[
        #     'TOTAL DOS SERVIÇOS',
        #     f"{make_price_adm(value_total_ust)}",
        #     f"R$ {make_price_adm(value_total)}"]]
        # size = (self._width - 50) / 6
        # tbl = Table(
        #     thead,
        #     colWidths=[size * 4, size, size],
        #     rowHeights=[20 for x in range(len(thead))])
        # tbl.setStyle(tblstyle)
        # self._story.append(tbl)

        return self.close()
