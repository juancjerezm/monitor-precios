import asyncio
import webbrowser
from pathlib import Path
import typer
import uvicorn
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .models import Sitio
from .scraper import scrapear
from .reportes.excel import generar_reporte

app = typer.Typer(
    name="moni",
    help="Monitor de precios - Scrapea productos y genera reportes Excel",
)
console = Console()

# Sitios de ejemplo pre-configurados
SITIOS_EJEMPLO = [
    Sitio(
        nombre="Books to Scrape",
        url="http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        selector_nombre="div.product_main h1",
        selector_precio="p.price_color",
        moneda="£",
    ),
]


@app.command()
def scrapear_ejemplo():
    """Scrapea los sitios de ejemplo y genera el reporte."""
    console.print(
        Panel.fit(
            "[bold blue]Monitor de Precios[/bold blue]\nScrapeando libros de ejemplo...",
            border_style="blue",
        )
    )

    productos = asyncio.run(scrapear(SITIOS_EJEMPLO))

    if not productos:
        console.print("[red]No se encontraron productos[/red]")
        raise typer.Exit(1)

    # Mostrar resultados en tabla
    tabla = Table(title="Productos Encontrados")
    tabla.add_column("Producto", style="white")
    tabla.add_column("Tienda", style="cyan")
    tabla.add_column("Precio", style="green")
    tabla.add_column("Disponible", style="yellow")

    for p in productos:
        tabla.add_row(
            p.nombre[:50],
            p.tienda,
            f"${p.precio:,.2f}",
            "✅" if p.disponible else "❌",
        )

    console.print(tabla)

    # Generar Excel
    salida = generar_reporte(productos)
    console.print(f"\n[green]✅ Reporte generado: {salida}[/green]")


@app.command()
def nuevo_sitio(
    nombre: str = typer.Option(..., prompt=True),
    url: str = typer.Option(..., prompt=True),
    selector_nombre: str = typer.Option(..., prompt="Selector CSS del nombre"),
    selector_precio: str = typer.Option(..., prompt="Selector CSS del precio"),
):
    """Agrega un nuevo sitio para monitorear."""
    sitio = Sitio(
        nombre=nombre,
        url=url,
        selector_nombre=selector_nombre,
        selector_precio=selector_precio,
    )
    rprint(f"[green]✅ Sitio agregado: {sitio.nombre}[/green]")
    rprint(sitio.model_dump_json(indent=2))


@app.command()
def web(port: int = 8000):
    """Inicia la interfaz web en el navegador."""
    console.print(
        Panel.fit(
            "[bold blue]🌐 Monitor de Precios[/bold blue]\n"
            f"Abriendo http://localhost:{port} ...",
            border_style="blue",
        )
    )
    webbrowser.open(f"http://localhost:{port}")
    uvicorn.run("src.web:app", host="0.0.0.0", port=port, reload=True)


def main():
    app()
