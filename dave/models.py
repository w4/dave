from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
Base = declarative_base()


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    nick = Column(String)
    location = Column(String)


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(UUID, server_default="uuid_generate_v4()", primary_key=True)
    quote = Column(String)
    attributed = Column(String)
    added_by = Column(String)
    created = Column(DateTime, default=func.now())