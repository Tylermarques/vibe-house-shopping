"""HTML parser for extracting home data from various real estate listing formats."""

import re
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Optional
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


class HomeDataParser:
    """Parser for extracting home data from HTML files."""

    def __init__(self):
        self.geolocator = Nominatim(user_agent="vibe-house-shopping")

    def parse_file(self, file_path: Path) -> Optional[dict]:
        """Parse an HTML file and extract home data."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "lxml")

        # Try different parsing strategies based on common real estate sites
        data = self._try_parse_generic(soup, html_content)

        if data:
            data["source_file"] = str(file_path.name)
            data["raw_html"] = html_content[:50000]  # Store first 50k chars

            # Geocode if we have an address but no coordinates
            if data.get("address") and not (data.get("latitude") and data.get("longitude")):
                self._geocode_address(data)

        return data

    def _try_parse_generic(self, soup: BeautifulSoup, html_content: str) -> Optional[dict]:
        """Generic parser that tries to extract data from various formats."""
        data = {}

        # Extract address - try multiple common patterns
        data["address"] = self._extract_address(soup, html_content)

        if not data["address"]:
            # If no address found, this probably isn't a valid listing
            return None

        # Parse location components from address
        self._parse_location_from_address(data)

        # Extract price
        data["price"] = self._extract_price(soup, html_content)

        # Extract bedrooms/bathrooms
        data["bedrooms"] = self._extract_bedrooms(soup, html_content)
        data["bathrooms"] = self._extract_bathrooms(soup, html_content)

        # Extract square footage
        data["sqft"] = self._extract_sqft(soup, html_content)

        # Extract lot size
        data["lot_size"] = self._extract_lot_size(soup, html_content)

        # Extract year built
        data["year_built"] = self._extract_year_built(soup, html_content)

        # Extract property type
        data["property_type"] = self._extract_property_type(soup, html_content)

        # Extract description
        data["description"] = self._extract_description(soup)

        # Try to extract coordinates from embedded maps or data attributes
        lat, lng = self._extract_coordinates(soup, html_content)
        if lat and lng:
            data["latitude"] = lat
            data["longitude"] = lng

        # Extract source URL if present
        data["source_url"] = self._extract_source_url(soup)

        return data

    def _extract_address(self, soup: BeautifulSoup, html_content: str) -> Optional[str]:
        """Extract address from HTML."""
        # Try common selectors
        selectors = [
            '[data-testid="home-details-summary-address"]',
            '[data-testid="address"]',
            ".property-address",
            ".listing-address",
            ".address",
            'h1[class*="address"]',
            '[class*="street-address"]',
            '[itemprop="streetAddress"]',
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return self._clean_text(elem.get_text())

        # Try meta tags
        meta = soup.find("meta", {"property": "og:title"})
        if meta and meta.get("content"):
            content = meta["content"]
            # Often contains address in title
            if re.search(r"\d+\s+\w+", content):
                return self._clean_text(content.split("|")[0].split("-")[0])

        # Try regex patterns in raw HTML
        patterns = [
            r"(\d+\s+[\w\s]+(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane|Ct|Court|Blvd|Boulevard|Way|Pl|Place)[\w\s,]*\d{5})",
            r"(\d+\s+[\w\s]+,\s*[\w\s]+,\s*[A-Z]{2}\s*\d{5})",
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return self._clean_text(match.group(1))

        return None

    def _parse_location_from_address(self, data: dict):
        """Parse city, state, zip from address string."""
        address = data.get("address", "")

        # Try to parse "City, ST ZIP" pattern
        match = re.search(r",\s*([^,]+),\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)", address)
        if match:
            data["city"] = match.group(1).strip()
            data["state"] = match.group(2)
            data["zip_code"] = match.group(3)
            return

        # Try "City, ST" pattern
        match = re.search(r",\s*([^,]+),\s*([A-Z]{2})\s*$", address)
        if match:
            data["city"] = match.group(1).strip()
            data["state"] = match.group(2)

    def _extract_price(self, soup: BeautifulSoup, html_content: str) -> Optional[float]:
        """Extract price from HTML."""
        selectors = [
            '[data-testid="price"]',
            ".price",
            ".listing-price",
            '[class*="price"]',
            '[itemprop="price"]',
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                price = self._parse_price_text(elem.get_text())
                if price:
                    return price

        # Try regex
        patterns = [
            r"\$\s*([\d,]+(?:\.\d{2})?)\s*(?:USD)?",
            r"Price[:\s]*\$?\s*([\d,]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content)
            if match:
                price = self._parse_price_text(match.group(1))
                if price and price > 10000:  # Sanity check
                    return price

        return None

    def _parse_price_text(self, text: str) -> Optional[float]:
        """Parse price from text string."""
        text = text.replace(",", "").replace("$", "").strip()
        match = re.search(r"(\d+(?:\.\d+)?)", text)
        if match:
            return float(match.group(1))
        return None

    def _extract_bedrooms(self, soup: BeautifulSoup, html_content: str) -> Optional[int]:
        """Extract bedroom count from HTML."""
        patterns = [
            r"(\d+)\s*(?:bed|br|bedroom)s?",
            r"(?:bed|br|bedroom)s?[:\s]*(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                count = int(match.group(1))
                if 0 < count < 20:  # Sanity check
                    return count

        return None

    def _extract_bathrooms(self, soup: BeautifulSoup, html_content: str) -> Optional[float]:
        """Extract bathroom count from HTML."""
        patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:bath|ba|bathroom)s?",
            r"(?:bath|ba|bathroom)s?[:\s]*(\d+(?:\.\d+)?)",
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                count = float(match.group(1))
                if 0 < count < 20:  # Sanity check
                    return count

        return None

    def _extract_sqft(self, soup: BeautifulSoup, html_content: str) -> Optional[int]:
        """Extract square footage from HTML."""
        patterns = [
            r"([\d,]+)\s*(?:sq\.?\s*ft|sqft|square\s*feet)",
            r"(?:sq\.?\s*ft|sqft|square\s*feet)[:\s]*([\d,]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                sqft = int(match.group(1).replace(",", ""))
                if 100 < sqft < 100000:  # Sanity check
                    return sqft

        return None

    def _extract_lot_size(self, soup: BeautifulSoup, html_content: str) -> Optional[float]:
        """Extract lot size from HTML (in acres)."""
        patterns = [
            r"([\d.]+)\s*(?:acre|ac)s?",
            r"lot[:\s]*([\d.]+)\s*(?:acre|ac)?",
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                size = float(match.group(1))
                if 0 < size < 10000:  # Sanity check
                    return size

        return None

    def _extract_year_built(self, soup: BeautifulSoup, html_content: str) -> Optional[int]:
        """Extract year built from HTML."""
        patterns = [
            r"(?:built|year\s*built|constructed)[:\s]*(\d{4})",
            r"(\d{4})\s*(?:built|construction)",
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                if 1800 < year < 2030:  # Sanity check
                    return year

        return None

    def _extract_property_type(self, soup: BeautifulSoup, html_content: str) -> Optional[str]:
        """Extract property type from HTML."""
        types = [
            "single family",
            "condo",
            "townhouse",
            "multi-family",
            "apartment",
            "land",
            "mobile home",
            "manufactured",
        ]

        html_lower = html_content.lower()
        for prop_type in types:
            if prop_type in html_lower:
                return prop_type.title()

        return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract property description from HTML."""
        selectors = [
            '[data-testid="description"]',
            ".property-description",
            ".listing-description",
            '[class*="description"]',
            '[itemprop="description"]',
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                text = self._clean_text(elem.get_text())
                if len(text) > 50:  # Sanity check
                    return text[:2000]  # Limit length

        return None

    def _extract_coordinates(self, soup: BeautifulSoup, html_content: str) -> tuple:
        """Extract latitude/longitude from HTML."""
        # Try data attributes
        for elem in soup.find_all(attrs={"data-lat": True, "data-lng": True}):
            try:
                lat = float(elem["data-lat"])
                lng = float(elem["data-lng"])
                return lat, lng
            except (ValueError, KeyError):
                pass

        # Try meta tags
        lat_meta = soup.find("meta", {"property": "place:location:latitude"})
        lng_meta = soup.find("meta", {"property": "place:location:longitude"})
        if lat_meta and lng_meta:
            try:
                return float(lat_meta["content"]), float(lng_meta["content"])
            except (ValueError, KeyError):
                pass

        # Try regex patterns
        patterns = [
            r'"latitude"[:\s]*([-\d.]+)[,\s]*"longitude"[:\s]*([-\d.]+)',
            r'"lat"[:\s]*([-\d.]+)[,\s]*"lng"[:\s]*([-\d.]+)',
            r'"lat"[:\s]*([-\d.]+)[,\s]*"lon"[:\s]*([-\d.]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content)
            if match:
                try:
                    lat = float(match.group(1))
                    lng = float(match.group(2))
                    if -90 <= lat <= 90 and -180 <= lng <= 180:
                        return lat, lng
                except ValueError:
                    pass

        return None, None

    def _extract_source_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the source URL from HTML."""
        # Try canonical link
        canonical = soup.find("link", {"rel": "canonical"})
        if canonical and canonical.get("href"):
            return canonical["href"]

        # Try og:url
        og_url = soup.find("meta", {"property": "og:url"})
        if og_url and og_url.get("content"):
            return og_url["content"]

        return None

    def _geocode_address(self, data: dict):
        """Geocode an address to get coordinates."""
        address_parts = [data.get("address")]
        if data.get("city"):
            address_parts.append(data["city"])
        if data.get("state"):
            address_parts.append(data["state"])
        if data.get("zip_code"):
            address_parts.append(data["zip_code"])

        full_address = ", ".join(filter(None, address_parts))

        try:
            location = self.geolocator.geocode(full_address, timeout=10)
            if location:
                data["latitude"] = location.latitude
                data["longitude"] = location.longitude
        except (GeocoderTimedOut, GeocoderServiceError):
            pass  # Geocoding failed, coordinates will remain None

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        text = re.sub(r"\s+", " ", text)
        return text.strip()
