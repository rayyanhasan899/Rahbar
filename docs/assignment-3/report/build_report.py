"""Render the eight-page report: the handoff draft, or the final version with the screenshot appendix."""
from __future__ import annotations
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image

ROOT = Path(__file__).resolve().parent


def build() -> None:
    rl_config.canvas_basefontname = 'Times-Roman'
    data = json.loads((ROOT / 'report-content.json').read_text(encoding='utf-8'))
    final = data.get('status') == 'FINAL'
    if not (final or data.get('status') == 'DRAFT - NOT SUBMISSION READY') or len(data['pages']) != 8:
        raise ValueError('The report needs eight main pages and status FINAL or the draft status.')
    styles = {
        'title': ParagraphStyle('title', fontName='Times-Bold', fontSize=18, leading=22, textColor=colors.black, spaceAfter=14),
        'body': ParagraphStyle('body', fontName='Times-Roman', fontSize=11, leading=14, textColor=colors.black, spaceAfter=9),
        'cell': ParagraphStyle('cell', fontName='Times-Roman', fontSize=9.5, leading=11.5, textColor=colors.black),
        'head': ParagraphStyle('head', fontName='Times-Bold', fontSize=9.5, leading=11.5, textColor=colors.black),
    }
    def text(value, style='body'):
        return Paragraph(escape(str(value)).replace('\n', '<br/>'), styles[style])
    story = []
    for index, page in enumerate(data['pages']):
        if index:
            story.append(PageBreak())
        story.append(text(page['title'], 'title'))
        if not final:
            story.append(text('DRAFT - NOT SUBMISSION READY'))
        for paragraph in page.get('paragraphs', []):
            story.append(text(paragraph))
        for block in page.get('tables', []):
            widths = block.get('widths') or [1] * len(block['headers'])
            total = sum(widths)
            width = A4[0] - 80
            rows = [[text(v, 'head') for v in block['headers']]] + [[text(v, 'cell') for v in row] for row in block['rows']]
            table = Table(rows, colWidths=[width * w / total for w in widths], repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,-1), 'Times-Roman'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('GRID', (0,0), (-1,-1), .5, colors.black),
                ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            story.extend([table, Spacer(1, 12)])
        for paragraph in page.get('after', []):
            story.append(text(paragraph))
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.black)
        canvas.setFont('Times-Bold', 7)
        if not final:
            canvas.drawString(40, 27, 'HANDOFF DRAFT | Live results, human provenance and screenshots pending | Do not submit')
        canvas.setFillColor(colors.black)
        canvas.setFont('Times-Roman', 9)
        canvas.drawRightString(A4[0]-40, 16, f'{doc.page}' if final else f'{doc.page} / 8')
        canvas.restoreState()
    for shot in data.get('appendix', []):
        story.append(PageBreak())
        story.append(text(f"Appendix {shot['label']}. {shot['caption']}", 'title'))
        picture = Image(str(ROOT / shot['path']))
        scale = min((A4[0] - 80) / picture.imageWidth, (A4[1] - 210) / picture.imageHeight)
        picture.drawWidth, picture.drawHeight = picture.imageWidth * scale, picture.imageHeight * scale
        story.append(picture)
    output = ROOT / ('RAHBAR-A3-REPORT.pdf' if final else 'RAHBAR-A3-HANDOFF-DRAFT.pdf')
    doc = SimpleDocTemplate(str(output), pagesize=A4, leftMargin=40, rightMargin=40, topMargin=35, bottomMargin=45,
                            title='RAHBAR Assignment 03' if final else 'RAHBAR Assignment 03 - Handoff Draft',
                            author='Abdul Moez Yousaf, Syed Rayyan Hassan' if final else 'Rayyan Hassan')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(output)


if __name__ == '__main__':
    build()
