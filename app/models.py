from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.database import Base


class Documents(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)

    file_type = Column(String(255), nullable=False)

    file_size = Column(Integer, nullable=False)

    status = Column(String(50), nullable=False)

    created_at = Column(DateTime, nullable=False)