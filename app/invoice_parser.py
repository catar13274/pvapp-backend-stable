"""
Invoice file parser for PDF, DOC, TXT, and XML files
Extracts invoice information and line items
"""

import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_pdf(file_path: str) -> Dict:
    """Parse PDF invoice file"""
    try:
        import PyPDF2
        
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        return extract_invoice_data(text, "PDF")
    except Exception as e:
        logger.error(f"Error parsing PDF: {e}")
        return {"error": str(e), "raw_text": ""}


def parse_docx(file_path: str) -> Dict:
    """Parse DOCX invoice file"""
    try:
        from docx import Document
        
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        
        # Also extract tables
        for table in doc.tables:
            for row in table.rows:
                text += "\n" + "\t".join([cell.text for cell in row.cells])
        
        return extract_invoice_data(text, "DOCX")
    except Exception as e:
        logger.error(f"Error parsing DOCX: {e}")
        return {"error": str(e), "raw_text": ""}


def parse_txt(file_path: str) -> Dict:
    """Parse TXT invoice file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        return extract_invoice_data(text, "TXT")
    except Exception as e:
        logger.error(f"Error parsing TXT: {e}")
        return {"error": str(e), "raw_text": ""}


def parse_xml(file_path: str) -> Dict:
    """Parse XML invoice file (e-factura format or generic XML)"""
    try:
        from lxml import etree
        
        # First, check if file exists and is not empty
        path_obj = Path(file_path)
        if not path_obj.exists():
            return {"error": "XML file not found"}
        
        file_size = path_obj.stat().st_size
        if file_size == 0:
            return {"error": "XML file is empty"}
        
        # Read and strip BOM if present
        file_content = path_obj.read_text(encoding='utf-8-sig')
        if not file_content.strip():
            return {"error": "XML file contains no data"}
        
        # Parse XML from string (handles BOM better than parse from file)
        root = etree.fromstring(file_content.encode('utf-8'))
        
        # Try to extract common fields
        result = {
            "supplier": None,
            "invoice_number": None,
            "invoice_date": None,
            "total_amount": None,
            "items": [],
            "raw_text": etree.tostring(root, pretty_print=True).decode('utf-8')
        }
        
        # Generic XML parsing - adapt based on your specific XML format
        # This is a basic implementation
        for elem in root.iter():
            text = (elem.text or "").strip()
            if not text:
                continue
                
            # Try to identify fields
            if 'supplier' in elem.tag.lower() or 'furnizor' in elem.tag.lower():
                result["supplier"] = text
            elif 'invoice' in elem.tag.lower() and 'number' in elem.tag.lower():
                result["invoice_number"] = text
            elif 'date' in elem.tag.lower() or 'data' in elem.tag.lower():
                result["invoice_date"] = text
            elif 'total' in elem.tag.lower():
                try:
                    result["total_amount"] = float(text.replace(',', '.'))
                except:
                    pass
        
        # Try to extract items (this is very generic)
        # You may need to customize based on your XML schema
        items = []
        for item_elem in root.findall(".//*[contains(local-name(), 'item') or contains(local-name(), 'line')]"):
            item = {
                "description": None,
                "quantity": 0.0,
                "unit": None,
                "unit_price": None,
                "total_price": None
            }
            
            for child in item_elem:
                text = (child.text or "").strip()
                if 'desc' in child.tag.lower():
                    item["description"] = text
                elif 'quant' in child.tag.lower() or 'qty' in child.tag.lower():
                    try:
                        item["quantity"] = float(text.replace(',', '.'))
                    except:
                        pass
                elif 'unit' in child.tag.lower() and 'price' not in child.tag.lower():
                    item["unit"] = text
                elif 'price' in child.tag.lower() and 'total' not in child.tag.lower():
                    try:
                        item["unit_price"] = float(text.replace(',', '.'))
                    except:
                        pass
                elif 'total' in child.tag.lower():
                    try:
                        item["total_price"] = float(text.replace(',', '.'))
                    except:
                        pass
            
            if item["description"]:
                items.append(item)
        
        result["items"] = items
        return result
        
    except Exception as e:
        logger.error(f"Error parsing XML: {e}")
        error_msg = str(e)
        # Provide more helpful error messages
        if "empty" in error_msg.lower():
            error_msg = "XML file is empty or contains no valid data"
        elif "line 1, column 1" in error_msg:
            error_msg = "XML file appears to be empty or has invalid encoding. Please ensure the file is a valid XML document."
        return {"error": error_msg, "raw_text": ""}


def extract_invoice_data(text: str, file_type: str) -> Dict:
    """
    Extract invoice information from text using regex patterns
    Returns dict with supplier, invoice_number, date, total, and items
    """
    result = {
        "supplier": None,
        "invoice_number": None,
        "invoice_date": None,
        "total_amount": None,
        "items": [],
        "raw_text": text
    }
    
    # Extract supplier (look for common patterns)
    supplier_patterns = [
        r'(?:supplier|furnizor|from)[:\s]+([^\n]+)',
        r'(?:company|societate)[:\s]+([^\n]+)',
    ]
    for pattern in supplier_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["supplier"] = match.group(1).strip()
            break
    
    # Extract invoice number
    invoice_patterns = [
        r'(?:invoice|factura)[^:]*(?:no|nr|number|numar)[.:\s#]+([A-Z0-9\-]+)',
        r'(?:no|nr)[.:\s]+([A-Z0-9\-]+)',
    ]
    for pattern in invoice_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["invoice_number"] = match.group(1).strip()
            break
    
    # Extract date (various formats)
    date_patterns = [
        r'(?:date|data)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{4}-\d{2}-\d{2})',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["invoice_date"] = match.group(1).strip()
            break
    
    # Extract total amount
    total_patterns = [
        r'(?:total|total general)[:\s]+([0-9.,]+)',
        r'(?:total)[^0-9]+([0-9.,]+)',
    ]
    for pattern in total_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                total_str = match.group(1).replace(',', '.')
                result["total_amount"] = float(total_str)
            except:
                pass
            break
    
    # Extract line items (this is more complex and may need customization)
    result["items"] = extract_line_items(text)
    
    return result


def extract_line_items(text: str) -> List[Dict]:
    """
    Extract line items from invoice text
    This is a heuristic approach and may need customization
    """
    items = []
    
    # Look for table-like structures
    lines = text.split('\n')
    
    # Try to find lines with quantity and price patterns
    item_pattern = re.compile(
        r'(.+?)\s+(\d+[.,]?\d*)\s+(?:buc|pcs|pc|unit|kg|m|l|set)?\s*(\d+[.,]\d+)\s+(\d+[.,]\d+)',
        re.IGNORECASE
    )
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 10:
            continue
            
        match = item_pattern.search(line)
        if match:
            try:
                description = match.group(1).strip()
                quantity = float(match.group(2).replace(',', '.'))
                unit_price = float(match.group(3).replace(',', '.'))
                total_price = float(match.group(4).replace(',', '.'))
                
                # Basic validation
                if abs(quantity * unit_price - total_price) < 0.01 or total_price > 0:
                    items.append({
                        "description": description,
                        "quantity": quantity,
                        "unit": None,
                        "unit_price": unit_price,
                        "total_price": total_price
                    })
            except:
                continue
    
    # If no items found, try simpler pattern (just description and numbers)
    if not items:
        simple_pattern = re.compile(r'(.{10,})\s+(\d+[.,]?\d*)\s+(\d+[.,]\d+)', re.IGNORECASE)
        for line in lines:
            line = line.strip()
            match = simple_pattern.search(line)
            if match:
                try:
                    items.append({
                        "description": match.group(1).strip(),
                        "quantity": float(match.group(2).replace(',', '.')),
                        "unit": None,
                        "unit_price": float(match.group(3).replace(',', '.')),
                        "total_price": None
                    })
                except:
                    continue
    
    return items


def parse_invoice_file(file_path: str) -> Dict:
    """
    Main function to parse invoice file based on extension
    """
    path = Path(file_path)
    extension = path.suffix.lower()
    
    if extension == '.pdf':
        return parse_pdf(file_path)
    elif extension in ['.doc', '.docx']:
        return parse_docx(file_path)
    elif extension == '.txt':
        return parse_txt(file_path)
    elif extension == '.xml':
        return parse_xml(file_path)
    else:
        return {"error": f"Unsupported file type: {extension}", "raw_text": ""}


def fuzzy_match_material(description: str, existing_materials: List[Dict]) -> Optional[Tuple[int, float]]:
    """
    Find the best matching material from existing materials
    Returns (material_id, confidence_score) or None
    """
    if not description or not existing_materials:
        return None
    
    description_lower = description.lower()
    best_match = None
    best_score = 0.0
    
    for material in existing_materials:
        material_name = (material.get('name') or '').lower()
        
        # Simple similarity scoring
        # Check if material name is in description
        if material_name in description_lower:
            score = len(material_name) / len(description_lower)
            if score > best_score:
                best_score = score
                best_match = material.get('id')
        
        # Check if description is in material name
        elif description_lower in material_name:
            score = len(description_lower) / len(material_name)
            if score > best_score:
                best_score = score
                best_match = material.get('id')
    
    # Only return if confidence is reasonable
    if best_match and best_score > 0.3:
        return (best_match, best_score)
    
    return None
