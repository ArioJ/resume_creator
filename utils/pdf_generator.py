import time
from datetime import datetime
from pathlib import Path
from typing import Dict
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# Import centralized logging
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Ensure reports directory exists
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)
logger.info(f"Reports directory initialized: {REPORTS_DIR.absolute()}")


class PDFReportGenerator:
    """Generates professional PDF reports for resume analysis"""
    
    def __init__(self):
        logger.info("Initializing PDFReportGenerator")
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        logger.info("✓ PDFReportGenerator initialized with custom styles")
    
    def _setup_custom_styles(self):
        """Define custom styles for the PDF"""
        logger.debug("Setting up custom PDF styles")
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a365d'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Score style
        self.styles.add(ParagraphStyle(
            name='ScoreStyle',
            parent=self.styles['Normal'],
            fontSize=48,
            textColor=colors.HexColor('#2c5282'),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c5282'),
            spaceAfter=12,
            spaceBefore=16,
            fontName='Helvetica-Bold'
        ))
        
        # Body style
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=8
        ))
        
        logger.debug("✓ Custom styles configured")
    
    def _get_score_color(self, score: float) -> colors.Color:
        """Return color based on score"""
        if score >= 80:
            return colors.HexColor('#22c55e')  # Green
        elif score >= 60:
            return colors.HexColor('#eab308')  # Yellow
        else:
            return colors.HexColor('#ef4444')  # Red
    
    def _create_cover_page(self, analysis: Dict) -> list:
        """Create cover page elements"""
        elements = []
        
        # Title
        title = Paragraph("Resume Analysis Report", self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Overall score with color
        score = analysis['overall_score']
        score_color = self._get_score_color(score)
        
        score_style = ParagraphStyle(
            name='ColoredScore',
            parent=self.styles['ScoreStyle'],
            textColor=score_color
        )
        
        score_text = Paragraph(f"{score}/100", score_style)
        elements.append(score_text)
        
        subtitle = Paragraph("Overall Fit Score", self.styles['Heading3'])
        elements.append(subtitle)
        elements.append(Spacer(1, 0.5 * inch))
        
        # Executive summary
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeading']))
        summary = Paragraph(analysis['executive_summary'], self.styles['BodyText'])
        elements.append(summary)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Generation date
        date_text = f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        date_para = Paragraph(date_text, self.styles['Normal'])
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(date_para)
        
        elements.append(PageBreak())
        return elements
    
    def _create_dimension_scores_table(self, analysis: Dict) -> list:
        """Create table of dimension scores"""
        elements = []
        
        elements.append(Paragraph("Dimension Scores", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Prepare table data
        table_data = [['Dimension', 'Score', 'Weight']]
        
        for dim in analysis['dimensions'].keys():
            score = analysis['dimensions'][dim]['score']
            weight = analysis['dimension_weights'][dim]
            table_data.append([
                dim,
                f"{score}/100",
                f"{weight * 100:.0f}%"
            ])
        
        # Add overall score
        table_data.append(['Overall Score', f"{analysis['overall_score']}/100", '100%'])
        
        # Create table
        table = Table(table_data, colWidths=[3.5 * inch, 1.2 * inch, 1 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e2e8f0')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _create_skills_section(self, analysis: Dict) -> list:
        """Create skills analysis section"""
        elements = []
        
        elements.append(Paragraph("Skills Analysis", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Overlapping skills
        elements.append(Paragraph("Overlapping Skills", self.styles['Heading3']))
        if analysis['overlapping_skills']:
            skills_text = ", ".join(analysis['overlapping_skills'])
            skills_para = Paragraph(f"<b>Matching skills found:</b> {skills_text}", self.styles['BodyText'])
            elements.append(skills_para)
        else:
            elements.append(Paragraph("No clear overlapping skills identified.", self.styles['BodyText']))
        
        elements.append(Spacer(1, 0.2 * inch))
        
        # Skill gaps
        elements.append(Paragraph("Skill Gaps", self.styles['Heading3']))
        
        if analysis['skill_gaps']:
            gap_data = [['Skill', 'Importance', 'Suggestion']]
            
            for gap in analysis['skill_gaps']:
                gap_data.append([
                    gap.get('skill', 'N/A'),
                    gap.get('importance', 'N/A').upper(),
                    gap.get('suggestion', 'N/A')
                ])
            
            gap_table = Table(gap_data, colWidths=[1.5 * inch, 1 * inch, 4.2 * inch])
            gap_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fef2f2')]),
            ]))
            
            elements.append(gap_table)
        else:
            elements.append(Paragraph("No significant skill gaps identified.", self.styles['BodyText']))
        
        elements.append(PageBreak())
        return elements
    
    def _create_dimension_details(self, analysis: Dict) -> list:
        """Create detailed dimension analysis"""
        elements = []
        
        elements.append(Paragraph("Detailed Dimension Analysis", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.2 * inch))
        
        for dim, data in analysis['dimensions'].items():
            # Dimension name and score
            score = data['score']
            score_color = self._get_score_color(score)
            
            dim_title = f"<b>{dim}</b> - Score: <font color='{score_color.hexval()}'>{score}/100</font>"
            elements.append(Paragraph(dim_title, self.styles['Heading3']))
            
            # Analysis
            elements.append(Paragraph("<b>Analysis:</b>", self.styles['Normal']))
            analysis_para = Paragraph(data['analysis'], self.styles['BodyText'])
            elements.append(analysis_para)
            
            # Recommendations
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("<b>Recommendations:</b>", self.styles['Normal']))
            
            for i, rec in enumerate(data['recommendations'], 1):
                rec_para = Paragraph(f"{i}. {rec}", self.styles['BodyText'])
                elements.append(rec_para)
            
            elements.append(Spacer(1, 0.2 * inch))
        
        return elements
    
    def _create_recommendations_section(self, analysis: Dict) -> list:
        """Create overall recommendations section"""
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("Overall Recommendations", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.1 * inch))
        
        intro = Paragraph(
            "Based on the comprehensive analysis, here are the prioritized actions to improve your resume:",
            self.styles['BodyText']
        )
        elements.append(intro)
        elements.append(Spacer(1, 0.1 * inch))
        
        for i, rec in enumerate(analysis['overall_recommendations'], 1):
            rec_para = Paragraph(f"{i}. {rec}", self.styles['BodyText'])
            elements.append(rec_para)
            elements.append(Spacer(1, 0.05 * inch))
        
        return elements
    
    def generate_report(self, analysis: Dict, report_id: str) -> Path:
        """
        Generate complete PDF report
        
        Args:
            analysis: Complete analysis results
            report_id: Unique identifier for the report
        
        Returns:
            Path to generated PDF file
        """
        logger.info("=" * 80)
        logger.info("📄 GENERATING PDF REPORT")
        logger.info("=" * 80)
        logger.info(f"Report ID: {report_id}")
        logger.info(f"Overall Score: {analysis.get('overall_score', 'N/A')}")
        
        start_time = time.time()
        
        try:
            pdf_path = REPORTS_DIR / f"{report_id}.pdf"
            logger.debug(f"PDF will be saved to: {pdf_path.absolute()}")
            
            # Create PDF document
            logger.debug("Creating PDF document structure")
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=letter,
                rightMargin=0.75 * inch,
                leftMargin=0.75 * inch,
                topMargin=0.75 * inch,
                bottomMargin=0.75 * inch
            )
            
            # Build content
            elements = []
            
            logger.debug("Building cover page...")
            elements.extend(self._create_cover_page(analysis))
            
            logger.debug("Building dimension scores table...")
            elements.extend(self._create_dimension_scores_table(analysis))
            
            logger.debug("Building skills section...")
            elements.extend(self._create_skills_section(analysis))
            
            logger.debug("Building dimension details...")
            elements.extend(self._create_dimension_details(analysis))
            
            logger.debug("Building recommendations section...")
            elements.extend(self._create_recommendations_section(analysis))
            
            logger.info(f"Total elements to render: {len(elements)}")
            
            # Build PDF
            logger.debug("Rendering PDF...")
            doc.build(elements)
            
            # Get file size
            file_size_kb = pdf_path.stat().st_size / 1024
            
            duration = time.time() - start_time
            logger.info("=" * 80)
            logger.info("✅ PDF REPORT GENERATED SUCCESSFULLY")
            logger.info("=" * 80)
            logger.info(f"File path: {pdf_path}")
            logger.info(f"File size: {file_size_kb:.2f} KB")
            logger.info(f"Duration: {duration:.2f}s")
            logger.info("=" * 80)
            
            return pdf_path
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error("=" * 80)
            logger.error("❌ PDF REPORT GENERATION FAILED")
            logger.error("=" * 80)
            logger.error(f"Report ID: {report_id}")
            logger.error(f"Error: {str(e)}")
            logger.error(f"Duration before failure: {duration:.2f}s")
            logger.error("=" * 80)
            logger.error("Full error details:", exc_info=True)
            raise

