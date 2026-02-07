import defusedxml.ElementTree as ET
from typing import List, Dict, Optional

def parse_invoice_products(xml_content: str) -> Dict:
    """
    Parsează o factură XML în format UBL (e-Factura RO) și extrage informații despre produse.
    
    Args:
        xml_content: Conținutul XML ca string
        
    Returns:
        Dict cu informații despre factură și produse
    """
    root = ET.fromstring(xml_content)
    
    namespaces = {
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
    }
    
    # Extrage informații generale despre factură
    invoice_number = root.find('cbc:ID', namespaces)
    invoice_date = root.find('cbc:IssueDate', namespaces)
    supplier_name = root.find('cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name', namespaces)
    
    # Extrage produsele
    products = []
    
    for line in root.findall('cac:InvoiceLine', namespaces):
        name = line.find('cac:Item/cbc:Name', namespaces)
        quantity = line.find('cbc:InvoicedQuantity', namespaces)
        price = line.find('cac:Price/cbc:PriceAmount', namespaces)
        total = line.find('cbc:LineExtensionAmount', namespaces)
        tax = line.find('cac:Item/cac:ClassifiedTaxCategory/cbc:Percent', namespaces)
        
        # Extrage SKU dacă există
        sku = line.find('cac:Item/cac:SellersItemIdentification/cbc:ID', namespaces)
        
        product = {
            "name": name.text if name is not None else "",
            "sku": sku.text if sku is not None else "",
            "quantity": float(quantity.text) if quantity is not None else 0.0,
            "unit": quantity.attrib.get('unitCode', 'buc') if quantity is not None else 'buc',
            "unit_price": float(price.text) if price is not None else 0.0,
            "total_price": float(total.text) if total is not None else 0.0,
            "tax_percent": float(tax.text) if tax is not None else 0.0
        }
        
        products.append(product)
    
    return {
        "invoice_number": invoice_number.text if invoice_number is not None else "",
        "invoice_date": invoice_date.text if invoice_date is not None else "",
        "supplier": supplier_name.text if supplier_name is not None else "",
        "products": products,
        "total_amount": sum(p["total_price"] for p in products)
    }
