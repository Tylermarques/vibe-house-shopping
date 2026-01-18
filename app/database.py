"""Database models and utilities for home data storage."""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DATABASE_PATH = DATA_DIR / "homes.db"

engine = create_engine(f"sqlite:///{DATABASE_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


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
    imported_at = Column(DateTime, default=datetime.utcnow)
    raw_html = Column(Text)

    def to_dict(self):
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
        }


def init_db():
    """Initialize the database, creating tables if they don't exist."""
    Base.metadata.create_all(engine)


def get_session():
    """Get a new database session."""
    return SessionLocal()


def get_all_homes():
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


def home_exists(address: str, source_file: str) -> bool:
    """Check if a home with the given address and source file already exists."""
    session = get_session()
    try:
        existing = (
            session.query(Home)
            .filter(Home.address == address, Home.source_file == source_file)
            .first()
        )
        return existing is not None
    finally:
        session.close()
