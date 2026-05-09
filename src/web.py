import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
import pandas as pd

from .models import Sitio, Producto
from .scraper import scrapear
from .reportes.excel import generar_reporte

BASE_DIR = Path(__file__).resolve().parent
SITIOS_JSON = Path("sitios.json")
HISTORICO = Path("historico_precios.xlsx")

app = FastAPI(title="Monitor de Precios")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
jinja = Environment(loader=FileSystemLoader(BASE_DIR / "templates"))


def _render(template: str, **kwargs) -> HTMLResponse:
    tpl = jinja.get_template(template)
    return HTMLResponse(tpl.render(**kwargs))


def _cargar_sitios() -> list[Sitio]:
    if SITIOS_JSON.exists():
        data = json.loads(SITIOS_JSON.read_text())
        return [Sitio(**s) for s in data]
    return []


def _guardar_sitios(sitios: list[Sitio]):
    SITIOS_JSON.write_text(json.dumps([s.model_dump() for s in sitios], indent=2, default=str))


def _historico_df() -> pd.DataFrame:
    if HISTORICO.exists():
        return pd.read_excel(HISTORICO)
    return pd.DataFrame(columns=["nombre", "tienda", "precio", "fecha", "disponible"])


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    sitios = _cargar_sitios()
    df = _historico_df()

    # Último precio por producto
    ultimos = []
    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"])
        ultimos = (
            df.sort_values("fecha")
            .groupby(["nombre", "tienda"], as_index=False)
            .last()
            .to_dict(orient="records")
        )
        for u in ultimos:
            if "fecha" in u and hasattr(u["fecha"], "isoformat"):
                u["fecha"] = u["fecha"].isoformat()

    return _render(
        "dashboard.html",
        request=request,
        productos=ultimos,
        sitios=sitios,
        total_sitios=len(sitios),
    )


@app.post("/scrapear", response_class=HTMLResponse)
async def ejecutar_scrapeo(request: Request):
    sitios = _cargar_sitios()
    if sitios:
        productos = await scrapear(sitios)
        if productos:
            generar_reporte(productos)
    return RedirectResponse("/", status_code=303)


@app.get("/sitios", response_class=HTMLResponse)
async def pagina_sitios(request: Request):
    sitios = _cargar_sitios()
    return _render("sitios.html", request=request, sitios=sitios)


@app.post("/sitios", response_class=HTMLResponse)
async def agregar_sitio(
    request: Request,
    nombre: str = Form(...),
    url: str = Form(...),
    selector_nombre: str = Form(...),
    selector_precio: str = Form(...),
):
    sitios = _cargar_sitios()
    sitios.append(
        Sitio(
            nombre=nombre,
            url=url,
            selector_nombre=selector_nombre,
            selector_precio=selector_precio,
        )
    )
    _guardar_sitios(sitios)
    return RedirectResponse("/sitios", status_code=303)


@app.post("/sitios/{idx}/eliminar")
async def eliminar_sitio(idx: int):
    sitios = _cargar_sitios()
    if 0 <= idx < len(sitios):
        sitios.pop(idx)
        _guardar_sitios(sitios)
    return RedirectResponse("/sitios", status_code=303)


@app.get("/descargar")
async def descargar_reporte():
    salida = Path("reporte_precios.xlsx")
    if salida.exists():
        return FileResponse(salida, filename="reporte_precios.xlsx")
    return {"error": "No hay reporte generado aún"}
