"""Reporte de inventario: existencias, productos por resurtir y valor a precio de venta."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_db
from ..modelos import Categoria, Producto, Usuario
from ..seguridad import exigir

router = APIRouter(prefix="/api/reportes", tags=["Reportes"])


@router.get("/inventario", summary="Existencias y valor del inventario")
def inventario(db: Session = Depends(get_db), _: Usuario = Depends(exigir("Reportes"))):
    productos = list(db.scalars(select(Producto).join(Categoria).where(Producto.activo.is_(True)).order_by(Categoria.nombre, Producto.nombre)))
    por_resurtir = lambda p: not p.es_servicio and p.existencias <= p.stock_minimo
    productos.sort(key=lambda p: not por_resurtir(p))  # los que requieren resurtido, primero (el orden previo se conserva)
    filas, por_cat, valor_total = [], {}, 0.0
    for p in productos:
        valor = round(float(p.precio) * p.existencias, 2)
        filas.append({"id_producto": p.id_producto, "nombre": p.nombre, "categoria": p.categoria, "precio": float(p.precio),
                      "existencias": p.existencias, "stock_minimo": p.stock_minimo, "es_servicio": p.es_servicio, "valor": valor})
        if not p.es_servicio:
            valor_total += valor
            c = por_cat.setdefault(p.categoria, {"categoria": p.categoria, "productos": 0, "valor": 0.0})
            c["productos"] += 1
            c["valor"] = round(c["valor"] + valor, 2)
    return {"productos": filas, "total_productos": len(filas), "bajos": sum(1 for p in productos if por_resurtir(p)),
            "valor_inventario": round(valor_total, 2), "por_categoria": list(por_cat.values())}
