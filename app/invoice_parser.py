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
        
        # Define namespaces for e-factura (UBL format) to prevent "invalid predicate" errors
        namespaces = {
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'
        }
        
        def find_with_fallback(root_elem, xpath_with_ns, xpath_without_ns=None):
            """Try to find element with namespaces, fallback to without. Prevents 'invalid predicate' errors."""
            try:
                elem = root_elem.find(xpath_with_ns, namespaces)
                if elem is not None:
                    return elem
            except Exception:
                pass  # XPath failed, try fallback
            # Fallback: try without namespaces
            if xpath_without_ns:
                try:
                    return root_elem.find(xpath_without_ns)
                except Exception:
                    pass
            return None
        
        # Try UBL e-factura format first
        supplier_elem = find_with_fallback(
            root,
            './/cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name',
            './/Party/PartyName/Name'
        )
        if supplier_elem is not None:
            result["supplier"] = supplier_elem.text
        
        invoice_number_elem = find_with_fallback(
            root,
            './/cbc:ID',
            './/ID'
        )
        if invoice_number_elem is not None:
            result["invoice_number"] = invoice_number_elem.text
        
        date_elem = find_with_fallback(
            root,
            './/cbc:IssueDate',
            './/IssueDate'
        )
        if date_elem is not None:
            result["invoice_date"] = date_elem.text
        
        total_elem = find_with_fallback(
            root,
            './/cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount',
            './/TaxInclusiveAmount'
        )
        if total_elem is None:
            total_elem = find_with_fallback(
                root,
                './/cac:LegalMonetaryTotal/cbc:PayableAmount',
                './/PayableAmount'
            )
        if total_elem is not None and total_elem.text:
            try:
                result["total_amount"] = float(total_elem.text.replace(',', '.'))
            except:
                pass
        
        # Generic fallback XML parsing - adapt based on your specific XML format
        # This runs if UBL extraction didn't find everything
        if not result["supplier"] or not result["invoice_number"]:
            for elem in root.iter():
                text = (elem.text or "").strip()
                if not text:
                    continue
                    
                # Try to identify fields
                if not result["supplier"] and ('supplier' in elem.tag.lower() or 'furnizor' in elem.tag.lower() or 'party' in elem.tag.lower() and 'name' in elem.tag.lower()):
                    result["supplier"] = text
                elif not result["invoice_number"] and ('invoice' in elem.tag.lower() or 'factura' in elem.tag.lower()) and ('number' in elem.tag.lower() or 'id' in elem.tag.lower() or 'nr' in elem.tag.lower()):
                    result["invoice_number"] = text
                elif not result["invoice_date"] and ('date' in elem.tag.lower() or 'data' in elem.tag.lower() or 'issue' in elem.tag.lower()):
                    result["invoice_date"] = text
                elif not result["total_amount"] and 'total' in elem.tag.lower():
                    try:
                        result["total_amount"] = float(text.replace(',', '.'))
                    except:
                        pass
        
        # Try to extract items from UBL format first
        items = []
        try:
            invoice_lines = root.findall('.//cac:InvoiceLine', namespaces)
            if not invoice_lines:
                invoice_lines = root.findall('.//InvoiceLine')
            
            for line in invoice_lines:
                item = {
                    "description": None,
                    "quantity": 0.0,
                    "unit": None,
                    "unit_price": None,
                    "total_price": None
                }
                
                # Extract description
                desc_elem = find_with_fallback(line, './/cac:Item/cbc:Description', './/Item/Description')
                if desc_elem is None:
                    desc_elem = find_with_fallback(line, './/cac:Item/cbc:Name', './/Item/Name')
                if desc_elem is not None:
                    item["description"] = desc_elem.text
                
                # Extract quantity
                qty_elem = find_with_fallback(line, './/cbc:InvoicedQuantity', './/InvoicedQuantity')
                if qty_elem is not None:
                    try:
                        item["quantity"] = float(qty_elem.text.replace(',', '.'))
                        # Get unit from attribute
                        unit_code = qty_elem.get('unitCode') or qty_elem.get('unit')
                        if unit_code:
                            item["unit"] = unit_code
                    except:
                        pass
                
                # Extract unit price
                price_elem = find_with_fallback(line, './/cac:Price/cbc:PriceAmount', './/Price/PriceAmount')
                if price_elem is not None:
                    try:
                        item["unit_price"] = float(price_elem.text.replace(',', '.'))
                    except:
                        pass
                
                # Extract line total
                total_elem = find_with_fallback(line, './/cbc:LineExtensionAmount', './/LineExtensionAmount')
                if total_elem is not None:
                    try:
                        item["total_price"] = float(total_elem.text.replace(',', '.'))
                    except:
                        pass
                
                if item["description"]:
                    items.append(item)
        except Exception:
            pass  # Fall through to generic extraction
        
        # Generic fallback for non-UBL XML
        if not items:
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
                    if not text:
                        continue
                    if 'desc' in child.tag.lower() or 'name' in child.tag.lower():
                        item["description"] = text
                    elif 'quant' in child.tag.lower() or 'qty' in child.tag.lower():
                        try:
                            item["quantity"] = float(text.replace(',', '.'))
                            # Check for unit in attributes
                            unit_attr = child.get('unitCode') or child.get('unit')
                            if unit_attr:
                                item["unit"] = unit_attr
                        except:
                            pass
                    elif 'unit' in child.tag.lower() and 'price' not in child.tag.lower():
                        item["unit"] = text
                    elif 'price' in child.tag.lower() and 'total' not in child.tag.lower():
                        try:
                            item["unit_price"] = float(text.replace(',', '.'))
                        except:
                            pass
                    elif 'total' in child.tag.lower() or 'amount' in child.tag.lower():
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
