"""Reporte de ventas, egresos y corte de caja (rutas /api/reportes)."""
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from ..config import get_db, hoy
from ..modelos import CorteCaja, DetalleDocumento, Documento, Egreso, Producto, Usuario
from ..schemas import CorteOut, DocumentoResumen, EgresoIn, EgresoOut
from ..seguridad import exigir

router = APIRouter(prefix="/api/reportes", tags=["Reportes"])


def resumen_ventas(db: Session, desde: date, hasta: date) -> dict:
    nota = Documento.tipo == "Nota de remisión"
    periodo = (func.date(Documento.fecha) >= desde, func.date(Documento.fecha) <= hasta)
    por = db.execute(select(Documento.metodo_pago, func.sum(Documento.total), func.count())
                     .where(nota, *periodo).group_by(Documento.metodo_pago)).all()
    por_metodo = [{"m": m, "t": float(t), "n": n} for m, t, n in por]
    egresos = db.scalar(select(func.coalesce(func.sum(Egreso.monto), 0)).where(
        func.date(Egreso.fecha) >= desde, func.date(Egreso.fecha) <= hasta))
    ventas = round(sum(x["t"] for x in por_metodo), 2)
    notas = db.scalars(select(Documento).where(nota, *periodo).order_by(desc(Documento.id_documento)))
    importe = func.sum(DetalleDocumento.subtotal)
    cantidad = func.sum(DetalleDocumento.cantidad)
    top = db.execute(select(Producto.nombre, cantidad, importe)
                     .join(DetalleDocumento, DetalleDocumento.id_producto == Producto.id_producto)
                     .join(Documento, Documento.id_documento == DetalleDocumento.id_documento)
                     .where(nota, *periodo).group_by(Producto.id_producto, Producto.nombre)
                     .order_by(desc(cantidad)).limit(5)).all()
    return {
        "desde": desde.isoformat(), "hasta": hasta.isoformat(), "por_metodo": por_metodo,
        "total_ventas": ventas, "total_egresos": float(egresos), "saldo": round(ventas - float(egresos), 2),
        "notas": [DocumentoResumen.model_validate(d).model_dump() for d in notas],
        "top_productos": [{"nombre": n, "cantidad": int(c), "importe": float(i)} for n, c, i in top],
    }


@router.get("/ventas", summary="Ventas, egresos y saldo de un periodo (por defecto, hoy)")
def ventas(desde: Optional[date] = None, hasta: Optional[date] = None, db: Session = Depends(get_db),
           _: Usuario = Depends(exigir("Reportes"))):
    desde, hasta = desde or hoy(), hasta or hoy()
    if desde > hasta:
        raise HTTPException(400, "La fecha inicial no puede ser mayor a la final")
    return resumen_ventas(db, desde, hasta)


@router.post("/corte", summary="Guardar el corte de caja del día de hoy")
def guardar_corte(db: Session = Depends(get_db), u: Usuario = Depends(exigir("Reportes"))):
    r = resumen_ventas(db, hoy(), hoy())
    db.add(CorteCaja(id_usuario=u.id_usuario, total_ventas=Decimal(str(r["total_ventas"])),
                     total_egresos=Decimal(str(r["total_egresos"])), saldo=Decimal(str(r["saldo"]))))
    db.commit()
    return {"ok": True}


@router.get("/cortes", response_model=list[CorteOut], summary="Cortes de caja guardados")
def cortes(db: Session = Depends(get_db), _: Usuario = Depends(exigir("Reportes"))):
    return list(db.scalars(select(CorteCaja).order_by(desc(CorteCaja.id_corte)).limit(50)))


@router.get("/egresos", response_model=list[EgresoOut], summary="Compras y egresos")
def egresos(db: Session = Depends(get_db), _: Usuario = Depends(exigir("Compras"))):
    return list(db.scalars(select(Egreso).order_by(desc(Egreso.id_egreso)).limit(100)))


@router.post("/egresos", summary="Registrar un egreso")
def crear_egreso(datos: EgresoIn, db: Session = Depends(get_db), u: Usuario = Depends(exigir("Compras"))):
    e = Egreso(id_usuario=u.id_usuario, tipo=datos.tipo, concepto=datos.concepto.strip(), monto=datos.monto)
    db.add(e)
    db.commit()
    return {"id": e.id_egreso}
