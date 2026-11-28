"""Render the eight-page report: the handoff draft, or the final version with the screenshot appendix.

Page 1 carries the names and roll numbers, so there is no separate cover page.
An appendix entry lists one or more screenshots under "paths"; they are placed two per page.
"""
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
        'heading': ParagraphStyle('heading', fontName='Times-Bold', fontSize=20, leading=24, textColor=colors.black,
                                  alignment=TA_CENTER, spaceAfter=12),
        'group': ParagraphStyle('group', fontName='Times-Roman', fontSize=11, leading=14, textColor=colors.black,
                                alignment=TA_CENTER),
        'body': ParagraphStyle('body', fontName='Times-Roman', fontSize=11, leading=14, textColor=colors.black, spaceAfter=9,
                               alignment=TA_JUSTIFY),
        'cell': ParagraphStyle('cell', fontName='Times-Roman', fontSize=9.5, leading=11.5, textColor=colors.black),
        'head': ParagraphStyle('head', fontName='Times-Bold', fontSize=9.5, leading=11.5, textColor=colors.black),
        'shot': ParagraphStyle('shot', fontName='Times-Italic', fontSize=9.5, leading=11.5, textColor=colors.black,
                               alignment=TA_CENTER, spaceBefore=4, spaceAfter=10),
    }
    width = A4[0] - 2 * MARGIN

    def text(value, style='body'):
        return Paragraph(escape(str(value)).replace('\n', '<br/>'), styles[style])

    def story():
        flow = []
        for index, page in enumerate(data['pages']):
            if index:
                flow.append(PageBreak())
            flow.append(text(page['title'], 'heading' if index == 0 else 'title'))
            if 'group' in page:
                group = page['group']
                members = Table([[text(name, 'cell'), text(roll, 'cell')] for name, roll in group['members']],
                                colWidths=[150, 70], hAlign='CENTER')
                members.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), 'Times-Roman'),
                                             ('GRID', (0,0), (-1,-1), .5, colors.black),
                                             ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3)]))
                flow.extend([members, Spacer(1, 6)])
                flow.extend(text(line, 'group') for line in group['lines'])
                flow.append(Spacer(1, 14))
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
            paths = shot['paths']
            for index, path in enumerate(paths):
                if index % 2 == 0:
                    flow.append(PageBreak())
                    heading = f"Appendix {shot['label']}. {shot['caption']}"
                    flow.append(text(heading if index == 0 else f"Appendix {shot['label']} (continued)", 'title'))
                picture = Image(str(ROOT / path))
                scale = min(width / picture.imageWidth, 270 / picture.imageHeight)
                picture.drawWidth, picture.drawHeight = picture.imageWidth * scale, picture.imageHeight * scale
                flow.append(picture)
                flow.append(text(f"{shot['label']}, screenshot {index + 1} of {len(paths)}: {Path(path).name}", 'shot'))
        return flow

    def border(canvas):
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(.8)
        canvas.rect(BORDER, BORDER, A4[0] - 2 * BORDER, A4[1] - 2 * BORDER)

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
            number = doc.page
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
        doc.build(story(), onFirstPage=page_frame(numbered), onLaterPages=page_frame(numbered))
        return doc.page

    numbered = render(io.BytesIO(), 0)
    output = ROOT / ('RAHBAR-A3-REPORT.pdf' if final else 'RAHBAR-A3-HANDOFF-DRAFT.pdf')
    render(str(output), numbered)
    print(output, numbered, 'numbered pages')


if __name__ == '__main__':
    build()
