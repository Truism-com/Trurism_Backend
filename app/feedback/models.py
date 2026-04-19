from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.core.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=True)

    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)

    subject = Column(String, nullable=True)
    message = Column(String, nullable=False)

    rating = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)