"""
Hidratar Popup - Lembrete para beber água
Suporta personalização via config.json (na mesma pasta do .exe)
Execute com --config para abrir as configurações.
"""

import os
import sys
import time
import json
import argparse
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont, filedialog
import pygame
import random

# ============ PATHS ============

def pasta_base():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

_config_path_override = None

def _dir_gravavel(pasta: str) -> bool:
    try:
        os.makedirs(pasta, exist_ok=True)
        teste = os.path.join(pasta, ".__waterpopup_write_test__")
        with open(teste, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(teste)
        return True
    except Exception:
        return False

def pasta_config():
    """
    Preferência:
    - se rodando como .exe: usa pasta do executável SE for gravável; senão, AppData do usuário
    - se rodando via Python: pasta do projeto (ao lado do .py) SE for gravável; senão, AppData do usuário
    """
    base = pasta_base()
    if _dir_gravavel(base):
        return base

    appdata = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    fallback = os.path.join(appdata, "WaterPopUp")
    os.makedirs(fallback, exist_ok=True)
    return fallback

def caminho_config():
    global _config_path_override
    if _config_path_override:
        return _config_path_override
    env_path = os.environ.get("WATERPOPUP_CONFIG_PATH")
    if env_path:
        return env_path
    return os.path.join(pasta_config(), "config.json")

def caminho_recurso(rel):
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = pasta_base()
    return os.path.join(base, rel)

def pasta_audios():
    externa = os.path.join(pasta_base(), "audios")
    if os.path.isdir(externa):
        return externa
    return caminho_recurso("audios")

# ============ PALETAS DE CORES ============

PALETAS = {
    "Pastel": [
        "#FFB6C1", "#87CEEB", "#98FB98", "#E6E6FA", "#FFDAB9",
        "#FFFFE0", "#DDA0DD", "#F0E68C", "#FFE4E1", "#E0FFFF",
        "#F5DEB3", "#D8BFD8", "#FAEBD7", "#F0FFF0", "#FFF0F5",
    ],
    "Vibrante": [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
        "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
        "#F8B500", "#00CED1", "#FF69B4", "#32CD32", "#FFD700",
    ],
    "Natureza": [
        "#2E8B57", "#3CB371", "#20B2AA", "#87CEEB", "#98FB98",
        "#90EE90", "#00FA9A", "#00CED1", "#48D1CC", "#AFEEEE",
        "#7CFC00", "#ADFF2F", "#9ACD32", "#6B8E23", "#556B2F",
    ],
    "Escuro": [
        "#2C3E50", "#34495E", "#1ABC9C", "#16A085", "#27AE60",
        "#2980B9", "#8E44AD", "#9B59B6", "#3498DB", "#2ECC71",
    ],
    "Clássico": [
        "light pink", "light blue", "light green", "lavender",
        "peach puff", "light yellow", "plum", "khaki",
        "misty rose", "alice blue", "honeydew", "lavender blush",
    ],
}

# ============ CONFIG ============

CONFIG_PADRAO = {
    "message": "Drink some water! 💧",
    "interval_minutes": 10,
    "popup_duration_seconds": 5,
    "stop_audio_on_close": True,
    "random_colors": True,
    "color_palette": "Pastel",
    "colors": PALETAS["Pastel"].copy(),
    "popup_animation": "slide",
    "popup_position": "top-right",
    "font_size": 14,
    "audio_mode": "random",
    "selected_audios": [],
    "control_window_title": "💧 Water Popup",
    "control_window_status": "Water Popup ativo",
    "control_window_hint": "Feche esta janela para encerrar os lembretes",
}

_config_cache = None
_config_mtime = 0
_lembretes_ativos = False
_lembrete_after_id = None
_proximo_lembrete_ts = None

def carregar_config():
    global _config_cache, _config_mtime
    path = caminho_config()
    if not os.path.exists(path):
        cfg_inicial = CONFIG_PADRAO.copy()
        salvar_config(cfg_inicial)
        return cfg_inicial

    try:
        mtime = os.path.getmtime(path)
        if mtime == _config_mtime and _config_cache:
            return _config_cache

        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        _config_cache = {**CONFIG_PADRAO, **cfg}
        if "color_palette" in cfg and cfg["color_palette"] in PALETAS:
            _config_cache["colors"] = PALETAS[cfg["color_palette"]].copy()
        _config_mtime = mtime
        return _config_cache
    except Exception:
        return CONFIG_PADRAO.copy()

def salvar_config(cfg):
    global _config_cache, _config_mtime
    path = caminho_config()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    # Mantém cache e mtime sincronizados com o último save
    _config_cache = {**CONFIG_PADRAO, **cfg}
    if _config_cache.get("color_palette") in PALETAS:
        _config_cache["colors"] = PALETAS[_config_cache["color_palette"]].copy()
    _config_mtime = os.path.getmtime(path)

# ============ ÁUDIO ============

pygame.mixer.init()

def listar_audios():
    p = pasta_audios()
    if not os.path.isdir(p):
        return []
    return [f for f in os.listdir(p) if f.lower().endswith((".wav", ".mp3", ".ogg"))]

def tocar_arquivo_audio(caminho):
    """Reproduz um arquivo específico (prévia na config ou lembrete)."""
    try:
        pygame.mixer.music.load(caminho)
        pygame.mixer.music.play()
    except Exception as e:
        raise RuntimeError(str(e)) from e

def tocar_som(cfg=None):
    if cfg is None:
        cfg = carregar_config()
    audios = listar_audios()
    if not audios:
        return

    if cfg.get("audio_mode") == "selected" and cfg.get("selected_audios"):
        validos = [a for a in cfg["selected_audios"] if a in audios]
        arquivo_escolhido = random.choice(validos) if validos else random.choice(audios)
    else:
        arquivo_escolhido = random.choice(audios)

    wav_path = os.path.join(pasta_audios(), arquivo_escolhido)
    try:
        tocar_arquivo_audio(wav_path)
    except Exception as e:
        print("Erro ao tocar som:", e)

def parar_som():
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass

def abrir_pasta_no_explorador(pasta):
    os.makedirs(pasta, exist_ok=True)
    pasta = os.path.normpath(pasta)
    if sys.platform == "win32":
        os.startfile(pasta)
    elif sys.platform == "darwin":
        subprocess.run(["open", pasta], check=False)
    else:
        subprocess.run(["xdg-open", pasta], check=False)

# ============ ANIMAÇÕES ============

_CANTOS_POPUP = ("top-right", "top-left", "bottom-right", "bottom-left")

def _resolver_posicao_popup(cfg):
    """Resolve 'random' para um canto concreto (cada chamada pode variar)."""
    c = dict(cfg)
    if c.get("popup_position") == "random":
        c["popup_position"] = random.choice(_CANTOS_POPUP)
    return c

def _pos_inicial(cfg, w, h, popup_w=300, popup_h=100):
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
    else:
        return w - popup_w - margin, margin

def _ease_out_elastic(t):
    """Easing: overshoot e settle (spring effect)."""
    if t <= 0:
        return 0
    if t >= 1:
        return 1
    p = 0.4
    return 2 ** (-10 * t) * ((t - p / 4) * (2 * 3.14159) / p) + 1

def _ease_out_bounce(t):
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

ANIMACOES = ["slide", "slide-vertical", "scale", "bounce", "elastic", "drop", "fade"]

def _animar_entrada(root, cfg, x1, y1, callback=None):
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

# ============ POPUP ============

def mostrar_popup(parent=None, cfg_override=None):
    base = cfg_override or carregar_config()
    cfg = _resolver_posicao_popup(base)
    tocar_som()

    root = tk.Toplevel(parent) if parent is not None else tk.Tk()
    root.title("Hidrate-se!")
    root.attributes("-topmost", True)
    root.overrideredirect(True)
    root.configure(bg="white")

    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    popup_w, popup_h = 340, 130
    x1, y1 = _pos_inicial(cfg, w, h, popup_w, popup_h)

    root.geometry(f"{popup_w}x{popup_h}+{x1}+{y1}")

    if cfg.get("random_colors", True):
        cores = cfg.get("colors", PALETAS["Pastel"])
        cor = random.choice(cores) if cores else "#87CEEB"
    else:
        cores = cfg.get("colors", PALETAS["Pastel"])
        cor = cores[0] if cores else "#87CEEB"

    msg = cfg.get("message", CONFIG_PADRAO["message"])
    duracao_ms = int(cfg.get("popup_duration_seconds", 12)) * 1000
    stop_audio = cfg.get("stop_audio_on_close", True)
    font_size = int(cfg.get("font_size", 14))

    lbl = tk.Label(
        root, text=msg, font=("Segoe UI", font_size, "bold"),
        bg=cor, fg="#1a1a2e", wraplength=300,
        cursor="hand2", relief="flat", padx=16, pady=16
    )
    lbl.pack(expand=True, fill="both")
    lbl.bind("<Button-1>", lambda e: fechar_popup())

    def fechar_popup():
        if stop_audio:
            parar_som()
        if root.winfo_exists():
            root.destroy()

    def agendar_fechar():
        root.after(duracao_ms, fechar_popup)

    _animar_entrada(root, cfg, x1, y1, agendar_fechar)
    if parent is None:
        root.mainloop()

def _agendar_proximo_lembrete(root, delay_ms):
    global _lembrete_after_id, _proximo_lembrete_ts
    _proximo_lembrete_ts = time.time() + (delay_ms / 1000.0)
    _lembrete_after_id = root.after(delay_ms, lambda: _mostrar_e_reagendar(root))

def _mostrar_e_reagendar(root):
    if not _lembretes_ativos or not root.winfo_exists():
        return
    mostrar_popup(parent=root)
    cfg = carregar_config()
    interval_ms = int(cfg.get("interval_minutes", 10)) * 60 * 1000
    _agendar_proximo_lembrete(root, max(1000, interval_ms))

# ============ JANELA PRINCIPAL (tema escuro) ============

COR_FUNDO = "#0f172a"
COR_CARD = "#111827"
COR_CARD_2 = "#1f2937"
COR_TEXTO = "#e5e7eb"
COR_SUBTEXTO = "#94a3b8"
COR_DESTAQUE = "#38bdf8"
COR_BOTAO = "#0ea5e9"
COR_BOTAO_HOVER = "#0284c7"

# Tema da janela de configuração (azul claro, legível)
CFG_FUNDO = "#dce6f5"
CFG_CARD = "#eef4fc"
CFG_CARD_INNER = "#e2ebf8"
CFG_TEXTO = "#1e3a5f"
CFG_SUB = "#5a6f8f"
CFG_ACCENT = "#2563eb"
CFG_ACCENT_HOVER = "#1d4ed8"
CFG_BORDER = "#b8cce8"

def abrir_configuracoes(parent=None):
    is_top_level = parent is not None
    root = tk.Toplevel(parent) if is_top_level else tk.Tk()
    root.title("💧 Hidratar — Configurações")
    root.geometry("880x760")
    root.minsize(560, 480)
    root.resizable(True, True)
    root.configure(bg=CFG_FUNDO)
    if is_top_level:
        root.transient(parent)
        root.grab_set()

    # Estilo (escopos separados para não afetar a janela principal)
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("CfgRoot.TFrame", background=CFG_FUNDO)
    style.configure("CfgCard.TLabelframe", background=CFG_CARD, foreground=CFG_TEXTO, borderwidth=1, relief="solid")
    style.configure("CfgCard.TLabelframe.Label", background=CFG_CARD, foreground=CFG_ACCENT, font=("Segoe UI", 11, "bold"))
    style.configure("CfgCard.TFrame", background=CFG_CARD)
    style.configure("CfgTFrame", background=CFG_FUNDO)
    style.configure("CfgTLabel", background=CFG_FUNDO, foreground=CFG_TEXTO, font=("Segoe UI", 10))
    style.configure("CfgCard.TLabel", background=CFG_CARD, foreground=CFG_TEXTO, font=("Segoe UI", 10))
    style.configure("Cfg.Subtle.TLabel", background=CFG_CARD, foreground=CFG_SUB, font=("Segoe UI", 9))
    style.configure("Cfg.TEntry", fieldbackground="white", foreground=CFG_TEXTO, insertcolor=CFG_TEXTO, borderwidth=1)
    style.configure("Cfg.TSpinbox", fieldbackground="white", foreground=CFG_TEXTO, borderwidth=1)
    style.configure("Cfg.TCheckbutton", background=CFG_CARD, foreground=CFG_TEXTO)
    style.configure("Cfg.TRadiobutton", background=CFG_CARD, foreground=CFG_TEXTO)
    style.map("Cfg.TCheckbutton", background=[("active", CFG_CARD)], foreground=[("active", CFG_TEXTO)])
    style.map("Cfg.TRadiobutton", background=[("active", CFG_CARD)], foreground=[("active", CFG_TEXTO)])
    style.configure("Cfg.Pri.TButton", font=("Segoe UI", 10, "bold"), padding=(16, 10), background=CFG_ACCENT, foreground="white", borderwidth=0)
    style.map("Cfg.Pri.TButton", background=[("active", CFG_ACCENT_HOVER)])
    style.configure("Cfg.Sec.TButton", font=("Segoe UI", 10), padding=(16, 10), background=CFG_CARD_INNER, foreground=CFG_TEXTO, borderwidth=0)
    style.map("Cfg.Sec.TButton", background=[("active", "#d0ddf0")])

    cfg = carregar_config()

    # Sem Canvas: no Windows, Canvas + formulário costuma ficar em branco. Abas + pack direto no root.
    main = tk.Frame(root, bg=CFG_FUNDO)
    main.pack(fill="both", expand=True, padx=14, pady=(10, 6))

    header = tk.Frame(main, bg=CFG_FUNDO)
    header.pack(fill="x", pady=(0, 10))
    tk.Label(
        header, text="Configurações",
        font=("Segoe UI", 18, "bold"), fg=CFG_TEXTO, bg=CFG_FUNDO
    ).pack(anchor="w")
    tk.Label(
        header,
        text="Personalize o lembrete de hidratação. As alterações são salvas no arquivo de configuração.",
        font=("Segoe UI", 9), fg=CFG_SUB, bg=CFG_FUNDO, wraplength=760, justify="left",
    ).pack(anchor="w", pady=(4, 0))

    nb = ttk.Notebook(main)
    nb.pack(fill="both", expand=True, pady=(0, 6))

    tab_geral = tk.Frame(nb, bg=CFG_FUNDO)
    tab_ap = tk.Frame(nb, bg=CFG_FUNDO)
    tab_aud = tk.Frame(nb, bg=CFG_FUNDO)
    nb.add(tab_geral, text="  Geral  ")
    nb.add(tab_ap, text="  Aparência  ")
    nb.add(tab_aud, text="  Áudio  ")

    # --- Seção: Mensagem ---
    f_msg = ttk.LabelFrame(tab_geral, text="  Mensagem  ", padding=16, style="CfgCard.TLabelframe")
    f_msg.pack(fill="x", pady=(0, 12))
    f_msg.columnconfigure(0, weight=1)

    msg_var = tk.StringVar(value=cfg.get("message", CONFIG_PADRAO["message"]))
    msg_entry = ttk.Entry(f_msg, textvariable=msg_var, style="Cfg.TEntry")
    msg_entry.grid(row=0, column=0, sticky="ew", pady=(4, 0))

    # --- Seção: Temporização ---
    f_temp = ttk.LabelFrame(tab_geral, text="  Temporização  ", padding=16, style="CfgCard.TLabelframe")
    f_temp.pack(fill="x", pady=(0, 0))
    f_temp.columnconfigure(0, weight=1)
    f_temp.columnconfigure(1, weight=1)

    interval_var = tk.StringVar(value=str(cfg.get("interval_minutes", 10)))
    duration_var = tk.StringVar(value=str(cfg.get("popup_duration_seconds", 12)))

    g_temp = ttk.Frame(f_temp, style="CfgCard.TFrame")
    g_temp.grid(row=0, column=0, columnspan=2, sticky="ew", pady=4)
    g_temp.columnconfigure(0, weight=1)
    g_temp.columnconfigure(1, weight=1)

    col_int = ttk.Frame(g_temp, style="CfgCard.TFrame")
    col_int.grid(row=0, column=0, sticky="ew", padx=(0, 8))
    ttk.Label(col_int, text="Intervalo entre lembretes (min)", style="CfgCard.TLabel").pack(anchor="w")
    ttk.Spinbox(col_int, textvariable=interval_var, from_=1, to=120, width=8, style="Cfg.TSpinbox").pack(anchor="w", pady=(4, 0))

    col_dur = ttk.Frame(g_temp, style="CfgCard.TFrame")
    col_dur.grid(row=0, column=1, sticky="ew", padx=(8, 0))
    ttk.Label(col_dur, text="Duração do popup na tela (seg)", style="CfgCard.TLabel").pack(anchor="w")
    ttk.Spinbox(col_dur, textvariable=duration_var, from_=3, to=60, width=8, style="Cfg.TSpinbox").pack(anchor="w", pady=(4, 0))

    stop_audio_var = tk.BooleanVar(value=cfg.get("stop_audio_on_close", True))
    ttk.Checkbutton(
        f_temp, text="Parar áudio ao fechar o popup (recomendado para áudios longos)",
        variable=stop_audio_var, style="Cfg.TCheckbutton"
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

    # --- Seção: Aparência ---
    f_ap = ttk.LabelFrame(tab_ap, text="  Aparência  ", padding=16, style="CfgCard.TLabelframe")
    f_ap.pack(fill="both", expand=True)
    f_ap.columnconfigure(0, weight=1)

    random_colors_var = tk.BooleanVar(value=cfg.get("random_colors", True))
    ttk.Checkbutton(f_ap, text="Cores aleatórias a cada popup", variable=random_colors_var, style="Cfg.TCheckbutton").grid(row=0, column=0, sticky="w")

    ttk.Label(f_ap, text="Paleta de cores", style="CfgCard.TLabel").grid(row=1, column=0, sticky="w", pady=(12, 4))
    palette_var = tk.StringVar(value=cfg.get("color_palette", "Pastel"))
    row_pal1 = ttk.Frame(f_ap, style="CfgCard.TFrame")
    row_pal1.grid(row=2, column=0, sticky="ew", pady=2)
    row_pal2 = ttk.Frame(f_ap, style="CfgCard.TFrame")
    row_pal2.grid(row=3, column=0, sticky="ew", pady=2)
    nomes_paletas = list(PALETAS.keys())
    for p in nomes_paletas[:3]:
        ttk.Radiobutton(row_pal1, text=p, variable=palette_var, value=p, style="Cfg.TRadiobutton").pack(side="left", padx=(0, 12))
    for p in nomes_paletas[3:]:
        ttk.Radiobutton(row_pal2, text=p, variable=palette_var, value=p, style="Cfg.TRadiobutton").pack(side="left", padx=(0, 12))

    ttk.Label(f_ap, text="Pré-visualização", style="CfgCard.TLabel").grid(row=4, column=0, sticky="w", pady=(12, 4))
    preview_frame = ttk.Frame(f_ap, style="CfgCard.TFrame")
    preview_frame.grid(row=5, column=0, sticky="ew", pady=4)

    def atualizar_preview():
        for w in preview_frame.winfo_children():
            w.destroy()
        cores = PALETAS.get(palette_var.get(), PALETAS["Pastel"])
        for c in cores[:12]:
            sw = tk.Frame(preview_frame, bg=CFG_BORDER, padx=1, pady=1)
            sw.pack(side="left", padx=3, pady=2)
            tk.Label(sw, text=" ", bg=c, width=3, height=1, relief="flat").pack()
    atualizar_preview()
    palette_var.trace_add("write", lambda *a: atualizar_preview())

    ttk.Label(f_ap, text="Animação de entrada", style="CfgCard.TLabel").grid(row=6, column=0, sticky="w", pady=(12, 4))
    anim_var = tk.StringVar(value=cfg.get("popup_animation", "slide"))
    anim_opts = [
        ("random", "Aleatória"),
        ("slide", "Deslizar"),
        ("slide-vertical", "Vertical"),
        ("scale", "Zoom"),
        ("bounce", "Bounce"),
        ("elastic", "Elástico"),
        ("drop", "Cair"),
        ("fade", "Fade"),
        ("none", "Nenhuma"),
    ]
    row_anim1 = ttk.Frame(f_ap, style="CfgCard.TFrame")
    row_anim1.grid(row=7, column=0, sticky="ew", pady=2)
    for opt, lbl in anim_opts[:5]:
        ttk.Radiobutton(row_anim1, text=lbl, variable=anim_var, value=opt, style="Cfg.TRadiobutton").pack(side="left", padx=(0, 10))
    row_anim2 = ttk.Frame(f_ap, style="CfgCard.TFrame")
    row_anim2.grid(row=8, column=0, sticky="ew", pady=2)
    for opt, lbl in anim_opts[5:]:
        ttk.Radiobutton(row_anim2, text=lbl, variable=anim_var, value=opt, style="Cfg.TRadiobutton").pack(side="left", padx=(0, 10))

    ttk.Label(f_ap, text="Posição na tela", style="CfgCard.TLabel").grid(row=9, column=0, sticky="w", pady=(14, 4))
    pos_saved = cfg.get("popup_position", "top-right")
    if pos_saved not in _CANTOS_POPUP + ("random",):
        pos_saved = "top-right"
    pos_var = tk.StringVar(value=pos_saved)
    row_pos0 = ttk.Frame(f_ap, style="CfgCard.TFrame")
    row_pos0.grid(row=10, column=0, sticky="ew", pady=2)
    ttk.Radiobutton(
        row_pos0, text="Aleatório (canto diferente a cada lembrete)",
        variable=pos_var, value="random", style="Cfg.TRadiobutton"
    ).pack(anchor="w")
    row_pos1 = ttk.Frame(f_ap, style="CfgCard.TFrame")
    row_pos1.grid(row=11, column=0, sticky="ew", pady=2)
    row_pos2 = ttk.Frame(f_ap, style="CfgCard.TFrame")
    row_pos2.grid(row=12, column=0, sticky="ew", pady=2)
    ttk.Radiobutton(row_pos1, text="Superior direito", variable=pos_var, value="top-right", style="Cfg.TRadiobutton").pack(side="left", padx=(0, 12))
    ttk.Radiobutton(row_pos1, text="Superior esquerdo", variable=pos_var, value="top-left", style="Cfg.TRadiobutton").pack(side="left", padx=(0, 12))
    ttk.Radiobutton(row_pos2, text="Inferior direito", variable=pos_var, value="bottom-right", style="Cfg.TRadiobutton").pack(side="left", padx=(0, 12))
    ttk.Radiobutton(row_pos2, text="Inferior esquerdo", variable=pos_var, value="bottom-left", style="Cfg.TRadiobutton").pack(side="left", padx=(0, 12))

    row_font = ttk.Frame(f_ap, style="CfgCard.TFrame")
    row_font.grid(row=13, column=0, sticky="ew", pady=(12, 0))
    ttk.Label(row_font, text="Tamanho da fonte", style="CfgCard.TLabel").pack(side="left", padx=(0, 12))
    font_var = tk.StringVar(value=str(cfg.get("font_size", 14)))
    ttk.Spinbox(row_font, textvariable=font_var, from_=10, to=24, width=6, style="Cfg.TSpinbox").pack(side="left")

    # --- Seção: Áudio ---
    f_aud = ttk.LabelFrame(tab_aud, text="  Áudio  ", padding=16, style="CfgCard.TLabelframe")
    f_aud.pack(fill="both", expand=True)
    f_aud.columnconfigure(0, weight=1)
    f_aud.rowconfigure(3, weight=1)

    audio_mode_var = tk.StringVar(value=cfg.get("audio_mode", "random"))
    ttk.Radiobutton(f_aud, text="Aleatório — todos os arquivos da pasta audios", variable=audio_mode_var, value="random", style="Cfg.TRadiobutton").grid(row=0, column=0, sticky="w", pady=2)
    ttk.Radiobutton(f_aud, text="Apenas os selecionados na lista abaixo (Ctrl+clique para vários)", variable=audio_mode_var, value="selected", style="Cfg.TRadiobutton").grid(row=1, column=0, sticky="w", pady=2)

    ttk.Label(
        f_aud,
        text="Lista de arquivos — use a barra de rolagem à direita se houver mais itens.",
        style="Cfg.Subtle.TLabel",
    ).grid(row=2, column=0, sticky="w", pady=(6, 2))

    list_wrap = tk.Frame(f_aud, bg=CFG_CARD)
    list_wrap.grid(row=3, column=0, sticky="nsew", pady=4)
    list_wrap.columnconfigure(0, weight=1)
    list_wrap.rowconfigure(0, weight=1)

    sb_aud = tk.Scrollbar(list_wrap, orient="vertical", width=16)
    lb = tk.Listbox(
        list_wrap,
        selectmode="extended",
        height=16,
        bg="white",
        fg=CFG_TEXTO,
        selectbackground=CFG_ACCENT,
        selectforeground="white",
        font=("Segoe UI", 10),
        highlightthickness=1,
        highlightbackground=CFG_BORDER,
        relief="solid",
        activestyle="dotbox",
        yscrollcommand=sb_aud.set,
    )
    sb_aud.config(command=lb.yview)
    lb.grid(row=0, column=0, sticky="nsew")
    sb_aud.grid(row=0, column=1, sticky="ns")

    selected_audios = cfg.get("selected_audios", [])

    def recarregar_lista_audios():
        sel_nomes = {lb.get(i) for i in lb.curselection()}
        lb.delete(0, tk.END)
        for a in listar_audios():
            lb.insert(tk.END, a)
        for i in range(lb.size()):
            if lb.get(i) in sel_nomes:
                lb.selection_set(i)

    for a in listar_audios():
        lb.insert(tk.END, a)
    for i in range(lb.size()):
        if lb.get(i) in selected_audios:
            lb.selection_set(i)

    def reproduzir_selecionado():
        sel = lb.curselection()
        if not sel:
            messagebox.showinfo("Áudio", "Selecione um arquivo na lista (ou dê duplo clique).")
            return
        nome = lb.get(sel[0])
        path = os.path.join(pasta_audios(), nome)
        if not os.path.isfile(path):
            messagebox.showerror("Áudio", f"Arquivo não encontrado:\n{path}")
            return
        try:
            tocar_arquivo_audio(path)
        except Exception as e:
            messagebox.showerror("Áudio", f"Não foi possível reproduzir:\n{e}")

    def on_duplo_clique_aud(event):
        idx = lb.nearest(event.y)
        if 0 <= idx < lb.size():
            lb.selection_clear(0, tk.END)
            lb.selection_set(idx)
            lb.activate(idx)
            nome = lb.get(idx)
            path = os.path.join(pasta_audios(), nome)
            if os.path.isfile(path):
                try:
                    tocar_arquivo_audio(path)
                except Exception as e:
                    messagebox.showerror("Áudio", f"Não foi possível reproduzir:\n{e}")

    lb.bind("<Double-Button-1>", on_duplo_clique_aud)

    def adicionar_audios_explorer():
        paths = filedialog.askopenfilenames(
            parent=root,
            title="Copiar áudios para a pasta do app",
            filetypes=[
                ("Áudio", "*.wav *.mp3 *.ogg"),
                ("Wave", "*.wav"),
                ("MP3", "*.mp3"),
                ("Ogg", "*.ogg"),
                ("Todos", "*.*"),
            ],
        )
        if not paths:
            return
        dest = pasta_audios()
        os.makedirs(dest, exist_ok=True)
        copiados = 0
        ignorados = 0
        for src in paths:
            nome = os.path.basename(src)
            if not nome.lower().endswith((".wav", ".mp3", ".ogg")):
                ignorados += 1
                continue
            dst = os.path.join(dest, nome)
            try:
                if os.path.exists(dst):
                    if not messagebox.askyesno(
                        "Substituir?",
                        f'Já existe "{nome}" na pasta audios.\n\nSubstituir pelo arquivo escolhido?',
                    ):
                        continue
                shutil.copy2(src, dst)
                copiados += 1
            except Exception as e:
                messagebox.showerror("Copiar", f"{nome}\n{e}")
        recarregar_lista_audios()
        msg = f"Arquivos copiados: {copiados}."
        if ignorados:
            msg += f"\nIgnorados (use .wav, .mp3 ou .ogg): {ignorados}."
        messagebox.showinfo("Áudios", msg)

    def abrir_pasta_audios_cmd():
        try:
            abrir_pasta_no_explorador(pasta_audios())
        except Exception as e:
            messagebox.showerror("Pasta", str(e))

    aud_actions = tk.Frame(f_aud, bg=CFG_CARD)
    aud_actions.grid(row=4, column=0, sticky="ew", pady=(10, 4))
    ttk.Button(aud_actions, text="▶ Ouvir seleção", command=reproduzir_selecionado, style="Cfg.Sec.TButton").pack(side="left", padx=(0, 6))
    ttk.Button(aud_actions, text="■ Parar som", command=parar_som, style="Cfg.Sec.TButton").pack(side="left", padx=6)
    ttk.Button(aud_actions, text="+ Adicionar arquivos…", command=adicionar_audios_explorer, style="Cfg.Sec.TButton").pack(side="left", padx=6)
    ttk.Button(aud_actions, text="Abrir pasta no Explorer", command=abrir_pasta_audios_cmd, style="Cfg.Sec.TButton").pack(side="left", padx=6)

    ttk.Label(
        f_aud,
        text="Dica: duplo clique em um item para ouvir a prévia.",
        style="Cfg.Subtle.TLabel",
    ).grid(row=5, column=0, sticky="w", pady=(2, 0))

    ttk.Label(f_aud, text="Pasta: " + pasta_audios(), style="Cfg.Subtle.TLabel").grid(row=6, column=0, sticky="w", pady=(6, 0))

    # --- Botões ---
    btn_frame = ttk.Frame(root, style="CfgRoot.TFrame")
    btn_frame.pack(fill="x", padx=14, pady=(0, 14))

    def testar():
        def _mostrar_popup_teste():
            cfg_teste = {
                "message": msg_var.get().strip() or "Teste! 💧",
                "random_colors": random_colors_var.get(),
                "colors": PALETAS.get(palette_var.get(), PALETAS["Pastel"]),
                "popup_animation": anim_var.get(),
                "popup_position": pos_var.get(),
                "font_size": int(font_var.get() or 14),
                "stop_audio_on_close": stop_audio_var.get(),
                "popup_duration_seconds": 4,
                "audio_mode": audio_mode_var.get(),
                "selected_audios": [lb.get(i) for i in lb.curselection()],
            }
            cfg_anim = _resolver_posicao_popup(cfg_teste)
            tocar_som(cfg_teste)

            win = tk.Toplevel(root)
            win.overrideredirect(True)
            win.attributes("-topmost", True)
            win.configure(bg="white")
            w, h = win.winfo_screenwidth(), win.winfo_screenheight()
            popup_w, popup_h = 340, 130
            x1, y1 = _pos_inicial(cfg_anim, w, h, popup_w, popup_h)
            win.geometry(f"{popup_w}x{popup_h}+{x1}+{y1}")

            if cfg_teste.get("random_colors", True):
                cor = random.choice(cfg_teste.get("colors", PALETAS["Pastel"]))
            else:
                cores = cfg_teste.get("colors", PALETAS["Pastel"])
                cor = cores[0] if cores else "#87CEEB"

            lbl = tk.Label(win, text=cfg_teste["message"], font=("Segoe UI", cfg_teste["font_size"], "bold"),
                          bg=cor, fg="#1a1a2e", wraplength=300, cursor="hand2", relief="flat", padx=16, pady=16)
            lbl.pack(expand=True, fill="both")

            def fechar():
                if cfg_teste.get("stop_audio_on_close", True):
                    parar_som()
                win.destroy()

            lbl.bind("<Button-1>", lambda e: fechar())
            duracao_ms = 4000

            def agendar_fechar():
                win.after(duracao_ms, fechar)

            _animar_entrada(win, cfg_anim, x1, y1, agendar_fechar)
        root.after(100, _mostrar_popup_teste)

    def salvar():
        try:
            interval = int(interval_var.get())
            duration = int(duration_var.get())
            fs = int(font_var.get())
        except ValueError:
            messagebox.showerror("Erro", "Preencha números válidos em intervalo, duração e fonte.")
            return

        sel_idx = lb.curselection()
        selected = [lb.get(i) for i in sel_idx]

        novo_cfg = {
            "message": msg_var.get().strip() or CONFIG_PADRAO["message"],
            "interval_minutes": max(1, min(120, interval)),
            "popup_duration_seconds": max(3, min(60, duration)),
            "stop_audio_on_close": stop_audio_var.get(),
            "random_colors": random_colors_var.get(),
            "color_palette": palette_var.get(),
            "colors": PALETAS.get(palette_var.get(), PALETAS["Pastel"]).copy(),
            "popup_animation": anim_var.get(),
            "popup_position": pos_var.get(),
            "font_size": max(10, min(24, fs)),
            "audio_mode": audio_mode_var.get(),
            "selected_audios": selected,
        }
        salvar_config(novo_cfg)
        messagebox.showinfo("Salvo", "Configurações salvas! As mudanças valerão no próximo lembrete.")
        root.destroy()

    ttk.Button(btn_frame, text="Testar popup", command=testar, style="Cfg.Sec.TButton").pack(side="left", padx=4)
    ttk.Button(btn_frame, text="Salvar", command=salvar, style="Cfg.Pri.TButton").pack(side="right", padx=4)

    if is_top_level:
        parent.wait_window(root)
    else:
        root.mainloop()

# ============ JANELA PRINCIPAL ============

def _iniciar_lembretes(root):
    global _lembretes_ativos
    if _lembretes_ativos:
        return False
    _lembretes_ativos = True
    _agendar_proximo_lembrete(root, 1000)
    return True

def _parar_lembretes(root=None):
    global _lembretes_ativos, _lembrete_after_id, _proximo_lembrete_ts
    estava_ativo = _lembretes_ativos
    _lembretes_ativos = False
    if root is not None and _lembrete_after_id is not None:
        try:
            root.after_cancel(_lembrete_after_id)
        except Exception:
            pass
    _lembrete_after_id = None
    _proximo_lembrete_ts = None
    return estava_ativo

def janela_app():
    """Janela principal do app para configurar e controlar lembretes."""
    cfg = carregar_config()
    root = tk.Tk()
    root.title(cfg.get("control_window_title", "💧 Water Popup"))
    root.geometry("560x330")
    root.minsize(520, 300)
    root.resizable(True, True)
    root.configure(bg=COR_FUNDO)
    root.attributes("-topmost", False)

    container = tk.Frame(root, bg=COR_FUNDO, padx=18, pady=16)
    container.pack(fill="both", expand=True)

    card = tk.Frame(container, bg=COR_CARD, padx=18, pady=14, bd=0, highlightthickness=0)
    card.pack(fill="both", expand=True)

    tk.Label(
        card,
        text=cfg.get("control_window_status", "Water Popup ativo"),
        font=("Segoe UI", 14, "bold"),
        fg=COR_TEXTO,
        bg=COR_CARD,
    ).pack(anchor="w")
    tk.Label(
        card,
        text=cfg.get("control_window_hint", "Feche esta janela para encerrar os lembretes"),
        font=("Segoe UI", 9),
        fg=COR_SUBTEXTO,
        bg=COR_CARD,
    ).pack(anchor="w", pady=(2, 10))

    status_var = tk.StringVar(value="Lembretes: iniciando...")
    timer_var = tk.StringVar(value="Próximo lembrete em: --:--")
    tk.Label(
        card, textvariable=status_var,
        font=("Segoe UI", 10, "bold"), fg=COR_DESTAQUE, bg=COR_CARD
    ).pack(anchor="w")
    tk.Label(
        card, textvariable=timer_var,
        font=("Consolas", 11), fg=COR_TEXTO, bg=COR_CARD
    ).pack(anchor="w", pady=(4, 10))
    tk.Label(
        card,
        text="Config em uso: " + caminho_config(),
        font=("Segoe UI", 8),
        fg=COR_SUBTEXTO,
        bg=COR_CARD,
        wraplength=500,
        justify="left",
    ).pack(anchor="w", pady=(0, 12))

    btns = tk.Frame(card, bg=COR_CARD)
    btns.pack(anchor="w")

    def _formatar_tempo(segundos):
        segundos = max(0, int(segundos))
        m, s = divmod(segundos, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def atualizar_status():
        status_var.set("Lembretes: ativos" if _lembretes_ativos else "Lembretes: pausados")
        if _lembretes_ativos and _proximo_lembrete_ts:
            restante = _proximo_lembrete_ts - time.time()
            timer_var.set(f"Próximo lembrete em: {_formatar_tempo(restante)}")
        else:
            timer_var.set("Próximo lembrete em: --:--")
        root.after(1000, atualizar_status)

    def abrir_cfg():
        estava_ativo = _lembretes_ativos
        abrir_configuracoes(root)
        if estava_ativo:
            _parar_lembretes(root)
            _iniciar_lembretes(root)

    def testar_agora():
        mostrar_popup(parent=root)

    def iniciar():
        _iniciar_lembretes(root)

    def pausar():
        _parar_lembretes(root)

    tk.Button(
        btns, text="Configurar", width=14, command=abrir_cfg,
        bg=COR_CARD_2, fg=COR_TEXTO, activebackground="#334155", activeforeground=COR_TEXTO, relief="flat"
    ).grid(row=0, column=0, padx=4, pady=4)
    tk.Button(
        btns, text="Testar agora", width=14, command=testar_agora,
        bg=COR_CARD_2, fg=COR_TEXTO, activebackground="#334155", activeforeground=COR_TEXTO, relief="flat"
    ).grid(row=0, column=1, padx=4, pady=4)
    tk.Button(
        btns, text="Iniciar", width=14, command=iniciar,
        bg=COR_BOTAO, fg="white", activebackground=COR_BOTAO_HOVER, activeforeground="white", relief="flat"
    ).grid(row=1, column=0, padx=4, pady=4)
    tk.Button(
        btns, text="Pausar", width=14, command=pausar,
        bg=COR_CARD_2, fg=COR_TEXTO, activebackground="#334155", activeforeground=COR_TEXTO, relief="flat"
    ).grid(row=1, column=1, padx=4, pady=4)

    def ao_fechar_app():
        _parar_lembretes(root)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", ao_fechar_app)
    _iniciar_lembretes(root)
    atualizar_status()
    root.mainloop()

# ============ MAIN ============

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--config", "-c", action="store_true", help="Abrir janela de configurações")
    parser.add_argument("--set", action="append", default=[], help="Define config: chave=valor (pode repetir)")
    parser.add_argument("--config-path", default=None, help="Caminho do config.json (opcional)")
    parser.add_argument("--print-config-path", action="store_true", help="Mostra onde o config está sendo usado")
    parser.add_argument("--print-config", action="store_true", help="Imprime o config atual e sai")
    args = parser.parse_args()

    if args.config_path:
        _config_path_override = args.config_path

    if args.print_config_path:
        print(caminho_config())
        sys.exit(0)

    if args.print_config:
        print(json.dumps(carregar_config(), indent=2, ensure_ascii=False))
        sys.exit(0)

    if args.set:
        atual = carregar_config()

        def parse_val(s: str):
            raw = s.strip()
            low = raw.lower()
            if low in ("true", "false"):
                return low == "true"
            # JSON (lista/objeto/número/string com aspas)
            if (raw.startswith("{") and raw.endswith("}")) or (raw.startswith("[") and raw.endswith("]")):
                try:
                    return json.loads(raw)
                except Exception:
                    return raw
            try:
                if "." in raw:
                    return float(raw)
                return int(raw)
            except Exception:
                return raw

        updates = {}
        for item in args.set:
            if "=" not in item:
                raise SystemExit(f"--set inválido: {item}. Use chave=valor")
            k, v = item.split("=", 1)
            updates[k.strip()] = parse_val(v)

        salvar_config({**atual, **updates})
        print("OK: config atualizado em", caminho_config())
        sys.exit(0)

    if args.config:
        abrir_configuracoes()
        sys.exit(0)

    janela_app()
