from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl


class Producto(BaseModel):
    """Un producto scrapeado de una tienda."""
    nombre: str
    precio: float
    url: HttpUrl
    tienda: str
    fecha: datetime
    disponible: bool = True
    precio_anterior: Optional[float] = None


class Sitio(BaseModel):
    """Configuración de un sitio a scrapear."""
    nombre: str
    url: HttpUrl
    selector_nombre: str
    selector_precio: str
    moneda: str = "$"
