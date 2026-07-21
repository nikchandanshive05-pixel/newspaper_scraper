"""
Clean, professional PDF generator for exam news digest.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.colors import HexColor, white, black
from datetime import datetime
from typing import Dict, List
import os


class ExamPDFGenerator:
    def __init__(self, output_path: str = "daily_newspaper.pdf"):
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Setup all custom styles with unique names."""

        # Main title
        self.styles.add(ParagraphStyle(
            name='ExamTitle',
            parent=self.styles['Heading1'],
            fontSize=26,
            textColor=HexColor('#1a237e'),
            spaceAfter=8,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=32
        ))

        # Subtitle
        self.styles.add(ParagraphStyle(
            name='ExamSubtitle',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=HexColor('#555555'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        ))

        # Topic header (colored band)
        self.styles.add(ParagraphStyle(
            name='TopicHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=white,
            spaceAfter=10,
            spaceBefore=16,
            fontName='Helvetica-Bold',
            leading=20,
            leftIndent=8,
            rightIndent=8,
            backColor=HexColor('#1565c0'),
            borderPadding=6
        ))

        # Article title
        self.styles.add(ParagraphStyle(
            name='ArticleTitle',
            parent=self.styles['Heading3'],
            fontSize=11,
            textColor=HexColor('#0d47a1'),
            spaceAfter=4,
            spaceBefore=10,
            fontName='Helvetica-Bold',
            leading=14
        ))

        # Source line
        self.styles.add(ParagraphStyle(
            name='SourceLine',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=HexColor('#666666'),
            spaceAfter=6,
            fontName='Helvetica-Oblique',
            leading=10
        ))

        # Body text
        self.styles.add(ParagraphStyle(
            name='ArticleBody',
            parent=self.styles['Normal'],
            fontSize=9.5,
            leading=13,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            fontName='Helvetica',
            firstLineIndent=0
        ))

        # URL
        self.styles.add(ParagraphStyle(
            name='ArticleURL',
            parent=self.styles['Normal'],
            fontSize=7.5,
            textColor=HexColor('#1565c0'),
            spaceAfter=12,
            fontName='Helvetica-Oblique',
            leading=9
        ))

        # Footer
        self.styles.add(ParagraphStyle(
            name='PageFooter',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=HexColor('#888888'),
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))

    def _clean_for_pdf(self, text: str) -> str:
        """Escape XML special chars for ReportLab."""
        if not text:
            return ""
        replacements = [
            ('&', '&amp;'), ('<', '&lt;'), ('>', '&gt;'),
            ('"', '&quot;'), ("'", '&apos;')
        ]
        for old, new in replacements:
            text = text.replace(old, new)
        return text

    def _truncate_text(self, text: str, max_chars: int = 3500) -> str:
        """Truncate long articles to keep PDF readable."""
        if len(text) <= max_chars:
            return text
        # Cut at last sentence boundary
        truncated = text[:max_chars]
        last_period = truncated.rfind('.')
        if last_period > max_chars * 0.8:
            return truncated[:last_period + 1] + " [Read full article at source]"
        return truncated + "... [Read full article at source]"

    def generate(self, categorized_articles: Dict[str, List[dict]], 
                 title: str = "Daily Exam News Digest") -> str:
        """Generate a clean, categorized PDF."""

        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=A4,
            rightMargin=60,
            leftMargin=60,
            topMargin=60,
            bottomMargin=40
        )

        story = []
        total_articles = sum(len(v) for v in categorized_articles.values())

        # ─── COVER PAGE ─────────────────────────────────────────────
        story.append(Spacer(1, 1.5*inch))
        story.append(Paragraph(title, self.styles['ExamTitle']))
        story.append(Paragraph(
            f"UPSC · MPSC · SSC · Banking · RBI · NDA · CDS",
            self.styles['ExamSubtitle']
        ))
        story.append(Spacer(1, 0.3*inch))

        # Date and stats box
        date_str = datetime.now().strftime("%A, %B %d, %Y")
        stats_data = [
            [f"📅 {date_str}"],
            [f"📊 {total_articles} articles from {len(categorized_articles)} topics"],
            [f"📰 Sources: The Hindu, Indian Express, Lokmat, Loksatta, eSakal"]
        ]
        stats_table = Table(stats_data, colWidths=[doc.width])
        stats_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#444444')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 0.5*inch))

        # Topic index
        story.append(Paragraph("📑 TOPICS COVERED", self.styles['ExamSubtitle']))
        for topic in sorted(categorized_articles.keys()):
            count = len(categorized_articles[topic])
            story.append(Paragraph(
                f"   {topic} — {count} articles",
                self.styles['SourceLine']
            ))

        story.append(PageBreak())

        # ─── ARTICLES BY TOPIC ──────────────────────────────────────
        for topic in sorted(categorized_articles.keys()):
            articles = categorized_articles[topic]
            if not articles:
                continue

            # Topic header
            story.append(Paragraph(f" {topic}", self.styles['TopicHeader']))
            story.append(Spacer(1, 0.1*inch))

            for i, article in enumerate(articles, 1):
                # Build article block
                title = self._clean_for_pdf(article['title'])
                body = self._truncate_text(article['text'])
                body = self._clean_for_pdf(body)
                url = article['url']
                source = article['source']
                date = article.get('publish_date', 'Today')
                score = article.get('score', 0)

                # Article number + title
                story.append(Paragraph(
                    f"{i}. {title}",
                    self.styles['ArticleTitle']
                ))

                # Source metadata
                story.append(Paragraph(
                    f"📰 {source}  |  📅 {date}  |  ⭐ Relevance: {score}/10",
                    self.styles['SourceLine']
                ))

                # Body
                story.append(Paragraph(body, self.styles['ArticleBody']))

                # URL
                story.append(Paragraph(
                    f"🔗 {url}",
                    self.styles['ArticleURL']
                ))

                story.append(Spacer(1, 0.08*inch))

            story.append(PageBreak())

        # ─── BUILD PDF ──────────────────────────────────────────────
        doc.build(story)
        print(f"\n✅ PDF generated: {os.path.abspath(self.output_path)}")
        return self.output_path
