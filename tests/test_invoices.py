"""
Integration tests for invoice upload and XML parsing.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
import os
from unittest.mock import patch, AsyncMock
from app.main import app
from app import models
from app.database import get_session


# Create in-memory test database
@pytest.fixture(name="session")
def session_fixture():
    """Create a fresh in-memory database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create test client with overridden database session."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_xml():
    """Load sample UBL invoice XML."""
    xml_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'services/xml_parser/tests/sample_invoice.xml'
    )
    with open(xml_path, 'rb') as f:
        return f.read()


@pytest.fixture
def mock_parser_response():
    """Mock response from XML parser service."""
    return {
        'success': True,
        'filename': 'test_invoice.xml',
        'data': {
            'invoice_metadata': {
                'invoice_number': 'INV-2024-001',
                'invoice_date': '2024-01-15',
                'supplier': 'Test Supplier Ltd',
                'total_amount': 1190.0
            },
            'line_items': [
                {
                    'line_id': '1',
                    'description': 'Widget A',
                    'sku_raw': 'SKU-001',
                    'quantity': 10.0,
                    'unit_code': 'EA',
                    'unit_price': 50.0,
                    'line_total': 500.0,
                    'tax_percent': 19.0,
                    'total_price': 500.0
                },
                {
                    'line_id': '2',
                    'description': 'Material B',
                    'sku_raw': 'SKU-002',
                    'quantity': 5.0,
                    'unit_code': 'KG',
                    'unit_price': 120.0,
                    'line_total': 600.0,
                    'tax_percent': 19.0,
                    'total_price': 600.0
                }
            ]
        }
    }


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/api/v1")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_invoice_health_endpoint_without_parser(client):
    """Test invoice health endpoint when parser is not configured."""
    with patch('app.config.config.XML_PARSER_URL', None):
        response = client.get("/api/invoices/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['xml_parser_configured'] is False


def test_invoice_health_endpoint_with_parser(client):
    """Test invoice health endpoint when parser is configured."""
    with patch('app.config.config.XML_PARSER_URL', 'http://localhost:5000'):
        response = client.get("/api/invoices/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['xml_parser_configured'] is True
        assert data['xml_parser_url'] == 'http://localhost:5000'


def test_upload_empty_file(client):
    """Test uploading an empty file."""
    response = client.post(
        "/api/invoices/upload",
        files={"file": ("empty.xml", b"", "application/xml")}
    )
    assert response.status_code == 400
    assert "Empty file" in response.json()['detail']


def test_upload_non_xml_file(client):
    """Test uploading a non-XML file."""
    response = client.post(
        "/api/invoices/upload",
        files={"file": ("test.pdf", b"dummy pdf content", "application/pdf")}
    )
    assert response.status_code == 400
    assert "Only XML invoice files" in response.json()['detail']


def test_upload_xml_without_parser_configured(client, sample_xml):
    """Test uploading XML when parser service is not configured."""
    with patch('app.config.config.XML_PARSER_URL', None):
        response = client.post(
            "/api/invoices/upload",
            files={"file": ("invoice.xml", sample_xml, "application/xml")}
        )
        assert response.status_code == 503
        assert "not configured" in response.json()['detail']


@pytest.mark.asyncio
async def test_upload_xml_with_parser_success(client, session, sample_xml, mock_parser_response):
    """Test successful XML upload with mocked parser service."""
    # Mock the httpx client response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: mock_parser_response  # Use regular function, not async
    
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    
    async def mock_async_client(*args, **kwargs):
        return mock_client
    
    with patch('app.config.config.XML_PARSER_URL', 'http://localhost:5000'):
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client
            response = client.post(
                "/api/invoices/upload",
                files={"file": ("test_invoice.xml", sample_xml, "application/xml")}
            )
    
    # Verify response
    assert response.status_code == 201
    data = response.json()
    assert data['success'] is True
    assert data['invoice_number'] == 'INV-2024-001'
    assert data['supplier'] == 'Test Supplier Ltd'
    assert data['total_amount'] == 1190.0
    assert data['items_count'] == 2
    
    # Verify purchase was created in database
    purchase = session.get(models.Purchase, data['purchase_id'])
    assert purchase is not None
    assert purchase.invoice_number == 'INV-2024-001'
    assert purchase.supplier == 'Test Supplier Ltd'
    
    # Verify purchase items were created
    from sqlmodel import select
    items = session.exec(
        select(models.PurchaseItem).where(models.PurchaseItem.purchase_id == purchase.id)
    ).all()
    assert len(items) == 2
    assert items[0].description == 'Widget A'
    assert items[0].sku_raw == 'SKU-001'
    assert items[0].quantity == 10.0
    assert items[1].description == 'Material B'


@pytest.mark.asyncio
async def test_upload_xml_parser_auth_failure(client, sample_xml):
    """Test XML upload when parser authentication fails."""
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_response.json = lambda: {'error': 'Unauthorized'}
    mock_response.text = '{"error": "Unauthorized"}'
    
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    
    with patch('app.config.config.XML_PARSER_URL', 'http://localhost:5000'):
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client
            response = client.post(
                "/api/invoices/upload",
                files={"file": ("test_invoice.xml", sample_xml, "application/xml")}
            )
    
    assert response.status_code == 502
    assert "authentication failed" in response.json()['detail']


@pytest.mark.asyncio
async def test_upload_xml_parser_error(client, sample_xml):
    """Test XML upload when parser returns an error."""
    mock_response = AsyncMock()
    mock_response.status_code = 400
    mock_response.json = lambda: {'error': 'Invalid XML'}
    mock_response.text = '{"error": "Invalid XML"}'
    
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    
    with patch('app.config.config.XML_PARSER_URL', 'http://localhost:5000'):
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client
            response = client.post(
                "/api/invoices/upload",
                files={"file": ("test_invoice.xml", sample_xml, "application/xml")}
            )
    
    assert response.status_code == 502
    assert "Parser service error" in response.json()['detail']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
