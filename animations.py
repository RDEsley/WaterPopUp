"""Posicionamento e animações de entrada do popup (não-fullscreen)."""

import random
from typing import Any, Callable, Dict, Optional, Tuple
import tkinter as tk

from config import CANTOS_POPUP, POSICOES_POPUP, ANIMACOES

def resolver_posicao_popup(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve 'random' para um canto concreto (cada chamada pode variar)."""
    c = dict(cfg)
    if c.get("popup_position") == "random":
        c["popup_position"] = random.choice(POSICOES_POPUP)
    return c

def pos_inicial(cfg: Dict[str, Any], w: int, h: int, popup_w: int = 300, popup_h: int = 100) -> Tuple[int, int]:
    pos = cfg.get("popup_position", "top-right")
    margin = 15
    if pos == "top-right":
        return w - popup_w - margin, margin
    elif pos == "top-left":
        return margin, margin
    elif pos == "bottom-right":
        return w - popup_w - margin, h - popup_h - margin
    elif pos == "bottom-left":
        return margin, h - popup_h - margin
    elif pos == "center":
        return max(0, (w - popup_w) // 2), max(0, (h - popup_h) // 2)
    else:
        return w - popup_w - margin, margin

def _ease_out_elastic(t: float) -> float:
    """Easing: overshoot e settle (spring effect)."""
    if t <= 0:
        return 0
    if t >= 1:
        return 1
    p = 0.4
    return 2 ** (-10 * t) * ((t - p / 4) * (2 * 3.14159) / p) + 1

def _ease_out_bounce(t: float) -> float:
    """Easing: bounce at the end."""
    if t < 1 / 2.75:
        return 7.5625 * t * t
    elif t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375

def animar_entrada(root, cfg: Dict[str, Any], x1: int, y1: int, callback: Optional[Callable[[], None]] = None) -> None:
    anim = cfg.get("popup_animation", "slide")
    if anim == "random":
        anim = random.choice(ANIMACOES)
    popup_w, popup_h = 340, 130
    steps = 18
    delay_ms = 22
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    margin = 15

    def done():
        root.geometry(f"{popup_w}x{popup_h}+{x1}+{y1}")
        root.update_idletasks()
        if callback:
            callback()

    if anim == "fade":
        try:
            root.attributes("-alpha", 0.0)
            root.geometry(f"{popup_w}x{popup_h}+{x1}+{y1}")
            root.update_idletasks()

            def step(n=0):
                n += 1
                alpha = n / steps
                if n >= steps:
                    root.attributes("-alpha", 1.0)
                    if callback:
                        callback()
                    return
                try:
                    root.attributes("-alpha", alpha)
                except tk.TclError:
                    if callback:
                        callback()
                    return
                root.after(delay_ms, lambda: step(n))
            root.after(50, lambda: step(0))
        except tk.TclError:
            done()

    elif anim == "slide":
        pos = cfg.get("popup_position", "top-right")
        if pos in ("top-left", "bottom-left"):
            root.geometry(f"1x{popup_h}+{x1}+{y1}")
            def slide(n=0):
                n += 1
                w_cur = max(1, int(popup_w * n / steps))
                root.geometry(f"{w_cur}x{popup_h}+{x1}+{y1}")
                root.update_idletasks()
                if n >= steps:
                    done()
                    return
                root.after(delay_ms, lambda: slide(n))
            root.after(50, lambda: slide(0))
        else:
            root.geometry(f"1x{popup_h}+{x1 + popup_w - 1}+{y1}")
            def slide(n=0):
                n += 1
                w_cur = max(1, int(popup_w * n / steps))
                x_cur = x1 + popup_w - w_cur
                root.geometry(f"{w_cur}x{popup_h}+{x_cur}+{y1}")
                root.update_idletasks()
                if n >= steps:
                    done()
                    return
                root.after(delay_ms, lambda: slide(n))
            root.after(50, lambda: slide(0))

    elif anim == "scale":
        root.geometry(f"1x1+{x1 + popup_w//2 - 1}+{y1 + popup_h//2 - 1}")
        def scale(n=0):
            n += 1
            t = n / steps
            if t >= 1:
                done()
                return
            w_cur = max(2, int(popup_w * t))
            h_cur = max(2, int(popup_h * t))
            x_cur = x1 + (popup_w - w_cur) // 2
            y_cur = y1 + (popup_h - h_cur) // 2
            root.geometry(f"{w_cur}x{h_cur}+{x_cur}+{y_cur}")
            root.update_idletasks()
            root.after(delay_ms, lambda: scale(n))
        root.after(50, lambda: scale(0))

    elif anim == "bounce":
        root.geometry(f"1x1+{x1 + popup_w//2 - 1}+{y1 + popup_h//2 - 1}")
        def scale(n=0):
            n += 1
            t = n / steps
            if t >= 1:
                done()
                return
            eased = _ease_out_bounce(t)
            w_cur = max(2, int(popup_w * eased))
            h_cur = max(2, int(popup_h * eased))
            x_cur = x1 + (popup_w - w_cur) // 2
            y_cur = y1 + (popup_h - h_cur) // 2
            root.geometry(f"{w_cur}x{h_cur}+{x_cur}+{y_cur}")
            root.update_idletasks()
            root.after(delay_ms, lambda: scale(n))
        root.after(50, lambda: scale(0))

    elif anim == "elastic":
        root.geometry(f"1x1+{x1 + popup_w//2 - 1}+{y1 + popup_h//2 - 1}")
        def scale(n=0):
            n += 1
            t = n / steps
            if t >= 1:
                done()
                return
            eased = max(0, min(1.0, _ease_out_elastic(t)))
            w_cur = max(2, int(popup_w * eased))
            h_cur = max(2, int(popup_h * eased))
            x_cur = x1 + (popup_w - w_cur) // 2
            y_cur = y1 + (popup_h - h_cur) // 2
            root.geometry(f"{w_cur}x{h_cur}+{x_cur}+{y_cur}")
            root.update_idletasks()
            root.after(delay_ms, lambda: scale(n))
        root.after(50, lambda: scale(0))

    elif anim == "slide-vertical":
        pos = cfg.get("popup_position", "top-right")
        if pos in ("top-left", "top-right"):
            start_y = -popup_h
        else:
            start_y = h + margin
        root.geometry(f"{popup_w}x{popup_h}+{x1}+{start_y}")
        def slide_v(n=0):
            n += 1
            t = n / steps
            if t >= 1:
                done()
                return
            y_cur = int(start_y + (y1 - start_y) * t)
            root.geometry(f"{popup_w}x{popup_h}+{x1}+{y_cur}")
            root.update_idletasks()
            root.after(delay_ms, lambda: slide_v(n))
        root.after(50, lambda: slide_v(0))

    elif anim == "drop":
        pos = cfg.get("popup_position", "top-right")
        if pos in ("top-left", "top-right"):
            start_y = -popup_h - 20
            def drop(n=0):
                n += 1
                t = n / steps
                if t >= 1:
                    done()
                    return
                eased = _ease_out_bounce(t)
                y_cur = int(start_y + (y1 - start_y) * eased)
                root.geometry(f"{popup_w}x{popup_h}+{x1}+{y_cur}")
                root.update_idletasks()
                root.after(delay_ms, lambda: drop(n))
            root.geometry(f"{popup_w}x{popup_h}+{x1}+{start_y}")
            root.after(50, lambda: drop(0))
        else:
            start_y = h + margin + 20
            def rise(n=0):
                n += 1
                t = n / steps
                if t >= 1:
                    done()
                    return
                eased = _ease_out_bounce(t)
                y_cur = int(start_y + (y1 - start_y) * eased)
                root.geometry(f"{popup_w}x{popup_h}+{x1}+{y_cur}")
                root.update_idletasks()
                root.after(delay_ms, lambda: rise(n))
            root.geometry(f"{popup_w}x{popup_h}+{x1}+{start_y}")
            root.after(50, lambda: rise(0))

    else:
        done()
