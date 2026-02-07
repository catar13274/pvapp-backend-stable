"""
Robust XML Invoice Parser Microservice
Uses defusedxml to prevent XXE attacks and avoid fragile XPath predicates.
Parses UBL XML invoices and returns structured JSON data.
"""
import logging
import os
import io
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import defusedxml.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# UBL 2.1 namespaces
NAMESPACES = {
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'
}

def parse_ubl_invoice(xml_content):
    """
    Parse UBL XML invoice using fully-qualified namespace tags.
    Avoids fragile XPath predicates by using iterative traversal.
    
    Returns dict with invoice metadata and line items.
    """
    try:
        # Parse XML safely with defusedxml
        root = ET.fromstring(xml_content)
        
        result = {
            'invoice_metadata': {},
            'line_items': []
        }
        
        # Extract invoice metadata using fully-qualified tags
        # Invoice number
        invoice_number_elem = root.find('.//{%s}ID' % NAMESPACES['cbc'])
        if invoice_number_elem is not None and invoice_number_elem.text:
            result['invoice_metadata']['invoice_number'] = invoice_number_elem.text.strip()
        
        # Invoice date
        invoice_date_elem = root.find('.//{%s}IssueDate' % NAMESPACES['cbc'])
        if invoice_date_elem is not None and invoice_date_elem.text:
            result['invoice_metadata']['invoice_date'] = invoice_date_elem.text.strip()
        
        # Supplier party name
        supplier_elem = root.find('.//{%s}AccountingSupplierParty//{%s}Name' % (NAMESPACES['cac'], NAMESPACES['cbc']))
        if supplier_elem is not None and supplier_elem.text:
            result['invoice_metadata']['supplier'] = supplier_elem.text.strip()
        
        # Total amount (TaxInclusiveAmount or PayableAmount)
        total_elem = root.find('.//{%s}LegalMonetaryTotal/{%s}TaxInclusiveAmount' % (NAMESPACES['cac'], NAMESPACES['cbc']))
        if total_elem is None:
            total_elem = root.find('.//{%s}LegalMonetaryTotal/{%s}PayableAmount' % (NAMESPACES['cac'], NAMESPACES['cbc']))
        if total_elem is not None and total_elem.text:
            try:
                result['invoice_metadata']['total_amount'] = float(total_elem.text.strip())
            except ValueError:
                logger.warning(f"Could not parse total amount: {total_elem.text}")
        
        # Parse invoice lines using iteration (avoiding fragile XPath predicates)
        for line in root.findall('.//{%s}InvoiceLine' % NAMESPACES['cac']):
            line_item = {}
            
            # Line ID
            line_id = line.find('{%s}ID' % NAMESPACES['cbc'])
            if line_id is not None and line_id.text:
                line_item['line_id'] = line_id.text.strip()
            
            # Quantity
            quantity_elem = line.find('.//{%s}InvoicedQuantity' % NAMESPACES['cbc'])
            if quantity_elem is not None and quantity_elem.text:
                try:
                    line_item['quantity'] = float(quantity_elem.text.strip())
                except ValueError:
                    logger.warning(f"Could not parse quantity: {quantity_elem.text}")
                    line_item['quantity'] = 0.0
                
                # Unit code attribute
                unit_code = quantity_elem.get('unitCode')
                if unit_code:
                    line_item['unit_code'] = unit_code
            
            # Line extension amount (line total before tax)
            line_total_elem = line.find('.//{%s}LineExtensionAmount' % NAMESPACES['cbc'])
            if line_total_elem is not None and line_total_elem.text:
                try:
                    line_item['line_total'] = float(line_total_elem.text.strip())
                except ValueError:
                    logger.warning(f"Could not parse line total: {line_total_elem.text}")
            
            # Unit price
            price_elem = line.find('.//{%s}Price/{%s}PriceAmount' % (NAMESPACES['cac'], NAMESPACES['cbc']))
            if price_elem is not None and price_elem.text:
                try:
                    line_item['unit_price'] = float(price_elem.text.strip())
                except ValueError:
                    logger.warning(f"Could not parse unit price: {price_elem.text}")
            
            # Item description/name
            item_name = line.find('.//{%s}Item/{%s}Name' % (NAMESPACES['cac'], NAMESPACES['cbc']))
            if item_name is not None and item_name.text:
                line_item['description'] = item_name.text.strip()
            
            # Item SKU/ID
            seller_id = line.find('.//{%s}Item/{%s}SellersItemIdentification/{%s}ID' % 
                                 (NAMESPACES['cac'], NAMESPACES['cac'], NAMESPACES['cbc']))
            if seller_id is not None and seller_id.text:
                line_item['sku_raw'] = seller_id.text.strip()
            
            # Tax percentage
            tax_percent_elem = line.find('.//{%s}TaxTotal/{%s}TaxSubtotal/{%s}TaxCategory/{%s}Percent' % 
                                        (NAMESPACES['cac'], NAMESPACES['cac'], NAMESPACES['cac'], NAMESPACES['cbc']))
            if tax_percent_elem is not None and tax_percent_elem.text:
                try:
                    line_item['tax_percent'] = float(tax_percent_elem.text.strip())
                except ValueError:
                    logger.warning(f"Could not parse tax percent: {tax_percent_elem.text}")
            
            # Calculate total_price if we have quantity and unit_price
            if 'quantity' in line_item and 'unit_price' in line_item:
                line_item['total_price'] = line_item['quantity'] * line_item['unit_price']
            elif 'line_total' in line_item:
                line_item['total_price'] = line_item['line_total']
            
            result['line_items'].append(line_item)
        
        logger.info(f"Successfully parsed {len(result['line_items'])} invoice lines")
        return result
        
    except ET.ParseError as e:
        logger.error(f"XML parsing error: {e}")
        raise ValueError(f"Invalid XML: {e}")
    except Exception as e:
        logger.error(f"Unexpected error parsing XML: {e}")
        raise ValueError(f"Failed to parse XML: {e}")


def xml_to_csv(parsed_data):
    """Convert parsed invoice data to CSV format."""
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['line_id', 'description', 'sku_raw', 'quantity', 'unit_code', 'unit_price', 'total_price', 'tax_percent'])
    
    # Data rows
    for item in parsed_data['line_items']:
        writer.writerow([
            item.get('line_id', ''),
            item.get('description', ''),
            item.get('sku_raw', ''),
            item.get('quantity', ''),
            item.get('unit_code', ''),
            item.get('unit_price', ''),
            item.get('total_price', ''),
            item.get('tax_percent', '')
        ])
    
    return output.getvalue()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'xml-parser'})


@app.route('/parse', methods=['POST'])
def parse_invoice():
    """
    Parse UBL XML invoice.
    
    Accepts:
    - multipart/form-data with 'file' field
    - application/xml or text/xml raw body
    
    Query params:
    - format: 'json' (default) or 'csv'
    
    Returns:
    - JSON with invoice_metadata and line_items
    - Or CSV if format=csv
    """
    # Check authentication token if configured
    expected_token = os.environ.get('XML_PARSER_TOKEN')
    if expected_token:
        auth_header = request.headers.get('Authorization')
        if not auth_header or auth_header != f'Bearer {expected_token}':
            logger.warning("Unauthorized access attempt")
            return jsonify({'error': 'Unauthorized'}), 401
    
    xml_content = None
    filename = 'unknown'
    
    try:
        # Check if multipart file upload
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                filename = secure_filename(file.filename)
            xml_content = file.read()
        # Check if raw XML in body
        elif request.content_type in ['application/xml', 'text/xml']:
            xml_content = request.data
            filename = request.args.get('filename', 'uploaded.xml')
        else:
            return jsonify({'error': 'No XML file or data provided'}), 400
        
        if not xml_content:
            return jsonify({'error': 'Empty XML content'}), 400
        
        logger.info(f"Parsing XML file: {filename}, size: {len(xml_content)} bytes")
        
        # Parse the XML
        parsed_data = parse_ubl_invoice(xml_content)
        
        # Return format
        output_format = request.args.get('format', 'json')
        
        if output_format == 'csv':
            csv_data = xml_to_csv(parsed_data)
            return csv_data, 200, {'Content-Type': 'text/csv', 'Content-Disposition': f'attachment; filename="{filename}.csv"'}
        else:
            return jsonify({
                'success': True,
                'filename': filename,
                'data': parsed_data
            })
    
    except ValueError as e:
        logger.error(f"Parse error for {filename}: {e}")
        return jsonify({'error': str(e), 'filename': filename}), 400
    except Exception as e:
        logger.error(f"Unexpected error for {filename}: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
