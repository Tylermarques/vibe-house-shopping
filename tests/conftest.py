"""Pytest fixtures for vibe-house-shopping tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the project root to Python path so 'app' can be imported
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# Pre-import modules that may have state issues with Python 3.14
# This avoids SQLAlchemy re-registration errors when running multiple tests
try:
    import sqlalchemy
    from sqlalchemy import create_engine
    from sqlalchemy.orm import declarative_base, sessionmaker
except ImportError:
    pass


# Mock geopy before importing parser to avoid dependency issues in test environments
@pytest.fixture(autouse=True)
def mock_geopy():
    """Mock geopy to avoid network calls during tests."""
    mock_nominatim = MagicMock()
    mock_nominatim.return_value.geocode.return_value = None

    with patch.dict(
        sys.modules,
        {
            "geopy": MagicMock(),
            "geopy.geocoders": MagicMock(Nominatim=mock_nominatim),
            "geopy.exc": MagicMock(
                GeocoderTimedOut=Exception, GeocoderServiceError=Exception
            ),
        },
    ):
        yield mock_nominatim


@pytest.fixture
def parser():
    """Create a HomeDataParser instance with mocked geocoder."""
    from app.parser import HomeDataParser

    p = HomeDataParser()
    # Mock the geocoder to avoid network calls
    p.geolocator = MagicMock()
    p.geolocator.geocode.return_value = None
    return p


@pytest.fixture
def example_html_path():
    """Path to the example HTML listing file."""
    return Path(__file__).parent / "examples" / "example_listing_1.html"


@pytest.fixture
def example_html_content(example_html_path):
    """Load the example HTML content."""
    with open(example_html_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


@pytest.fixture
def sample_residence_json_ld():
    """Sample JSON-LD data for a Residence type."""
    return {
        "@context": "http://schema.org",
        "@type": ["Place", "Residence", "RealEstateListing", "SingleFamilyResidence"],
        "name": "Test Property",
        "description": "A beautiful test property with modern amenities.",
        "numberOfRooms": 8,
        "numberOfBedrooms": 3,
        "numberOfBathroomsTotal": 2,
        "floorSize": {"@type": "QuantitativeValue", "value": 1495, "unitCode": "FTK"},
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "123 Test Street",
            "addressLocality": "Vancouver",
            "addressRegion": "BC",
            "postalCode": "V6B1A1",
            "addressCountry": "CA",
        },
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": 49.2827,  # Normal coordinates
            "longitude": -123.1207,
        },
        "image": "https://example.com/image.jpg",
        "video": {
            "@type": "VideoObject",
            "contentUrl": "https://youtube.com/watch?v=test123",
        },
        "url": "https://example.com/listing/123",
    }


@pytest.fixture
def sample_product_json_ld():
    """Sample JSON-LD data for a Product type (contains price and MLS)."""
    return {
        "@context": "http://schema.org",
        "@type": "Product",
        "name": "Test Property Listing",
        "sku": "R3065322",
        "offers": {
            "@type": "Offer",
            "price": 999900,
            "priceCurrency": "CAD",
            "availability": "https://schema.org/InStock",
        },
    }


@pytest.fixture
def swapped_coordinates_json_ld():
    """JSON-LD with swapped lat/lng (like HouseSigma sometimes returns)."""
    return {
        "@context": "http://schema.org",
        "@type": "Residence",
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": -123.154841617,  # This is actually longitude!
            "longitude": 49.7030265,  # This is actually latitude!
        },
    }


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.database import Base, engine, init_db

    db_path = tmp_path / "test_homes.db"
    test_engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(test_engine)

    Session = sessionmaker(bind=test_engine)
    session = Session()

    yield session

    session.close()
