"""
eFactura.ro API Integration
Handles parsing and syncing invoices from eFactura.ro
"""
import httpx
from typing import Optional, List, Dict
from datetime import datetime
import xml.etree.ElementTree as ET

class EFacturaClient:
    def __init__(self, api_key: str, base_url: str = "https://api.efactura.ro"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def get_invoices(self, company_tax_id: str, date_from: str, date_to: str) -> List[Dict]:
        """Fetch invoices from eFactura.ro"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "cif": company_tax_id,
            "data_inceput": date_from,
            "data_sfarsit": date_to
        }
        
        response = await self.client.get(
            f"{self.base_url}/api/v1/invoices",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        return []
    
    async def download_invoice_xml(self, invoice_id: str) -> Optional[str]:
        """Download invoice XML from eFactura.ro"""
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        response = await self.client.get(
            f"{self.base_url}/api/v1/invoices/{invoice_id}/download",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.text
        return None
    
    def parse_invoice_xml(self, xml_content: str) -> Dict:
        """Parse eFactura XML to extract invoice data"""
        try:
            root = ET.fromstring(xml_content)
            
            # Extract basic invoice info
            invoice_data = {
                "invoice_number": self._get_element_text(root, ".//cbc:ID"),
                "invoice_date": self._get_element_text(root, ".//cbc:IssueDate"),
                "supplier_name": self._get_element_text(root, ".//cac:AccountingSupplierParty//cbc:Name"),
                "supplier_tax_id": self._get_element_text(root, ".//cac:AccountingSupplierParty//cbc:CompanyID"),
                "total_amount": float(self._get_element_text(root, ".//cbc:TaxInclusiveAmount") or 0),
                "currency": self._get_element_text(root, ".//cbc:DocumentCurrencyCode"),
                "items": []
            }
            
            # Extract line items
            for line in root.findall(".//cac:InvoiceLine"):
                item = {
                    "description": self._get_element_text(line, ".//cbc:Name"),
                    "quantity": float(self._get_element_text(line, ".//cbc:InvoicedQuantity") or 0),
                    "unit_price": float(self._get_element_text(line, ".//cbc:PriceAmount") or 0),
                    "total_price": float(self._get_element_text(line, ".//cbc:LineExtensionAmount") or 0),
                    "unit": self._get_element_text(line, ".//cbc:InvoicedQuantity[@unitCode]")
                }
                invoice_data["items"].append(item)
            
            return invoice_data
        except Exception as e:
            print(f"Error parsing XML: {e}")
            return {}
    
    def _get_element_text(self, root, xpath: str) -> Optional[str]:
        """Helper to safely extract text from XML element"""
        element = root.find(xpath)
        return element.text if element is not None else None
    
    async def sync_invoice_to_db(self, invoice_data: Dict, company_id: int, db_session):
        """Sync parsed invoice data to database"""
        from app.models import Purchase, PurchaseItem, Material
        
        # Create purchase record
        purchase = Purchase(
            company_id=company_id,
            supplier=invoice_data.get("supplier_name"),
            invoice_number=invoice_data.get("invoice_number"),
            invoice_date=invoice_data.get("invoice_date"),
            total_amount=invoice_data.get("total_amount"),
            efactura_id=invoice_data.get("invoice_id")
        )
        
        db_session.add(purchase)
        await db_session.commit()
        await db_session.refresh(purchase)
        
        # Create purchase items
        for item in invoice_data.get("items", []):
            # Try to find existing material by description
            material = await db_session.exec(
                f"SELECT * FROM material WHERE company_id = {company_id} AND name LIKE '%{item['description']}%' LIMIT 1"
            )
            
            purchase_item = PurchaseItem(
                purchase_id=purchase.id,
                material_id=material.id if material else None,
                description=item["description"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                total_price=item["total_price"]
            )
            
            db_session.add(purchase_item)
        
        await db_session.commit()
        return purchase
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()