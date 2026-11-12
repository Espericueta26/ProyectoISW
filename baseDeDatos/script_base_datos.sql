-- =====================================================================
-- Triates Papelería · Gestor de Venta (POS)
-- Script de base de datos (MySQL 5.7+ / MariaDB 10.3+)
-- Ejecutar UNA sola vez:  mysql -u root -p < baseDeDatos/script_base_datos.sql
-- Para reiniciar desde cero, descomenta la línea DROP DATABASE.
-- =====================================================================
SET NAMES utf8mb4;
-- DROP DATABASE IF EXISTS triates_pos;
CREATE DATABASE IF NOT EXISTS triates_pos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE triates_pos;

-- ---------- Seguridad: roles, usuarios y permisos ----------
CREATE TABLE IF NOT EXISTS rol (
  id_rol INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(40) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS usuario (
  id_usuario      INT AUTO_INCREMENT PRIMARY KEY,
  id_rol          INT NOT NULL,
  nombre          VARCHAR(80) NOT NULL,
  usuario         VARCHAR(40) NOT NULL UNIQUE,
  contrasena_hash VARCHAR(255) NOT NULL,
  activo          TINYINT(1) NOT NULL DEFAULT 1,
  CONSTRAINT fk_usuario_rol FOREIGN KEY (id_rol) REFERENCES rol(id_rol)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS permiso (
  id_permiso INT AUTO_INCREMENT PRIMARY KEY,
  nombre     VARCHAR(40) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS usuario_permiso (
  id_usuario INT NOT NULL,
  id_permiso INT NOT NULL,
  PRIMARY KEY (id_usuario, id_permiso),
  CONSTRAINT fk_up_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
  CONSTRAINT fk_up_permiso FOREIGN KEY (id_permiso) REFERENCES permiso(id_permiso) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------- Clientes ----------
CREATE TABLE IF NOT EXISTS cliente (
  id_cliente INT AUTO_INCREMENT PRIMARY KEY,
  nombre     VARCHAR(100) NOT NULL,
  telefono   VARCHAR(30),
  correo     VARCHAR(100)
) ENGINE=InnoDB;

-- ---------- Inventario ----------
CREATE TABLE IF NOT EXISTS categoria (
  id_categoria INT AUTO_INCREMENT PRIMARY KEY,
  nombre       VARCHAR(40) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS producto (
  id_producto  INT AUTO_INCREMENT PRIMARY KEY,
  id_categoria INT NOT NULL,
  nombre       VARCHAR(100) NOT NULL,
  precio       DECIMAL(10,2) NOT NULL,
  existencias  INT NOT NULL DEFAULT 0,
  es_servicio  TINYINT(1) NOT NULL DEFAULT 0,
  stock_minimo INT NOT NULL DEFAULT 5,
  activo       TINYINT(1) NOT NULL DEFAULT 1,
  CONSTRAINT fk_producto_categoria FOREIGN KEY (id_categoria) REFERENCES categoria(id_categoria),
  CONSTRAINT ck_producto_precio CHECK (precio > 0),
  CONSTRAINT ck_producto_existencias CHECK (existencias >= 0),
  INDEX idx_producto_categoria (id_categoria)
) ENGINE=InnoDB;

-- ---------- Ventas y cotizaciones ----------
CREATE TABLE IF NOT EXISTS documento (
  id_documento INT AUTO_INCREMENT PRIMARY KEY,
  id_usuario   INT NOT NULL,
  id_cliente   INT NOT NULL,
  folio        INT NOT NULL UNIQUE,
  tipo         ENUM('Cotización','Nota de remisión') NOT NULL,
  fecha        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  metodo_pago  ENUM('Efectivo','Tarjeta','Transferencia') NULL,
  total        DECIMAL(10,2) NOT NULL,
  CONSTRAINT fk_documento_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario),
  CONSTRAINT fk_documento_cliente FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente),
  CONSTRAINT ck_documento_pago CHECK (tipo = 'Cotización' OR metodo_pago IS NOT NULL),
  INDEX idx_documento_fecha (fecha),
  INDEX idx_documento_cliente (id_cliente)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS detalle_documento (
  id_detalle      INT AUTO_INCREMENT PRIMARY KEY,
  id_documento    INT NOT NULL,
  id_producto     INT NOT NULL,
  cantidad        INT NOT NULL,
  precio_unitario DECIMAL(10,2) NOT NULL,
  subtotal        DECIMAL(10,2) NOT NULL,
  CONSTRAINT fk_detalle_documento FOREIGN KEY (id_documento) REFERENCES documento(id_documento) ON DELETE CASCADE,
  CONSTRAINT fk_detalle_producto FOREIGN KEY (id_producto) REFERENCES producto(id_producto),
  CONSTRAINT ck_detalle_cantidad CHECK (cantidad > 0),
  INDEX idx_detalle_documento (id_documento)
) ENGINE=InnoDB;

-- ---------- Compras, egresos y resurtidos ----------
CREATE TABLE IF NOT EXISTS egreso (
  id_egreso  INT AUTO_INCREMENT PRIMARY KEY,
  id_usuario INT NOT NULL,
  fecha      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  tipo       ENUM('Mercancía','Sueldos','Otros gastos') NOT NULL,
  concepto   VARCHAR(150) NOT NULL,
  monto      DECIMAL(10,2) NOT NULL,
  CONSTRAINT fk_egreso_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario),
  CONSTRAINT ck_egreso_monto CHECK (monto > 0),
  INDEX idx_egreso_fecha (fecha)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS resurtido (
  id_resurtido INT AUTO_INCREMENT PRIMARY KEY,
  id_producto  INT NOT NULL,
  id_egreso    INT NULL UNIQUE,
  cantidad     INT NOT NULL,
  fecha        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_resurtido_producto FOREIGN KEY (id_producto) REFERENCES producto(id_producto),
  CONSTRAINT fk_resurtido_egreso FOREIGN KEY (id_egreso) REFERENCES egreso(id_egreso),
  CONSTRAINT ck_resurtido_cantidad CHECK (cantidad > 0)
) ENGINE=InnoDB;

-- ---------- Corte de caja y respaldos ----------
CREATE TABLE IF NOT EXISTS corte_caja (
  id_corte      INT AUTO_INCREMENT PRIMARY KEY,
  id_usuario    INT NOT NULL,
  fecha         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  total_ventas  DECIMAL(10,2) NOT NULL,
  total_egresos DECIMAL(10,2) NOT NULL,
  saldo         DECIMAL(10,2) NOT NULL,
  CONSTRAINT fk_corte_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS copia_seguridad (
  id_copia   INT AUTO_INCREMENT PRIMARY KEY,
  id_usuario INT NOT NULL,
  fecha      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  archivo    VARCHAR(120) NOT NULL,
  CONSTRAINT fk_copia_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
) ENGINE=InnoDB;

-- ---------- Datos iniciales de demostración (contraseña de ambos usuarios: 1234) ----------
INSERT INTO rol(nombre) VALUES ('Propietario'),('Encargado de mostrador');
INSERT INTO permiso(nombre) VALUES ('Inventario'),('Compras'),('Reportes');
INSERT INTO usuario(id_rol,nombre,usuario,contrasena_hash) VALUES
 (1,'Propietario','propietario','$2y$10$jMz83OLi.Ng7.MRZd3.DN.imUxDbBZI3DhuFJ8O6oOVGxaqzVeqMa'),
 (2,'Encargado de mostrador','mostrador','$2y$10$jMz83OLi.Ng7.MRZd3.DN.imUxDbBZI3DhuFJ8O6oOVGxaqzVeqMa');
INSERT INTO categoria(nombre) VALUES ('Papel'),('Oficina'),('Manualidades'),('Regalos'),('Servicios');
INSERT INTO cliente(nombre,telefono,correo) VALUES
 ('Público en general',NULL,NULL),
 ('María López','844 555 0192','maria@correo.com'),
 ('Escuela Primaria Benito Juárez','844 555 0147','direccion@bj.edu.mx');
INSERT INTO producto(id_categoria,nombre,precio,existencias,es_servicio,stock_minimo) VALUES
 (1,'Resma de papel carta',105,24,0,7),(1,'Cuaderno profesional',38,40,0,7),
 (2,'Carpeta tamaño carta',22,6,0,7),(3,'Pegamento blanco 250 ml',28,15,0,7),
 (3,'Pintura acrílica',18,30,0,7),(4,'Papel de regalo',15,50,0,7),
 (4,'Listón (metro)',6,3,0,7),(4,'Peluche chico',85,9,0,7),
 (5,'Fotocopia B/N',1,0,1,0),(5,'Impresión a color',5,0,1,0),(5,'Escaneo',3,0,1,0),
 (5,'Engargolado',25,0,1,0),(5,'Enmicado',12,0,1,0);
