"""
SQLAlchemy models for HDB data.
"""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class ResalePrice(Base):
    """
    Model for HDB resale flat price data.
    """
    __tablename__ = 'resale_prices'

    id = Column(Integer, primary_key=True)
    month = Column(Date, index=True, nullable=False)
    town = Column(String(50), index=True, nullable=False)
    flat_type = Column(String(20), index=True, nullable=False)
    block = Column(String(10))
    street_name = Column(String(100))
    storey_range = Column(String(10))
    floor_area_sqm = Column(Float, nullable=False)
    flat_model = Column(String(50))
    lease_commence_date = Column(Integer)
    resale_price = Column(Float, nullable=False)
    remaining_lease_years = Column(Float)

    def __repr__(self):
        return f"<ResalePrice(id={self.id}, town='{self.town}', month='{self.month}', price={self.resale_price})>"
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a ResalePrice model instance from a dictionary.
        """
        return cls(
            month=data.get('month'),
            town=data.get('town'),
            flat_type=data.get('flat_type'),
            block=data.get('block'),
            street_name=data.get('street_name'),
            storey_range=data.get('storey_range'),
            floor_area_sqm=data.get('floor_area_sqm'),
            flat_model=data.get('flat_model'),
            lease_commence_date=data.get('lease_commence_date'),
            resale_price=data.get('resale_price'),
            remaining_lease_years=data.get('remaining_lease_years')
        )


class CompletionStatus(Base):
    """
    Model for HDB completion status data.
    """
    __tablename__ = 'completion_status'

    id = Column(Integer, primary_key=True)
    financial_year = Column(Integer, index=True, nullable=False)
    town_or_estate = Column(String(50), index=True, nullable=False)
    status = Column(String(50), nullable=False)
    no_of_units = Column(Integer)

    def __repr__(self):
        return f"<CompletionStatus(id={self.id}, town='{self.town_or_estate}', year={self.financial_year})>"
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a CompletionStatus model instance from a dictionary.
        """
        return cls(
            financial_year=data.get('financial_year'),
            town_or_estate=data.get('town_or_estate'),
            status=data.get('status'),
            no_of_units=data.get('no_of_units')
        ) 