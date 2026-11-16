# Uso de inteligencia artificial

## Herramienta utilizada

Claude (Anthropic), mediante la aplicación web claude.ai.

## Prompts utilizados

Los prompts se escribieron en español. Resumen en orden cronológico:

1. *"Creacion de la conexion a la db"*.
2. *"diagrama de base de datos"*.
3. *"documentaciones sobre el fontend"*

## Código generado

Código base generado por la IA a partir de los prompts anteriores:

| Parte | Archivos |
|-------|----------|
| Base de datos | `baseDeDatos/script_base_datos.sql` |
| Documentación | `README.md`, los diagramas y `descripcion_software.pdf` |

## Verificación realizada

El código generado se probó antes de la entrega: se instaló el script SQL en MySql, se ejecutaron 36 verificaciones
automáticas sobre la API en Python (inicio de sesión, permisos por rol, ventas, cotizaciones, existencias, resurtido,
reportes, corte de caja, usuarios y respaldos) y se cargaron todas las páginas del frontend contra el servidor, con un
flujo completo de venta. No se probó en XAMPP ni en un navegador real, por lo que el equipo debe ejecutarlo en su
equipo y revisarlo.

## Ajustes realizados por el equipo

> Esta sección debe describir lo que el equipo cambió, corrigió o validó.
> Ejemplos del tipo de información esperada (reemplazar por lo que realmente se hizo):

| Archivo o módulo | Qué se ajustó | Quién | Fecha |
|------------------|---------------|-------|-------|
