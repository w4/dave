from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
Base = declarative_base()


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    nick = Column(String)
    location = Column(String)

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    nick = Column(String)
    channel = Column(String)
    message = Column(String)
    userhost = Column(String)
    created_at = Column(DateTime)
