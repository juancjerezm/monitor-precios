import asyncio
from datetime import datetime
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .models import Producto, Sitio

console = Console()


def _extraer_precio(texto: str, moneda: str) -> float:
    """Limpia un texto de precio y lo convierte a float.
    
    Ejemplos: "$ 1,299.00" -> 1299.0, "1.299" -> 1299.0
    """
    limpio = texto.strip().replace(moneda, "").replace(",", "").strip()
    return float(limpio)


async def _scrapear_sitio(
    cliente: httpx.AsyncClient, sitio: Sitio
) -> Optional[Producto]:
    """Scrapea un producto de un sitio web."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = await cliente.get(
            str(sitio.url), headers=headers, timeout=15, follow_redirects=True
        )
        resp.raise_for_status()
    except Exception as e:
        console.print(f"[red]Error en {sitio.nombre}: {e}[/red]")
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    nombre_el = soup.select_one(sitio.selector_nombre)
    precio_el = soup.select_one(sitio.selector_precio)

    if not nombre_el or not precio_el:
        console.print(
            f"[yellow]No se encontró selector en {sitio.nombre}[/yellow]"
        )
        return None

    nombre = nombre_el.get_text(strip=True)
    precio = _extraer_precio(precio_el.get_text(strip=True), sitio.moneda)

    return Producto(
        nombre=nombre,
        precio=precio,
        url=sitio.url,
        tienda=sitio.nombre,
        fecha=datetime.now(),
        disponible=True,
    )


async def scrapear(sitios: list[Sitio]) -> list[Producto]:
    """Scrapea múltiples sitios en paralelo."""
    async with httpx.AsyncClient() as cliente:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            tarea = progress.add_task("Scrapeando sitios...", total=len(sitios))
            tareas = [_scrapear_sitio(cliente, s) for s in sitios]
            resultados = await asyncio.gather(*tareas)
            progress.update(tarea, completed=len(sitios))

    productos = [p for p in resultados if p is not None]
    return productos
