from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from config.db import Base

class Representantes(Base):
    __tablename__ = "representantes"

    id_representante = Column(Integer, primary_key=True, index=True, autoincrement=True)  
    id_cliente = Column(Integer, ForeignKey("clientes.id_cliente"), nullable=False)
    nombre = Column(String(255), nullable=False)
    apellido = Column(String(255), nullable=False)
    correo = Column(String(255), nullable=True)
    telefono = Column(String(255), nullable=True)
    area = Column(String(255), nullable=True)
    estado = Column(Boolean, nullable=False, default=True)

    clientes = relationship("Clientes", back_populates="representantes")