from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from config.db import Base

class Multimedia(Base):
    __tablename__ = "multimedia"

    id_multimedia = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_archivo = Column(String(255), nullable=False, unique=True)
    
    tickets = relationship("MultimediaTickets", back_populates="multimedia")