"""
Hidratar Popup - Lembrete para beber água
Suporta personalização via config.json (na mesma pasta do .exe)
Execute com --config para abrir as configurações.
"""

import os
import sys
import time
import json
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
from threading import Thread
import pygame
import random

# ============ PATHS ============

def pasta_base():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def caminho_config():
    return os.path.join(pasta_base(), "config.json")

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
    "popup_duration_seconds": 12,
    "stop_audio_on_close": True,
    "random_colors": True,
    "color_palette": "Pastel",
    "colors": PALETAS["Pastel"].copy(),
    "popup_animation": "slide",
    "popup_position": "top-right",
    "font_size": 14,
    "audio_mode": "random",
    "selected_audios": [],
}

_config_cache = None
_config_mtime = 0

def carregar_config():
    global _config_cache, _config_mtime
    path = caminho_config()
    if not os.path.exists(path):
        salvar_config(CONFIG_PADRAO)
        return CONFIG_PADRAO.copy()

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
    path = caminho_config()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    global _config_mtime
    _config_mtime = os.path.getmtime(path)

# ============ ÁUDIO ============

pygame.mixer.init()

def listar_audios():
    p = pasta_audios()
    if not os.path.isdir(p):
        return []
    return [f for f in os.listdir(p) if f.lower().endswith((".wav", ".mp3", ".ogg"))]

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
        pygame.mixer.music.load(wav_path)
        pygame.mixer.music.play()
    except Exception as e:
        print("Erro ao tocar som:", e)

def parar_som():
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass

# ============ ANIMAÇÕES ============

def _pos_inicial(cfg, w, h, popup_w=340, popup_h=130):
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

def mostrar_popup():
    cfg = carregar_config()
    tocar_som()

    root = tk.Tk()
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
        root.destroy()

    def agendar_fechar():
        root.after(duracao_ms, fechar_popup)

    _animar_entrada(root, cfg, x1, y1, agendar_fechar)
    root.mainloop()

def loop_lembretes():
    while True:
        mostrar_popup()
        cfg = carregar_config()
        interval = int(cfg.get("interval_minutes", 10)) * 60
        time.sleep(interval)

# ============ JANELA DE CONFIGURAÇÕES ============

COR_FUNDO = "#1a1a2e"
COR_CARD = "#16213e"
COR_TEXTO = "#eaeaea"
COR_DESTAQUE = "#0f3460"
COR_BOTAO = "#e94560"
COR_BOTAO_HOVER = "#ff6b6b"

def abrir_configuracoes():
    root = tk.Tk()
    root.title("💧 Hidratar - Configurações")
    root.geometry("560x680")
    root.resizable(True, True)
    root.configure(bg=COR_FUNDO)

    # Estilo
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame", background=COR_FUNDO)
    style.configure("TLabel", background=COR_FUNDO, foreground=COR_TEXTO, font=("Segoe UI", 10))
    style.configure("TLabelframe", background=COR_CARD, foreground=COR_TEXTO)
    style.configure("TLabelframe.Label", background=COR_CARD, foreground="#00d9ff", font=("Segoe UI", 11, "bold"))
    style.configure("TButton", font=("Segoe UI", 10), padding=8)
    style.map("TButton", background=[("active", COR_BOTAO_HOVER)])
    style.configure("TEntry", fieldbackground=COR_CARD, foreground=COR_TEXTO, insertcolor=COR_TEXTO)
    style.configure("TCheckbutton", background=COR_FUNDO, foreground=COR_TEXTO)
    style.configure("TRadiobutton", background=COR_FUNDO, foreground=COR_TEXTO)

    cfg = carregar_config()

    # Container com scroll
    canvas = tk.Canvas(root, bg=COR_FUNDO, highlightthickness=0)
    scrollbar = ttk.Scrollbar(root)
    scroll_frame = ttk.Frame(canvas)

    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.configure(command=canvas.yview)

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    root.bind("<MouseWheel>", _on_mousewheel)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # --- Seção: Mensagem ---
    f_msg = ttk.LabelFrame(scroll_frame, text="  ✏️  Mensagem  ", padding=12)
    f_msg.pack(fill="x", padx=16, pady=8)

    msg_var = tk.StringVar(value=cfg.get("message", CONFIG_PADRAO["message"]))
    msg_entry = ttk.Entry(f_msg, textvariable=msg_var, width=55)
    msg_entry.pack(fill="x", pady=4)

    # --- Seção: Temporização ---
    f_temp = ttk.LabelFrame(scroll_frame, text="  ⏱️  Temporização  ", padding=12)
    f_temp.pack(fill="x", padx=16, pady=8)

    row1 = ttk.Frame(f_temp)
    row1.pack(fill="x", pady=4)
    ttk.Label(row1, text="Intervalo (min):").pack(side="left", padx=(0, 8))
    interval_var = tk.StringVar(value=str(cfg.get("interval_minutes", 10)))
    ttk.Spinbox(row1, textvariable=interval_var, from_=1, to=120, width=6).pack(side="left", padx=4)
    ttk.Label(row1, text="Duração popup (seg):").pack(side="left", padx=(16, 8))
    duration_var = tk.StringVar(value=str(cfg.get("popup_duration_seconds", 12)))
    ttk.Spinbox(row1, textvariable=duration_var, from_=3, to=60, width=6).pack(side="left", padx=4)

    stop_audio_var = tk.BooleanVar(value=cfg.get("stop_audio_on_close", True))
    ttk.Checkbutton(f_temp, text="Parar áudio quando o popup fechar (recomendado se o áudio for longo)", variable=stop_audio_var).pack(anchor="w", pady=4)

    # --- Seção: Aparência ---
    f_ap = ttk.LabelFrame(scroll_frame, text="  🎨  Aparência  ", padding=12)
    f_ap.pack(fill="x", padx=16, pady=8)

    random_colors_var = tk.BooleanVar(value=cfg.get("random_colors", True))
    ttk.Checkbutton(f_ap, text="Cores aleatórias a cada popup", variable=random_colors_var).pack(anchor="w", pady=2)

    row_pal = ttk.Frame(f_ap)
    row_pal.pack(fill="x", pady=6)
    ttk.Label(row_pal, text="Paleta:").pack(side="left", padx=(0, 8))
    palette_var = tk.StringVar(value=cfg.get("color_palette", "Pastel"))
    for p in PALETAS:
        ttk.Radiobutton(row_pal, text=p, variable=palette_var, value=p).pack(side="left", padx=4)

    ttk.Label(f_ap, text="Preview das cores:").pack(anchor="w", pady=(8, 4))
    preview_frame = ttk.Frame(f_ap)
    preview_frame.pack(fill="x", pady=4)

    def atualizar_preview():
        for w in preview_frame.winfo_children():
            w.destroy()
        cores = PALETAS.get(palette_var.get(), PALETAS["Pastel"])
        for c in cores[:12]:
            tk.Label(preview_frame, text=" ", bg=c, width=2, relief="flat", cursor="hand2").pack(side="left", padx=1, pady=2)
    atualizar_preview()
    palette_var.trace_add("write", lambda *a: atualizar_preview())

    ttk.Label(f_ap, text="Animação:").pack(anchor="w", pady=(6, 4))
    anim_var = tk.StringVar(value=cfg.get("popup_animation", "slide"))
    anim_opts = [
        ("random", "Aleatória"),
        ("slide", "Deslizar"),
        ("slide-vertical", "Deslizar vertical"),
        ("scale", "Zoom"),
        ("bounce", "Bounce"),
        ("elastic", "Elástico"),
        ("drop", "Cair"),
        ("fade", "Fade"),
        ("none", "Nenhuma"),
    ]
    row_anim1 = ttk.Frame(f_ap)
    row_anim1.pack(fill="x", pady=2)
    for opt, lbl in anim_opts[:4]:
        ttk.Radiobutton(row_anim1, text=lbl, variable=anim_var, value=opt).pack(side="left", padx=4)
    row_anim2 = ttk.Frame(f_ap)
    row_anim2.pack(fill="x", pady=2)
    for opt, lbl in anim_opts[4:]:
        ttk.Radiobutton(row_anim2, text=lbl, variable=anim_var, value=opt).pack(side="left", padx=4)

    row_pos = ttk.Frame(f_ap)
    row_pos.pack(fill="x", pady=4)
    ttk.Label(row_pos, text="Posição:").pack(side="left", padx=(0, 8))
    pos_var = tk.StringVar(value=cfg.get("popup_position", "top-right"))
    for opt, lbl in [("top-right", "Canto superior direito"), ("top-left", "Canto superior esquerdo"),
                     ("bottom-right", "Canto inferior direito"), ("bottom-left", "Canto inferior esquerdo")]:
        ttk.Radiobutton(row_pos, text=lbl, variable=pos_var, value=opt).pack(side="left", padx=4)

    row_font = ttk.Frame(f_ap)
    row_font.pack(fill="x", pady=4)
    ttk.Label(row_font, text="Tamanho da fonte:").pack(side="left", padx=(0, 8))
    font_var = tk.StringVar(value=str(cfg.get("font_size", 14)))
    ttk.Spinbox(row_font, textvariable=font_var, from_=10, to=24, width=4).pack(side="left", padx=4)

    # --- Seção: Áudio ---
    f_aud = ttk.LabelFrame(scroll_frame, text="  🔊  Áudio  ", padding=12)
    f_aud.pack(fill="x", padx=16, pady=8)

    audio_mode_var = tk.StringVar(value=cfg.get("audio_mode", "random"))
    ttk.Radiobutton(f_aud, text="Aleatório (todos da pasta audios)", variable=audio_mode_var, value="random").pack(anchor="w", pady=2)
    ttk.Radiobutton(f_aud, text="Apenas os selecionados:", variable=audio_mode_var, value="selected").pack(anchor="w", pady=2)

    audios_disponiveis = listar_audios()
    selected_audios = cfg.get("selected_audios", [])

    lb_frame = ttk.Frame(f_aud)
    lb_frame.pack(fill="both", expand=True, pady=6)
    lb = tk.Listbox(lb_frame, selectmode="extended", height=5, bg=COR_CARD, fg=COR_TEXTO,
                    selectbackground=COR_BOTAO, selectforeground="white", font=("Segoe UI", 9),
                    highlightthickness=0, relief="flat")
    lb.pack(side="left", fill="both", expand=True)
    for a in audios_disponiveis:
        lb.insert("end", a)
    for i, a in enumerate(audios_disponiveis):
        if a in selected_audios:
            lb.selection_set(i)

    ttk.Label(lb_frame, text="Ctrl+clique para\nselecionar vários").pack(side="left", padx=8)

    ttk.Label(f_aud, text="Pasta: " + pasta_audios(), font=("Segoe UI", 8), foreground="gray").pack(anchor="w", pady=2)

    # --- Botões ---
    btn_frame = ttk.Frame(scroll_frame)
    btn_frame.pack(fill="x", padx=16, pady=16)

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
                "selected_audios": [audios_disponiveis[i] for i in lb.curselection()] if audios_disponiveis else [],
            }
            tocar_som(cfg_teste)

            win = tk.Toplevel(root)
            win.overrideredirect(True)
            win.attributes("-topmost", True)
            win.configure(bg="white")
            w, h = win.winfo_screenwidth(), win.winfo_screenheight()
            popup_w, popup_h = 340, 130
            x1, y1 = _pos_inicial(cfg_teste, w, h, popup_w, popup_h)
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

            _animar_entrada(win, cfg_teste, x1, y1, agendar_fechar)
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
        selected = [audios_disponiveis[i] for i in sel_idx] if audios_disponiveis else []

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

    ttk.Button(btn_frame, text="👁️ Testar popup", command=testar).pack(side="left", padx=4)
    ttk.Button(btn_frame, text="💾 Salvar", command=salvar).pack(side="left", padx=4)

    root.mainloop()

# ============ MAIN ============

if __name__ == "__main__":
    if "--config" in sys.argv or "-c" in sys.argv:
        abrir_configuracoes()
        sys.exit(0)

    Thread(target=loop_lembretes, daemon=True).start()
    while True:
        time.sleep(1)
