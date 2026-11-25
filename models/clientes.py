from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from config.db import Base

class Clientes(Base):
    __tablename__ = "clientes"

    id_cliente = Column(Integer, primary_key=True, index=True, autoincrement=True)  
    nombre = Column(String(255), nullable=False, unique=True)
    pais = Column(String(255), nullable=False)
    estado = Column(Boolean, nullable=False, default=True)

    tickets = relationship("Tickets", back_populates="clientes")
    representantes = relationship("Representantes", back_populates="clientes")