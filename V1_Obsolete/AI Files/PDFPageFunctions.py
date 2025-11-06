from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from typing import List
import os
import tempfile
import subprocess

def split_pdf_to_pages(pdf_path: str) -> List[BytesIO]:
    """
    Split a PDF file into individual pages stored in memory.
    Args:
        pdf_path (str): Path to the PDF file to split
    Returns:
        List[BytesIO]: List of BytesIO objects, each containing a single page PDF
    """
    # Load the PDF file
    reader = PdfReader(pdf_path)
    pages_array = []

    # Loop through each page and save it as a separate PDF
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        
        # Save the individual page to a BytesIO object
        pdf_bytes = BytesIO()
        writer.write(pdf_bytes)
        pdf_bytes.seek(0)
        
        # Append the BytesIO object to the array
        pages_array.append(pdf_bytes)

    return pages_array


    """
    Recombine an array of PDF pages back into a single PDF file.
    
    Args:
        pdf_pages (List[BytesIO]): List of BytesIO objects containing PDF pages
        output_path (str, optional): Path where to save the combined PDF. 
                                   If None, saves to a temporary file.
    
    Returns:
        str: Path to the combined PDF file
    """
    if not pdf_pages:
        raise ValueError("No PDF pages provided to recombine")
    
    # Create a new PDF writer
    writer = PdfWriter()
    
    # Process each page individually with complete isolation
    for i, pdf_page in enumerate(pdf_pages):
        try:
            # Create a completely isolated copy of the page
            pdf_page.seek(0)
            original_data = pdf_page.getvalue()  # Get all data at once
            
            # Create a new BytesIO with the copied data
            isolated_page = BytesIO(original_data)
            
            # Create a new reader for this isolated page
            temp_reader = PdfReader(isolated_page)
            
            # Verify the page has content
            if len(temp_reader.pages) == 0:
                print(f"Warning: Page {i+1} appears to be empty, skipping")
                continue
            
            # Get the page and clone it to avoid any shared references
            source_page = temp_reader.pages[0]
            
            # Create a temporary writer to clone the page cleanly
            temp_writer = PdfWriter()
            temp_writer.add_page(source_page)
            
            # Write to temporary buffer and read back to ensure clean separation
            temp_buffer = BytesIO()
            temp_writer.write(temp_buffer)
            temp_buffer.seek(0)
            
            # Read the clean page back
            clean_reader = PdfReader(temp_buffer)
            clean_page = clean_reader.pages[0]
            
            # Add the completely clean page to final writer
            writer.add_page(clean_page)
            
            # Clean up temporary objects
            isolated_page.close()
            temp_buffer.close()
            
            print(f"Successfully processed page {i+1}")
                
        except Exception as e:
            print(f"Error processing page {i+1}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Determine output path
    if output_path is None:
        # Create a temporary file
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"recombined_pdf_{int(__import__('time').time())}.pdf")
    
    # Write the combined PDF to file
    try:
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"Successfully recombined {len(pdf_pages)} pages into: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error writing combined PDF: {e}")
        raise

def extract_pages_from_original(original_pdf_path: str, page_indices: List[int], output_path: str = None, open_pdf: bool = False) -> str:
    """
    Extract specific pages from the original PDF file and create a new PDF.
    
    Args:
        original_pdf_path (str): Path to the original PDF file
        page_indices (List[int]): List of page indices to extract (0-based)
        output_path (str, optional): Path where to save the extracted pages PDF. 
                                   If None, saves to a temporary file.
        open_pdf (bool): If True, opens the extracted PDF file after creation
    
    Returns:
        str: Path to the extracted pages PDF file
    """
    if not page_indices:
        raise ValueError("No page indices provided to extract")
    
    # Read the original PDF file
    reader = PdfReader(original_pdf_path)
    total_pages = len(reader.pages)
    
    # Validate page indices
    valid_indices = []
    for idx in page_indices:
        if 0 <= idx < total_pages:
            valid_indices.append(idx)
        else:
            print(f"Warning: Page index {idx} is out of range (PDF has {total_pages} pages)")
    
    if not valid_indices:
        raise ValueError(f"No valid page indices found. PDF has {total_pages} pages (0-{total_pages-1})")
    
    # Create a new PDF writer
    writer = PdfWriter()
    
    # Extract requested pages directly from original
    for idx in valid_indices:
        try:
            writer.add_page(reader.pages[idx])
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            continue
    
    # Determine output path
    if output_path is None:
        # Create a temporary file
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"recombined_pdf_{int(__import__('time').time())}.pdf")
    
    # Write the combined PDF to file
    try:
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"Successfully extracted {len(valid_indices)} pages into: {output_path}")
        
        # Open the PDF if requested (Windows only)
        if open_pdf:
            try:
                os.startfile(output_path)
                print(f"Opened extracted pages PDF in default PDF viewer")
                
            except Exception as e:
                print(f"Error opening PDF: {e}")
                print(f"You can manually open: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"Error writing combined PDF: {e}")
        raise

#Only Used to Test Opening PDFs
def open_pdf_page_in_adobe(pdf_page: BytesIO, page_number: int = 1) -> str:
    """
    Save a PDF page to a temporary file and open it in Adobe.
    Args:
        pdf_page (BytesIO): BytesIO object containing a PDF page
        page_number (int): Page number for naming the temp file 
    Returns:
        str: Path to the temporary file created
    """
    # Reset the BytesIO position to the beginning
    pdf_page.seek(0)
    
    # Create a temporary file with .pdf extension
    temp_dir = tempfile.gettempdir()
    temp_filename = f"pdf_page_{page_number}.pdf"
    temp_path = os.path.join(temp_dir, temp_filename)
    
    # Write the PDF data to the temporary file
    with open(temp_path, 'wb') as temp_file:
        temp_file.write(pdf_page.read())
    
    # Open the file with the default PDF application (Adobe if it's the default)
    try:
        if os.name == 'nt':  # Windows
            os.startfile(temp_path)
        elif os.name == 'posix':  # macOS/Linux
            subprocess.run(['open', temp_path])  # macOS
            # subprocess.run(['xdg-open', temp_path])  # Linux alternative
        
        print(f"Opened PDF page {page_number} in default PDF viewer")
        print(f"Temporary file saved at: {temp_path}")
        return temp_path
        
    except Exception as e:
        print(f"Error opening PDF: {e}")
        print(f"You can manually open: {temp_path}")
        return temp_path

#Only Used to Test Opening PDFs
def open_pdf_by_index(pdf_pages: List[BytesIO], page_index: int) -> str:
    """
    Open a PDF page from an array by index in Adobe.
    Args:
        pdf_pages (List[BytesIO]): List of PDF pages
        page_index (int): Index of the page to open (0-based)
    Returns:
        str: Path to the temporary file created
    """
    if not pdf_pages:
        print("No PDF pages found in the array")
        return ""
    
    if page_index < 0 or page_index >= len(pdf_pages):
        print(f"Invalid page index {page_index}. PDF has {len(pdf_pages)} pages (indices 0-{len(pdf_pages)-1})")
        return ""
    
    return open_pdf_page_in_adobe(pdf_pages[page_index], page_number=page_index + 1)


