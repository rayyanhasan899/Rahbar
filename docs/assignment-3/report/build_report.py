"""Render the eight-page report: the handoff draft, or the final version with the screenshot appendix."""
from __future__ import annotations
import io
import json
from pathlib import Path
from xml.sax.saxutils import escape
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image

ROOT = Path(__file__).resolve().parent


def build() -> None:
    data = json.loads((ROOT / 'report-content.json').read_text(encoding='utf-8'))
    final = data.get('status') == 'FINAL'
    if not (final or data.get('status') == 'DRAFT - NOT SUBMISSION READY') or len(data['pages']) != 8:
        raise ValueError('The report needs eight main pages and status FINAL or the draft status.')
    styles = {
        'title': ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor('#153349'), spaceAfter=14),
        'body': ParagraphStyle('body', fontName='Helvetica', fontSize=9.5, leading=13, spaceAfter=9),
        'cell': ParagraphStyle('cell', fontName='Helvetica', fontSize=8, leading=10.5),
        'head': ParagraphStyle('head', fontName='Helvetica-Bold', fontSize=8, leading=10.5, textColor=colors.white),
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
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#153349')),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('GRID', (0,0), (-1,-1), .35, colors.HexColor('#ccd5dc')),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f2f5f8'), colors.white]),
                ('TOPPADDING', (0,0), (-1,-1), 7), ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ]))
            story.extend([table, Spacer(1, 12)])
        for paragraph in page.get('after', []):
            story.append(text(paragraph))
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor('#9b3131'))
        canvas.setFont('Helvetica-Bold', 7)
        if not final:
            canvas.drawString(40, 27, 'HANDOFF DRAFT | Live results, human provenance and screenshots pending | Do not submit')
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(A4[0]-40, 16, f'{doc.page}' if final else f'{doc.page} / 8')
        canvas.restoreState()
    for shot in data.get('appendix', []):
        story.append(PageBreak())
        story.append(text(f"Appendix {shot['label']}. {shot['caption']}", 'title'))
        shot_image = PILImage.open(ROOT / shot['path'])
        if shot_image.width > shot_image.height:
            shot_image = shot_image.rotate(90, expand=True)
        buffer = io.BytesIO()
        shot_image.save(buffer, 'PNG')
        buffer.seek(0)
        picture = Image(buffer)
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
