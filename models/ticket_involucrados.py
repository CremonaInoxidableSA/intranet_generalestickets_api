from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from config.db import Base

class TicketInvolucrados(Base):
    __tablename__ = "ticket_involucrados"

    id_ticket_involucrado = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_ticket = Column(Integer, ForeignKey("tickets.id_ticket"), nullable=False)
    id_usuario_interviniente = Column(String(255), nullable=False)
    nombre_usuario_interviniente = Column(String(255), nullable=False)
    apellido_usuario_interviniente = Column(String(255), nullable=False)
    correo = Column(String(255), nullable=False)
    
    tickets = relationship("Tickets", back_populates="ticket_involucrados")