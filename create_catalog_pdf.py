from fpdf import FPDF
import re

class PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'Jiu-Jitsu Video Catalog', border=False, align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

def create_pdf(input_md, output_pdf):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Add Free Unicode Font if standard fonts fail for special chars, 
    # but for simplicity we'll try to stick to standard encoding or replace chars.
    # To handle unicode properly in fpdf2, loading a TTF is best, but we'll try basic approach first.
    
    with open(input_md, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    pdf.set_font("helvetica", size=10)
    
    replacements = {
        '\u2013': '-', # en-dash
        '\u2014': '--', # em-dash
        '\u2018': "'", # left quote
        '\u2019': "'", # right quote
        '\u201c': '"', # left double quote
        '\u201d': '"', # right double quote
    }

    for line in lines:
        line = line.strip('\n')
        # Replace common chars
        for k, v in replacements.items():
            line = line.replace(k, v)
        # Strip remaining unsupported chars
        line = line.encode('latin-1', 'ignore').decode('latin-1')

        
        # Skip title as it's in header
        if line.startswith('# Jiu-Jitsu Video Catalog'):
            continue
            
        # Source Dir
        if line.startswith('**Source Directory:**'):
            pdf.set_font("helvetica", 'B', 10)
            pdf.cell(0, 8, txt=line.replace('**', '').replace('`', ''), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", size=10)
            pdf.ln(2)
            continue
            
        # Determine indentation
        indent_level = (len(line) - len(line.lstrip(' '))) // 2
        content = line.strip()
        
        # Format Folder
        if '**' in content: 
            # It's a folder line like: - **📁 Folder Name/**
            clean_text = content.replace('**', '').replace('- ', '').replace('📁 ', '').replace('📄 ', '')
            pdf.set_font("helvetica", 'B', 10)
            pdf.set_x(10 + (indent_level * 5))
            # Use raw string or encode to latin-1 to avoid errors with standard fonts if possible
            # Replacing common emojis for text only version if font doesn't support
            clean_text = f"[DIR] {clean_text}"
            try:
                pdf.cell(0, 6, txt=clean_text, new_x="LMARGIN", new_y="NEXT")
            except UnicodeEncodeError:
                pdf.cell(0, 6, txt=clean_text.encode('latin-1', 'replace').decode('latin-1'), new_x="LMARGIN", new_y="NEXT")
                
        # Format File
        elif content.startswith('- '):
            clean_text = content.replace('- ', '').replace('📄 ', '')
            pdf.set_font("helvetica", '', 10)
            pdf.set_x(10 + (indent_level * 5))
            clean_text = f"- {clean_text}"
            try:
                pdf.cell(0, 6, txt=clean_text, new_x="LMARGIN", new_y="NEXT")
            except UnicodeEncodeError:
                pdf.cell(0, 6, txt=clean_text.encode('latin-1', 'replace').decode('latin-1'), new_x="LMARGIN", new_y="NEXT")
        
        else:
            # Empty lines or other text
            if content:
                pdf.write(5, content)
                pdf.ln()

    pdf.output(output_pdf)

if __name__ == "__main__":
    create_pdf("JiuJitsu_Catalog.md", "JiuJitsu_Catalog.pdf")
