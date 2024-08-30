import re
import time
from color import Color
from fpdf import FPDF
from chat_config import ChatConfig
import json
from pathlib import Path

def save_log(log_file_name, chat_history):
    """Save conversation log to a JSON file"""
    log_file_name = f"{ChatConfig.LOG_FOLDER}/{log_file_name}.json"
    with open(log_file_name, "w") as file:
        json.dump(chat_history, file, indent=4)
    print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.PASTELPINK}Conversation history saved to {log_file_name}{Color.ENDC}\n")

class PDF(FPDF):
    def header(self):
        """Custom header for each page"""
        self.set_font("DejaVu", 'BI', 12)
        self.set_text_color(0, 0, 128)  # Dark Blue
        self.cell(0, 10, 'Conversation Log', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        """Custom footer with page numbering"""
        self.set_y(-15)
        self.set_font("DejaVu", 'I', 8)
        self.set_text_color(128, 128, 128)  # Gray
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def add_fonts(pdf):
    """Add all necessary fonts for the PDF."""
    fonts_path = Path(__file__).parent / "fonts"

    # Register each font with its various styles
    pdf.add_font("DejaVu", '', str(fonts_path / "DejaVuSans.ttf"), uni=True)
    pdf.add_font("DejaVu", 'B', str(fonts_path / "DejaVuSans-Bold.ttf"), uni=True)
    pdf.add_font("DejaVu", 'I', str(fonts_path / "DejaVuSans-Oblique.ttf"), uni=True)
    pdf.add_font("DejaVu", 'BI', str(fonts_path / "DejaVuSans-BoldOblique.ttf"), uni=True)

    pdf.add_font("DejaVuSansMono", '', str(fonts_path / "DejaVuSansMono-BoldOblique.ttf"), uni=True)
    pdf.add_font("DejaVuSerif", '', str(fonts_path / "DejaVuSerif.ttf"), uni=True)
    pdf.add_font("DejaVuSerif", 'B', str(fonts_path / "DejaVuSerif-Bold.ttf"), uni=True)
    pdf.add_font("DejaVuSerif", 'I', str(fonts_path / "DejaVuSerif-Italic.ttf"), uni=True)
    pdf.add_font("DejaVuSerif", 'BI', str(fonts_path / "DejaVuSerif-BoldItalic.ttf"), uni=True)

    pdf.add_font("DejaVuSerifCondensed", '', str(fonts_path / "DejaVuSerifCondensed.ttf"), uni=True)
    pdf.add_font("DejaVuSerifCondensed", 'B', str(fonts_path / "DejaVuSerifCondensed-Bold.ttf"), uni=True)
    pdf.add_font("DejaVuSerifCondensed", 'I', str(fonts_path / "DejaVuSerifCondensed-Italic.ttf"), uni=True)
    pdf.add_font("DejaVuSerifCondensed", 'BI', str(fonts_path / "DejaVuSerifCondensed-BoldItalic.ttf"), uni=True)

def replace_markdown(text, pdf):
    """Enhanced function to replace Markdown elements for PDF formatting."""
    bold_pattern = re.compile(r'\*\*(.*?)\*\*')  # Bold text
    italic_pattern = re.compile(r'\*(.*?)\*')  # Italic text
    header_patterns = [
        (re.compile(r'^######\s*(.*)', re.MULTILINE), 14, "DejaVuSerifCondensed", 'BI'),   # H6
        (re.compile(r'^#####\s*(.*)', re.MULTILINE), 16, "DejaVuSerifCondensed", 'B'),    # H5
        (re.compile(r'^####\s*(.*)', re.MULTILINE), 18, "DejaVuSerif", 'BI'),     # H4
        (re.compile(r'^###\s*(.*)', re.MULTILINE), 20, "DejaVuSerif", 'B'),       # H3
        (re.compile(r'^##\s*(.*)', re.MULTILINE), 22, "DejaVu", 'B'),        # H2
        (re.compile(r'^#\s*(.*)', re.MULTILINE), 24, "DejaVu", 'B')         # H1
    ]
    bullet_list_pattern = re.compile(r'^\s*[-*+]\s+(.*)', re.MULTILINE)  # Bullet list
    numbered_list_pattern = re.compile(r'^\s*\d+\.\s+(.*)', re.MULTILINE)  # Numbered list
    code_pattern = re.compile(r'`([^`]+)`')  # Inline code
    block_code_pattern = re.compile(r'```([^`]+)```', re.DOTALL)  # Block code

    for pattern, font_size, font, style in header_patterns:
        matches = pattern.findall(text)
        for match in matches:
            pdf.set_font(font, style, font_size)
            pdf.set_text_color(0, 0, 0)  # Black
            pdf.multi_cell(0, 10, match.strip())
            text = pattern.sub('', text, count=1)

    text = bullet_list_pattern.sub(lambda m: f" • {m.group(1).strip()}", text)
    text = numbered_list_pattern.sub(lambda m: f" {m.group(0).strip()}", text)
    text = block_code_pattern.sub(lambda m: format_code_block(m.group(1), pdf), text)
    text = code_pattern.sub(lambda m: format_inline_code(m.group(1), pdf), text)
    text = bold_pattern.sub(lambda m: format_bold_text(m.group(1), pdf), text)
    text = italic_pattern.sub(lambda m: format_italic_text(m.group(1), pdf), text)

    return text

def format_code_block(code, pdf):
    """Format multi-line code blocks."""
    pdf.set_font("DejaVuSansMono", '', 10)
    pdf.set_fill_color(240, 240, 240)  # Light grey background
    pdf.multi_cell(0, 8, code.strip(), fill=True)
    pdf.ln(2)
    return ''

def format_inline_code(code, pdf):
    """Format inline code."""
    pdf.set_font("DejaVuSansMono", '', 10)
    pdf.set_text_color(0, 102, 204)  # Blue color for inline code
    return f' {code} '

def format_bold_text(text, pdf):
    """Format bold text."""
    pdf.set_font("DejaVu", 'B', 11)
    pdf.set_text_color(0, 0, 0)  # Black
    return text

def format_italic_text(text, pdf):
    """Format italic text."""
    pdf.set_font("DejaVu", 'I', 11)
    pdf.set_text_color(0, 0, 0)  # Black
    return text

def parse_markdown_to_pdf(pdf, text):
    """Convert Markdown-formatted text to PDF content."""
    formatted_text = replace_markdown(text, pdf)
    pdf.multi_cell(0, 10, formatted_text)
    pdf.ln(5)

def print_log(log_file_name, chat_history):
    """Save conversation log to a PDF file"""
    log_file_name = f"{ChatConfig.LOG_FOLDER}/{log_file_name}.pdf"
    pdf = PDF()

    add_fonts(pdf)

    # Title Page
    pdf.add_page()
    pdf.set_font("DejaVu", 'B', 18)
    pdf.set_text_color(0, 0, 128)  # Dark Blue
    pdf.cell(0, 10, 'Conversation Log', ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("DejaVu", '', 14)
    pdf.set_text_color(0, 0, 0)  # Black
    pdf.cell(0, 10, f"Log File: {log_file_name}", ln=True, align='C')
    pdf.cell(0, 10, f"Date: {time.strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(20)

    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("DejaVu", '', 12)

    for entry in chat_history:
        role = entry.get("role", "unknown")
        parts = entry.get("parts", [])

        # Title for each new section
        if role == "user":
            pdf.set_font("DejaVuSerifCondensed", 'B', 14)
            pdf.set_text_color(0, 102, 204)  # Blue for user
            pdf.cell(0, 10, 'User:', ln=True)
        elif role == "model":
            pdf.set_font("DejaVuSerifCondensed", 'BI', 14)
            pdf.set_text_color(0, 153, 0)  # Green for model
            pdf.cell(0, 10, 'Model:', ln=True)
        else:
            pdf.set_font("DejaVu", '', 12)
            pdf.set_text_color(0, 0, 0)  # Black
            pdf.cell(0, 10, f'{role.capitalize()}:', ln=True)

        pdf.set_font("DejaVu", '', 12)
        pdf.set_text_color(0, 0, 0)  # Black
        for part in parts:
            parse_markdown_to_pdf(pdf, part)
        pdf.ln(10)

    pdf.output(log_file_name)
    print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.PASTELPINK}Conversation history saved to {log_file_name}{Color.ENDC}\n")
