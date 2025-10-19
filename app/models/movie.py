from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    file_path = Column(String, nullable=False)  # путь в MinIO
    poster_path = Column(String)
    duration = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
