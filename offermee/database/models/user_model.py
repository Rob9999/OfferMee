from sqlalchemy import Column, Integer, String
from offermee.database.database_manager import DatabaseManager
from sqlalchemy.ext.declarative import declarative_base

Base = DatabaseManager.Base


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)  # Klartext-Name (z.B. "John Smith")
    password_hash = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    role = Column(String, nullable=True)  # optionales Feld, z.B. "admin" / "user"
