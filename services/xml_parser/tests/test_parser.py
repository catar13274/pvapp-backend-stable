"""
Unit tests for XML invoice parser.
"""
import pytest
import sys
import os
from io import BytesIO

# Add parent directory to path to import parser_app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser_app import app, parse_ubl_invoice


@pytest.fixture
def client():
    """Create test client for Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_xml():
    """Load sample UBL invoice XML."""
    xml_path = os.path.join(os.path.dirname(__file__), 'sample_invoice.xml')
    with open(xml_path, 'rb') as f:
        return f.read()


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'xml-parser'


def test_parse_ubl_invoice_function(sample_xml):
    """Test the parse_ubl_invoice function directly."""
    result = parse_ubl_invoice(sample_xml)
    
    # Check metadata
    assert 'invoice_metadata' in result
    assert 'line_items' in result
    
    metadata = result['invoice_metadata']
    assert metadata['invoice_number'] == 'INV-2024-001'
    assert metadata['invoice_date'] == '2024-01-15'
    assert metadata['supplier'] == 'Test Supplier Ltd'
    assert metadata['total_amount'] == 1190.00
    
    # Check line items
    items = result['line_items']
    assert len(items) == 2
    
    # First line item
    item1 = items[0]
    assert item1['line_id'] == '1'
    assert item1['description'] == 'Widget A'
    assert item1['sku_raw'] == 'SKU-001'
    assert item1['quantity'] == 10.0
    assert item1['unit_code'] == 'EA'
    assert item1['unit_price'] == 50.00
    assert item1['line_total'] == 500.00
    assert item1['tax_percent'] == 19.00
    assert item1['total_price'] == 500.00  # quantity * unit_price
    
    # Second line item
    item2 = items[1]
    assert item2['line_id'] == '2'
    assert item2['description'] == 'Material B'
    assert item2['sku_raw'] == 'SKU-002'
    assert item2['quantity'] == 5.0
    assert item2['unit_code'] == 'KG'
    assert item2['unit_price'] == 120.00
    assert item2['line_total'] == 600.00
    assert item2['tax_percent'] == 19.00
    assert item2['total_price'] == 600.00


def test_parse_endpoint_with_file(client, sample_xml):
    """Test /parse endpoint with multipart file upload."""
    data = {
        'file': (BytesIO(sample_xml), 'test_invoice.xml')
    }
    
    response = client.post('/parse', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    
    result = response.get_json()
    assert result['success'] is True
    assert result['filename'] == 'test_invoice.xml'
    assert 'data' in result
    
    # Verify parsed data
    parsed = result['data']
    assert len(parsed['line_items']) == 2
    assert parsed['invoice_metadata']['invoice_number'] == 'INV-2024-001'


def test_parse_endpoint_with_raw_xml(client, sample_xml):
    """Test /parse endpoint with raw XML body."""
    response = client.post('/parse', data=sample_xml, content_type='application/xml')
    assert response.status_code == 200
    
    result = response.get_json()
    assert result['success'] is True
    assert len(result['data']['line_items']) == 2


def test_parse_endpoint_csv_format(client, sample_xml):
    """Test /parse endpoint with CSV output format."""
    data = {
        'file': (BytesIO(sample_xml), 'test_invoice.xml')
    }
    
    response = client.post('/parse?format=csv', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    assert 'text/csv' in response.content_type
    
    csv_content = response.data.decode('utf-8')
    assert 'line_id,description,sku_raw,quantity' in csv_content
    assert 'Widget A' in csv_content
    assert 'Material B' in csv_content


def test_parse_endpoint_no_file(client):
    """Test /parse endpoint without file."""
    response = client.post('/parse')
    assert response.status_code == 400
    
    result = response.get_json()
    assert 'error' in result


def test_parse_endpoint_invalid_xml(client):
    """Test /parse endpoint with invalid XML."""
    bad_xml = b'<not>valid<xml>'
    data = {
        'file': (BytesIO(bad_xml), 'bad.xml')
    }
    
    response = client.post('/parse', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    
    result = response.get_json()
    assert 'error' in result


def test_parse_endpoint_with_auth_token(client, sample_xml, monkeypatch):
    """Test /parse endpoint with authentication token."""
    # Set environment variable for token
    monkeypatch.setenv('XML_PARSER_TOKEN', 'test-secret-token')
    
    # Request without token should fail
    data = {
        'file': (BytesIO(sample_xml), 'test_invoice.xml')
    }
    response = client.post('/parse', data=data, content_type='multipart/form-data')
    assert response.status_code == 401
    
    # Request with correct token should succeed
    # Need to create fresh BytesIO for second request
    data2 = {
        'file': (BytesIO(sample_xml), 'test_invoice.xml')
    }
    headers = {'Authorization': 'Bearer test-secret-token'}
    response = client.post('/parse', data=data2, content_type='multipart/form-data', headers=headers)
    assert response.status_code == 200


def test_parse_malformed_xml_elements():
    """Test parsing XML with missing or malformed elements."""
    minimal_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
             xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
             xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
        <cac:InvoiceLine>
            <cbc:ID>1</cbc:ID>
            <cbc:InvoicedQuantity unitCode="EA">invalid_number</cbc:InvoicedQuantity>
        </cac:InvoiceLine>
    </Invoice>
    """
    
    result = parse_ubl_invoice(minimal_xml)
    assert 'line_items' in result
    assert len(result['line_items']) == 1
    # Should handle invalid quantity gracefully
    assert result['line_items'][0]['quantity'] == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
