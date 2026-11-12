"""Sesión y permisos. Uso en una ruta:  u: Usuario = Depends(exigir("Inventario"))"""
from typing import Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_db
from .modelos import Usuario


def usuario_actual(request: Request, db: Session) -> Optional[Usuario]:
    uid = request.session.get("id_usuario")
    if not uid:
        return None
    return db.scalar(select(Usuario).where(Usuario.id_usuario == uid, Usuario.activo.is_(True)))


def exigir(requisito: Optional[str] = None):
    """exigir() -> cualquier usuario con sesión · exigir("owner") -> solo Propietario ·
    exigir("Inventario") -> Propietario o usuario con ese permiso."""
    def dependencia(request: Request, db: Session = Depends(get_db)) -> Usuario:
        u = usuario_actual(request, db)
        if not u:
            raise HTTPException(401, "Sesión no válida")
        dueno = u.rol == "Propietario"
        if not (dueno or requisito is None or (requisito != "owner" and requisito in u.permisos)):
            raise HTTPException(403, "No tienes permiso para esta acción")
        return u
    return dependencia
