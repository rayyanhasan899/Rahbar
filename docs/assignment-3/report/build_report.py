"""Render the eight-page report: the handoff draft, or the final version with the screenshot appendix."""
from __future__ import annotations
import io
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image

ROOT = Path(__file__).resolve().parent
TITLE = 'RAHBAR Assignment 03: RAGOps'
COURSE = 'CS4032, FAST-NUCES'
ROLLS = '24i-3048 | 24i-3000'
BORDER = 22
MARGIN = 40


def build() -> None:
    rl_config.canvas_basefontname = 'Times-Roman'
    data = json.loads((ROOT / 'report-content.json').read_text(encoding='utf-8'))
    final = data.get('status') == 'FINAL'
    if not (final or data.get('status') == 'DRAFT - NOT SUBMISSION READY') or len(data['pages']) != 8:
        raise ValueError('The report needs eight main pages and status FINAL or the draft status.')
    styles = {
        'title': ParagraphStyle('title', fontName='Times-Bold', fontSize=18, leading=22, textColor=colors.black, spaceAfter=14),
        'body': ParagraphStyle('body', fontName='Times-Roman', fontSize=11, leading=14, textColor=colors.black, spaceAfter=9,
                               alignment=TA_JUSTIFY),
        'cell': ParagraphStyle('cell', fontName='Times-Roman', fontSize=9.5, leading=11.5, textColor=colors.black),
        'head': ParagraphStyle('head', fontName='Times-Bold', fontSize=9.5, leading=11.5, textColor=colors.black),
        'wordmark': ParagraphStyle('wordmark', fontName='Times-Bold', fontSize=48, leading=56, textColor=colors.black,
                                   alignment=TA_CENTER),
        'cover-title': ParagraphStyle('cover-title', fontName='Times-Bold', fontSize=24, leading=30, textColor=colors.black,
                                      alignment=TA_CENTER, spaceAfter=10),
        'cover-line': ParagraphStyle('cover-line', fontName='Times-Roman', fontSize=14, leading=19, textColor=colors.black,
                                     alignment=TA_CENTER),
        'cover-cell': ParagraphStyle('cover-cell', fontName='Times-Roman', fontSize=14, leading=19, textColor=colors.black),
    }
    width = A4[0] - 2 * MARGIN

    def text(value, style='body'):
        return Paragraph(escape(str(value)).replace('\n', '<br/>'), styles[style])

    def cover():
        names = Table([[text('Abdul Moez Yousaf', 'cover-cell'), text('24i-3048', 'cover-cell')],
                       [text('Syed Rayyan Hassan', 'cover-cell'), text('24i-3000', 'cover-cell')]],
                      colWidths=[190, 90], hAlign='CENTER')
        names.setStyle(TableStyle([('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3)]))
        rule = Table([['']], colWidths=[width * 0.6], rowHeights=[1], hAlign='CENTER')
        rule.setStyle(TableStyle([('LINEABOVE', (0,0), (-1,-1), 1, colors.black)]))
        return [Spacer(1, 150), text('RAHBAR', 'wordmark'), Spacer(1, 10), rule, Spacer(1, 30),
                text(TITLE, 'cover-title'), text('CS4032 Software Construction and Design, Fall 2026', 'cover-line'),
                text('FAST-NUCES Islamabad', 'cover-line'), Spacer(1, 60), names, Spacer(1, 60),
                text('Submitted 28 November 2026', 'cover-line'), PageBreak()]

    def story():
        flow = cover()
        for index, page in enumerate(data['pages']):
            if index:
                flow.append(PageBreak())
            flow.append(text(page['title'], 'title'))
            if not final:
                flow.append(text('DRAFT - NOT SUBMISSION READY'))
            for paragraph in page.get('paragraphs', []):
                flow.append(text(paragraph))
            for block in page.get('tables', []):
                widths = block.get('widths') or [1] * len(block['headers'])
                total = sum(widths)
                rows = [[text(v, 'head') for v in block['headers']]] + [[text(v, 'cell') for v in row] for row in block['rows']]
                table = Table(rows, colWidths=[width * w / total for w in widths], repeatRows=1, hAlign='LEFT')
                table.setStyle(TableStyle([
                    ('FONTNAME', (0,0), (-1,-1), 'Times-Roman'),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('GRID', (0,0), (-1,-1), .5, colors.black),
                    ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ]))
                flow.extend([table, Spacer(1, 12)])
            for paragraph in page.get('after', []):
                flow.append(text(paragraph))
        for shot in data.get('appendix', []):
            flow.append(PageBreak())
            flow.append(text(f"Appendix {shot['label']}. {shot['caption']}", 'title'))
            picture = Image(str(ROOT / shot['path']))
            scale = min(width / picture.imageWidth, (A4[1] - 250) / picture.imageHeight)
            picture.drawWidth, picture.drawHeight = picture.imageWidth * scale, picture.imageHeight * scale
            flow.append(picture)
        return flow

    def border(canvas):
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(.8)
        canvas.rect(BORDER, BORDER, A4[0] - 2 * BORDER, A4[1] - 2 * BORDER)

    def cover_page(canvas, doc):
        canvas.saveState()
        border(canvas)
        canvas.restoreState()

    def page_frame(numbered):
        def decorate(canvas, doc):
            canvas.saveState()
            border(canvas)
            top = A4[1] - BORDER - 22
            canvas.setFillColor(colors.black)
            canvas.setFont('Times-Bold', 10)
            canvas.drawString(MARGIN, top, TITLE)
            canvas.setFont('Times-Roman', 10)
            canvas.drawRightString(A4[0] - MARGIN, top, COURSE)
            canvas.setLineWidth(.5)
            canvas.line(MARGIN, top - 6, A4[0] - MARGIN, top - 6)
            bottom = BORDER + 14
            canvas.line(MARGIN, bottom + 12, A4[0] - MARGIN, bottom + 12)
            canvas.setFont('Times-Roman', 9)
            canvas.drawString(MARGIN, bottom, ROLLS)
            number = doc.page - 1
            canvas.drawRightString(A4[0] - MARGIN, bottom, f'Page {number} of {numbered}' if final else f'{number} / 8')
            if not final:
                canvas.setFont('Times-Bold', 7)
                canvas.drawCentredString(A4[0] / 2, bottom, 'HANDOFF DRAFT | Do not submit')
            canvas.restoreState()
        return decorate

    def render(target, numbered):
        doc = SimpleDocTemplate(target, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=72, bottomMargin=66,
                                title='RAHBAR Assignment 03' if final else 'RAHBAR Assignment 03 - Handoff Draft',
                                author='Abdul Moez Yousaf, Syed Rayyan Hassan' if final else 'Rayyan Hassan')
        doc.build(story(), onFirstPage=cover_page, onLaterPages=page_frame(numbered))
        return doc.page - 1

    numbered = render(io.BytesIO(), 0)
    output = ROOT / ('RAHBAR-A3-REPORT.pdf' if final else 'RAHBAR-A3-HANDOFF-DRAFT.pdf')
    render(str(output), numbered)
    print(output, numbered, 'numbered pages')


if __name__ == '__main__':
    build()
