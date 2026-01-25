from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Frame, PageTemplate, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT

def create_structured_catalog(input_md, output_pdf):
    doc = SimpleDocTemplate(output_pdf, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)

    styles = getSampleStyleSheet()
    
    # 1. Instructor Style (Level 0 Folder)
    instructor_style = ParagraphStyle(
        'InstructorHeader',
        parent=styles['Heading2'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#2c3e50'), # Dark Blue-Grey
        backColor=colors.HexColor('#ecf0f1'), # Light Grey Background
        borderPadding=(5, 5, 20, 5),          # Top, Right, Bottom, Left (Approx)
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )

    # 2. Series Style (Level 1 Folder)
    series_style = ParagraphStyle(
        'SeriesHeader',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#e67e22'), # Orange/Bronze
        leftIndent=10,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    
    # 3. Generic Subfolder (Level 2+)
    subfolder_style = ParagraphStyle(
        'SubFolder',
        parent=styles['Heading4'],
        fontSize=11,
        textColor=colors.HexColor('#7f8c8d'),
        leftIndent=20,
        spaceBefore=5,
        spaceAfter=2
    )

    # 4. Video Files
    video_style = ParagraphStyle(
        'VideoFile',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        leftIndent=25,
        spaceBefore=1,
        spaceAfter=1,
        bulletIndent=15,
        bulletFontName='Symbol'
    )

    story = []
    
    # Title Page
    story.append(Paragraph("Jiu-Jitsu Video Library", styles['Title']))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("<b>Catalog hierarchy:</b> Instructor > Series > Videos", styles['Normal']))
    story.append(Spacer(1, 0.5*inch))

    with open(input_md, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_section = [] # To group items for KeepTogether if needed

    for line in lines:
        line = line.strip('\n')
        # Basic ASCII cleaning
        line = line.encode('latin-1', 'ignore').decode('latin-1')

        if line.startswith("#") or line.startswith("**Source"):
            continue

        raw_content = line.strip()
        
        # Calculate indentation depth (0 = Instructor, 1 = Series, 2 = Subfolders)
        # Markdown uses 2 spaces per level in the previous script output
        indent_spaces = len(line) - len(line.lstrip(' '))
        depth = indent_spaces // 2

        if not raw_content:
            continue

        # Handle Folders
        if "**" in raw_content:
            # - **📁 Name/**
            clean_name = raw_content.replace("- ", "").replace("**", "").replace("📁 ", "").replace("/", "")
            
            if depth == 0:
                # Level 0: Instructor
                story.append(Spacer(1, 10))
                story.append(Paragraph(f"<b>{clean_name}</b>", instructor_style))
            elif depth == 1:
                # Level 1: Series
                story.append(Paragraph(f"{clean_name}", series_style))
            else:
                # Level 2+: Deeper Categories
                indent_amount = (depth - 1) * 10
                style = ParagraphStyle('DynSub', parent=subfolder_style, leftIndent=20 + indent_amount)
                story.append(Paragraph(f"📂 {clean_name}", style))

        # Handle Files
        elif raw_content.startswith("- "):
            # - 📄 Filename
            clean_name = raw_content.replace("- ", "").replace("📄 ", "")
            
            # Align file indentation with its parent
            # Base indent for files is dependent on depth
            file_indent = 25 + (depth * 10)
            
            f_style = ParagraphStyle(
                'DynFile', 
                parent=video_style, 
                leftIndent=file_indent
            )
            story.append(Paragraph(f"• {clean_name}", f_style))

    doc.build(story)

if __name__ == "__main__":
    create_structured_catalog("JiuJitsu_Catalog.md", "JiuJitsu_Catalog_Hierarchy.pdf")
