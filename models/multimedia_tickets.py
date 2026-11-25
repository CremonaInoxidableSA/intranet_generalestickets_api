from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from config.db import Base

class MultimediaTickets(Base):
    __tablename__ = "multimedia_tickets"

    id_ticket = Column(Integer, ForeignKey("tickets.id_ticket"), primary_key=True, nullable=False)
    id_multimedia = Column(Integer, ForeignKey("multimedia.id_multimedia"), primary_key=True, nullable=False)
    tipo = Column(String(255), nullable=False)
    
    tickets = relationship("Tickets", back_populates="multimedia_tickets")
    multimedia = relationship("Multimedia", back_populates="tickets")