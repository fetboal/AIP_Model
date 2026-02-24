from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import os

class ReportGenerator:
    def __init__(self, report_name: str, save_location: str):
        """
        Initialize the ReportGenerator and create a blank PDF optimized for tables.
        Uses ReportLab's Platypus module which is ideal for table-heavy documents.
        
        Args:
            report_name (str): Name of the report (will be used as filename).
            save_location (str): Directory path where the PDF will be saved.
        """
        self.report_name = report_name
        self.save_location = save_location
        
        # Ensure save location exists
        os.makedirs(save_location, exist_ok=True)
        
        # Create full file path
        self.file_path = os.path.join(save_location, f"{report_name}.pdf")
        
        # Create PDF document using SimpleDocTemplate (better for tables)
        self.doc = SimpleDocTemplate(
            self.file_path,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.5*inch
        )
        
        # Initialize styles for text elements
        self.styles = getSampleStyleSheet()
        
        # Initialize story (list of flowables to build the PDF)
        self.story = []

    def add_table_from_df(self, df, title=None):
        """
        Add a table to the PDF from a pandas DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame to be converted into a table.
            title (str, optional): Title to be added above the table.
        """

        # Add title if provided
        if title:
            title_style = ParagraphStyle(
                name='TitleStyle',
                fontSize=14,
                leading=16,
                alignment=1,  # Centered
                spaceAfter=12
            )
            self.story.append(Paragraph(title, title_style))
        
        # Calculate available width
        available_width = self.doc.width
        num_columns = len(df.columns)
        col_width = available_width / num_columns
        
        # Create styles for wrapping text in cells
        header_style = ParagraphStyle(
            name='HeaderStyle',
            fontSize=8,
            fontName='Helvetica-Bold',
            textColor=colors.whitesmoke,
            alignment=1,  # Center
            leading=10
        )
        
        cell_style = ParagraphStyle(
            name='CellStyle',
            fontSize=7,
            alignment=1,  # Center
            leading=9
        )
        
        # Convert DataFrame to list of lists with Paragraph objects for wrapping
        data = []
        
        # Add headers as Paragraph objects
        header_row = [Paragraph(str(col), header_style) for col in df.columns]
        data.append(header_row)
        
        # Add data rows as Paragraph objects
        for _, row in df.iterrows():
            data_row = [Paragraph(str(val), cell_style) for val in row]
            data.append(data_row)
        
        # Create Table with calculated column widths
        table = Table(data, colWidths=[col_width]*num_columns, hAlign='LEFT', repeatRows=1)
        
        # Add style to the table
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        # Add table to the story
        self.story.append(table)
        self.story.append(Spacer(1, 12))  # Add space after the table
    
    def save(self):
        """Build and save the PDF with all added content."""
        self.doc.build(self.story)
        print(f"PDF report saved to: {self.file_path}")
