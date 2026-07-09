"""Detecção de monitores conectados e ajuste de DPI awareness no Windows."""

import sys
import ctypes
import logging
from typing import List, Optional

try:
    from screeninfo import get_monitors as _screeninfo_get_monitors
    SCREENINFO_DISPONIVEL = True
except Exception:
    _screeninfo_get_monitors = None
    SCREENINFO_DISPONIVEL = False


class Monitor:
    """Geometria de um monitor em coordenadas de tela (pixels físicos)."""

    __slots__ = ("x", "y", "width", "height")

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


def habilitar_dpi_awareness() -> None:
    """Alinha as coordenadas do Tk com as do Windows quando há monitores com
    escalas de DPI diferentes. Sem isso, a geometria retornada pelo screeninfo
    pode não bater com a que o Tk usa para posicionar janelas."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def listar_monitores(root=None) -> List[Monitor]:
    """Retorna a lista de monitores conectados (Monitor: x, y, width, height).

    Usa screeninfo quando disponível. Se a lib não estiver instalada ou a
    detecção falhar, cai graciosamente para um único monitor (o retângulo de
    tela que o próprio Tk enxerga), preservando o comportamento anterior.
    """
    if SCREENINFO_DISPONIVEL:
        try:
            monitores = _screeninfo_get_monitors()
            if monitores:
                return [Monitor(m.x, m.y, m.width, m.height) for m in monitores]
        except Exception as e:
            logging.warning("Falha ao detectar monitores via screeninfo: %s", e)
    else:
        logging.warning("screeninfo não disponível; usando apenas o monitor primário.")

    if root is not None:
        try:
            return [Monitor(0, 0, root.winfo_screenwidth(), root.winfo_screenheight())]
        except Exception:
            pass
    return [Monitor(0, 0, 1920, 1080)]
