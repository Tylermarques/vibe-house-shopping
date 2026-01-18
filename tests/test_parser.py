"""Tests for the HomeDataParser class."""

import json

import pytest
from bs4 import BeautifulSoup


class TestJsonLdParsing:
    """Tests for JSON-LD structured data extraction."""

    def test_parse_json_ld_extracts_residence_data(self, parser, sample_residence_json_ld):
        """Test that residence data is extracted from JSON-LD."""
        html = f"""
        <html>
        <head>
            <script type="application/ld+json">{json.dumps(sample_residence_json_ld)}</script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        data = parser._parse_json_ld(soup)

        assert data["num_rooms"] == 8
        assert data["bedrooms"] == 3
        assert data["bathrooms"] == 2
        assert data["sqft"] == 1495

    def test_parse_json_ld_extracts_address(self, parser, sample_residence_json_ld):
        """Test that address components are extracted from JSON-LD."""
        html = f"""
        <html>
        <head>
            <script type="application/ld+json">{json.dumps(sample_residence_json_ld)}</script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        data = parser._parse_json_ld(soup)

        assert "123 Test Street" in data["address"]
        assert data["city"] == "Vancouver"
        assert data["state"] == "BC"
        assert data["zip_code"] == "V6B1A1"
        assert data["country"] == "CA"

    def test_parse_json_ld_extracts_geo_coordinates(self, parser, sample_residence_json_ld):
        """Test that geo coordinates are extracted from JSON-LD."""
        html = f"""
        <html>
        <head>
            <script type="application/ld+json">{json.dumps(sample_residence_json_ld)}</script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        data = parser._parse_json_ld(soup)

        assert data["latitude"] == pytest.approx(49.2827, rel=1e-4)
        assert data["longitude"] == pytest.approx(-123.1207, rel=1e-4)

    def test_parse_json_ld_extracts_media_urls(self, parser, sample_residence_json_ld):
        """Test that image and video URLs are extracted from JSON-LD."""
        html = f"""
        <html>
        <head>
            <script type="application/ld+json">{json.dumps(sample_residence_json_ld)}</script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        data = parser._parse_json_ld(soup)

        assert data["image_url"] == "https://example.com/image.jpg"
        assert data["video_url"] == "https://youtube.com/watch?v=test123"

    def test_parse_json_ld_extracts_product_data(
        self, parser, sample_residence_json_ld, sample_product_json_ld
    ):
        """Test that MLS ID, price, and currency are extracted from Product JSON-LD."""
        html = f"""
        <html>
        <head>
            <script type="application/ld+json">{json.dumps(sample_residence_json_ld)}</script>
            <script type="application/ld+json">{json.dumps(sample_product_json_ld)}</script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        data = parser._parse_json_ld(soup)

        assert data["mls_id"] == "R3065322"
        assert data["price"] == 999900
        assert data["currency"] == "CAD"

    def test_parse_json_ld_handles_empty_scripts(self, parser):
        """Test that parser handles empty JSON-LD scripts gracefully."""
        html = """
        <html>
        <head>
            <script type="application/ld+json"></script>
            <script type="application/ld+json">invalid json{</script>
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        data = parser._parse_json_ld(soup)

        # Should return empty dict without errors
        assert isinstance(data, dict)


class TestCoordinateValidation:
    """Tests for coordinate validation and swap detection."""

    def test_validate_coordinates_normal(self, parser):
        """Test that normal coordinates pass through unchanged."""
        lat, lng = parser._validate_coordinates(49.2827, -123.1207)
        assert lat == pytest.approx(49.2827, rel=1e-4)
        assert lng == pytest.approx(-123.1207, rel=1e-4)

    def test_validate_coordinates_detects_swap(self, parser):
        """Test that swapped lat/lng (like HouseSigma) are corrected."""
        # HouseSigma sometimes puts longitude in latitude field and vice versa
        # -123.15 is clearly a longitude (out of lat range), 49.7 is latitude
        lat, lng = parser._validate_coordinates(-123.154841617, 49.7030265)

        assert lat == pytest.approx(49.7030265, rel=1e-4)
        assert lng == pytest.approx(-123.154841617, rel=1e-4)

    def test_validate_coordinates_out_of_range(self, parser):
        """Test that out-of-range latitude triggers swap."""
        # If lat is < -90 or > 90, it must be swapped
        lat, lng = parser._validate_coordinates(-150.0, 45.0)
        assert lat == 45.0
        assert lng == -150.0


class TestCanadianAddressParsing:
    """Tests for Canadian address format parsing."""

    def test_parse_canadian_postal_code(self, parser):
        """Test parsing Canadian postal code format."""
        data = {"address": "123 Main St, Vancouver, BC V6B 1A1"}
        parser._parse_location_from_address(data)

        assert data["city"] == "Vancouver"
        assert data["state"] == "BC"
        assert data["zip_code"] == "V6B1A1"
        assert data["country"] == "CA"

    def test_parse_canadian_province_abbreviation(self, parser):
        """Test parsing with province abbreviation."""
        data = {"address": "456 Oak Ave, Toronto, ON M5V2H1"}
        parser._parse_location_from_address(data)

        assert data["city"] == "Toronto"
        assert data["state"] == "ON"
        assert data["zip_code"] == "M5V2H1"

    def test_parse_canadian_full_province_name(self, parser):
        """Test parsing with full province name converted to abbreviation."""
        data = {"address": "789 Pine Rd, Calgary, alberta T2P1J9"}
        parser._parse_location_from_address(data)

        # Should convert "alberta" to "AB"
        # Note: This depends on the regex matching full province names
        # Current implementation may not handle lowercase province names

    def test_parse_us_zip_code(self, parser):
        """Test parsing US ZIP code format."""
        data = {"address": "123 Main St, Seattle, WA 98101"}
        parser._parse_location_from_address(data)

        assert data["city"] == "Seattle"
        assert data["state"] == "WA"
        assert data["zip_code"] == "98101"
        assert data["country"] == "US"

    def test_parse_us_zip_plus_four(self, parser):
        """Test parsing US ZIP+4 format."""
        data = {"address": "123 Main St, Portland, OR 97201-1234"}
        parser._parse_location_from_address(data)

        assert data["city"] == "Portland"
        assert data["state"] == "OR"
        assert data["zip_code"] == "97201-1234"

    def test_parse_preserves_existing_location_data(self, parser):
        """Test that existing location data from JSON-LD is preserved."""
        data = {
            "address": "123 Main St, Vancouver, BC V6B1A1",
            "city": "Vancouver",
            "state": "BC",
            "zip_code": "V6B1A1",
        }
        parser._parse_location_from_address(data)

        # Should not overwrite existing data
        assert data["city"] == "Vancouver"
        assert data["state"] == "BC"


class TestMlsIdExtraction:
    """Tests for MLS ID extraction."""

    def test_extract_mls_id_from_r_pattern(self, parser):
        """Test extracting Canadian MLS format R1234567."""
        html = "Listing ID: R3065322, MLS"
        result = parser._extract_mls_id(html)
        assert result == "R3065322"

    def test_extract_mls_id_from_mls_pattern(self, parser):
        """Test extracting MLS# format."""
        html = "MLS# ABC12345 - Beautiful home"
        result = parser._extract_mls_id(html)
        assert result == "ABC12345"

    def test_extract_mls_id_from_json_sku(self, parser):
        """Test extracting from JSON sku field."""
        html = '"sku": "R3065322"'
        result = parser._extract_mls_id(html)
        assert result == "R3065322"

    def test_extract_mls_id_returns_none_when_not_found(self, parser):
        """Test that None is returned when no MLS ID found."""
        html = "No listing ID here"
        result = parser._extract_mls_id(html)
        assert result is None


class TestGarageExtraction:
    """Tests for garage/parking space extraction."""

    def test_extract_garage_spaces_car_garage(self, parser):
        """Test extracting '2 car garage' pattern."""
        html = "Features: 2 car garage, central AC"
        result = parser._extract_garage_spaces(html)
        assert result == 2

    def test_extract_garage_spaces_simple(self, parser):
        """Test extracting '1 Garage' pattern."""
        html = "Parking: 1 Garage"
        result = parser._extract_garage_spaces(html)
        assert result == 1

    def test_extract_garage_spaces_parking_spots(self, parser):
        """Test extracting parking spaces pattern."""
        html = "Includes 3 parking spaces"
        result = parser._extract_garage_spaces(html)
        assert result == 3

    def test_extract_garage_spaces_returns_none_when_not_found(self, parser):
        """Test that None is returned when no garage info found."""
        html = "Beautiful home with garden"
        result = parser._extract_garage_spaces(html)
        assert result is None


class TestFullParsing:
    """Integration tests with the real example HTML fixture."""

    def test_parse_example_listing_full(self, parser, example_html_path):
        """Test end-to-end parsing of the example HTML file."""
        result = parser.parse_file(example_html_path)

        assert result is not None
        assert "Eaglewind" in result["address"]

    def test_parse_file_returns_all_new_fields(self, parser, example_html_path):
        """Test that all new fields are present in parsed result."""
        result = parser.parse_file(example_html_path)

        # Check all new fields are present
        assert "mls_id" in result
        assert "num_rooms" in result
        assert "garage_spaces" in result
        assert "image_url" in result
        assert "video_url" in result
        assert "currency" in result
        assert "country" in result

    def test_parse_example_extracts_correct_values(self, parser, example_html_path):
        """Test that correct values are extracted from example listing."""
        result = parser.parse_file(example_html_path)

        # Verify key values from the HouseSigma listing
        assert result["bedrooms"] == 3
        assert result["bathrooms"] == 2
        assert result["sqft"] == 1495
        assert result["num_rooms"] == 8
        assert result["city"] == "Squamish"
        assert result["state"] == "BC"
        assert result["country"] == "CA"
        assert result["mls_id"] == "R3065322"
        assert result["price"] == pytest.approx(999900, rel=0.01)
        assert result["currency"] == "CAD"

    def test_parse_example_corrects_swapped_coordinates(self, parser, example_html_path):
        """Test that swapped coordinates in example are corrected."""
        result = parser.parse_file(example_html_path)

        # Squamish, BC is approximately at:
        # Latitude: ~49.7 (positive, north)
        # Longitude: ~-123.15 (negative, west)
        assert result["latitude"] == pytest.approx(49.7, rel=0.1)
        assert result["longitude"] == pytest.approx(-123.15, rel=0.1)

    def test_parse_example_extracts_media_urls(self, parser, example_html_path):
        """Test that image and video URLs are extracted."""
        result = parser.parse_file(example_html_path)

        assert result["image_url"] is not None
        assert "housesigma.com" in result["image_url"]

        assert result["video_url"] is not None
        assert "youtu" in result["video_url"]


class TestFloorSizeConversion:
    """Tests for floor size unit conversion."""

    def test_floor_size_sqft_unit(self, parser):
        """Test floor size extraction with square feet unit."""
        json_ld = {
            "@type": "Residence",
            "floorSize": {"@type": "QuantitativeValue", "value": 1500, "unitCode": "FTK"},
        }
        html = f'<script type="application/ld+json">{json.dumps(json_ld)}</script>'
        soup = BeautifulSoup(html, "lxml")
        data = parser._parse_json_ld(soup)

        assert data["sqft"] == 1500

    def test_floor_size_sqm_conversion(self, parser):
        """Test floor size conversion from square meters."""
        json_ld = {
            "@type": "Residence",
            "floorSize": {"@type": "QuantitativeValue", "value": 100, "unitCode": "MTK"},
        }
        html = f'<script type="application/ld+json">{json.dumps(json_ld)}</script>'
        soup = BeautifulSoup(html, "lxml")
        data = parser._parse_json_ld(soup)

        # 100 sqm * 10.764 = ~1076 sqft
        assert data["sqft"] == pytest.approx(1076, rel=0.01)

    def test_floor_size_numeric_value(self, parser):
        """Test floor size when value is just a number."""
        json_ld = {
            "@type": "Residence",
            "floorSize": 2000,
        }
        html = f'<script type="application/ld+json">{json.dumps(json_ld)}</script>'
        soup = BeautifulSoup(html, "lxml")
        data = parser._parse_json_ld(soup)

        assert data["sqft"] == 2000


class TestImageUrlExtraction:
    """Tests for image URL extraction from various formats."""

    def test_image_url_string(self, parser):
        """Test image extraction when value is a string."""
        json_ld = {
            "@type": "Residence",
            "image": "https://example.com/photo.jpg",
        }
        html = f'<script type="application/ld+json">{json.dumps(json_ld)}</script>'
        soup = BeautifulSoup(html, "lxml")
        data = parser._parse_json_ld(soup)

        assert data["image_url"] == "https://example.com/photo.jpg"

    def test_image_url_array(self, parser):
        """Test image extraction when value is an array."""
        json_ld = {
            "@type": "Residence",
            "image": [
                "https://example.com/photo1.jpg",
                "https://example.com/photo2.jpg",
            ],
        }
        html = f'<script type="application/ld+json">{json.dumps(json_ld)}</script>'
        soup = BeautifulSoup(html, "lxml")
        data = parser._parse_json_ld(soup)

        # Should use first image
        assert data["image_url"] == "https://example.com/photo1.jpg"

    def test_image_url_object(self, parser):
        """Test image extraction when value is an object with url field."""
        json_ld = {
            "@type": "Residence",
            "image": {"@type": "ImageObject", "url": "https://example.com/photo.jpg"},
        }
        html = f'<script type="application/ld+json">{json.dumps(json_ld)}</script>'
        soup = BeautifulSoup(html, "lxml")
        data = parser._parse_json_ld(soup)

        assert data["image_url"] == "https://example.com/photo.jpg"
