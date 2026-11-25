from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from config.db import Base

class Hilos(Base):
    __tablename__ = "hilos"

    id_hilo = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_archivo = Column(String(255), nullable=False)
    
    hilo_tickets = relationship("HiloTickets", back_populates="hilos")