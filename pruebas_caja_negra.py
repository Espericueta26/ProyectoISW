#!/usr/bin/env python3
"""Pruebas de caja negra · Triates Papelería POS

Se prueba el sistema SOLO por sus entradas y salidas (API HTTP), sin mirar el código. Los casos se diseñaron con las
técnicas de partición de equivalencia y análisis de valores límite.

Uso (con el servidor encendido y la base de datos importada):
    python pruebas_caja_negra.py                       # usa http://localhost:8000
    python pruebas_caja_negra.py http://localhost:8001

Genera la tabla en pantalla y el archivo evidencia_pruebas_caja_negra.csv (ábrelo con Excel).
No necesita instalar librerías. Crea datos de prueba (productos, ventas y usuarios "CN"); al terminar puedes
volver a importar baseDeDatos/script_base_datos.sql si quieres la base limpia.
"""
import csv
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from http.cookiejar import CookieJar

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
SFX = str(int(time.time()))[-6:]


class Cliente:
    """Un navegador simulado con su propia sesión (cookie)."""

    def __init__(self):
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    def __call__(self, metodo, ruta, cuerpo=None):
        datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
        req = urllib.request.Request(BASE + "/api" + ruta, data=datos, method=metodo,
                                     headers={"Content-Type": "application/json"} if datos else {})
        try:
            with self.op.open(req, timeout=20) as r:
                codigo, texto = r.status, r.read()
        except urllib.error.HTTPError as e:
            codigo, texto = e.code, e.read()
        try:
            return codigo, json.loads(texto)
        except ValueError:
            return codigo, {}


anon, prop, sinperm, rep = Cliente(), Cliente(), Cliente(), Cliente()
E = {}  # datos compartidos entre casos (ids creados durante la prueba)
CASOS = []


def caso(id_, modulo, tecnica, entrada, esperado):
    def deco(f):
        CASOS.append((id_, modulo, tecnica, entrada, esperado, f))
        return f
    return deco


def ok(cond, obtenido):
    return ("APROBADO" if cond else "FALLIDO", obtenido)


def msg(d):
    return d.get("error", "") if isinstance(d, dict) else ""


def producto(pid):
    return next((p for p in prop("GET", "/inventario/productos")[1] if p["id_producto"] == pid), None)


def nuevo_producto(nombre, precio, existencias, servicio=False):
    c, d = prop("POST", "/inventario/productos", {"nombre": f"{nombre} {SFX}", "id_categoria": 2, "precio": precio,
                                                    "existencias": existencias, "stock_minimo": 1, "es_servicio": servicio})
    return d.get("id")


def venta(cli, pid, cant, tipo="Nota de remisión", pago="Efectivo", cliente=1):
    return cli("POST", "/ventas/documentos", {"tipo": tipo, "id_cliente": cliente, "metodo_pago": pago if tipo != "Cotización" else None,
                                              "items": [{"id_producto": pid, "cantidad": cant}]})


# ======================= AUTENTICACIÓN =======================
@caso("CN-01", "Autenticación", "Clase válida", "Usuario propietario / contraseña 1234", "200 y rol Propietario")
def _():
    c, d = prop("POST", "/usuarios/login", {"usuario": "propietario", "contrasena": "1234"})
    return ok(c == 200 and d.get("rol") == "Propietario", f"{c}, rol {d.get('rol')}")


@caso("CN-02", "Autenticación", "Clase válida", "Usuario mostrador / contraseña 1234", "200 y rol Encargado de mostrador")
def _():
    c, d = Cliente()("POST", "/usuarios/login", {"usuario": "mostrador", "contrasena": "1234"})
    return ok(c == 200 and d.get("rol") == "Encargado de mostrador", f"{c}, rol {d.get('rol')}")


@caso("CN-03", "Autenticación", "Clase inválida", "Usuario válido con contraseña incorrecta", "401 y mensaje de error")
def _():
    c, d = anon("POST", "/usuarios/login", {"usuario": "propietario", "contrasena": "xxxx"})
    return ok(c == 401 and "incorrectos" in msg(d), f"{c}, {msg(d)}")


@caso("CN-04", "Autenticación", "Clase inválida", "Usuario que no existe", "401 y mensaje de error")
def _():
    c, d = anon("POST", "/usuarios/login", {"usuario": "noexiste", "contrasena": "1234"})
    return ok(c == 401, f"{c}, {msg(d)}")


@caso("CN-05", "Autenticación", "Valor límite", "Usuario vacío", "400 (dato inválido)")
def _():
    c, d = anon("POST", "/usuarios/login", {"usuario": "", "contrasena": "1234"})
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-06", "Autenticación", "Valor límite", "Contraseña vacía", "400 (dato inválido)")
def _():
    c, d = anon("POST", "/usuarios/login", {"usuario": "propietario", "contrasena": ""})
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-07", "Autenticación", "Clase inválida", "Consultar productos sin haber iniciado sesión", "401")
def _():
    c, d = anon("GET", "/inventario/productos")
    return ok(c == 401, f"{c}, {msg(d)}")


# ======================= USUARIOS Y PERMISOS =======================
@caso("CN-08", "Usuarios", "Valor límite", "Crear usuario con contraseña de 3 caracteres", "400 (mínimo 4)")
def _():
    c, d = prop("POST", "/usuarios", {"nombre": "Prueba", "usuario": f"cn_corta_{SFX}", "contrasena": "abc", "rol": "Encargado de mostrador"})
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-09", "Usuarios", "Valor límite", "Crear usuario con contraseña de 4 caracteres", "200")
def _():
    c, d = prop("POST", "/usuarios", {"nombre": "Prueba sin permisos", "usuario": f"cn_sin_{SFX}", "contrasena": "abcd", "rol": "Encargado de mostrador"})
    prop("POST", "/usuarios", {"nombre": "Prueba reportes", "usuario": f"cn_rep_{SFX}", "contrasena": "abcd", "rol": "Encargado de mostrador"})
    return ok(c == 200, f"{c}, id {d.get('id')}")


@caso("CN-10", "Usuarios", "Clase inválida", "Crear usuario con nombre de usuario repetido", "409")
def _():
    c, d = prop("POST", "/usuarios", {"nombre": "Otro", "usuario": f"cn_sin_{SFX}", "contrasena": "abcd", "rol": "Encargado de mostrador"})
    return ok(c == 409, f"{c}, {msg(d)}")


@caso("CN-11", "Usuarios", "Clase inválida", "Crear usuario con un rol que no existe", "400")
def _():
    c, d = prop("POST", "/usuarios", {"nombre": "Otro", "usuario": f"cn_rol_{SFX}", "contrasena": "abcd", "rol": "Gerente"})
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-12", "Usuarios", "Clase válida", "Iniciar sesión con el usuario recién creado", "200")
def _():
    c, d = sinperm("POST", "/usuarios/login", {"usuario": f"cn_sin_{SFX}", "contrasena": "abcd"})
    rep("POST", "/usuarios/login", {"usuario": f"cn_rep_{SFX}", "contrasena": "abcd"})
    return ok(c == 200, f"{c}, rol {d.get('rol')}")


@caso("CN-13", "Usuarios", "Control de acceso", "Usuario sin permisos consulta la lista de usuarios", "403")
def _():
    c, d = sinperm("GET", "/usuarios")
    return ok(c == 403, f"{c}, {msg(d)}")


@caso("CN-14", "Usuarios", "Clase válida", "El propietario otorga el permiso Reportes a un usuario", "200 y el permiso aparece en su sesión")
def _():
    uid = next(u["id"] for u in prop("GET", "/usuarios")[1] if u["usuario"] == f"cn_rep_{SFX}")
    c, d = prop("PUT", f"/usuarios/{uid}/permisos", {"permisos": ["Reportes"]})
    perm = rep("GET", "/usuarios/me")[1].get("permisos")
    return ok(c == 200 and perm == ["Reportes"], f"{c}, permisos {perm}")


# ======================= INVENTARIO =======================
@caso("CN-15", "Inventario", "Clase válida", "Registrar producto: nombre, categoría 2, precio 10.00, existencias 5", "200 y el producto aparece en el listado")
def _():
    E["inv"] = nuevo_producto("Producto CN", 10, 5)
    p = producto(E["inv"])
    return ok(p is not None and p["existencias"] == 5, f"id {E['inv']}, existencias {p and p['existencias']}")


@caso("CN-16", "Inventario", "Valor límite", "Registrar producto con precio 0", "400")
def _():
    c, d = prop("POST", "/inventario/productos", {"nombre": "X", "id_categoria": 2, "precio": 0})
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-17", "Inventario", "Clase inválida", "Registrar producto con precio negativo (-5)", "400")
def _():
    c, d = prop("POST", "/inventario/productos", {"nombre": "X", "id_categoria": 2, "precio": -5})
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-18", "Inventario", "Clase inválida", "Registrar producto con precio no numérico (\"abc\")", "400")
def _():
    c, d = prop("POST", "/inventario/productos", {"nombre": "X", "id_categoria": 2, "precio": "abc"})
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-19", "Inventario", "Valor límite", "Registrar producto con nombre vacío", "400")
def _():
    c, d = prop("POST", "/inventario/productos", {"nombre": "", "id_categoria": 2, "precio": 10})
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-20", "Inventario", "Valor límite", "Registrar producto con existencias negativas (-1)", "400")
def _():
    c, d = prop("POST", "/inventario/productos", {"nombre": "X", "id_categoria": 2, "precio": 10, "existencias": -1})
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-21", "Inventario", "Clase inválida", "Registrar producto con una categoría que no existe", "400")
def _():
    c, d = prop("POST", "/inventario/productos", {"nombre": "X", "id_categoria": 9999, "precio": 10})
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-22", "Inventario", "Control de acceso", "Usuario sin permiso Inventario intenta registrar un producto", "403")
def _():
    c, d = sinperm("POST", "/inventario/productos", {"nombre": "X", "id_categoria": 2, "precio": 10})
    return ok(c == 403, f"{c}, {msg(d)}")


@caso("CN-23", "Inventario", "Clase válida", "Editar el producto: precio 10 → 15", "200 y el nuevo precio queda guardado")
def _():
    c, d = prop("PUT", f"/inventario/productos/{E['inv']}", {"nombre": f"Producto CN editado {SFX}", "id_categoria": 2, "precio": 15, "existencias": 5, "stock_minimo": 1})
    p = producto(E["inv"])
    return ok(c == 200 and p["precio"] == 15, f"{c}, precio {p and p['precio']}")


@caso("CN-24", "Inventario", "Valor límite", "Resurtir con cantidad 0", "400")
def _():
    c, d = prop("POST", f"/inventario/productos/{E['inv']}/resurtir", {"cantidad": 0, "costo": 50})
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-25", "Inventario", "Clase válida", "Resurtir 10 piezas con costo 50", "200 y las existencias pasan de 5 a 15")
def _():
    c, d = prop("POST", f"/inventario/productos/{E['inv']}/resurtir", {"cantidad": 10, "costo": 50})
    p = producto(E["inv"])
    return ok(c == 200 and p["existencias"] == 15, f"{c}, existencias {p and p['existencias']}")


@caso("CN-26", "Inventario", "Clase válida", "Dar de baja el producto", "200 y ya no aparece en el inventario")
def _():
    c, d = prop("DELETE", f"/inventario/productos/{E['inv']}")
    c2, _d = prop("GET", f"/inventario/productos/{E['inv']}")
    return ok(c == 200 and c2 == 404, f"baja {c}, consulta posterior {c2}")


# ======================= VENTAS =======================
@caso("CN-27", "Ventas", "Clase válida", "Nota de remisión: 2 piezas de un producto de $12.50, pago en efectivo", "200, total $25.00 y folio asignado")
def _():
    E["p"] = nuevo_producto("Producto venta CN", 12.5, 10)
    c, d = venta(sinperm, E["p"], 2)
    E["doc"] = d.get("id_documento")
    return ok(c == 200 and d.get("total") == 25.0 and d.get("folio"), f"{c}, total {d.get('total')}, folio {d.get('folio')}")


@caso("CN-28", "Ventas", "Clase válida", "Revisar el inventario después de la nota anterior", "Las existencias bajan de 10 a 8")
def _():
    p = producto(E["p"])
    return ok(p["existencias"] == 8, f"existencias {p['existencias']}")


@caso("CN-29", "Ventas", "Valor límite", "Venta con cantidad 0", "400, no se registra")
def _():
    c, d = venta(sinperm, E["p"], 0)
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-30", "Ventas", "Clase inválida", "Venta con cantidad negativa (-3)", "400, no se registra")
def _():
    c, d = venta(sinperm, E["p"], -3)
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-31", "Ventas", "Clase inválida", "Venta con cantidad decimal (1.5)", "400, no se registra")
def _():
    c, d = venta(sinperm, E["p"], 1.5)
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-32", "Ventas", "Valor límite", "Venta sin ningún producto (lista vacía)", "400, no se registra")
def _():
    c, d = sinperm("POST", "/ventas/documentos", {"tipo": "Nota de remisión", "metodo_pago": "Efectivo", "items": []})
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-33", "Ventas", "Clase inválida", "Venta de un producto que no existe (id 999999)", "400, no se registra")
def _():
    c, d = venta(sinperm, 999999, 1)
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-34", "Ventas", "Valor límite", "Producto con 3 existencias: vender 4 (una más que las existencias)", "400 por existencias insuficientes; el inventario no cambia")
def _():
    E["q"] = nuevo_producto("Producto limite CN", 10, 3)
    c, d = venta(sinperm, E["q"], 4)
    return ok(c == 400 and producto(E["q"])["existencias"] == 3, f"{c}, {msg(d)}, existencias {producto(E['q'])['existencias']}")


@caso("CN-35", "Ventas", "Valor límite", "Producto con 3 existencias: vender exactamente 3", "200 y las existencias quedan en 0")
def _():
    c, d = venta(sinperm, E["q"], 3)
    return ok(c == 200 and producto(E["q"])["existencias"] == 0, f"{c}, existencias {producto(E['q'])['existencias']}")


@caso("CN-36", "Ventas", "Clase inválida", "Nota de remisión sin método de pago", "400")
def _():
    c, d = sinperm("POST", "/ventas/documentos", {"tipo": "Nota de remisión", "items": [{"id_producto": E["p"], "cantidad": 1}]})
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-37", "Ventas", "Clase inválida", "Nota con método de pago no permitido (\"Cheque\")", "400")
def _():
    c, d = venta(sinperm, E["p"], 1, pago="Cheque")
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-38", "Ventas", "Clase válida", "Cotización de 1 pieza", "200 y las existencias NO cambian (siguen en 8)")
def _():
    c, d = venta(sinperm, E["p"], 1, tipo="Cotización")
    return ok(c == 200 and producto(E["p"])["existencias"] == 8, f"{c}, existencias {producto(E['p'])['existencias']}")


@caso("CN-39", "Ventas", "Clase válida", "Venta de 500 piezas de un servicio (no maneja existencias)", "200")
def _():
    s = nuevo_producto("Servicio CN", 1, 0, servicio=True)
    c, d = venta(sinperm, s, 500)
    return ok(c == 200 and d.get("total") == 500.0, f"{c}, total {d.get('total')}")


@caso("CN-40", "Ventas", "Clase válida", "Consultar el ticket de la venta CN-27", "200 con cliente, productos, cantidades y total")
def _():
    c, d = sinperm("GET", f"/ventas/documentos/{E['doc']}")
    return ok(c == 200 and d.get("total") == 25.0 and d["items"][0]["cantidad"] == 2, f"{c}, total {d.get('total')}, renglones {len(d.get('items', []))}")


@caso("CN-41", "Ventas", "Clase inválida", "Consultar el ticket de una venta que no existe", "404, no se genera ticket")
def _():
    c, d = sinperm("GET", "/ventas/documentos/99999999")
    return ok(c == 404, f"{c}, {msg(d)}")


@caso("CN-42", "Ventas", "Control de acceso", "Usuario sin permisos intenta eliminar una venta", "403 (o 405 si falta el archivo nuevo)")
def _():
    c, d = sinperm("DELETE", f"/ventas/documentos/{E['doc']}")
    if c == 405:
        return ("OMITIDO", "405: falta instalar el registrar_vts.py nuevo (UPDATE/DELETE)")
    return ok(c == 403, f"{c}, {msg(d)}")


@caso("CN-43", "Ventas", "Clase válida", "El propietario modifica la venta: 5 piezas en lugar de 2", "200, total $62.50 y existencias 10 − 5 = 5")
def _():
    c, d = prop("PUT", f"/ventas/documentos/{E['doc']}", {"tipo": "Nota de remisión", "metodo_pago": "Tarjeta", "items": [{"id_producto": E["p"], "cantidad": 5}]})
    if c == 405:
        return ("OMITIDO", "405: falta instalar el registrar_vts.py nuevo (UPDATE/DELETE)")
    return ok(c == 200 and d.get("total") == 62.5 and producto(E["p"])["existencias"] == 5, f"{c}, total {d.get('total')}, existencias {producto(E['p'])['existencias']}")


@caso("CN-44", "Ventas", "Clase válida", "El propietario elimina la venta modificada", "200, la venta ya no existe y las existencias regresan a 10")
def _():
    c, d = prop("DELETE", f"/ventas/documentos/{E['doc']}")
    if c == 405:
        return ("OMITIDO", "405: falta instalar el registrar_vts.py nuevo (UPDATE/DELETE)")
    c2, _d = prop("GET", f"/ventas/documentos/{E['doc']}")
    return ok(c == 200 and c2 == 404 and producto(E["p"])["existencias"] == 10, f"{c}, consulta posterior {c2}, existencias {producto(E['p'])['existencias']}")


# ======================= REPORTES =======================
@caso("CN-45", "Reportes", "Clase válida", "Reporte de ventas de hoy (usuario con permiso Reportes)", "200 con ventas, egresos y saldo")
def _():
    c, d = rep("GET", "/reportes/ventas")
    return ok(c == 200 and d.get("total_ventas", 0) >= 500 and "saldo" in d, f"{c}, ventas {d.get('total_ventas')}, saldo {d.get('saldo')}")


@caso("CN-46", "Reportes", "Valor límite", "Rango de fechas invertido (desde 2026-12-01, hasta 2026-01-01)", "400")
def _():
    c, d = rep("GET", "/reportes/ventas?desde=2026-12-01&hasta=2026-01-01")
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-47", "Reportes", "Valor límite", "Rango de un solo día (desde = hasta = hoy)", "200")
def _():
    hoy = datetime.now().strftime("%Y-%m-%d")
    c, d = rep("GET", f"/reportes/ventas?desde={hoy}&hasta={hoy}")
    return ok(c == 200, f"{c}")


@caso("CN-48", "Reportes", "Control de acceso", "Usuario sin permiso Reportes consulta el reporte de ventas", "403")
def _():
    c, d = sinperm("GET", "/reportes/ventas")
    return ok(c == 403, f"{c}, {msg(d)}")


@caso("CN-49", "Reportes", "Valor límite", "Registrar egreso con monto 0", "400")
def _():
    c, d = prop("POST", "/reportes/egresos", {"tipo": "Otros gastos", "concepto": "Prueba", "monto": 0})
    return ok(c == 400, f"{c}, {msg(d)}")


@caso("CN-50", "Reportes", "Clase válida", "Registrar egreso de $50 (concepto \"Luz\")", "200")
def _():
    c, d = prop("POST", "/reportes/egresos", {"tipo": "Otros gastos", "concepto": f"Luz CN {SFX}", "monto": 50})
    return ok(c == 200, f"{c}")


@caso("CN-51", "Reportes", "Control de acceso", "Usuario con Reportes pero sin Compras intenta registrar un egreso", "403")
def _():
    c, d = rep("POST", "/reportes/egresos", {"tipo": "Otros gastos", "concepto": "x", "monto": 5})
    return ok(c == 403, f"{c}, {msg(d)}")


@caso("CN-52", "Reportes", "Clase válida", "Guardar el corte de caja del día", "200 y aparece en el historial de cortes")
def _():
    c, d = prop("POST", "/reportes/corte")
    c2, lista = prop("GET", "/reportes/cortes")
    return ok(c == 200 and len(lista) >= 1, f"{c}, cortes guardados {len(lista)}")


def main():
    print(f"\nPruebas de caja negra · {BASE} · {datetime.now():%Y-%m-%d %H:%M}\n")
    filas = []
    for id_, modulo, tecnica, entrada, esperado, f in CASOS:
        try:
            estado, obtenido = f()
        except Exception as e:  # un caso roto no detiene a los demás
            estado, obtenido = "FALLIDO", f"error al ejecutar: {e}"
        filas.append([id_, modulo, tecnica, entrada, esperado, obtenido, estado])
        marca = {"APROBADO": "OK   ", "FALLIDO": "FALLA", "OMITIDO": "OMIT "}[estado]
        print(f"[{marca}] {id_}  {modulo:<14} {entrada[:62]:<62} -> {obtenido[:60]}")
    n = {e: sum(1 for f in filas if f[6] == e) for e in ("APROBADO", "FALLIDO", "OMITIDO")}
    print(f"\nTotal: {len(filas)} casos · {n['APROBADO']} aprobados · {n['FALLIDO']} fallidos · {n['OMITIDO']} omitidos")
    with open("evidencia_pruebas_caja_negra.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["ID", "Módulo", "Técnica", "Entrada / acción", "Resultado esperado", "Resultado obtenido", "Estado"])
        w.writerows(filas)
    print("Evidencia guardada en evidencia_pruebas_caja_negra.csv")
    sys.exit(1 if n["FALLIDO"] else 0)


if __name__ == "__main__":
    main()