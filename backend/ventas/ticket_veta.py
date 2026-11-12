"""Consulta de tickets: historial y detalle de una nota o cotización (rutas /api/ventas)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_db
from ..modelos import Documento, Usuario
from ..schemas import DocumentoOut, DocumentoResumen
from ..seguridad import exigir

router = APIRouter(prefix="/api/ventas", tags=["Ventas"])


@router.get("/documentos", response_model=list[DocumentoResumen], summary="Historial de notas y cotizaciones")
def historial(db: Session = Depends(get_db), _: Usuario = Depends(exigir())):
    return list(db.scalars(select(Documento).order_by(Documento.id_documento.desc()).limit(200)))


@router.get("/documentos/{id_documento}", response_model=DocumentoOut, summary="Ticket completo")
def ticket(id_documento: int, db: Session = Depends(get_db), _: Usuario = Depends(exigir())):
    d = db.get(Documento, id_documento)
    if not d:
        raise HTTPException(404, "Documento no encontrado")
    return d
