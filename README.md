# Sistema de Gestión de Ventas (POS) · Triates Papelería

Proyecto de la materia **Ingeniería de Software** · Ingeniería en Sistemas Computacionales
**Instituto Tecnológico de Saltillo** · Docente: Ing. Alejandra Margarita Sánchez Malacara

## Nombre del sistema

**Gestor de Venta (POS) para Triates Papelería**

## Integrantes del equipo

- Yazmin Alejandra García Álvarez
- Luis Ángel Espericueta Medina
- Abraham Mancillas Solis

## Descripción del proyecto

Triates Papelería es un negocio local de Saltillo, Coahuila que vende artículos escolares, de oficina y de regalo,
y ofrece servicios de copiado, impresión, escaneo, engargolado y enmicado. Hoy sus ventas, pedidos e inventario se
llevan en hojas de Excel, WhatsApp y correo, lo que genera información desintegrada, errores de captura,
inventario desactualizado y dependencia del propietario.

Este sistema centraliza esa información y permite:

- Registrar **ventas** y generar la **nota de remisión** (descuenta existencias automáticamente).
- Realizar **cotizaciones** sin afectar el inventario.
- Administrar **productos y servicios**, alertas de existencias bajas y resurtidos.
- Consultar **reportes** de ventas, egresos, corte de caja e inventario.
- Controlar el acceso con **usuarios, contraseñas, roles y permisos**.
- Crear **copias de seguridad** de la base de datos.

La metodología de desarrollo es **RUP** (Proceso Unificado Racional).

## Tecnologías utilizadas

| Capa | Tecnología |
|------|------------|
| Frontend | HTML5, CSS3 y JavaScript |
| Backend | Python 3.10+ con **FastAPI** (API REST), **SQLAlchemy 2** (ORM), **Pydantic** (validación) y **Uvicorn** (servidor) |
| Seguridad | Sesiones firmadas (Starlette) y contraseñas con **bcrypt** |
| Base de datos | MySQL / MariaDB |
| Control de versiones | Git y GitHub |

## Estructura del repositorio

```
sistema-papeleria-triates/
├── README.md
├── IA_USO.md
├── requirements.txt
├── documentación/
│   ├── arquitectura_software.png
│   ├── modelo_uml.png
│   └── descripcion_software.pdf
├── frontend/
│   ├── usuarios/     login.html · registro_usuarios.html
│   ├── inventario/   productos.html · registrar_producto.html
│   ├── ventas/       registrar_venta.html · ticket_venta.html
│   ├── reportes/     reporte_ventas.html · reporte_inventario.html
│   └── assets/       estilos.css · app.js   (recursos compartidos)
├── backend/
│   ├── main.py       (aplicación FastAPI)
│   ├── config.py · modelos.py · schemas.py · seguridad.py   (base de datos, ORM, validación y permisos)
│   ├── usuarios/     usuarioController.py · usuarioService.py
│   ├── inventario/   productos_ctr.py · registrar_producto.py
│   ├── ventas/       registrar_vts.py · ticket_veta.py
│   └── reportes/     reporte_vts.py · reporte_inv.py
├── baseDeDatos/
│   └── script_base_datos.sql
└── backups/          (respaldos generados por el sistema)
```

## Instalación y ejecución

Requisitos: **Python 3.10 o superior** y un servidor **MySQL o MariaDB** en ejecución (por ejemplo, el de XAMPP).

1. **Crear la base de datos.** Con XAMPP, abre phpMyAdmin (http://localhost/phpmyadmin), ve a **Importar** y selecciona
   `baseDeDatos/script_base_datos.sql`. También puedes usar la terminal:

   ```bash
   mysql -u root -p < baseDeDatos/script_base_datos.sql
   ```

2. **Instalar las dependencias** (desde la carpeta del proyecto):

   ```bash
   python -m venv venv
   venv\Scripts\activate          # en Linux/macOS: source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Iniciar el servidor:**

   ```bash
   venv/bin/uvicorn backend.main:app --reload
   ```

4. Abre http://localhost:8000/ para usar el sistema. La documentación interactiva de la API (Swagger) está en
   http://localhost:8000/docs.

### Configuración de la base de datos

Por defecto se conecta a `127.0.0.1:3306`, base `triates_pos`, usuario `root` sin contraseña (valores de XAMPP).
Para cambiarlos, define las variables de entorno `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` y `DB_PASS`
(o `DATABASE_URL` completa). Define también `SECRET_KEY` con un texto propio para firmar las sesiones.

## Usuarios de prueba

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| `propietario` | `1234` | Propietario (acceso total) |
| `mostrador` | `1234` | Encargado de mostrador |

> Cambia estas contraseñas antes de usar el sistema en el negocio real.

## Roles y permisos

- **Encargado de mostrador:** registrar ventas y cotizaciones, registrar clientes, consultar tickets.
- **Propietario:** todo lo anterior, además de inventario, reportes, egresos, usuarios, permisos y respaldos.
- El Propietario puede otorgar a cada usuario los permisos adicionales **Inventario**, **Compras** y **Reportes**.
  Los permisos se validan en el servidor, no solo en la interfaz.

## Reglas de negocio principales

- El servidor calcula precios y totales y valida las existencias; no confía en lo que envía el navegador.
- Una **nota de remisión** descuenta existencias; una **cotización** no.
- Los **servicios** (fotocopia, engargolado, etc.) no manejan existencias.
- Resurtir un producto registra el egreso de mercancía y el aumento de existencias en una sola transacción.
- Eliminar un producto es una baja lógica (`activo = 0`) para conservar el historial de ventas.
- Las contraseñas se guardan con hash (bcrypt).

## Documentación

- Diagrama de arquitectura: `documentación/arquitectura_software.png`
- Modelo de base de datos: `documentación/modelo_uml.png`
- Descripción del software: `documentación/descripcion_software.pdf`
- Uso de inteligencia artificial: `IA_USO.md`

## Notas

- La carpeta `backups/` contiene respaldos con información del negocio (incluidos los hashes de contraseñas). El
  servidor no la publica, pero no la subas a GitHub: ya está en `.gitignore`.
- El archivo `ticket_veta.py` conserva el nombre indicado en la estructura de entrega del curso.
- Los endpoints de la API están organizados por módulo: `/api/usuarios`, `/api/inventario`, `/api/ventas` y `/api/reportes`.
