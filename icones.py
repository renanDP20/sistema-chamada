import sys
from pathlib import Path
from PySide6.QtGui import QIcon

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

ICONES_DIR = BASE_DIR / "icones"

_ICONES_CACHE: dict[str, QIcon] = {}

def get_icon(nome: str) -> QIcon:
    """Retorna um QIcon a partir do nome (suporta .ico, .png, .svg)."""
    if nome in _ICONES_CACHE:
        return _ICONES_CACHE[nome]

    candidatos = [nome, f"{nome}.ico", f"{nome}.png", f"{nome}.svg"]
    for c in candidatos:
        p = ICONES_DIR / c
        if p.exists():
            icon = QIcon(str(p))
            _ICONES_CACHE[nome] = icon
            return icon
        p_root = BASE_DIR / c
        if p_root.exists():
            icon = QIcon(str(p_root))
            _ICONES_CACHE[nome] = icon
            return icon

    _ICONES_CACHE[nome] = QIcon()
    return _ICONES_CACHE[nome]
