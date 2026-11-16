"""Módulo de ventas (rutas /api/ventas): CREATE, UPDATE y DELETE de notas y cotizaciones, y alta de clientes.
La consulta (READ) está en ticket_veta.py."""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import get_db
from ..modelos import Cliente, DetalleDocumento, Documento, Producto, Usuario
from ..schemas import ClienteIn, ClienteOut, DocumentoIn, ItemIn
from ..seguridad import exigir

router = APIRouter(prefix="/api/ventas", tags=["Ventas"])


def _validar_items(db: Session, items: list[ItemIn], nota: bool):
    """Une renglones repetidos, bloquea los productos, revisa existencias y calcula los importes.
    Devuelve (total, [(producto, cantidad, subtotal), ...])."""
    lineas: dict[int, int] = {}
    for i in items:
        lineas[i.id_producto] = lineas.get(i.id_producto, 0) + i.cantidad
    total, detalles = Decimal("0"), []
    for id_producto, cantidad in lineas.items():
        p = db.scalar(select(Producto).where(Producto.id_producto == id_producto, Producto.activo.is_(True)).with_for_update())
        if not p:
            raise HTTPException(400, "Uno de los productos ya no está disponible")
        if nota and not p.es_servicio and p.existencias < cantidad:
            raise HTTPException(400, f"Existencias insuficientes de {p.nombre} (quedan {p.existencias})")
        subtotal = (p.precio * cantidad).quantize(Decimal("0.01"))  # el servidor calcula los importes
        total += subtotal
        detalles.append((p, cantidad, subtotal))
    return total, detalles


def _devolver_existencias(db: Session, doc: Documento) -> None:
    """Regresa al inventario las piezas de una nota de remisión (al modificarla o eliminarla)."""
    for d in doc.items:
        p = db.scalar(select(Producto).where(Producto.id_producto == d.id_producto).with_for_update())
        if p and not p.es_servicio:
            p.existencias += d.cantidad


@router.get("/clientes", response_model=list[ClienteOut], summary="Listar clientes")
def clientes(db: Session = Depends(get_db), _: Usuario = Depends(exigir())):
    return list(db.scalars(select(Cliente).order_by(Cliente.id_cliente)))


@router.post("/clientes", summary="Registrar cliente")
def crear_cliente(datos: ClienteIn, db: Session = Depends(get_db), _: Usuario = Depends(exigir())):
    c = Cliente(nombre=datos.nombre.strip(), telefono=datos.telefono, correo=datos.correo)
    db.add(c)
    db.commit()
    return {"id": c.id_cliente}


@router.post("/documentos", summary="CREATE: registrar una nota de remisión o una cotización")
def registrar(datos: DocumentoIn, db: Session = Depends(get_db), u: Usuario = Depends(exigir())):
    nota = datos.tipo == "Nota de remisión"
    if nota and not datos.metodo_pago:
        raise HTTPException(400, "Selecciona un método de pago")
    if not db.get(Cliente, datos.id_cliente or 1):
        raise HTTPException(404, "Cliente no encontrado")

    total, detalles = _validar_items(db, datos.items, nota)
    folio = (db.scalar(select(func.coalesce(func.max(Documento.folio), 0))) or 0) + 1
    doc = Documento(id_usuario=u.id_usuario, id_cliente=datos.id_cliente or 1, folio=folio, tipo=datos.tipo,
                    metodo_pago=datos.metodo_pago if nota else None, total=total)
    for p, cantidad, subtotal in detalles:
        doc.items.append(DetalleDocumento(id_producto=p.id_producto, cantidad=cantidad, precio_unitario=p.precio, subtotal=subtotal))
        if nota and not p.es_servicio:
            p.existencias -= cantidad  # solo la nota descuenta existencias
    db.add(doc)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "No se pudo asignar el folio; intenta de nuevo")
    return {"id_documento": doc.id_documento, "folio": doc.folio, "total": float(total)}


@router.put("/documentos/{id_documento}", summary="UPDATE: modificar una nota o cotización (solo Propietario)")
def modificar(id_documento: int, datos: DocumentoIn, db: Session = Depends(get_db), _: Usuario = Depends(exigir("owner"))):
    doc = db.get(Documento, id_documento, with_for_update=True)
    if not doc:
        raise HTTPException(404, "Documento no encontrado")
    if datos.tipo != doc.tipo:
        raise HTTPException(400, "No se puede cambiar el tipo de documento")
    nota = doc.tipo == "Nota de remisión"
    if nota and not datos.metodo_pago:
        raise HTTPException(400, "Selecciona un método de pago")
    if not db.get(Cliente, datos.id_cliente or 1):
        raise HTTPException(404, "Cliente no encontrado")

    if nota:
        _devolver_existencias(db, doc)  # primero regresa lo vendido y luego aplica los renglones nuevos
    total, detalles = _validar_items(db, datos.items, nota)
    doc.items.clear()
    db.flush()
    for p, cantidad, subtotal in detalles:
        doc.items.append(DetalleDocumento(id_producto=p.id_producto, cantidad=cantidad, precio_unitario=p.precio, subtotal=subtotal))
        if nota and not p.es_servicio:
            p.existencias -= cantidad
    doc.id_cliente = datos.id_cliente or 1
    doc.metodo_pago = datos.metodo_pago if nota else None
    doc.total = total
    db.commit()
    return {"id_documento": doc.id_documento, "folio": doc.folio, "total": float(total)}


@router.delete("/documentos/{id_documento}", summary="DELETE: eliminar una nota o cotización (solo Propietario)")
def eliminar(id_documento: int, db: Session = Depends(get_db), _: Usuario = Depends(exigir("owner"))):
    doc = db.get(Documento, id_documento, with_for_update=True)
    if not doc:
        raise HTTPException(404, "Documento no encontrado")
    if doc.tipo == "Nota de remisión":
        _devolver_existencias(db, doc)  # la venta se cancela: las piezas regresan al inventario
    db.delete(doc)
    db.commit()
    return {"ok": True}