from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import black, blue, lightgrey, grey
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import pandas as pd

class ReportGenerator:
    """A class to generate professional PDF reports from analysis data."""

    def __init__(self, output_path):
        """Initializes the report generator with an output path and default styles."""
        self.output_path = output_path
        self.doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=1*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)
        self.story = []
        self.styles = getSampleStyleSheet()
        self._define_styles()

    def _define_styles(self):
        """Defines custom paragraph and table styles for the reports."""
        self.title_style = ParagraphStyle('CustomTitle', parent=self.styles['Title'], fontSize=24, textColor=blue, alignment=TA_CENTER, spaceAfter=20)
        self.h1_style = ParagraphStyle('CustomH1', parent=self.styles['Heading1'], fontSize=18, textColor=blue, spaceBefore=12, spaceAfter=6)
        self.h2_style = ParagraphStyle('CustomH2', parent=self.styles['Heading2'], fontSize=14, textColor=blue, spaceBefore=10, spaceAfter=4)
        self.h3_style = ParagraphStyle('CustomH3', parent=self.styles['Heading3'], fontSize=12, textColor=black, spaceBefore=8, spaceAfter=4)
        self.body_style = self.styles['BodyText']
        self.bullet_style = ParagraphStyle('Bullet', parent=self.body_style, firstLineIndent=0, leftIndent=18, spaceBefore=2, spaceAfter=2)
        self.italic_style = self.styles['Italic']
        self.normal_style = self.styles['Normal']

    def _df_to_reportlab_table(self, df: pd.DataFrame):
        """Converts a pandas DataFrame to a ReportLab Table object."""
        if df is None or df.empty:
            return None

        header_style = ParagraphStyle('ReportTableHeader', parent=self.normal_style, fontName='Helvetica-Bold', textColor='white', alignment=TA_CENTER)
        cell_style = ParagraphStyle('ReportTableCell', parent=self.normal_style, alignment=TA_CENTER)

        df_reset = df.reset_index()
        header = [Paragraph(str(col), header_style) for col in df_reset.columns] # Original line

        # Format body cells, rounding numbers to 2 decimal places
        formatted_body = []
        for row in df_reset.values:
            formatted_row = []
            for cell in row:
                if isinstance(cell, (int, float)):
                    formatted_row.append(Paragraph(f"{cell:,.2f}", cell_style))
                else:
                    formatted_row.append(Paragraph(str(cell), cell_style))
            formatted_body.append(formatted_row)
        data = [header] + formatted_body

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), grey),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), 'white'),
            ('GRID', (0, 0), (-1, -1), 1, lightgrey)
        ]))
        return table

    def build(self):
        """Builds the PDF document from the story."""
        self.doc.build(self.story)
        print(f"PDF report generated: {self.output_path}")

    def generate_classification_report(self, page_classifications):
        """Generates the content for the classification report."""
        # Title page
        self.story.append(Paragraph("PDF Classification Analysis Report", self.title_style))
        self.story.append(Spacer(1, 0.5*inch))
        self.story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.normal_style))
        self.story.append(Paragraph(f"Total Pages Analyzed: {len(page_classifications)}", self.normal_style))
        self.story.append(PageBreak())

        # Executive Summary
        self.story.append(Paragraph("1. Executive Summary", self.h1_style))
        category_stats = pd.Series([d['category'] for d in page_classifications.values()]).value_counts()
        summary_data = [['Category', 'Page Count', 'Percentage']]
        total_pages = len(page_classifications)
        for category, count in category_stats.items():
            percentage = (count / total_pages) * 100
            summary_data.append([category, str(count), f"{percentage:.1f}%"])
        
        summary_table = Table(summary_data, colWidths=[3*inch, 1*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), lightgrey), ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12), ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), 'white'), ('GRID', (0, 0), (-1, -1), 1, black)
        ]))
        self.story.append(summary_table)
        self.story.append(PageBreak())

        # Detailed Results
        self.story.append(Paragraph("2. Classification Results by Page", self.h1_style))
        for page_idx in sorted(page_classifications.keys()):
            data = page_classifications[page_idx]
            self.story.append(Paragraph(f"Page {data['page_number']} - {data['category']}", self.h2_style))
            self.story.append(Paragraph(f"<b>Overall Focus:</b> {data['overall_focus']}", self.normal_style))
            self.story.append(Spacer(1, 6))
            self.story.append(Paragraph("<b>Reasoning Points:</b>", self.normal_style))
            for i, point in enumerate(data['reasoning_points'], 1):
                self.story.append(Paragraph(f"{i}. {point}", self.bullet_style))
            
            metrics = data.get('key_metrics', {})
            if 'business_segment' in metrics and metrics['business_segment']:
                self.story.append(Spacer(1, 6))
                self.story.append(Paragraph("<b>Identified Business Segment(s):</b>", self.normal_style))
                self.story.append(Paragraph(f"• {', '.join(metrics['business_segment'])}", self.bullet_style))
            self.story.append(Spacer(1, 12))

    def generate_analysis_report(self, analysis_results: dict):
        """Generates the content for the full analysis report."""
        # Title Page
        self.story.append(Paragraph("10-K Document Analysis Report", self.title_style))
        self.story.append(Spacer(1, 0.25*inch))
        self.story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.normal_style))
        self.story.append(PageBreak())

        # --- Sections ---
        self._add_financial_analysis_section(analysis_results.get('financial'))
        self._add_operational_analysis_section(analysis_results.get('operational'))
        self._add_debt_analysis_section(analysis_results.get('debt'))
        self._add_legal_analysis_section(analysis_results.get('legal'))

    def _add_financial_analysis_section(self, fin_data):
        if not fin_data: return
        self.story.append(Paragraph("Financial Analysis", self.h1_style))
        
        if fin_data.get('reconstructed_statements'):
            self.story.append(Paragraph("Reconstructed Financial Statements", self.h2_style))
            for name, df in fin_data['reconstructed_statements'].items():
                self.story.append(Paragraph(name, self.h3_style))
                table = self._df_to_reportlab_table(df)
                if table: self.story.extend([table, Spacer(1, 12)])
        
        if fin_data.get('financial_ratios'):
            self.story.append(Paragraph("Financial Ratios", self.h2_style))
            for name, df in fin_data['financial_ratios'].items():
                self.story.append(Paragraph(name, self.h3_style))
                table = self._df_to_reportlab_table(df)
                if table: self.story.extend([table, Spacer(1, 12)])

        if 'cash_flow_summary' in fin_data and not fin_data['cash_flow_summary'].empty:
            self.story.append(Paragraph("Cash Flow Summary", self.h2_style))
            table = self._df_to_reportlab_table(fin_data['cash_flow_summary'])
            if table: self.story.extend([table, Spacer(1, 12)])
        
        self.story.append(PageBreak())

    def _add_operational_analysis_section(self, op_data):
        if not op_data: return
        self.story.append(Paragraph("Operational and Risk Analysis", self.h1_style))

        if 'segment_summary' in op_data and not op_data['segment_summary'].empty:
            self.story.append(Paragraph("Business Segment Summary", self.h2_style))
            table = self._df_to_reportlab_table(op_data['segment_summary'])
            if table: self.story.extend([table, Spacer(1, 12)])

        if 'competition_summary' in op_data:
            self.story.append(Paragraph("Competitive Landscape", self.h2_style))
            self.story.append(Paragraph(f"<b>Identified Competitors:</b> {', '.join(op_data['competition_summary'].get('identified_competitors', []))}", self.body_style))
            self.story.append(Spacer(1, 6))
            self.story.append(Paragraph("<b>Market Position Statements:</b>", self.body_style))
            for stmt in op_data['competition_summary'].get('market_position_statements', []):
                self.story.append(Paragraph(f"• {stmt}", self.bullet_style))
            self.story.append(Spacer(1, 12))

        if 'risks_summary' in op_data:
            self.story.append(Paragraph("Key Risks Summary", self.h2_style))
            for risk in op_data['risks_summary'].split('• '):
                if risk.strip(): self.story.append(Paragraph(f"• {risk.strip()}", self.bullet_style))
                cleaned_risk = risk.strip().replace('\n', ' ')
                if cleaned_risk:
                    self.story.append(Paragraph(f"• {cleaned_risk}", self.bullet_style))
            self.story.append(Spacer(1, 12))

        if 'geo_summary' in op_data and not op_data['geo_summary'].empty:
            self.story.append(Paragraph("Geographic Exposure Summary", self.h2_style))
            self.story.append(Paragraph("(Top 10 most mentioned regions)", self.italic_style))
            table = self._df_to_reportlab_table(op_data['geo_summary'])
            if table: self.story.extend([table, Spacer(1, 12)])

        if 'mda_summary' in op_data:
            self.story.append(Paragraph("Management Discussion & Analysis", self.h2_style))
            mda_text = op_data['mda_summary'].replace('\n', '<br/>')
            self.story.append(Paragraph(mda_text, self.body_style))
            self.story.append(Spacer(1, 12))

        self.story.append(PageBreak())

    def _add_debt_analysis_section(self, debt_data):
        if not debt_data: return
        self.story.append(Paragraph("Debt and Capital Structure Analysis", self.h1_style))

        if 'covenants' in debt_data:
            self.story.append(Paragraph("Debt Covenants", self.h2_style))
            for cov in debt_data['covenants'].split('• '):
                if cov.strip(): self.story.append(Paragraph(f"• {cov.strip()}", self.bullet_style))
            self.story.append(Spacer(1, 12))

        if 'capital_structure' in debt_data and not debt_data['capital_structure'].empty:
            self.story.append(Paragraph("Capital Structure Summary", self.h2_style))
            table = self._df_to_reportlab_table(debt_data['capital_structure'])
            if table: self.story.extend([table, Spacer(1, 12)])

        self.story.append(PageBreak())

    def _add_legal_analysis_section(self, legal_data):
        if not legal_data: return
        self.story.append(Paragraph("Legal Analysis", self.h1_style))

        if 'litigation_summary' in legal_data:
            self.story.append(Paragraph("Litigation Summary", self.h2_style))
            self.story.append(Paragraph(legal_data['litigation_summary'].replace('\n', '<br/>'), self.body_style))
            self.story.append(Spacer(1, 12))

        if 'regulatory_summary' in legal_data:
            self.story.append(Paragraph("Regulatory Matters", self.h2_style))
            for matter in legal_data['regulatory_summary'].split('• '):
                if matter.strip(): self.story.append(Paragraph(f"• {matter.strip()}", self.bullet_style))
            self.story.append(Spacer(1, 12))

        if 'governance_summary' in legal_data:
            self.story.append(Paragraph("Corporate Governance Commentary", self.h2_style))
            for comment in legal_data['governance_summary'].split('• '):
                if comment.strip(): self.story.append(Paragraph(f"• {comment.strip()}", self.bullet_style))
            self.story.append(Spacer(1, 12))
