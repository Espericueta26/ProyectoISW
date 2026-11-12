"""Controlador de usuarios (rutas /api/usuarios). Delega la lógica en UsuarioService."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..config import get_db
from ..modelos import Usuario
from ..schemas import CopiaOut, LoginIn, PermisosIn, UsuarioIn, UsuarioOut
from ..seguridad import exigir
from .usuarioService import UsuarioService

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios"])


@router.post("/login", response_model=UsuarioOut, summary="Iniciar sesión")
def login(datos: LoginIn, request: Request, db: Session = Depends(get_db)):
    u = UsuarioService.autenticar(db, datos.usuario, datos.contrasena)
    request.session.clear()
    request.session["id_usuario"] = u.id_usuario
    return u


@router.post("/logout", summary="Cerrar sesión")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/me", response_model=UsuarioOut, summary="Usuario con sesión activa")
def me(u: Usuario = Depends(exigir())):
    return u


@router.get("/respaldos", response_model=list[CopiaOut], summary="Historial de copias de seguridad")
def respaldos(db: Session = Depends(get_db), _: Usuario = Depends(exigir("owner"))):
    return UsuarioService.listar_respaldos(db)


@router.post("/respaldos", summary="Crear una copia de seguridad")
def crear_respaldo(db: Session = Depends(get_db), u: Usuario = Depends(exigir("owner"))):
    return {"archivo": UsuarioService.crear_respaldo(db, u)}


@router.get("", response_model=list[UsuarioOut], summary="Listar usuarios")
def listar(db: Session = Depends(get_db), _: Usuario = Depends(exigir("owner"))):
    return UsuarioService.listar(db)


@router.post("", summary="Registrar usuario")
def crear(datos: UsuarioIn, db: Session = Depends(get_db), _: Usuario = Depends(exigir("owner"))):
    return {"id": UsuarioService.crear(db, datos).id_usuario}


@router.put("/{id_usuario}/permisos", summary="Actualizar permisos adicionales")
def permisos(id_usuario: int, datos: PermisosIn, db: Session = Depends(get_db), _: Usuario = Depends(exigir("owner"))):
    UsuarioService.actualizar_permisos(db, id_usuario, datos.permisos)
    return {"ok": True}
