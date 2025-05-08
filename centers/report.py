# python
import io
import os

from cgi import escape
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
from charges.constants import BASIC_SERVICE_MAP
from core.utils import time_format
from phonecalls.constants import CALLTYPE_CHOICES
from phonecalls.constants import VC1, VC2, VC3, LOCAL, LDN

# local
from .utils import make_price


CALLTYPE_MAP = dict(CALLTYPE_CHOICES)


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
        self._orgLogo = \
            self.org.settings.logo.name if self.org.settings.logo else None
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

        if self._orgLogo:
            header_list.append({
                'text': f'<img src="{settings.MEDIA_ROOT}{self._orgLogo}"'
                        'width="550" height="86" valign="top"/>',
                'width': 20,
                'height': self._height - 20})
        header_list.append({
            'text': f'<font size=8><b>Período: {self._dateBegin}'
                    f' - {self._dateEnd}</b></font>',
            'width': 30,
            'height': self._height - 135})
        header_list.append({
            'text': f'<font size=8><b>Emissão: {self._issueDate}</b></font>',
            'width': self._width - 105,
            'height': self._height - 135})

        for header_data in header_list:
            insertParagraph = Paragraph(header_data['text'], style=self.style)
            insertParagraph.wrapOn(canvas, self._width, self._height)
            insertParagraph.drawOn(canvas, header_data['width'], header_data['height'])

    def header_resume(self, canvas, doc):
        header_list = []

        if self._orgLogo:
            header_list.append({
                'text': f'<img src="{settings.MEDIA_ROOT}{self._orgLogo}"'
                        'width="550" height="86" valign="top"/>',
                'width': 20,
                'height': self._height - 20})
        header_list.append({
            'text': f'<font size=10><b>Período: {self._dateBegin}'
                    f' - {self._dateEnd}</b></font>',
            'width': 30,
            'height': self._height - 120})
        header_list.append({
            'text': f'<font size=10><b>Emissão: {self._issueDate}</b></font>',
            'width': self._width - 125,
            'height': self._height - 120})

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

        p = Paragraph(f"<font size=9><b>{escape(title)}</b></font><br/>", style=self.style)
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
            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
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

    def create_table_detail(self, context):  # TODO remover
        for ramal in context:
            self.insert_title_table(title=f'RAMAL: {ramal}')

            call_list = context[ramal]['call_list']
            call_count = context[ramal]['call_count']
            duration_count = context[ramal]['duration_count']
            billed_count = context[ramal]['billed_count']

            size = (self._width - 50) / 7
            data = {
                'thead': ['Data', 'Hora', 'Ramal', 'Número Discado', 'Tipo', 'Duração', 'Valor'],
                'len_col': [size, size, size, size+10, size-10, size, size],
                'align': ['CENTER', 'CENTER', 'CENTER', 'CENTER', 'CENTER', 'CENTER', 'CENTER'],
                'values': []}
            for value in call_list:
                data['values'].append([
                    value.calldate.strftime('%d/%m/%Y'),
                    value.calltime.strftime('%H:%M:%S'),
                    value.ramal,
                    value.dialednumber,
                    value.type,
                    datetime.fromtimestamp(value.billedtime.seconds).strftime("%H:%M:%S"),
                    f"R$ {value.billedamount:.2f}"])
            data['values'].append([
                'Total',
                '',
                value.ramal,
                call_count,
                '',
                datetime.fromtimestamp(duration_count.seconds).strftime("%H:%M:%S"),
                f"R$ {billed_count:.2f}"])
            self.create_table(data)
            self.space_between_tables()
        return self.close()

    def create_table_resume(self, context):  # TODO remover
        value_ddd = value_vc2 = value_vc3 = 0
        for call_long_distance in context['call_long_distance']:
            if call_long_distance.type == 'DDD':
                value_ddd = call_long_distance.costcharged
            elif call_long_distance.type == 'VC2':
                value_vc2 = call_long_distance.costcharged
            elif call_long_distance.type == 'VC3':
                value_vc3 = call_long_distance.costcharged

        value_local = value_vc1 = 0
        for call_local in context['call_local']:
            if call_local.type == 'LOCAL':
                value_local = call_local.costcharged
            elif call_local.type == 'VC1':
                value_vc1 = call_local.costcharged

        value_total = context['cost_total']

        size = (self._width - 50) / 7
        data = {
            'thead': ['DISCAGEM LOCAL', ''],
            'len_col': [6*size, size],
            'align': ['LEFT', 'RIGHT'],
            'values': []}
        data['values'].append(['Local Fixo-Fixo Extragrupo', f"R$ {value_local:.2f}"])
        data['values'].append(['Local Fixo-Móvel (VC1)', f"R$ {value_vc1:.2f}"])
        self.create_table(data)
        self.space_between_tables()
        data = {
            'thead': ['LONGA DISTÂNCIA NACIONAL', ''],
            'len_col': [6*size, size],
            'align': ['LEFT', 'RIGHT'],
            'values': []}
        data['values'].append(['LDN-fixo/fixo-D1/D2/D3/D4', f"R$ {value_ddd:.2f}"])
        data['values'].append(['LDN-VC2 Fixo-Móvel', f"R$ {value_vc2:.2f}"])
        data['values'].append(['LDN-VC3 Fixo-Móvel', f"R$ {value_vc3:.2f}"])
        self.create_table(data)
        self.space_between_tables()
        data = {
            'thead': ['TOTAL', ''],
            'len_col': [6*size, size],
            'align': ['LEFT', 'RIGHT'],
            'values': []}
        data['values'].append(['Total dos Serviços', f"R$ {value_total:.2f} "])
        self.create_table(data)
        return self.close()

    def make_phonecall_table(self, context):
        for ramal, phonecall_data in context['phonecall_data'].items():
            self.insert_title_table(title=f'RAMAL: {ramal}')
            size = (self._width - 50) / 7
            data = {
                'thead':   ['Data', 'Hora', 'Ramal', 'Número Discado', 'Tipo', 'Duração', 'Valor'],
                'len_col': [size-20, size-25, size-15, size, size+115, size-25, size-25],
                'align':   ['CENTER', 'CENTER', 'CENTER', 'CENTER', 'CENTER', 'CENTER', 'CENTER'],
                'values':  []}
            for phonecall in phonecall_data['phonecall_list']:
                data['values'].append([
                    phonecall['startdate'].strftime('%d/%m/%Y'),
                    phonecall['starttime'].strftime('%H:%M:%S'),
                    ramal,
                    phonecall['dialednumber'],
                    CALLTYPE_MAP[phonecall['calltype']],
                    time_format(phonecall['duration']),
                    f"R$ {make_price(phonecall['billedamount'])}"])
            data['values'].append([
                'Total',
                '',
                ramal,
                phonecall_data['count'],
                '',
                time_format(phonecall_data['billedtime_sum']),
                f"R$ {make_price(phonecall_data['cost_sum'])}"])
            self.create_table(data)
            self.space_between_tables()
        return self.close()

    def make_phonecall_resume_table(self, context):
        #flag = True
        #if self.org.id == 2:
            #flag = False
        if context['basic_service'] and len(context['basic_service']) > 0:
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

            service_amount = 0
            service_cost = 0
            for key, value in BASIC_SERVICE_MAP.items():
                if key in context['basic_service']:
                    service_amount += context['basic_service'][key]['amount']
                    service_cost += context['basic_service'][key]['cost']
                    thead.append([
                        value,
                        f"R$ {make_price(context['basic_service'][key]['price'])}",
                        str(context['basic_service'][key]['amount']),
                        f"R$ {make_price(context['basic_service'][key]['cost'])}"])

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
        for phonecall in context['phonecall_long_distance']:
            if phonecall['calltype'] == LDN:
                cost_ldn = phonecall['cost_sum']
                qnt_ldn = phonecall['count']
                value_unid_ldn = phonecall['value_unid']
            elif phonecall['calltype'] == VC2:
                cost_vc2 = phonecall['cost_sum']
                qnt_vc2 = phonecall['count']
                value_unid_vc2 = phonecall['value_unid']
            elif phonecall['calltype'] == VC3:
                cost_vc3 = phonecall['cost_sum']
                qnt_vc3 = phonecall['count']
                value_unid_vc3 = phonecall['value_unid']
        for phonecall in context['phonecall_local']:
            if phonecall['calltype'] == LOCAL:
                cost_local = phonecall['cost_sum']
                qnt_local = phonecall['count']
                value_unid_local = phonecall['value_unid']
            elif phonecall['calltype'] == VC1:
                cost_vc1 = phonecall['cost_sum']
                qnt_vc1 = phonecall['count']
                value_unid_vc1 = phonecall['value_unid']
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
            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#ffffff')),
            ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
        tblstyle = TableStyle(array_tblstyle)
        thead = [[
            'Local Fixo-Fixo Extragrupo',
            f"R$ {make_price(value_unid_local)}",
            qnt_local,
            f"R$ {make_price(cost_local)}"
        ], [
            'Local Fixo-Móvel (VC1)',
            f"R$ {make_price(value_unid_vc1)}",
            qnt_vc1,
            f"R$ {make_price(cost_vc1)}"
        ]]
        size = (self._width - 50) / 5
        tbl = Table(
            thead,
            colWidths=[size * 2, size, size, size],
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
            ('FONTSIZE', (0, 0), (-1, -1), 9),  # middle column
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#ffffff')),
            ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.50, colors.white)]
        tblstyle = TableStyle(array_tblstyle)
        thead = [[
            'LDN-fixo/fixo-D1/D2/D3/D4',
            f"R$ {make_price(value_unid_ldn)}",
            qnt_ldn,
            f"R$ {make_price(cost_ldn)}"
        ], [
            'LDN-VC2 Fixo-Móvel',
            f"R$ {make_price(value_unid_vc2)}",
            qnt_vc2,
            f"R$ {make_price(cost_vc2)}"
        ], [
            'LDN-VC3 Fixo-Móvel',
            f"R$ {make_price(value_unid_vc3)}",
            qnt_vc3,
            f"R$ {make_price(cost_vc3)}"
        ]]
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
        total_comunication = float(cost_total)-float(service_cost)
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
        thead = [['Total dos Serviços', f"R$ {make_price(cost_total)}"]]
        size = (self._width - 50) / 5
        tbl = Table(
            thead,
            colWidths=[size * 4, size],
            rowHeights=[20 for x in range(len(thead))])
        tbl.setStyle(tblstyle)
        self._story.append(tbl)
        return self.close_resume()


class SystemReportOrganization(object):

    def __init__(self, dateBegin, dateEnd, reportTitle, context):
        self._dateBegin = dateBegin
        self._dateEnd = dateEnd
        self._issueDate = datetime.now().strftime('%d/%m/%Y')
        self._reportTitle = reportTitle
        self._orgLogo = \
            context['organization'].settings.logo.name \
            if context['organization'].settings.logo else None
        self._buffer = io.BytesIO()
        self._doc = SimpleDocTemplate(
            self._buffer,
            rightMargin=35,
            leftMargin=35,
            topMargin=125,
            bottomMargin=56)
        self._width, self._height = self._doc.pagesize
        self._story = []

        pdfmetrics.registerFont(TTFont('Sans',  "Microsoft Sans Serif.ttf"))
        self.style = ParagraphStyle(
            name='Sans',
            fontName='Sans',
            fontSize=8)

    def header(self, canvas, doc):

        header_list = []
        if self._orgLogo:
            header_list.append({
                'text': f'<img src="{settings.MEDIA_ROOT}{self._orgLogo}"'
                        'width="550" height="66" valign="top"/>',
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

    def create_header_and_footer(self, canvas, doc):
        """
        Add the header, title and footer to each page
        """
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
        for company, call_company_map in context.items():
            service_amount = 0
            service_cost = 0
            if company == 'SERVIÇOS DE COMUNICAÇÃO':
                self.insert_title_table(title=company)
                value_service_comunication_total = call_company_map['cost_sum']

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
                    colWidths=[size * 2, size, size, size],
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
                        'desc': 'Local Fixo-Móvel (VC1)'
                    }, {
                        'type': VC2,  # VC2
                        'desc': 'Local Fixo-Móvel (VC2)'
                    }, {
                        'type': VC3,  # VC3
                        'desc': 'Local Fixo-Móvel (VC3)'
                    }]
                thead = []
                for local in local_list:
                    if local['type'] in call_company_map:
                        call_company = call_company_map[local['type']]
                        if type(call_company) is not dict:
                            call_company = call_company._asdict()
                        minutes = call_company['billedtime_sum']
                        thead.append([
                            local['desc'],
                            str(call_company['count']),
                            time_format(minutes),
                            f"R$ {make_price(call_company['cost_sum'])}"])
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
                if 'local' in call_company_map:
                    minutes = call_company_map['local']['billedtime_sum']
                    thead = [[
                        'Total de Discagem Local',
                        str(call_company_map['local']['count']),
                        time_format(minutes),
                        f"R$ {make_price(call_company_map['local']['cost_sum'])}"]]
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
                if LDN in call_company_map:
                    call_company = call_company_map[LDN]
                    if type(call_company) is not dict:
                        call_company = call_company._asdict()
                    minutes = call_company['billedtime_sum']
                    thead = [[
                        'LDN-fixo/fixo-D1/D2/D3/D4',
                        str(call_company['count']),
                        time_format(minutes),
                        f"R$ {make_price(call_company['cost_sum'])}"]]
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
                if 'national' in call_company_map:
                    minutes = call_company_map['national']['billedtime_sum']
                    thead = [[
                        'Total de Longa Distancia Nacional',
                        str(call_company_map['national']['count']),
                        time_format(minutes),
                        f"R$ {make_price(call_company_map['national']['cost_sum'])}"]]
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
                thead = [['Longa Distância Internacional', '0', '00:00:00', 'R$ 0,00']]
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
                if 'international' in call_company_map:
                    minutes = call_company_map['international']['billedtime_sum']
                    thead = [[
                        'Total de Longa Distancia Internacional',
                        str(call_company_map['international']['count']),
                        time_format(minutes),
                        f"R$ {make_price(call_company_map['international']['cost_sum'])}"]]
                else:
                    thead = [[
                        'Total de Longa Distancia Internacional',
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
                minutes = call_company_map['billedtime_sum'] * 60
                thead = [[
                    'TOTAL DOS SERVIÇOS DE COMUNICAÇÃO',
                    str(call_company_map['count']),
                    time_format(minutes),
                    f"R$ {make_price(call_company_map['cost_sum'])}"]]
                size = (self._width - 50) / 5
                tbl = Table(
                    thead,
                    colWidths=[size * 2, size, size, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)

                self._story.append(tbl)
                self.space_between_tables()
                self.space_between_tables2()
            elif company == 'SERVIÇOS BÁSICOS':
                self.insert_title_table(title=company)

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
                for key, value in BASIC_SERVICE_MAP.items():
                    if key in call_company_map:
                        service_amount += call_company_map[key]['amount']
                        service_cost += call_company_map[key]['cost']
                        value_mask = make_price(call_company_map[key]['cost'])
                        thead.append([
                            value,
                            str(call_company_map[key]['amount']),
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
                    f"R$ {make_price(service_cost)}"]]
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
                self.insert_title_table(title=f"Cliente: {company} - {call_company_map['desc']}")

                if 'service_basic' in call_company_map:
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

                    for key, value in BASIC_SERVICE_MAP.items():
                        if key in call_company_map:
                            service_amount += call_company_map[key]['amount']
                            service_cost += call_company_map[key]['cost']
                            thead.append([
                                value,
                                f"R$ {make_price(call_company_map[key]['price'])}",
                                str(call_company_map[key]['amount']),
                                f"R$ {make_price(call_company_map[key]['cost'])}"])

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
                        f"R$ {make_price(service_cost)}"]]
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
                thead = [[
                    'SERVIÇO', 'VALOR UNITÁRIO', 'CHAMADAS', 'TEMPO FATURADO', 'VALOR PERÍODO']]
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
                        'desc': 'Local Fixo-Móvel (VC1)'
                    }, {
                        'type': VC2,  # VC2
                        'desc': 'Local Fixo-Móvel (VC2)'
                    }, {
                        'type': VC3,  # VC3
                        'desc': 'Local Fixo-Móvel (VC3)'
                    }]
                thead = []
                for local in local_list:
                    if local['type'] in call_company_map:
                        call_company = call_company_map[local['type']]
                        if type(call_company) is not dict:
                            call_company = call_company._asdict()
                        minutes = call_company['billedtime_sum']
                        thead.append([
                            local['desc'],
                            f"R$ {make_price(call_company['price'])}",
                            str(call_company['count']),
                            time_format(minutes),
                            f"R$ {make_price(call_company['cost_sum'])}"])
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
                        f"R$ {make_price(call_company_map['local']['cost_sum'])}"]]
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
                        f"R$ {make_price(call_company['price'])}",
                        str(call_company['count']),
                        time_format(minutes),
                        f"R$ {make_price(call_company['cost_sum'])}"]]
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
                if 'national' in call_company_map:
                    minutes = call_company_map['national']['billedtime_sum']
                    thead = [[
                        'Total de Longa Distancia Nacional',
                        str(call_company_map['national']['count']),
                        time_format(minutes),
                        f"R$ {make_price(call_company_map['national']['cost_sum'])}"]]
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
                if 'international' in call_company_map:
                    minutes = call_company_map['international']['billedtime_sum']
                    thead = [[
                        'Total de Longa Distancia Internacional',
                        str(call_company_map['international']['count']),
                        time_format(minutes),
                        f"R$ {make_price(call_company_map['international']['cost_sum'])}"]]
                else:
                    thead = [[
                        'Total de Longa Distancia Internacional',
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
                minutes = call_company_map['billedtime_sum'] * 60
                thead = [[
                    'TOTAL DOS SERVIÇOS DE COMUNICAÇÃO',
                    str(call_company_map['count']),
                    time_format(minutes),
                    f"R$ {make_price(call_company_map['cost_sum'])}"]]
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

                value_total = float(service_cost) + float(call_company_map['cost_sum'])

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
                minutes = call_company_map['billedtime_sum'] * 60
                thead = [[
                    'TOTAL DOS SERVIÇOS',
                    f"R$ {make_price(value_total)}"]]
                size = (self._width - 50) / 6
                tbl = Table(
                    thead,
                    colWidths=[size * 5, size],
                    rowHeights=[20 for x in range(len(thead))])
                tbl.setStyle(tblstyle)
                self._story.append(tbl)
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
        minutes = call_company_map['billedtime_sum'] * 60
        thead = [[
            'TOTAL DOS SERVIÇOS',
            f"R$ {make_price(value_total)}"]]
        size = (self._width - 50) / 6
        tbl = Table(
            thead,
            colWidths=[size * 5, size],
            rowHeights=[20 for x in range(len(thead))])
        tbl.setStyle(tblstyle)
        self._story.append(tbl)

        return self.close()
