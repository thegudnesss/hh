"""
Database configuration for payment system
SQLAlchemy setup for PayTechUZ integration
"""

from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from paytechuz.integrations.fastapi import Base as PaymentsBase
from paytechuz.integrations.fastapi.models import run_migrations

# Database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./payments.db"

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite uchun kerak
)

# Create base
Base = declarative_base()

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Order(Base):
    """
    Order modeli - MongoDB'dagi Order bilan sinxronlashish uchun
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, unique=True, index=True)
    user_id = Column(Integer, index=True)
    products = Column(JSON)  # [{"product_id": 1, "count": 2}, ...]
    total_amount = Column(Float)
    status = Column(String, default="pending")  # pending, paid, cancelled
    payment_method = Column(String)  # click, payme
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    """
    Database'ni initialize qilish
    PayTechUZ payment tables va Order table yaratish
    """
    # PayTechUZ payment tables yaratish
    run_migrations(engine)

    # Order table yaratish
    Base.metadata.create_all(bind=engine)

    print("✅ Database initialized successfully!")


def get_db():
    """
    Database session dependency
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
