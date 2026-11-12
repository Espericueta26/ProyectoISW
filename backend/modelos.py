"""Modelos ORM (SQLAlchemy). Corresponden a las 13 tablas de baseDeDatos/script_base_datos.sql."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .config import Base

usuario_permiso = Table(
    "usuario_permiso", Base.metadata,
    Column("id_usuario", ForeignKey("usuario.id_usuario", ondelete="CASCADE"), primary_key=True),
    Column("id_permiso", ForeignKey("permiso.id_permiso", ondelete="CASCADE"), primary_key=True))


class Rol(Base):
    __tablename__ = "rol"
    id_rol: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40), unique=True)


class Permiso(Base):
    __tablename__ = "permiso"
    id_permiso: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40), unique=True)


class Usuario(Base):
    __tablename__ = "usuario"
    id_usuario: Mapped[int] = mapped_column(primary_key=True)
    id_rol: Mapped[int] = mapped_column(ForeignKey("rol.id_rol"))
    nombre: Mapped[str] = mapped_column(String(80))
    usuario: Mapped[str] = mapped_column(String(40), unique=True)
    contrasena_hash: Mapped[str] = mapped_column(String(255))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    rol_obj: Mapped[Rol] = relationship(lazy="joined")
    permisos_obj: Mapped[list[Permiso]] = relationship(secondary=usuario_permiso, lazy="selectin")

    @property
    def rol(self) -> str:
        return self.rol_obj.nombre

    @property
    def permisos(self) -> list[str]:
        return [p.nombre for p in self.permisos_obj]

    @property
    def id(self) -> int:
        return self.id_usuario


class Cliente(Base):
    __tablename__ = "cliente"
    id_cliente: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    telefono: Mapped[Optional[str]] = mapped_column(String(30))
    correo: Mapped[Optional[str]] = mapped_column(String(100))


class Categoria(Base):
    __tablename__ = "categoria"
    id_categoria: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40), unique=True)


class Producto(Base):
    __tablename__ = "producto"
    id_producto: Mapped[int] = mapped_column(primary_key=True)
    id_categoria: Mapped[int] = mapped_column(ForeignKey("categoria.id_categoria"))
    nombre: Mapped[str] = mapped_column(String(100))
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    existencias: Mapped[int] = mapped_column(Integer, default=0)
    es_servicio: Mapped[bool] = mapped_column(Boolean, default=False)
    stock_minimo: Mapped[int] = mapped_column(Integer, default=5)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    categoria_obj: Mapped[Categoria] = relationship(lazy="joined")

    @property
    def categoria(self) -> str:
        return self.categoria_obj.nombre


class Documento(Base):
    __tablename__ = "documento"
    id_documento: Mapped[int] = mapped_column(primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"))
    id_cliente: Mapped[int] = mapped_column(ForeignKey("cliente.id_cliente"))
    folio: Mapped[int] = mapped_column(unique=True)
    tipo: Mapped[str] = mapped_column(String(20))
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    metodo_pago: Mapped[Optional[str]] = mapped_column(String(20))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    cliente_obj: Mapped[Cliente] = relationship(lazy="joined")
    usuario_obj: Mapped[Usuario] = relationship(lazy="joined")
    items: Mapped[list["DetalleDocumento"]] = relationship(
        back_populates="documento", cascade="all, delete-orphan", order_by="DetalleDocumento.id_detalle", lazy="selectin")

    @property
    def cliente(self) -> str:
        return self.cliente_obj.nombre

    @property
    def usuario(self) -> str:
        return self.usuario_obj.nombre


class DetalleDocumento(Base):
    __tablename__ = "detalle_documento"
    id_detalle: Mapped[int] = mapped_column(primary_key=True)
    id_documento: Mapped[int] = mapped_column(ForeignKey("documento.id_documento", ondelete="CASCADE"))
    id_producto: Mapped[int] = mapped_column(ForeignKey("producto.id_producto"))
    cantidad: Mapped[int] = mapped_column(Integer)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    documento: Mapped[Documento] = relationship(back_populates="items")
    producto_obj: Mapped[Producto] = relationship(lazy="joined")

    @property
    def nombre(self) -> str:
        return self.producto_obj.nombre


class Egreso(Base):
    __tablename__ = "egreso"
    id_egreso: Mapped[int] = mapped_column(primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"))
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    tipo: Mapped[str] = mapped_column(String(20))
    concepto: Mapped[str] = mapped_column(String(150))
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    usuario_obj: Mapped[Usuario] = relationship(lazy="joined")

    @property
    def usuario(self) -> str:
        return self.usuario_obj.nombre


class Resurtido(Base):
    __tablename__ = "resurtido"
    id_resurtido: Mapped[int] = mapped_column(primary_key=True)
    id_producto: Mapped[int] = mapped_column(ForeignKey("producto.id_producto"))
    id_egreso: Mapped[Optional[int]] = mapped_column(ForeignKey("egreso.id_egreso"), unique=True)
    cantidad: Mapped[int] = mapped_column(Integer)
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CorteCaja(Base):
    __tablename__ = "corte_caja"
    id_corte: Mapped[int] = mapped_column(primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"))
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    total_ventas: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_egresos: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    saldo: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    usuario_obj: Mapped[Usuario] = relationship(lazy="joined")

    @property
    def usuario(self) -> str:
        return self.usuario_obj.nombre


class CopiaSeguridad(Base):
    __tablename__ = "copia_seguridad"
    id_copia: Mapped[int] = mapped_column(primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"))
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    archivo: Mapped[str] = mapped_column(String(120))
    usuario_obj: Mapped[Usuario] = relationship(lazy="joined")

    @property
    def usuario(self) -> str:
        return self.usuario_obj.nombre
