"""Alta (POST) y edición (PUT) de productos y servicios."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import get_db
from ..modelos import Categoria, Producto, Usuario
from ..schemas import ProductoIn
from ..seguridad import exigir

router = APIRouter(prefix="/api/inventario", tags=["Inventario"])


def _aplicar(p: Producto, d: ProductoIn, db: Session) -> None:
    if not db.get(Categoria, d.id_categoria):
        raise HTTPException(400, "La categoría no existe")
    p.id_categoria, p.nombre, p.precio = d.id_categoria, d.nombre.strip(), d.precio
    p.es_servicio, p.stock_minimo = d.es_servicio, d.stock_minimo
    p.existencias = 0 if d.es_servicio else d.existencias  # los servicios no manejan existencias


@router.post("/productos", summary="Registrar producto o servicio")
def registrar(datos: ProductoIn, db: Session = Depends(get_db), _: Usuario = Depends(exigir("Inventario"))):
    p = Producto()
    _aplicar(p, datos, db)
    db.add(p)
    db.commit()
    return {"id": p.id_producto}


@router.put("/productos/{id_producto}", summary="Editar producto o servicio")
def editar(id_producto: int, datos: ProductoIn, db: Session = Depends(get_db), _: Usuario = Depends(exigir("Inventario"))):
    p = db.get(Producto, id_producto)
    if not p or not p.activo:
        raise HTTPException(404, "Producto no encontrado")
    _aplicar(p, datos, db)
    db.commit()
    return {"id": p.id_producto}
