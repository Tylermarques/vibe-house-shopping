"""HTML parser for extracting home data from various real estate listing formats."""

import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim


class HomeDataParser:
    """Parser for extracting home data from HTML files."""

    # Canadian province name to abbreviation mapping
    PROVINCE_MAP = {
        "british columbia": "BC",
        "ontario": "ON",
        "quebec": "QC",
        "alberta": "AB",
        "manitoba": "MB",
        "saskatchewan": "SK",
        "nova scotia": "NS",
        "new brunswick": "NB",
        "newfoundland and labrador": "NL",
        "prince edward island": "PE",
        "northwest territories": "NT",
        "yukon": "YT",
        "nunavut": "NU",
    }

    def __init__(self):
        self.geolocator = Nominatim(user_agent="vibe-house-shopping")

    def parse_file(self, file_path: Path) -> dict[str, Any] | None:
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

    def _parse_json_ld(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extract data from JSON-LD structured data blocks (schema.org)."""
        data = {}

        # Find all JSON-LD script tags
        scripts = soup.find_all("script", type="application/ld+json")

        for script in scripts:
            if not script.string:
                continue
            try:
                json_data = json.loads(script.string)

                # Handle @type as string or list
                types = json_data.get("@type", [])
                if isinstance(types, str):
                    types = [types]

                # Process Residence/RealEstateListing data
                if any(
                    t in types
                    for t in [
                        "Residence",
                        "RealEstateListing",
                        "SingleFamilyResidence",
                        "House",
                        "Apartment",
                    ]
                ):
                    self._extract_residence_json_ld(json_data, data)

                # Process Product data (contains price and MLS ID)
                if "Product" in types:
                    self._extract_product_json_ld(json_data, data)

            except json.JSONDecodeError:
                continue

        return data

    def _extract_residence_json_ld(self, json_data: dict[str, Any], data: dict[str, Any]) -> None:
        """Extract residence-specific data from JSON-LD."""
        # Basic property info
        if "numberOfRooms" in json_data and "num_rooms" not in data:
            data["num_rooms"] = json_data["numberOfRooms"]

        if "numberOfBedrooms" in json_data and "bedrooms" not in data:
            data["bedrooms"] = json_data["numberOfBedrooms"]

        if "numberOfBathroomsTotal" in json_data and "bathrooms" not in data:
            data["bathrooms"] = json_data["numberOfBathroomsTotal"]

        # Floor size
        floor_size = json_data.get("floorSize")
        if floor_size and "sqft" not in data:
            if isinstance(floor_size, dict):
                value = floor_size.get("value")
                unit = floor_size.get("unitCode", "")
                if value:
                    # Convert if needed (FTK = square feet)
                    if unit in ("FTK", "SQF", "sqft", ""):
                        data["sqft"] = int(value)
                    elif unit in ("MTK", "SQM"):  # Square meters
                        data["sqft"] = int(value * 10.764)
            elif isinstance(floor_size, (int, float)):
                data["sqft"] = int(floor_size)

        # Address
        address = json_data.get("address")
        if address and isinstance(address, dict):
            if "streetAddress" in address and "address" not in data:
                parts = [address.get("streetAddress", "")]
                if address.get("addressLocality"):
                    parts.append(address["addressLocality"])
                if address.get("addressRegion"):
                    parts.append(address["addressRegion"])
                if address.get("postalCode"):
                    parts.append(address["postalCode"])
                data["address"] = ", ".join(filter(None, parts))

            if "addressLocality" in address and "city" not in data:
                data["city"] = address["addressLocality"]

            if "addressRegion" in address and "state" not in data:
                region = address["addressRegion"]
                # Normalize province names to abbreviations
                if region.lower() in self.PROVINCE_MAP:
                    region = self.PROVINCE_MAP[region.lower()]
                data["state"] = region

            if "postalCode" in address and "zip_code" not in data:
                data["zip_code"] = address["postalCode"]

            if "addressCountry" in address and "country" not in data:
                data["country"] = address["addressCountry"]

        # Geo coordinates (with swap detection)
        geo = json_data.get("geo")
        if geo and isinstance(geo, dict):
            raw_lat = geo.get("latitude")
            raw_lng = geo.get("longitude")
            if raw_lat is not None and raw_lng is not None:
                lat, lng = self._validate_coordinates(float(raw_lat), float(raw_lng))
                if lat is not None and "latitude" not in data:
                    data["latitude"] = lat
                if lng is not None and "longitude" not in data:
                    data["longitude"] = lng

        # Image URL
        image = json_data.get("image")
        if image and "image_url" not in data:
            if isinstance(image, str):
                data["image_url"] = image
            elif isinstance(image, list) and image:
                data["image_url"] = image[0] if isinstance(image[0], str) else image[0].get("url", "")
            elif isinstance(image, dict):
                data["image_url"] = image.get("url", "")

        # Video URL
        video = json_data.get("video")
        if video and "video_url" not in data:
            if isinstance(video, dict):
                data["video_url"] = video.get("contentUrl") or video.get("url", "")
            elif isinstance(video, str):
                data["video_url"] = video

        # Description
        description = json_data.get("description")
        if description and "description" not in data:
            data["description"] = description[:2000]

        # URL
        url = json_data.get("url")
        if url and "source_url" not in data:
            data["source_url"] = url

    def _extract_product_json_ld(self, json_data: dict[str, Any], data: dict[str, Any]) -> None:
        """Extract product data from JSON-LD (contains MLS ID and price)."""
        # MLS ID from SKU
        sku = json_data.get("sku")
        if sku and "mls_id" not in data:
            data["mls_id"] = sku

        # Price from offers
        offers = json_data.get("offers")
        if offers:
            if isinstance(offers, list):
                offers = offers[0] if offers else {}

            if isinstance(offers, dict):
                price = offers.get("price")
                if price and "price" not in data:
                    try:
                        data["price"] = float(str(price).replace(",", ""))
                    except ValueError:
                        pass

                currency = offers.get("priceCurrency")
                if currency and "currency" not in data:
                    data["currency"] = currency

    def _validate_coordinates(self, lat: float, lng: float) -> tuple[float, float]:
        """Validate and correct potentially swapped lat/lng coordinates.

        Some data sources (like HouseSigma) incorrectly swap latitude and longitude.
        This method detects and corrects such issues.
        """
        # If lat is out of valid range (-90 to 90), values are definitely swapped
        if lat < -90 or lat > 90:
            return lng, lat

        # For North America: latitude should be positive (roughly 20-70),
        # longitude should be negative (roughly -50 to -170)
        # If we see the opposite pattern, they're likely swapped
        if lat < 0 and lng > 0:
            # Negative "lat" with positive "lng" suggests swap
            # (NA latitudes are positive, longitudes are negative)
            if -180 <= lat <= -50 and 20 <= lng <= 70:
                return lng, lat

        return lat, lng

    def _try_parse_generic(self, soup: BeautifulSoup, html_content: str) -> dict[str, Any] | None:
        """Generic parser that tries to extract data from various formats."""
        # Start with JSON-LD structured data (most reliable)
        data = self._parse_json_ld(soup)

        # Extract address - try multiple common patterns (if not from JSON-LD)
        if "address" not in data or not data["address"]:
            data["address"] = self._extract_address(soup, html_content)

        if not data.get("address"):
            # If no address found, this probably isn't a valid listing
            return None

        # Parse location components from address (fills in missing city/state/zip)
        self._parse_location_from_address(data)

        # Extract price (fallback if not from JSON-LD)
        if "price" not in data or not data["price"]:
            data["price"] = self._extract_price(soup, html_content)

        # Extract bedrooms/bathrooms (fallback)
        if "bedrooms" not in data:
            data["bedrooms"] = self._extract_bedrooms(soup, html_content)
        if "bathrooms" not in data:
            data["bathrooms"] = self._extract_bathrooms(soup, html_content)

        # Extract square footage (fallback)
        if "sqft" not in data:
            data["sqft"] = self._extract_sqft(soup, html_content)

        # Extract lot size
        if "lot_size" not in data:
            data["lot_size"] = self._extract_lot_size(soup, html_content)

        # Extract year built
        if "year_built" not in data:
            data["year_built"] = self._extract_year_built(soup, html_content)

        # Extract property type
        if "property_type" not in data:
            data["property_type"] = self._extract_property_type(soup, html_content)

        # Extract description (fallback)
        if "description" not in data:
            data["description"] = self._extract_description(soup)

        # Try to extract coordinates from embedded maps or data attributes (fallback)
        if "latitude" not in data or "longitude" not in data:
            lat, lng = self._extract_coordinates(soup, html_content)
            if lat and lng:
                data["latitude"] = lat
                data["longitude"] = lng

        # Extract source URL if present (fallback)
        if "source_url" not in data:
            data["source_url"] = self._extract_source_url(soup)

        # Extract new fields using regex fallbacks
        if "mls_id" not in data:
            data["mls_id"] = self._extract_mls_id(html_content)

        if "garage_spaces" not in data:
            data["garage_spaces"] = self._extract_garage_spaces(html_content)

        # Extract cost analysis fields
        if "property_tax_rate" not in data:
            data["property_tax_rate"] = self._extract_property_tax_rate(soup, html_content)

        if "hoa_monthly" not in data:
            data["hoa_monthly"] = self._extract_hoa_monthly(soup, html_content)

        if "estimated_repair_pct" not in data:
            data["estimated_repair_pct"] = None  # Default, user can override

        return data

    def _extract_address(self, soup: BeautifulSoup, html_content: str) -> str | None:
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

    def _parse_location_from_address(self, data: dict[str, Any]) -> None:
        """Parse city, state, zip from address string."""
        address = data.get("address", "")

        # Skip if we already have all location data from JSON-LD
        if data.get("city") and data.get("state") and data.get("zip_code"):
            return

        # Try Canadian format: "City, Province A1A 1A1" or "City, BC A1A1A1"
        match = re.search(
            r",\s*([^,]+),\s*([A-Z]{2})\s*([A-Z]\d[A-Z]\s*\d[A-Z]\d)",
            address,
            re.IGNORECASE,
        )
        if match:
            if "city" not in data or not data["city"]:
                data["city"] = match.group(1).strip()
            if "state" not in data or not data["state"]:
                data["state"] = match.group(2).upper()
            if "zip_code" not in data or not data["zip_code"]:
                data["zip_code"] = match.group(3).upper().replace(" ", "")
            if "country" not in data:
                data["country"] = "CA"
            return

        # Try Canadian with full province name
        for province_name, abbrev in self.PROVINCE_MAP.items():
            pattern = rf",\s*([^,]+),\s*{province_name}\s*([A-Z]\d[A-Z]\s*\d[A-Z]\d)"
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                if "city" not in data or not data["city"]:
                    data["city"] = match.group(1).strip()
                if "state" not in data or not data["state"]:
                    data["state"] = abbrev
                if "zip_code" not in data or not data["zip_code"]:
                    data["zip_code"] = match.group(2).upper().replace(" ", "")
                if "country" not in data:
                    data["country"] = "CA"
                return

        # Try US format: "City, ST ZIP" pattern
        match = re.search(r",\s*([^,]+),\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)", address)
        if match:
            if "city" not in data or not data["city"]:
                data["city"] = match.group(1).strip()
            if "state" not in data or not data["state"]:
                data["state"] = match.group(2)
            if "zip_code" not in data or not data["zip_code"]:
                data["zip_code"] = match.group(3)
            if "country" not in data:
                data["country"] = "US"
            return

        # Try "City, ST" pattern (no zip)
        match = re.search(r",\s*([^,]+),\s*([A-Z]{2})\s*$", address)
        if match:
            if "city" not in data or not data["city"]:
                data["city"] = match.group(1).strip()
            if "state" not in data or not data["state"]:
                data["state"] = match.group(2)

    def _extract_price(self, soup: BeautifulSoup, html_content: str) -> float | None:
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

    def _parse_price_text(self, text: str) -> float | None:
        """Parse price from text string."""
        text = text.replace(",", "").replace("$", "").strip()
        match = re.search(r"(\d+(?:\.\d+)?)", text)
        if match:
            return float(match.group(1))
        return None

    def _extract_bedrooms(self, soup: BeautifulSoup, html_content: str) -> int | None:
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

    def _extract_bathrooms(self, soup: BeautifulSoup, html_content: str) -> float | None:
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

    def _extract_sqft(self, soup: BeautifulSoup, html_content: str) -> int | None:
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

    def _extract_lot_size(self, soup: BeautifulSoup, html_content: str) -> float | None:
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

    def _extract_year_built(self, soup: BeautifulSoup, html_content: str) -> int | None:
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

    def _extract_property_type(self, soup: BeautifulSoup, html_content: str) -> str | None:
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

    def _extract_description(self, soup: BeautifulSoup) -> str | None:
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

    def _extract_coordinates(self, soup: BeautifulSoup, html_content: str) -> tuple[float | None, float | None]:
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

    def _extract_source_url(self, soup: BeautifulSoup) -> str | None:
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

    def _extract_mls_id(self, html_content: str) -> str | None:
        """Extract MLS listing ID from HTML."""
        # Common MLS ID patterns
        patterns = [
            r"MLS[#®\s]*[:\s]*([A-Z0-9-]+)",  # MLS# R3065322 or MLS: R3065322
            r'"sku"[:\s]*"([A-Z0-9-]+)"',  # JSON sku field
            r"(?:listing|property)[_\s-]*(?:id|number)[:\s]*([A-Z0-9-]+)",
            r"\b(R\d{7})\b",  # Canadian MLS format: R1234567
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                mls_id = match.group(1).strip()
                if mls_id and len(mls_id) >= 5:  # Sanity check
                    return mls_id

        return None

    def _extract_garage_spaces(self, html_content: str) -> int | None:
        """Extract garage/parking spaces from HTML."""
        patterns = [
            r"(\d+)\s*(?:car\s+)?garage",  # "2 car garage" or "2 garage"
            r"garage[:\s]*(\d+)",  # "garage: 2"
            r"(\d+)\s*parking\s*(?:space|spot)s?",  # "2 parking spaces"
            r"parking[:\s]*(\d+)",  # "parking: 2"
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                count = int(match.group(1))
                if 0 < count < 20:  # Sanity check
                    return count

        return None

    def _extract_property_tax_rate(self, soup: BeautifulSoup, html_content: str) -> float | None:
        """Extract property tax rate from HTML.

        Returns the rate as a decimal (e.g., 0.012 for 1.2%).
        If an annual dollar amount is found with a price, calculates the rate.
        """
        # Try HouseSigma format first: <span class="title">Tax:</span> followed by value
        # Pattern: Tax:</span>...>$3,402 / 2025
        housesigma_pattern = r'class="title"[^>]*>Tax:</span>.*?>\$?([\d,]+)(?:\s*/\s*\d{4})?'
        match = re.search(housesigma_pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                tax_amount = float(match.group(1).replace(",", ""))
                # Sanity check: annual tax should be between $100 and $100,000
                if 100 <= tax_amount <= 100000:
                    return tax_amount
            except ValueError:
                pass

        # Try to find property tax as annual amount
        patterns = [
            r"(?:property\s*)?tax(?:es)?[:\s]*\$?\s*([\d,]+)(?:\s*/\s*(?:year|yr|annual))?",
            r"annual\s*(?:property\s*)?tax(?:es)?[:\s]*\$?\s*([\d,]+)",
            r"\$\s*([\d,]+)\s*/\s*(?:year|yr)\s*(?:property\s*)?tax",
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                try:
                    tax_amount = float(match.group(1).replace(",", ""))
                    # Sanity check: annual tax should be between $500 and $100,000
                    if 500 <= tax_amount <= 100000:
                        # Return as placeholder - will need home price to calculate rate
                        # For now, store raw amount and we'll handle conversion in analysis
                        return tax_amount
                except ValueError:
                    continue

        # Try to find tax rate directly as percentage
        rate_patterns = [
            r"(?:property\s*)?tax\s*rate[:\s]*([\d.]+)\s*%",
            r"([\d.]+)\s*%\s*(?:property\s*)?tax\s*rate",
        ]

        for pattern in rate_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                try:
                    rate = float(match.group(1)) / 100  # Convert percentage to decimal
                    if 0.001 <= rate <= 0.05:  # 0.1% to 5% is reasonable
                        return rate
                except ValueError:
                    continue

        return None

    def _extract_hoa_monthly(self, soup: BeautifulSoup, html_content: str) -> float | None:
        """Extract monthly HOA/condo/maintenance fees from HTML."""
        # Try HouseSigma format first: <span class="title">Maintenance:</span> followed by value
        # Pattern: Maintenance:</span>...>$668/month
        housesigma_pattern = r'class="title"[^>]*>Maintenance:</span>.*?>\$?([\d,]+)(?:/(?:month|mo))?'
        match = re.search(housesigma_pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                amount = float(match.group(1).replace(",", ""))
                # Sanity check: monthly maintenance should be between $50 and $10,000
                if 50 <= amount <= 10000:
                    return amount
            except ValueError:
                pass

        patterns = [
            r"(?:hoa|condo|strata)\s*(?:fees?|dues)?[:\s]*\$?\s*([\d,]+)(?:\s*/\s*(?:month|mo))?",
            r"\$\s*([\d,]+)\s*/\s*(?:month|mo)\s*(?:hoa|condo|strata)",
            r"(?:monthly\s*)?(?:hoa|condo|strata)\s*(?:fees?|dues)[:\s]*\$?\s*([\d,]+)",
            r"maintenance\s*fees?[:\s]*\$?\s*([\d,]+)(?:\s*/\s*(?:month|mo))?",
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1).replace(",", ""))
                    # Sanity check: monthly HOA should be between $50 and $5,000
                    if 50 <= amount <= 5000:
                        return amount
                except ValueError:
                    continue

        return None

    def _geocode_address(self, data: dict[str, Any]) -> None:
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

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean and normalize text."""
        text = re.sub(r"\s+", " ", text)
        return text.strip()
