import time
from pathlib import Path
from typing import Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import re

# Import centralized logging
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Ensure reports directory exists
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


class MarkdownToPDFConverter:
    """Converts Markdown resume to professional PDF"""
    
    def __init__(self):
        logger.info("Initializing MarkdownToPDFConverter")
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        logger.info("✓ MarkdownToPDFConverter initialized")
    
    def _setup_custom_styles(self):
        """Define custom styles for resume PDF"""
        logger.debug("Setting up custom PDF styles for resume")
        
        # H1 - Name style
        if 'ResumeName' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ResumeName',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a365d'),
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ))
        
        # H2 - Section headings
        if 'ResumeSection' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ResumeSection',
                parent=self.styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#2563eb'),
                spaceAfter=8,
                spaceBefore=12,
                fontName='Helvetica-Bold',
                borderWidth=0,
                borderPadding=0,
                borderColor=colors.HexColor('#2563eb'),
                borderRadius=None
            ))
        
        # H3 - Job titles
        if 'ResumeJobTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ResumeJobTitle',
                parent=self.styles['Heading3'],
                fontSize=12,
                textColor=colors.HexColor('#1e40af'),
                spaceAfter=4,
                spaceBefore=8,
                fontName='Helvetica-Bold'
            ))
        
        # Body text
        if 'ResumeBody' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ResumeBody',
                parent=self.styles['Normal'],
                fontSize=10,
                leading=14,
                alignment=TA_LEFT,
                spaceAfter=6
            ))
        
        # Bullet points
        if 'ResumeBullet' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ResumeBullet',
                parent=self.styles['Normal'],
                fontSize=10,
                leading=14,
                leftIndent=20,
                bulletIndent=10,
                spaceAfter=4
            ))
        
        # Contact info / italic text
        if 'ResumeItalic' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ResumeItalic',
                parent=self.styles['Normal'],
                fontSize=10,
                leading=12,
                alignment=TA_CENTER,
                spaceAfter=4,
                textColor=colors.HexColor('#475569')
            ))
        
        logger.debug("✓ Custom styles configured")
    
    def _parse_markdown_to_elements(self, markdown_text: str) -> list:
        """Parse markdown and convert to PDF elements"""
        elements = []
        
        # Split by lines and process
        lines = markdown_text.strip().split('\n')
        i = 0
        is_first_heading = True
        
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                # Empty line - add small spacer
                elements.append(Spacer(1, 0.05 * inch))
                i += 1
                continue
            
            # H1 - Name (centered)
            if line.startswith('# '):
                name = line[2:].strip()
                elements.append(Paragraph(name, self.styles['ResumeName']))
                is_first_heading = False
                i += 1
                continue
            
            # H2 - Section headers
            if line.startswith('## '):
                section = line[3:].strip()
                # Add section divider line
                if not is_first_heading:
                    elements.append(Spacer(1, 0.1 * inch))
                elements.append(Paragraph(f"<b><font color='#2563eb'>{section}</font></b>", self.styles['ResumeSection']))
                # Add a line under section
                elements.append(Spacer(1, 0.05 * inch))
                i += 1
                continue
            
            # H3 - Job titles / subsections
            if line.startswith('### '):
                job_title = line[4:].strip()
                elements.append(Paragraph(f"<b>{job_title}</b>", self.styles['ResumeJobTitle']))
                i += 1
                continue
            
            # Italic text (dates, locations)
            if line.startswith('*') and line.endswith('*') and not line.startswith('**'):
                text = line[1:-1].strip()
                elements.append(Paragraph(f"<i>{text}</i>", self.styles['ResumeItalic']))
                i += 1
                continue
            
            # Bullet points
            if line.startswith('- ') or line.startswith('* '):
                bullet_text = line[2:].strip()
                # Process bold and italic markdown
                bullet_text = self._process_inline_markdown(bullet_text)
                elements.append(Paragraph(f"• {bullet_text}", self.styles['ResumeBullet']))
                i += 1
                continue
            
            # Regular paragraph
            processed_line = self._process_inline_markdown(line)
            elements.append(Paragraph(processed_line, self.styles['ResumeBody']))
            i += 1
        
        return elements
    
    def _process_inline_markdown(self, text: str) -> str:
        """Process inline markdown (bold, italic, links)"""
        # Bold text: **text** or __text__
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)
        
        # Italic text: *text* or _text_ (but not already processed)
        text = re.sub(r'(?<!\*)\*([^\*]+?)\*(?!\*)', r'<i>\1</i>', text)
        text = re.sub(r'(?<!_)_([^_]+?)_(?!_)', r'<i>\1</i>', text)
        
        # Links: [text](url)
        text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<link href="\2">\1</link>', text)
        
        # Escape special characters for ReportLab
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;').replace('>', '&gt;')
        
        # Restore our tags
        text = text.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
        text = text.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
        text = text.replace('&lt;link href="', '<link href="').replace('"&gt;', '">')
        text = text.replace('&lt;/link&gt;', '</link>')
        
        return text
    
    def convert_to_pdf(self, markdown_text: str, output_filename: str) -> Path:
        """
        Convert markdown resume to PDF
        
        Args:
            markdown_text: Resume in markdown format
            output_filename: Name of output PDF file (without extension)
        
        Returns:
            Path to generated PDF
        """
        logger.info("=" * 80)
        logger.info("📄 CONVERTING MARKDOWN TO PDF")
        logger.info("=" * 80)
        logger.info(f"Output filename: {output_filename}")
        logger.info(f"Markdown length: {len(markdown_text)} characters")
        
        start_time = time.time()
        
        try:
            pdf_path = REPORTS_DIR / f"{output_filename}.pdf"
            logger.debug(f"PDF will be saved to: {pdf_path.absolute()}")
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=letter,
                rightMargin=0.75 * inch,
                leftMargin=0.75 * inch,
                topMargin=0.75 * inch,
                bottomMargin=0.75 * inch
            )
            
            # Parse markdown and build elements
            logger.debug("Parsing markdown content...")
            elements = self._parse_markdown_to_elements(markdown_text)
            
            logger.info(f"Total elements to render: {len(elements)}")
            
            # Build PDF
            logger.debug("Rendering PDF...")
            doc.build(elements)
            
            # Get file size
            file_size_kb = pdf_path.stat().st_size / 1024
            duration = time.time() - start_time
            
            logger.info("=" * 80)
            logger.info("✅ PDF CONVERSION COMPLETE")
            logger.info("=" * 80)
            logger.info(f"File path: {pdf_path}")
            logger.info(f"File size: {file_size_kb:.2f} KB")
            logger.info(f"Duration: {duration:.2f}s")
            logger.info("=" * 80)
            
            return pdf_path
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error("=" * 80)
            logger.error("❌ PDF CONVERSION FAILED")
            logger.error("=" * 80)
            logger.error(f"Output filename: {output_filename}")
            logger.error(f"Error: {str(e)}")
            logger.error(f"Duration before failure: {duration:.2f}s")
            logger.error("=" * 80)
            logger.error("Full error details:", exc_info=True)
            raise


def get_markdown_converter():
    """Get or create a singleton instance of MarkdownToPDFConverter"""
    global _converter_instance
    if '_converter_instance' not in globals():
        _converter_instance = MarkdownToPDFConverter()
    return _converter_instance

