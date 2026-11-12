"""Registro de ventas y cotizaciones, y alta de clientes (rutas /api/ventas)."""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import get_db
from ..modelos import Cliente, DetalleDocumento, Documento, Producto, Usuario
from ..schemas import ClienteIn, ClienteOut, DocumentoIn
from ..seguridad import exigir

router = APIRouter(prefix="/api/ventas", tags=["Ventas"])


@router.get("/clientes", response_model=list[ClienteOut], summary="Listar clientes")
def clientes(db: Session = Depends(get_db), _: Usuario = Depends(exigir())):
    return list(db.scalars(select(Cliente).order_by(Cliente.id_cliente)))


@router.post("/clientes", summary="Registrar cliente")
def crear_cliente(datos: ClienteIn, db: Session = Depends(get_db), _: Usuario = Depends(exigir())):
    c = Cliente(nombre=datos.nombre.strip(), telefono=datos.telefono, correo=datos.correo)
    db.add(c)
    db.commit()
    return {"id": c.id_cliente}


@router.post("/documentos", summary="Registrar una nota de remisión o una cotización")
def registrar(datos: DocumentoIn, db: Session = Depends(get_db), u: Usuario = Depends(exigir())):
    nota = datos.tipo == "Nota de remisión"
    if nota and not datos.metodo_pago:
        raise HTTPException(400, "Selecciona un método de pago")
    if not db.get(Cliente, datos.id_cliente or 1):
        raise HTTPException(404, "Cliente no encontrado")

    lineas: dict[int, int] = {}  # une renglones repetidos del mismo producto
    for i in datos.items:
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
