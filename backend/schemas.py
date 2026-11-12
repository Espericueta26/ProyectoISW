"""Esquemas Pydantic: validan lo que llega del frontend y definen lo que se responde."""
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator

Fecha = Annotated[datetime, PlainSerializer(lambda d: d.strftime("%Y-%m-%d %H:%M:%S"), return_type=str)]
Dinero = Annotated[Decimal, PlainSerializer(lambda d: float(d), return_type=float)]


class Salida(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def _vacio_a_none(v):
    return None if isinstance(v, str) and not v.strip() else v


# ---------- Usuarios ----------
class LoginIn(BaseModel):
    usuario: str = Field(min_length=1)
    contrasena: str = Field(min_length=1)


class UsuarioIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=80)
    usuario: str = Field(min_length=1, max_length=40)
    contrasena: str = Field(min_length=4)
    rol: str


class PermisosIn(BaseModel):
    permisos: list[str] = []


class UsuarioOut(Salida):
    id: int
    nombre: str
    usuario: str
    rol: str
    permisos: list[str]


class CopiaOut(Salida):
    id_copia: int
    fecha: Fecha
    archivo: str
    usuario: str


# ---------- Inventario ----------
class CategoriaOut(Salida):
    id_categoria: int
    nombre: str


class ProductoIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    id_categoria: int = Field(gt=0)
    precio: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    existencias: int = Field(default=0, ge=0)
    stock_minimo: int = Field(default=5, ge=0)
    es_servicio: bool = False

    @field_validator("existencias", "stock_minimo", mode="before")
    @classmethod
    def _vacios(cls, v):
        return 0 if isinstance(v, str) and not v.strip() else v


class ResurtirIn(BaseModel):
    cantidad: int = Field(gt=0)
    costo: Decimal = Field(gt=0)


class ProductoOut(Salida):
    id_producto: int
    id_categoria: int
    nombre: str
    categoria: str
    precio: Dinero
    existencias: int
    es_servicio: bool
    stock_minimo: int


# ---------- Ventas ----------
class ClienteIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    telefono: Optional[str] = None
    correo: Optional[str] = None

    @field_validator("telefono", "correo", mode="before")
    @classmethod
    def _limpiar(cls, v):
        return _vacio_a_none(v)


class ClienteOut(Salida):
    id_cliente: int
    nombre: str
    telefono: Optional[str] = None
    correo: Optional[str] = None


class ItemIn(BaseModel):
    id_producto: int = Field(gt=0)
    cantidad: int = Field(gt=0)


class DocumentoIn(BaseModel):
    tipo: Literal["Cotización", "Nota de remisión"]
    id_cliente: Optional[int] = 1
    metodo_pago: Optional[Literal["Efectivo", "Tarjeta", "Transferencia"]] = None
    items: list[ItemIn] = Field(min_length=1)


class ItemTicket(Salida):
    nombre: str
    cantidad: int
    precio_unitario: Dinero
    subtotal: Dinero


class DocumentoResumen(Salida):
    id_documento: int
    folio: int
    tipo: str
    fecha: Fecha
    total: Dinero
    metodo_pago: Optional[str] = None
    cliente: str


class DocumentoOut(DocumentoResumen):
    usuario: str
    items: list[ItemTicket]


# ---------- Reportes ----------
class EgresoIn(BaseModel):
    tipo: Literal["Mercancía", "Sueldos", "Otros gastos"]
    concepto: str = Field(min_length=1, max_length=150)
    monto: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class EgresoOut(Salida):
    id_egreso: int
    fecha: Fecha
    tipo: str
    concepto: str
    monto: Dinero
    usuario: str


class CorteOut(Salida):
    id_corte: int
    fecha: Fecha
    total_ventas: Dinero
    total_egresos: Dinero
    saldo: Dinero
    usuario: str
