import pandas as pd
from pathlib import Path
from datetime import datetime

from ..models import Producto


def _cargar_historico(archivo: Path) -> pd.DataFrame:
    """Carga el histórico si existe, o crea DataFrame vacío."""
    if archivo.exists():
        return pd.read_excel(archivo)
    return pd.DataFrame(
        columns=["nombre", "precio", "tienda", "fecha", "url", "disponible"]
    )


def generar_reporte(
    productos: list[Producto], salida: Path = Path("reporte_precios.xlsx")
) -> Path:
    """Genera un Excel con los precios actuales + histórico y hoja de cambios."""
    archivo = Path("historico_precios.xlsx")
    historico = _cargar_historico(archivo)

    # Nuevos datos
    nuevos = pd.DataFrame([p.model_dump() for p in productos])

    # Guardar histórico actualizado
    if not nuevos.empty:
        historico_actualizado = pd.concat(
            [historico, nuevos], ignore_index=True
        )
        historico_actualizado.to_excel(archivo, index=False)

    # Crear reporte con formato
    with pd.ExcelWriter(salida, engine="xlsxwriter") as writer:
        # Hoja 1: Precios actuales
        if not nuevos.empty:
            tabla = nuevos[["nombre", "tienda", "precio", "disponible"]].copy()
            tabla["precio"] = tabla["precio"].apply(lambda x: f"${x:,.2f}")
            tabla.to_excel(writer, sheet_name="Precios Actuales", index=False)

        # Hoja 2: Histórico completo
        historico_actualizado.to_excel(
            writer, sheet_name="Histórico", index=False
        )

        # Formato
        wb = writer.book
        ws = writer.sheets["Precios Actuales"]
        ws.set_column("A:A", 40)
        ws.set_column("B:B", 20)
        ws.set_column("C:C", 15)
        ws.set_column("D:D", 12)

        # Estilo de encabezados
        header_fmt = wb.add_format({
            "bold": True,
            "bg_color": "#2563EB",
            "font_color": "white",
            "border": 1,
        })
        for col_num, value in enumerate(tabla.columns.values):
            ws.write(0, col_num, value, header_fmt)

    return salida
