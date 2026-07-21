"""
PDF generation module using ReportLab.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from datetime import datetime
from typing import Dict, List
import os


class PDFGenerator:
    def __init__(self, output_path: str = "daily_newspaper.pdf"):
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1a1a2e'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Source header style
        self.styles.add(ParagraphStyle(
            name='SourceHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=HexColor('#16213e'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold',
            borderColor=HexColor('#e94560'),
            borderWidth=2,
            borderPadding=5,
            leftIndent=0
        ))
        
        # Article title style
        self.styles.add(ParagraphStyle(
            name='ArticleTitle',
            parent=self.styles['Heading3'],
            fontSize=13,
            textColor=HexColor('#0f3460'),
            spaceAfter=6,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Article metadata style
        self.styles.add(ParagraphStyle(
            name='ArticleMeta',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=HexColor('#666666'),
            spaceAfter=6,
            fontName='Helvetica-Oblique'
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
            fontName='Helvetica'
        ))
        
        # URL style
        self.styles.add(ParagraphStyle(
            name='URLStyle',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=HexColor('#0066cc'),
            spaceAfter=15,
            fontName='Helvetica-Oblique'
        ))

    def _clean_text(self, text: str) -> str:
        """Clean text for PDF rendering."""
        if not text:
            return ""
        # Escape XML special characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text

    def generate(self, articles_by_source: Dict[str, List[Dict]], 
                 title: str = "Daily Newspaper Digest") -> str:
        """
        Generate PDF from scraped articles.
        """
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Title page
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            self.styles['ArticleMeta']
        ))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(
            f"Total Sources: {len(articles_by_source)} | "
            f"Total Articles: {sum(len(v) for v in articles_by_source.values())}",
            self.styles['ArticleMeta']
        ))
        story.append(PageBreak())
        
        # Articles by source
        for source_name, articles in articles_by_source.items():
            if not articles:
                continue
                
            # Source header
            story.append(Paragraph(f"📰 {source_name}", self.styles['SourceHeader']))
            story.append(Spacer(1, 0.1*inch))
            
            for article in articles:
                # Article title
                story.append(Paragraph(
                    self._clean_text(article['title']),
                    self.styles['ArticleTitle']
                ))
                
                # Metadata
                meta_text = f"By {article['authors']} | {article['publish_date']}"
                story.append(Paragraph(meta_text, self.styles['ArticleMeta']))
                
                # Article body
                body_text = self._clean_text(article['text'])
                # Truncate very long articles
                if len(body_text) > 8000:
                    body_text = body_text[:8000] + "... [truncated]"
                story.append(Paragraph(body_text, self.styles['BodyText']))
                
                # Source URL
                story.append(Paragraph(
                    f"Source: {article['url']}",
                    self.styles['URLStyle']
                ))
                
                story.append(Spacer(1, 0.15*inch))
            
            story.append(PageBreak())
        
        # Build PDF
        doc.build(story)
        print(f"\n✅ PDF generated: {os.path.abspath(self.output_path)}")
        return self.output_path
              
