"""Lógica de negocio de usuarios, permisos y copias de seguridad."""
import bcrypt
from pymysql.converters import escape_item
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ..config import RAIZ, Base, ErrorServicio, ahora
from ..modelos import CopiaSeguridad, Permiso, Rol, Usuario
from ..schemas import UsuarioIn


class UsuarioService:
    @staticmethod
    def autenticar(db: Session, usuario: str, contrasena: str) -> Usuario:
        u = db.scalar(select(Usuario).where(Usuario.usuario == usuario.strip(), Usuario.activo.is_(True)))
        if not u or not bcrypt.checkpw(contrasena.encode(), u.contrasena_hash.encode()):
            raise ErrorServicio("Usuario o contraseña incorrectos", 401)
        return u

    @staticmethod
    def listar(db: Session) -> list[Usuario]:
        return list(db.scalars(select(Usuario).where(Usuario.activo.is_(True)).order_by(Usuario.id_usuario)))

    @staticmethod
    def crear(db: Session, datos: UsuarioIn) -> Usuario:
        rol = db.scalar(select(Rol).where(Rol.nombre == datos.rol))
        if not rol:
            raise ErrorServicio("El rol no existe")
        if db.scalar(select(Usuario).where(Usuario.usuario == datos.usuario.strip())):
            raise ErrorServicio("Ese nombre de usuario ya existe", 409)
        u = Usuario(id_rol=rol.id_rol, nombre=datos.nombre.strip(), usuario=datos.usuario.strip(),
                    contrasena_hash=bcrypt.hashpw(datos.contrasena.encode(), bcrypt.gensalt()).decode())
        db.add(u)
        db.commit()
        return u

    @staticmethod
    def actualizar_permisos(db: Session, id_usuario: int, permisos: list[str]) -> None:
        u = db.get(Usuario, id_usuario)
        if not u:
            raise ErrorServicio("Usuario no encontrado", 404)
        u.permisos_obj = list(db.scalars(select(Permiso).where(Permiso.nombre.in_(permisos))))
        db.commit()

    @staticmethod
    def crear_respaldo(db: Session, usuario: Usuario) -> str:
        """Respaldo lógico: un archivo .sql con los INSERT de todas las tablas, en la carpeta /backups."""
        carpeta = RAIZ / "backups"
        carpeta.mkdir(exist_ok=True)
        archivo = f"respaldo_{ahora():%Y%m%d_%H%M%S}.sql"
        with open(carpeta / archivo, "w", encoding="utf-8") as f:
            f.write(f"-- Respaldo Triates POS {ahora().isoformat()}\nSET FOREIGN_KEY_CHECKS=0;\n")
            for tabla in Base.metadata.sorted_tables:
                for fila in db.execute(text(f"SELECT * FROM `{tabla.name}`")).mappings():
                    cols = ",".join(f"`{c}`" for c in fila.keys())
                    vals = ",".join(escape_item(v, "utf8mb4") for v in fila.values())
                    f.write(f"INSERT INTO `{tabla.name}` ({cols}) VALUES ({vals});\n")
            f.write("SET FOREIGN_KEY_CHECKS=1;\n")
        db.add(CopiaSeguridad(id_usuario=usuario.id_usuario, archivo=archivo))
        db.commit()
        return archivo

    @staticmethod
    def listar_respaldos(db: Session) -> list[CopiaSeguridad]:
        return list(db.scalars(select(CopiaSeguridad).order_by(CopiaSeguridad.id_copia.desc()).limit(100)))
