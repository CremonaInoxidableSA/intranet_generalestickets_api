from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from config.db import Base

class TicketResolutores(Base):
    __tablename__ = "ticket_resolutores"

    id_ticket_resolutor = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_ticket = Column(Integer, ForeignKey("tickets.id_ticket"), nullable=False)
    id_usuario_resolutor = Column(String(255), nullable=False)
    nombre_usuario_resolutor = Column(String(255), nullable=False)
    apellido_usuario_resolutor = Column(String(255), nullable=False)
    
    tickets = relationship("Tickets", back_populates="ticket_resolutores")