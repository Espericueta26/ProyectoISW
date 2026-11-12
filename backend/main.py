"""Aplicación FastAPI: registra los módulos, la sesión y sirve el frontend.

Ejecutar desde la raíz del proyecto:   uvicorn backend.main:app --reload
Documentación interactiva de la API:   http://localhost:8000/docs
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import RAIZ, SECRET_KEY, ErrorServicio
from .inventario import productos_ctr, registrar_producto
from .reportes import reporte_inv, reporte_vts
from .usuarios import usuarioController
from .ventas import registrar_vts, ticket_veta

app = FastAPI(title="Triates Papelería · Gestor de Venta (POS)", version="1.0.0",
              description="API del sistema de ventas e inventario de Triates Papelería (Ingeniería de Software, ITS).")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, session_cookie="triates_sesion", same_site="lax", max_age=8 * 3600)


# El frontend espera los errores como {"error": "mensaje"}
@app.exception_handler(HTTPException)
async def error_http(_: Request, e: HTTPException):
    return JSONResponse({"error": str(e.detail)}, status_code=e.status_code)


@app.exception_handler(ErrorServicio)
async def error_servicio(_: Request, e: ErrorServicio):
    return JSONResponse({"error": e.mensaje}, status_code=e.codigo)


@app.exception_handler(RequestValidationError)
async def error_validacion(_: Request, e: RequestValidationError):
    campos = ", ".join(sorted({str(x["loc"][-1]) for x in e.errors() if x.get("loc")}))
    return JSONResponse({"error": f"Revisa los datos capturados ({campos})"}, status_code=400)


for modulo in (usuarioController, productos_ctr, registrar_producto, registrar_vts, ticket_veta, reporte_vts, reporte_inv):
    app.include_router(modulo.router)

app.mount("/frontend", StaticFiles(directory=RAIZ / "frontend"), name="frontend")


@app.get("/", include_in_schema=False)
def inicio():
    return RedirectResponse("/frontend/usuarios/login.html")
