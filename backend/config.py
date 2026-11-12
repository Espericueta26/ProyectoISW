"""Configuración común: conexión a MySQL (SQLAlchemy), zona horaria y sesión."""
import os
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

RAIZ = Path(__file__).resolve().parent.parent
ZONA = ZoneInfo(os.getenv("APP_TZ", "America/Monterrey"))
SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esta-clave-antes-de-produccion")


def ahora() -> datetime:
    return datetime.now(ZONA)


def hoy() -> date:
    return ahora().date()


DATABASE_URL = os.getenv("DATABASE_URL") or "mysql+pymysql://{u}:{p}@{h}:{port}/{db}?charset=utf8mb4".format(
    u=os.getenv("DB_USER", "root"), p=quote_plus(os.getenv("DB_PASS", "")), h=os.getenv("DB_HOST", "127.0.0.1"),
    port=os.getenv("DB_PORT", "3306"), db=os.getenv("DB_NAME", "triates_pos"))

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


@event.listens_for(engine, "connect")
def _alinear_zona_horaria(conexion, _registro):
    """Hace que NOW() de MySQL y la fecha de Python usen la misma zona horaria."""
    z = ahora().strftime("%z")
    cur = conexion.cursor()
    cur.execute(f"SET time_zone = '{z[:3]}:{z[3:]}'")
    cur.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependencia de FastAPI: una sesión de base de datos por petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ErrorServicio(Exception):
    """Error de negocio que se responde al frontend como {"error": mensaje}."""

    def __init__(self, mensaje: str, codigo: int = 400):
        super().__init__(mensaje)
        self.mensaje, self.codigo = mensaje, codigo
