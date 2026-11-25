from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from config.db import Base

class Tickets(Base):
    __tablename__ = "tickets"

    id_ticket = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_usuario_creador = Column(String(255), nullable=False)
    nombre_usuario_creador = Column(String(255), nullable=False)
    apellido_usuario_creador = Column(String(255), nullable=False)
    fecha_creacion = Column(DateTime, nullable=False)
    id_cliente = Column(Integer, ForeignKey("clientes.id_cliente"), nullable=False)
    id_representante = Column(Integer, ForeignKey("representantes.id_representante"), nullable=False)
    nombre_proyecto = Column(String(255), nullable=False)
    descripcion = Column(String(255), nullable=False)
    fecha_ocurrencia = Column(DateTime, nullable=False)
    estado = Column(String(255), nullable=False)
    resolucion = Column(String(255), nullable=True)
    fecha_resolucion = Column(DateTime, nullable=True)
    tiempo_empleado = Column(Integer, nullable=True)

    comentarios = relationship("Comentarios", back_populates="tickets")
    clientes = relationship("Clientes", back_populates="tickets")
    multimedia_tickets = relationship("MultimediaTickets", back_populates="tickets")
    ticket_involucrados = relationship("TicketInvolucrados", back_populates="tickets")
    ticket_resolutores = relationship("TicketResolutores", back_populates="tickets")
    hilo_tickets = relationship("HiloTickets", back_populates="tickets")