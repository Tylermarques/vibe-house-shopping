"""Database models and utilities for home data storage."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


# Base must be defined at module level so models can inherit from it
Base = declarative_base()


class DatabaseManager:
    """Factory for creating database engines and sessions.

    This class allows configurable database paths, making it easy to:
    - Use different database paths in production vs testing
    - Create isolated database instances for tests
    - Avoid global state issues from module-level initialization

    Usage:
        # Default (uses DATA_DIR/homes.db):
        db = DatabaseManager()

        # Custom path:
        db = DatabaseManager(db_path="/path/to/test.db")

        # In-memory database for tests:
        db = DatabaseManager(db_url="sqlite:///:memory:")

        # Get a session:
        with db.get_session() as session:
            # do work
            session.commit()
    """

    _default_data_dir: Path = Path(__file__).parent.parent / "data"

    def __init__(
        self,
        db_path: Optional[Path] = None,
        db_url: Optional[str] = None,
        echo: bool = False,
    ):
        """Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file. If None, uses default.
            db_url: Full database URL (overrides db_path if provided).
            echo: If True, log all SQL statements.
        """
        if db_url:
            self._db_url = db_url
        elif db_path:
            self._db_url = f"sqlite:///{db_path}"
        else:
            # Default path
            self._default_data_dir.mkdir(exist_ok=True)
            default_path = self._default_data_dir / "homes.db"
            self._db_url = f"sqlite:///{default_path}"

        self._echo = echo
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

    @property
    def engine(self) -> Engine:
        """Get or create the database engine (lazy initialization)."""
        if self._engine is None:
            self._engine = create_engine(self._db_url, echo=self._echo)
        return self._engine

    @property
    def session_factory(self) -> sessionmaker:
        """Get or create the session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine)
        return self._session_factory

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.session_factory()

    def init_db(self) -> None:
        """Initialize the database, creating tables if they don't exist."""
        Base.metadata.create_all(self.engine)

    def dispose(self) -> None:
        """Dispose of the engine and release connections."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None


# Default global instance for backward compatibility
_default_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get the default database manager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = DatabaseManager()
    return _default_manager


def set_db_manager(manager: DatabaseManager) -> None:
    """Set a custom database manager (useful for testing)."""
    global _default_manager
    _default_manager = manager


def reset_db_manager() -> None:
    """Reset the default database manager (useful for testing cleanup)."""
    global _default_manager
    if _default_manager is not None:
        _default_manager.dispose()
    _default_manager = None


class Home(Base):
    """Model representing a home listing."""

    __tablename__ = "homes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(String(500), nullable=False)
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    price = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    sqft = Column(Integer)
    lot_size = Column(Float)
    year_built = Column(Integer)
    property_type = Column(String(50))
    latitude = Column(Float)
    longitude = Column(Float)
    description = Column(Text)
    source_url = Column(String(1000))
    source_file = Column(String(500))
    imported_at = Column(DateTime, default=lambda: datetime.now(UTC))
    raw_html = Column(Text)

    # New fields for enhanced data capture
    mls_id = Column(String(50))  # MLS listing number (e.g., R3065322)
    num_rooms = Column(Integer)  # Total number of rooms
    garage_spaces = Column(Integer)  # Number of garage/parking spaces
    image_url = Column(String(1000))  # Main listing photo URL
    video_url = Column(String(1000))  # Video tour URL
    currency = Column(String(10))  # Currency code (CAD, USD)
    country = Column(String(10))  # Country code (CA, US)

    # Cost analysis fields
    property_tax_rate = Column(Float)  # Annual property tax rate (e.g., 0.012 for 1.2%)
    hoa_monthly = Column(Float)  # Monthly HOA/condo fees
    estimated_repair_pct = Column(Float)  # Monthly repair estimate as % of home value (e.g., 0.0003)

    def to_dict(self) -> dict[str, Any]:
        """Convert home to dictionary for display."""
        return {
            "id": self.id,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "price": self.price,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "sqft": self.sqft,
            "lot_size": self.lot_size,
            "year_built": self.year_built,
            "property_type": self.property_type,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "description": self.description,
            "source_url": self.source_url,
            "source_file": self.source_file,
            "imported_at": self.imported_at.isoformat() if self.imported_at else None,
            # New fields
            "mls_id": self.mls_id,
            "num_rooms": self.num_rooms,
            "garage_spaces": self.garage_spaces,
            "image_url": self.image_url,
            "video_url": self.video_url,
            "currency": self.currency,
            "country": self.country,
            # Cost analysis fields
            "property_tax_rate": self.property_tax_rate,
            "hoa_monthly": self.hoa_monthly,
            "estimated_repair_pct": self.estimated_repair_pct,
        }


def init_db() -> None:
    """Initialize the database, creating tables if they don't exist."""
    get_db_manager().init_db()


def get_session() -> Session:
    """Get a new database session."""
    return get_db_manager().get_session()


def get_all_homes() -> list[dict[str, Any]]:
    """Retrieve all homes from the database."""
    session = get_session()
    try:
        homes = session.query(Home).all()
        return [home.to_dict() for home in homes]
    finally:
        session.close()


def add_home(home_data: dict) -> Home:
    """Add a new home to the database."""
    session = get_session()
    try:
        home = Home(**home_data)
        session.add(home)
        session.commit()
        session.refresh(home)
        return home
    finally:
        session.close()


def home_exists(address: str, source_file: str, mls_id: str | None = None) -> bool:
    """Check if a home already exists using MLS ID (preferred) or address+source_file.

    The MLS ID is always unique and is the most reliable way to detect duplicates.
    Falls back to address + source_file check if MLS ID is not available.
    """
    session = get_session()
    try:
        # First, check by MLS ID if available (most reliable)
        if mls_id:
            existing = session.query(Home).filter(Home.mls_id == mls_id).first()
            if existing is not None:
                return True

        # Also check by address alone (catch duplicates from different files)
        if address:
            existing = session.query(Home).filter(Home.address == address).first()
            if existing is not None:
                return True

        return False
    finally:
        session.close()


def get_home_by_id(home_id: int) -> dict | None:
    """Retrieve a single home by its ID."""
    session = get_session()
    try:
        home = session.query(Home).filter(Home.id == home_id).first()
        return home.to_dict() if home else None
    finally:
        session.close()
