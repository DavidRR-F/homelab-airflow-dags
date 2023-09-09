from sqlalchemy import (
    Column,
    Date,
    ForeignKeyConstraint,
    Integer,
    String,
    Float,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from airflow.models.connection import Connection
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

connection = Connection.get_connection_from_secrets("postgres")
conn_str = f"postgresql://{connection.login}:{connection.password}@{connection.host}/{connection.schema}"
engine = create_engine(conn_str, pool_pre_ping=True)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class HouseListing(Base):
    __tablename__ = "house_listings"

    address = Column(String, primary_key=True)
    city = Column(String, primary_key=True)
    state = Column(String, primary_key=True)
    zip = Column(Integer, primary_key=True)
    beds = Column(Integer)
    baths = Column(Float)
    sqft = Column(Integer)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)

    price_listings = relationship("PriceListing", back_populates="house_listing")


class PriceListing(Base):
    __tablename__ = "price_listings"

    transaction_id = Column(Integer, primary_key=True)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    zip = Column(Integer)
    price = Column(Integer)
    date = Column(Date)

    house_listing = relationship("HouseListing", back_populates="price_listings")

    __table_args__ = (
        UniqueConstraint("address", "city", "state", "zip", "date"),
        ForeignKeyConstraint(
            ["address", "city", "state", "zip"],
            [
                "house_listings.address",
                "house_listings.city",
                "house_listings.state",
                "house_listings.zip",
            ],
        ),
    )
