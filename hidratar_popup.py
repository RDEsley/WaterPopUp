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
    """Pasta onde está o exe (ou o script) - onde ficam config e audios externos."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def caminho_config():
    return os.path.join(pasta_base(), "config.json")

def caminho_recurso(rel):
    """Localiza arquivo dentro do bundle PyInstaller ou na pasta do projeto."""
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = pasta_base()
    return os.path.join(base, rel)

def pasta_audios():
    """Prefere audios ao lado do exe; senão usa os do bundle."""
    externa = os.path.join(pasta_base(), "audios")
    if os.path.isdir(externa):
        return externa
    return caminho_recurso("audios")

# ============ CONFIG ============

CONFIG_PADRAO = {
    "message": "Drink some water! 💧",
    "interval_minutes": 10,
    "popup_duration_seconds": 12,
    "random_colors": True,
    "colors": [
        "light pink", "light blue", "light green", "lavender",
        "peach puff", "light yellow", "plum", "khaki",
        "#FFB6C1", "#87CEEB", "#98FB98", "#E6E6FA",
        "#FFDAB9", "#FFFFE0", "#DDA0DD", "#F0E68C"
    ],
    "audio_mode": "random",  # "random" ou "selected"
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

def tocar_som():
    cfg = carregar_config()
    audios = listar_audios()
    if not audios:
        return

    if cfg.get("audio_mode") == "selected" and cfg.get("selected_audios"):
        validos = [a for a in cfg["selected_audios"] if a in audios]
        if validos:
            arquivo_escolhido = random.choice(validos)
        else:
            arquivo_escolhido = random.choice(audios)
    else:
        arquivo_escolhido = random.choice(audios)

    wav_path = os.path.join(pasta_audios(), arquivo_escolhido)
    try:
        pygame.mixer.music.load(wav_path)
        pygame.mixer.music.play()
    except Exception as e:
        print("Erro ao tocar som:", e)

# ============ POPUP ============

def mostrar_popup():
    cfg = carregar_config()
    tocar_som()

    root = tk.Tk()
    root.title("Hidrate-se!")
    root.attributes("-topmost", True)
    root.overrideredirect(True)

    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"320x120+{w-330}+10")

    if cfg.get("random_colors", True):
        cores = cfg.get("colors", CONFIG_PADRAO["colors"])
        cor = random.choice(cores)
    else:
        cores = cfg.get("colors", CONFIG_PADRAO["colors"])
        cor = cores[0] if cores else "light blue"

    msg = cfg.get("message", CONFIG_PADRAO["message"])
    duracao = int(cfg.get("popup_duration_seconds", 12)) * 1000

    tk.Label(
        root, text=msg, font=("Sans Serif", 14),
        bg=cor, fg="black", wraplength=280
    ).pack(expand=True, fill="both", padx=8, pady=8)

    root.after(duracao, root.destroy)
    root.mainloop()

def loop_lembretes():
    while True:
        mostrar_popup()
        cfg = carregar_config()
        interval = int(cfg.get("interval_minutes", 10)) * 60
        time.sleep(interval)

# ============ JANELA DE CONFIGURAÇÕES ============

def abrir_configuracoes():
    root = tk.Tk()
    root.title("Hidratar - Configurações")
    root.geometry("480x520")
    root.resizable(True, True)

    cfg = carregar_config()

    # Mensagem
    ttk.Label(root, text="Mensagem:").pack(anchor="w", padx=12, pady=(12, 2))
    msg_var = tk.StringVar(value=cfg.get("message", CONFIG_PADRAO["message"]))
    msg_entry = ttk.Entry(root, textvariable=msg_var, width=55)
    msg_entry.pack(fill="x", padx=12, pady=(0, 8))

    # Intervalo
    ttk.Label(root, text="Intervalo (minutos):").pack(anchor="w", padx=12, pady=(8, 2))
    interval_var = tk.StringVar(value=str(cfg.get("interval_minutes", 10)))
    interval_spin = ttk.Spinbox(root, textvariable=interval_var, from_=1, to=120, width=8)
    interval_spin.pack(anchor="w", padx=12, pady=(0, 8))

    # Duração do popup
    ttk.Label(root, text="Duração do popup (segundos):").pack(anchor="w", padx=12, pady=(8, 2))
    duration_var = tk.StringVar(value=str(cfg.get("popup_duration_seconds", 12)))
    duration_spin = ttk.Spinbox(root, textvariable=duration_var, from_=3, to=60, width=8)
    duration_spin.pack(anchor="w", padx=12, pady=(0, 8))

    # Cores aleatórias
    random_colors_var = tk.BooleanVar(value=cfg.get("random_colors", True))
    ttk.Checkbutton(root, text="Usar cores aleatórias a cada popup", variable=random_colors_var).pack(
        anchor="w", padx=12, pady=8
    )

    # Cores personalizadas (uma por linha)
    ttk.Label(root, text="Cores (uma por linha, nomes ou #hex):").pack(anchor="w", padx=12, pady=(8, 2))
    colors_text = tk.Text(root, height=4, width=55, wrap="word")
    colors_text.pack(fill="x", padx=12, pady=(0, 8))
    colors_text.insert("1.0", "\n".join(cfg.get("colors", CONFIG_PADRAO["colors"])))

    # Áudio
    ttk.Separator(root, orient="horizontal").pack(fill="x", padx=12, pady=12)
    ttk.Label(root, text="Áudio:").pack(anchor="w", padx=12, pady=(4, 2))

    audio_mode_var = tk.StringVar(value=cfg.get("audio_mode", "random"))
    ttk.Radiobutton(root, text="Aleatório (todos da pasta audios)", variable=audio_mode_var, value="random").pack(
        anchor="w", padx=12, pady=2
    )
    ttk.Radiobutton(root, text="Apenas selecionados:", variable=audio_mode_var, value="selected").pack(
        anchor="w", padx=12, pady=2
    )

    audios_disponiveis = listar_audios()
    selected_audios = cfg.get("selected_audios", [])

    frame_audios = ttk.Frame(root)
    frame_audios.pack(fill="both", expand=True, padx=12, pady=(4, 8))

    lb = tk.Listbox(frame_audios, listvariable=tk.Variable(value=audios_disponiveis), selectmode="extended", height=6)
    lb.pack(side="left", fill="both", expand=True)
    for i, a in enumerate(audios_disponiveis):
        if a in selected_audios:
            lb.selection_set(i)

    ttk.Label(frame_audios, text="Ctrl+clique para\nselecionar vários").pack(side="left", padx=4)

    ttk.Label(root, text="Pasta audios: " + pasta_audios(), font=("", 8), foreground="gray").pack(
        anchor="w", padx=12, pady=(0, 4)
    )

    def salvar():
        try:
            interval = int(interval_var.get())
            duration = int(duration_var.get())
        except ValueError:
            messagebox.showerror("Erro", "Intervalo e duração devem ser números.")
            return

        cores_raw = colors_text.get("1.0", "end").strip().split("\n")
        cores = [c.strip() for c in cores_raw if c.strip()]

        sel_idx = lb.curselection()
        selected = [audios_disponiveis[i] for i in sel_idx] if audios_disponiveis else []

        novo_cfg = {
            "message": msg_var.get().strip() or CONFIG_PADRAO["message"],
            "interval_minutes": max(1, min(120, interval)),
            "popup_duration_seconds": max(3, min(60, duration)),
            "random_colors": random_colors_var.get(),
            "colors": cores if cores else CONFIG_PADRAO["colors"],
            "audio_mode": audio_mode_var.get(),
            "selected_audios": selected,
        }
        salvar_config(novo_cfg)
        messagebox.showinfo("Salvo", "Configurações salvas! As mudanças valerão no próximo lembrete.")
        root.destroy()

    ttk.Button(root, text="Salvar", command=salvar).pack(pady=12)
    root.mainloop()

# ============ MAIN ============

if __name__ == "__main__":
    if "--config" in sys.argv or "-c" in sys.argv:
        abrir_configuracoes()
        sys.exit(0)

    Thread(target=loop_lembretes, daemon=True).start()
    while True:
        time.sleep(1)
