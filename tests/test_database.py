"""Tests for the database models."""

from datetime import datetime

import pytest

# Skip all tests in this module if sqlalchemy is not installed
sqlalchemy = pytest.importorskip("sqlalchemy")


class TestHomeModel:
    """Tests for the Home database model."""

    def test_home_model_has_new_columns(self):
        """Test that Home model has all new columns defined."""
        from app.database import Home

        # Check that new columns exist on the model
        assert hasattr(Home, "mls_id")
        assert hasattr(Home, "num_rooms")
        assert hasattr(Home, "garage_spaces")
        assert hasattr(Home, "image_url")
        assert hasattr(Home, "video_url")
        assert hasattr(Home, "currency")
        assert hasattr(Home, "country")

    def test_home_model_has_original_columns(self):
        """Test that Home model still has all original columns."""
        from app.database import Home

        # Check original columns
        assert hasattr(Home, "id")
        assert hasattr(Home, "address")
        assert hasattr(Home, "city")
        assert hasattr(Home, "state")
        assert hasattr(Home, "zip_code")
        assert hasattr(Home, "price")
        assert hasattr(Home, "bedrooms")
        assert hasattr(Home, "bathrooms")
        assert hasattr(Home, "sqft")
        assert hasattr(Home, "lot_size")
        assert hasattr(Home, "year_built")
        assert hasattr(Home, "property_type")
        assert hasattr(Home, "latitude")
        assert hasattr(Home, "longitude")
        assert hasattr(Home, "description")
        assert hasattr(Home, "source_url")
        assert hasattr(Home, "source_file")
        assert hasattr(Home, "imported_at")
        assert hasattr(Home, "raw_html")

    def test_to_dict_includes_new_fields(self):
        """Test that to_dict() includes all new fields."""
        from app.database import Home

        home = Home(
            address="123 Test St",
            city="Vancouver",
            state="BC",
            zip_code="V6B1A1",
            price=999900.0,
            bedrooms=3,
            bathrooms=2.0,
            sqft=1495,
            latitude=49.2827,
            longitude=-123.1207,
            mls_id="R3065322",
            num_rooms=8,
            garage_spaces=2,
            image_url="https://example.com/image.jpg",
            video_url="https://youtube.com/watch?v=test",
            currency="CAD",
            country="CA",
        )

        result = home.to_dict()

        # Verify new fields are in the dictionary
        assert "mls_id" in result
        assert result["mls_id"] == "R3065322"

        assert "num_rooms" in result
        assert result["num_rooms"] == 8

        assert "garage_spaces" in result
        assert result["garage_spaces"] == 2

        assert "image_url" in result
        assert result["image_url"] == "https://example.com/image.jpg"

        assert "video_url" in result
        assert result["video_url"] == "https://youtube.com/watch?v=test"

        assert "currency" in result
        assert result["currency"] == "CAD"

        assert "country" in result
        assert result["country"] == "CA"

    def test_to_dict_handles_none_values(self):
        """Test that to_dict() handles None values for new fields."""
        from app.database import Home

        home = Home(
            address="123 Test St",
            # All new fields left as None
        )

        result = home.to_dict()

        # New fields should be present but None
        assert "mls_id" in result
        assert result["mls_id"] is None

        assert "num_rooms" in result
        assert result["num_rooms"] is None

        assert "garage_spaces" in result
        assert result["garage_spaces"] is None

        assert "image_url" in result
        assert result["image_url"] is None

        assert "video_url" in result
        assert result["video_url"] is None

        assert "currency" in result
        assert result["currency"] is None

        assert "country" in result
        assert result["country"] is None

    def test_to_dict_includes_original_fields(self):
        """Test that to_dict() still includes all original fields."""
        from app.database import Home

        home = Home(
            address="123 Test St",
            city="Vancouver",
            state="BC",
            zip_code="V6B1A1",
            price=999900.0,
            bedrooms=3,
            bathrooms=2.0,
            sqft=1495,
            lot_size=0.25,
            year_built=2020,
            property_type="Townhouse",
            latitude=49.2827,
            longitude=-123.1207,
            description="A beautiful home",
            source_url="https://example.com/listing",
            source_file="test.html",
        )

        result = home.to_dict()

        # Verify original fields
        assert result["address"] == "123 Test St"
        assert result["city"] == "Vancouver"
        assert result["state"] == "BC"
        assert result["zip_code"] == "V6B1A1"
        assert result["price"] == 999900.0
        assert result["bedrooms"] == 3
        assert result["bathrooms"] == 2.0
        assert result["sqft"] == 1495
        assert result["lot_size"] == 0.25
        assert result["year_built"] == 2020
        assert result["property_type"] == "Townhouse"
        assert result["latitude"] == 49.2827
        assert result["longitude"] == -123.1207
        assert result["description"] == "A beautiful home"
        assert result["source_url"] == "https://example.com/listing"
        assert result["source_file"] == "test.html"


class TestDatabaseOperations:
    """Tests for database operations with new fields."""

    def test_create_home_with_new_fields(self, tmp_path):
        """Test creating a Home record with all new fields."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.database import Base, Home

        # Create temporary database
        db_path = tmp_path / "test.db"
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Create home with all fields
            home = Home(
                address="38226 Eaglewind Boulevard",
                city="Squamish",
                state="BC",
                zip_code="V8B0T2",
                country="CA",
                price=999900.0,
                currency="CAD",
                bedrooms=3,
                bathrooms=2.0,
                sqft=1495,
                num_rooms=8,
                garage_spaces=2,
                property_type="Townhouse",
                latitude=49.7030265,
                longitude=-123.154841617,
                mls_id="R3065322",
                image_url="https://example.com/image.jpg",
                video_url="https://youtube.com/watch?v=test",
                source_file="example_listing_1.html",
            )

            session.add(home)
            session.commit()

            # Query and verify
            result = session.query(Home).first()

            assert result.address == "38226 Eaglewind Boulevard"
            assert result.mls_id == "R3065322"
            assert result.num_rooms == 8
            assert result.garage_spaces == 2
            assert result.currency == "CAD"
            assert result.country == "CA"
            assert result.image_url == "https://example.com/image.jpg"
            assert result.video_url == "https://youtube.com/watch?v=test"

        finally:
            session.close()

    def test_query_homes_by_new_fields(self, tmp_path):
        """Test querying homes by new fields."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.database import Base, Home

        # Create temporary database
        db_path = tmp_path / "test.db"
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Create multiple homes
            home1 = Home(
                address="Home 1",
                garage_spaces=2,
                country="CA",
            )
            home2 = Home(
                address="Home 2",
                garage_spaces=1,
                country="US",
            )
            home3 = Home(
                address="Home 3",
                garage_spaces=3,
                country="CA",
            )

            session.add_all([home1, home2, home3])
            session.commit()

            # Query by garage spaces
            homes_with_2_plus_garage = (
                session.query(Home).filter(Home.garage_spaces >= 2).all()
            )
            assert len(homes_with_2_plus_garage) == 2

            # Query by country
            canadian_homes = session.query(Home).filter(Home.country == "CA").all()
            assert len(canadian_homes) == 2

        finally:
            session.close()

    def test_nullable_new_fields(self, tmp_path):
        """Test that new fields are nullable (can be None)."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.database import Base, Home

        # Create temporary database
        db_path = tmp_path / "test.db"
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Create home with only required field
            home = Home(address="Minimal Home")
            session.add(home)
            session.commit()

            # Query and verify nulls are allowed
            result = session.query(Home).first()

            assert result.address == "Minimal Home"
            assert result.mls_id is None
            assert result.num_rooms is None
            assert result.garage_spaces is None
            assert result.image_url is None
            assert result.video_url is None
            assert result.currency is None
            assert result.country is None

        finally:
            session.close()


class TestDuplicateDetection:
    """Tests for duplicate detection in home_exists function."""

    def _setup_test_db(self, tmp_path, monkeypatch):
        """Helper to setup a fresh test database."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app import database
        from app.database import Base

        db_path = tmp_path / "test.db"
        test_engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(test_engine)

        TestSession = sessionmaker(bind=test_engine)
        monkeypatch.setattr(database, "get_session", TestSession)

        return TestSession, database

    def test_duplicate_detected_by_mls_id(self, tmp_path, monkeypatch):
        """Test that duplicates are detected by MLS ID."""
        from app.database import Home

        TestSession, database = self._setup_test_db(tmp_path, monkeypatch)

        # Add a home with MLS ID
        session = TestSession()
        try:
            home = Home(
                address="123 Main St",
                mls_id="R3065322",
                source_file="original.html",
            )
            session.add(home)
            session.commit()
        finally:
            session.close()

        # Test: Same MLS ID should be detected as duplicate, even with different address/file
        assert database.home_exists("999 Different St", "different.html", "R3065322") is True

    def test_duplicate_detected_by_address(self, tmp_path, monkeypatch):
        """Test that duplicates are detected by address alone."""
        from app.database import Home

        TestSession, database = self._setup_test_db(tmp_path, monkeypatch)

        # Add a home with just address (no MLS ID)
        session = TestSession()
        try:
            home = Home(
                address="123 Main St, City, ST 12345",
                source_file="original.html",
            )
            session.add(home)
            session.commit()
        finally:
            session.close()

        # Test: Same address should be detected as duplicate, even from different file
        assert database.home_exists("123 Main St, City, ST 12345", "another.html") is True

    def test_no_duplicate_for_new_home(self, tmp_path, monkeypatch):
        """Test that a genuinely new home is not flagged as duplicate."""
        from app.database import Home

        TestSession, database = self._setup_test_db(tmp_path, monkeypatch)

        # Add an existing home
        session = TestSession()
        try:
            home = Home(
                address="123 Main St",
                mls_id="R1111111",
                source_file="original.html",
            )
            session.add(home)
            session.commit()
        finally:
            session.close()

        # Test: Different address and different MLS ID should not be a duplicate
        assert database.home_exists("456 Oak Ave", "new.html", "R2222222") is False

    def test_mls_id_takes_priority_over_address(self, tmp_path, monkeypatch):
        """Test that MLS ID check runs first and catches duplicates."""
        from app.database import Home

        TestSession, database = self._setup_test_db(tmp_path, monkeypatch)

        # Add a home
        session = TestSession()
        try:
            home = Home(
                address="123 Main St",
                mls_id="R3065322",
                source_file="original.html",
            )
            session.add(home)
            session.commit()
        finally:
            session.close()

        # Test: Even if address is completely different, MLS ID match = duplicate
        assert database.home_exists("Completely Different Address", "new.html", "R3065322") is True

    def test_duplicate_from_different_source_file(self, tmp_path, monkeypatch):
        """Test that a listing re-imported from a different file is detected as duplicate."""
        from app.database import Home

        TestSession, database = self._setup_test_db(tmp_path, monkeypatch)

        # Add a home from file1.html
        session = TestSession()
        try:
            home = Home(
                address="38226 Eaglewind Boulevard, Squamish, BC V8B0T2",
                mls_id="R3065322",
                source_file="listing_v1.html",
            )
            session.add(home)
            session.commit()
        finally:
            session.close()

        # Test: Same listing saved as a different file should be detected
        # This is the key bug fix - before, it would allow this as a new entry
        assert database.home_exists(
            "38226 Eaglewind Boulevard, Squamish, BC V8B0T2",
            "listing_v2.html",  # Different source file
            "R3065322",  # Same MLS ID
        ) is True

    def test_empty_mls_id_falls_back_to_address(self, tmp_path, monkeypatch):
        """Test that when MLS ID is None, address check still works."""
        from app.database import Home

        TestSession, database = self._setup_test_db(tmp_path, monkeypatch)

        # Add a home without MLS ID
        session = TestSession()
        try:
            home = Home(
                address="123 Main St",
                source_file="original.html",
            )
            session.add(home)
            session.commit()
        finally:
            session.close()

        # Test: Same address without MLS ID should be caught by address check
        assert database.home_exists("123 Main St", "different.html", None) is True