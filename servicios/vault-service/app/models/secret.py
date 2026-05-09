from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Secret(Base):
    __tablename__ = "secrets"
    id = Column(Integer, primary_key=True, index=True)
    site = Column(String)
    encrypted_password = Column(String)
    category = Column(String, default="other")
    description = Column(Text, default="")
    owner = Column(String, index=True)
