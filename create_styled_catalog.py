from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re

def create_styled_catalog(input_md, output_pdf):
    # Setup Document
    doc = SimpleDocTemplate(output_pdf, pagesize=letter,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)

    # Styles
    styles = getSampleStyleSheet()
    
    # Title Style
    title_style = ParagraphStyle(
        'CatalogTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#2c3e50')
    )
    
    # Section Header Style (Source Directory)
    meta_style = ParagraphStyle(
        'CatalogMeta',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=20
    )

    # Folder Style
    folder_style = ParagraphStyle(
        'CatalogFolder',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#2980b9'),
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )
    
    # Sub-Folder Style (for nested folders)
    subfolder_style = ParagraphStyle(
        'CatalogSubFolder',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#34495e'),
        leftIndent=20,
        spaceBefore=5
    )

    # File Style
    file_style = ParagraphStyle(
        'CatalogFile',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=colors.black,
        leftIndent=30,
        spaceBefore=1,
        bulletIndent=20
    )

    story = []

    # Read Content
    with open(input_md, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Process Lines
    story.append(Paragraph("Jiu-Jitsu Video Catalog", title_style))
    story.append(Spacer(1, 12))

    for line in lines:
        line = line.strip('\n')
        clean_text = line.encode('latin-1', 'ignore').decode('latin-1')

        # Skip Title Line from MD (we added it manually)
        if line.startswith("# Jiu-Jitsu"):
            continue

        # Meta Info
        if line.startswith("**Source Directory:**"):
            text = clean_text.replace("**", "")
            story.append(Paragraph(text, meta_style))
            story.append(Spacer(1, 12))
            continue

        indent_level = (len(line) - len(line.lstrip(' '))) // 2
        content = line.strip()

        # Folders
        if "**" in content:
            # - **📁 Folder Name/**
            # Remove MD formatting
            text = content.replace("- ", "").replace("**", "").replace("📁 ", "").replace("/", "")
            
            # Choose style based on depth
            if indent_level == 0:
                 story.append(Paragraph(f"<b>{text}</b>", folder_style))
            else:
                 # Calculate variable indent for subfolders
                 style = ParagraphStyle(
                    f'SubFolder-{indent_level}',
                    parent=subfolder_style,
                    leftIndent=20 * indent_level
                 )
                 story.append(Paragraph(f"<b>{text}</b>", style))

        # Files
        elif content.startswith("- "):
             text = content.replace("- ", "").replace("📄 ", "")
             
             style = ParagraphStyle(
                f'File-{indent_level}',
                parent=file_style,
                leftIndent=20 * indent_level + 10  # Files indented slightly more than their parent folder
             )
             story.append(Paragraph(text, style))

    doc.build(story)

if __name__ == "__main__":
    create_styled_catalog("JiuJitsu_Catalog.md", "JiuJitsu_Catalog_Styled.pdf")
