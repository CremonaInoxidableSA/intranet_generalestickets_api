import importlib

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv

from config import db
from config.sql_loader import cargar_datos_iniciales

from models.clientes import Clientes
from models.comentarios import Comentarios
from models.hilo_tickets import HiloTickets
from models.hilos import Hilos
from models.multimedia_tickets import MultimediaTickets
from models.multimedia import Multimedia
from models.representantes import Representantes
from models.ticket_involucrados import TicketInvolucrados
from models.ticket_resolutores import TicketResolutores
from models.tickets import Tickets

from routers.clientes.lista import router as clientes_lista_router
from routers.clientes.habilitar import router as clientes_habilitar_router
from routers.clientes.deshabilitar import router as clientes_deshabilitar_router
from routers.clientes.crear import router as clientes_crear_router
from routers.clientes.editar import router as clientes_editar_router

from routers.representantes.crear import router as representantes_crear_router
from routers.representantes.editar import router as representantes_editar_router
from routers.representantes.lista import router as representantes_lista_router
from routers.representantes.habilitar import router as representantes_habilitar_router
from routers.representantes.deshabilitar import router as representantes_deshabilitar_router

from routers.tickets.crear import router as tickets_crear_router
from routers.tickets.lista import router as tickets_lista_router
from routers.tickets.imagen import router as tickets_imagen_router
from routers.tickets.detalle import router as tickets_detalle_router
from routers.tickets.editar import router as tickets_editar_router

from routers.comentarios.crear import router as comentarios_crear_router
from routers.comentarios.listaticket import router as comentarios_listaticket_router

from routers.tickets.descargaarchivos import router as tickets_descarga_router
from routers.tickets.eliminararchivos import router as tickets_eliminar_archivos_router
from routers.tickets.agregararchivos import router as tickets_agregar_archivos_router

from routers.hiloscorreos.guardar import router as hiloscorreos_guardar_router
from routers.hiloscorreos.leerhilo import router as hiloscorreos_leerhilo_router
from routers.hiloscorreos.listaticket import router as hiloscorreos_listaticket_router
from routers.hiloscorreos.eliminar import router as hiloscorreos_eliminar_router

load_dotenv()
    
with create_engine(
    f"mysql+pymysql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD', ''))}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}"
).connect() as connection:
    connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {os.getenv('DB_NAME')}"))
    print(f"✓ Base de datos '{os.getenv('DB_NAME')}' verificada o creada exitosamente")

db.Base.metadata.drop_all(bind=db.engine)
db.Base.metadata.create_all(bind=db.engine)
cargar_datos_iniciales()

app = FastAPI(title="API Tickets postventa", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clientes_lista_router)
app.include_router(clientes_habilitar_router)
app.include_router(clientes_deshabilitar_router)
app.include_router(clientes_crear_router)
app.include_router(clientes_editar_router)

app.include_router(representantes_lista_router)
app.include_router(representantes_habilitar_router)
app.include_router(representantes_deshabilitar_router)
app.include_router(representantes_crear_router)
app.include_router(representantes_editar_router)

app.include_router(tickets_crear_router)
app.include_router(tickets_lista_router)
app.include_router(tickets_imagen_router)
app.include_router(tickets_detalle_router)
app.include_router(tickets_editar_router)
app.include_router(tickets_descarga_router)
app.include_router(tickets_eliminar_archivos_router)
app.include_router(tickets_agregar_archivos_router)

app.include_router(hiloscorreos_guardar_router)
app.include_router(hiloscorreos_leerhilo_router)
app.include_router(hiloscorreos_listaticket_router)
app.include_router(hiloscorreos_eliminar_router)

app.include_router(comentarios_crear_router)
app.include_router(comentarios_listaticket_router)