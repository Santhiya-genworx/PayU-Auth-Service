from sqlalchemy import Column, Enum, ForeignKey, Integer, Numeric, String, DateTime, func
from sqlalchemy.orm import relationship
from src.data.clients.database import Base
from enum import Enum as PyEnum

class Methods(PyEnum): 
    post = "POST"
    put = "PUT"
    delete = "DELETE"

class Logs(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    method = Column(Enum(Methods))
    url = Column(String(255), nullable=False)
    status_code = Column(Integer, nullable=False)
    time_taken = Column(Numeric, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="logs")