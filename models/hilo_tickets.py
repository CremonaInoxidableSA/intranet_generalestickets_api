from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from config.db import Base

class HiloTickets(Base):
    __tablename__ = "hilo_tickets"

    id_ticket = Column(Integer, ForeignKey("tickets.id_ticket"), primary_key=True, nullable=False)
    id_hilo = Column(Integer, ForeignKey("hilos.id_hilo"), primary_key=True, nullable=False)
    
    tickets = relationship("Tickets", back_populates="hilo_tickets")
    hilos = relationship("Hilos", back_populates="hilo_tickets")