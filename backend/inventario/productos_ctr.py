"""Controlador de inventario (rutas /api/inventario): consulta, baja y resurtido."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_db
from ..modelos import Categoria, Egreso, Producto, Resurtido, Usuario
from ..schemas import CategoriaOut, ProductoOut, ResurtirIn
from ..seguridad import exigir

router = APIRouter(prefix="/api/inventario", tags=["Inventario"])


@router.get("/productos", response_model=list[ProductoOut], summary="Listar productos activos")
def listar(db: Session = Depends(get_db), _: Usuario = Depends(exigir())):
    return list(db.scalars(select(Producto).join(Categoria).where(Producto.activo.is_(True)).order_by(Categoria.nombre, Producto.nombre)))


@router.get("/categorias", response_model=list[CategoriaOut], summary="Listar categorías")
def categorias(db: Session = Depends(get_db), _: Usuario = Depends(exigir())):
    return list(db.scalars(select(Categoria).order_by(Categoria.nombre)))


@router.get("/productos/{id_producto}", response_model=ProductoOut, summary="Obtener un producto")
def obtener(id_producto: int, db: Session = Depends(get_db), _: Usuario = Depends(exigir())):
    p = db.scalar(select(Producto).where(Producto.id_producto == id_producto, Producto.activo.is_(True)))
    if not p:
        raise HTTPException(404, "Producto no encontrado")
    return p


@router.delete("/productos/{id_producto}", summary="Dar de baja un producto (baja lógica)")
def eliminar(id_producto: int, db: Session = Depends(get_db), _: Usuario = Depends(exigir("Inventario"))):
    p = db.get(Producto, id_producto)
    if p:
        p.activo = False  # conserva el historial de ventas
        db.commit()
    return {"ok": True}


@router.post("/productos/{id_producto}/resurtir", summary="Resurtir: aumenta existencias y registra el egreso")
def resurtir(id_producto: int, datos: ResurtirIn, db: Session = Depends(get_db), u: Usuario = Depends(exigir("Inventario"))):
    p = db.scalar(select(Producto).where(Producto.id_producto == id_producto, Producto.activo.is_(True),
                                         Producto.es_servicio.is_(False)).with_for_update())
    if not p:
        raise HTTPException(404, "Producto no encontrado o es un servicio")
    egreso = Egreso(id_usuario=u.id_usuario, tipo="Mercancía", concepto=f"Resurtido: {p.nombre} (+{datos.cantidad})", monto=datos.costo)
    db.add(egreso)
    db.flush()
    db.add(Resurtido(id_producto=p.id_producto, id_egreso=egreso.id_egreso, cantidad=datos.cantidad))
    p.existencias += datos.cantidad
    db.commit()  # todo en una sola transacción
    return {"ok": True}
