"""Janela gráfica de configurações (abas Geral/Notificação/Aparência/Áudio/Extras)."""

import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from .config import carregar_config, salvar_config, CONFIG_PADRAO, PALETAS, POSICOES_POPUP, CANTOS_POPUP
from .audio import listar_audios, tocar_arquivo_audio, parar_som, pasta_audios, abrir_pasta_no_explorador
from .popup import normalizar_historico_gifs, importar_gif_para_app, mostrar_popup

# Tema da janela de configuração (azul claro, legível)
CFG_FUNDO = "#dce6f5"
CFG_CARD = "#eef4fc"
CFG_CARD_INNER = "#e2ebf8"
CFG_TEXTO = "#1e3a5f"
CFG_SUB = "#5a6f8f"
CFG_ACCENT = "#2563eb"
CFG_ACCENT_HOVER = "#1d4ed8"
CFG_BORDER = "#b8cce8"
CFG_BTN_SEC_BG = "#ffffff"
CFG_BTN_SEC_ACTIVE = "#d8e4f8"

def _cfg_btn_sec(parent, **kw):
    """Botão secundário com relevo (ttk+clam no Windows costuma ficar achatado)."""
    opts = {
        "font": ("Segoe UI", 10),
        "bg": CFG_BTN_SEC_BG,
        "fg": CFG_TEXTO,
        "activebackground": CFG_BTN_SEC_ACTIVE,
        "activeforeground": CFG_TEXTO,
        "relief": tk.RAISED,
        "borderwidth": 2,
        "highlightthickness": 0,
        "padx": 14,
        "pady": 8,
        "cursor": "hand2",
    }
    opts.update(kw)
    return tk.Button(parent, **opts)

def _cfg_btn_pri(parent, **kw):
    opts = {
        "font": ("Segoe UI", 10, "bold"),
        "bg": CFG_ACCENT,
        "fg": "white",
        "activebackground": CFG_ACCENT_HOVER,
        "activeforeground": "white",
        "relief": tk.RAISED,
        "borderwidth": 2,
        "highlightthickness": 0,
        "padx": 20,
        "pady": 9,
        "cursor": "hand2",
    }
    opts.update(kw)
    return tk.Button(parent, **opts)

def abrir_configuracoes(parent=None):
    is_top_level = parent is not None
    root = tk.Toplevel(parent) if is_top_level else tk.Tk()
    root.title("🔔 Water Popup — Configurações")
    root.geometry("980x780")
    root.minsize(700, 560)
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

    cfg = carregar_config()

    main = tk.Frame(root, bg=CFG_FUNDO)
    main.pack(fill="both", expand=True, padx=14, pady=(10, 6))
    main.grid_columnconfigure(0, weight=1)
    main.grid_rowconfigure(1, weight=1)

    header = tk.Frame(main, bg=CFG_FUNDO)
    header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    tk.Label(
        header, text="Configurações",
        font=("Segoe UI", 18, "bold"), fg=CFG_TEXTO, bg=CFG_FUNDO
    ).pack(anchor="w")
    tk.Label(
        header,
        text="Personalize suas notificações. As alterações são salvas no arquivo de configuração.",
        font=("Segoe UI", 9), fg=CFG_SUB, bg=CFG_FUNDO, wraplength=760, justify="left",
    ).pack(anchor="w", pady=(4, 0))

    # ========= Variáveis-base =========
    msg_var = tk.StringVar(value=cfg.get("message", CONFIG_PADRAO["message"]))
    interval_var = tk.StringVar(value=str(cfg.get("interval_minutes", 10)))
    duration_var = tk.StringVar(value=str(cfg.get("popup_duration_seconds", 12)))
    stop_audio_var = tk.BooleanVar(value=cfg.get("stop_audio_on_close", True))
    fullscreen_var = tk.BooleanVar(value=cfg.get("fullscreen_notification", False))

    random_colors_var = tk.BooleanVar(value=cfg.get("random_colors", True))
    palette_var = tk.StringVar(value=cfg.get("color_palette", "Pastel"))
    anim_var = tk.StringVar(value=cfg.get("popup_animation", "slide"))
    font_var = tk.StringVar(value=str(cfg.get("font_size", 14)))

    pos_saved = cfg.get("popup_position", "top-right")
    if pos_saved not in POSICOES_POPUP + ("random",):
        pos_saved = "top-right"
    pos_var = tk.StringVar(value=pos_saved)

    visual_mode_saved = str(cfg.get("visual_mode", "notification")).lower().strip()
    if visual_mode_saved not in ("notification", "gif"):
        visual_mode_saved = "notification"
    visual_mode_var = tk.StringVar(value=visual_mode_saved)

    gif_mode_saved = str(cfg.get("gif_mode", "single")).lower().strip()
    if gif_mode_saved not in ("single", "random_history"):
        gif_mode_saved = "single"
    gif_mode_var = tk.StringVar(value=gif_mode_saved)
    gif_fit_mode_saved = str(cfg.get("gif_fit_mode", "contain")).lower().strip()
    if gif_fit_mode_saved not in ("contain", "cover"):
        gif_fit_mode_saved = "contain"
    gif_fit_mode_var = tk.StringVar(value=gif_fit_mode_saved)
    gif_zoom_saved = cfg.get("gif_fullscreen_zoom_percent", 140)
    try:
        gif_zoom_saved = max(100, min(300, int(round(float(gif_zoom_saved)))))
    except (TypeError, ValueError):
        gif_zoom_saved = 140
    gif_zoom_var = tk.StringVar(value=str(gif_zoom_saved))
    gif_path_var = tk.StringVar(value=(cfg.get("gif_path") or "").strip())
    gif_history = normalizar_historico_gifs(cfg.get("gif_history", []))

    fun_mode_saved = str(cfg.get("fun_mode", "none")).lower().strip()
    if fun_mode_saved not in ("none", "sparkles", "water", "party"):
        fun_mode_saved = "none"
    fun_mode_var = tk.StringVar(value=fun_mode_saved)

    _vol_saved = cfg.get("notification_volume", CONFIG_PADRAO["notification_volume"])
    try:
        _vol_saved = max(0, min(100, int(round(float(_vol_saved)))))
    except (TypeError, ValueError):
        _vol_saved = 100
    vol_var = tk.DoubleVar(value=_vol_saved)

    audio_mode_var = tk.StringVar(value=cfg.get("audio_mode", "random"))

    nb = ttk.Notebook(main)
    nb.grid(row=1, column=0, sticky="nsew", pady=(0, 6))

    tab_geral = tk.Frame(nb, bg=CFG_FUNDO)
    tab_notif = tk.Frame(nb, bg=CFG_FUNDO)
    tab_ap = tk.Frame(nb, bg=CFG_FUNDO)
    tab_aud = tk.Frame(nb, bg=CFG_FUNDO)
    tab_extra = tk.Frame(nb, bg=CFG_FUNDO)

    nb.add(tab_geral, text="  Geral  ")
    nb.add(tab_notif, text="  Notificação  ")
    nb.add(tab_ap, text="  Aparência  ")
    nb.add(tab_aud, text="  Áudio  ")
    nb.add(tab_extra, text="  Extras  ")

    # ========= Aba Geral =========
    f_msg = ttk.LabelFrame(tab_geral, text="  Mensagem principal  ", padding=16, style="CfgCard.TLabelframe")
    f_msg.pack(fill="x", pady=(0, 12))
    f_msg.columnconfigure(0, weight=1)
    msg_entry = ttk.Entry(f_msg, textvariable=msg_var, style="Cfg.TEntry")
    msg_entry.grid(row=0, column=0, sticky="ew", pady=(4, 0))
    ttk.Label(
        f_msg,
        text="Mensagem exibida em todas as notificações.",
        style="Cfg.Subtle.TLabel",
    ).grid(row=1, column=0, sticky="w", pady=(6, 0))

    f_temp = ttk.LabelFrame(tab_geral, text="  Temporização  ", padding=16, style="CfgCard.TLabelframe")
    f_temp.pack(fill="x", pady=(0, 0))
    f_temp.columnconfigure(0, weight=1)
    f_temp.columnconfigure(1, weight=1)

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

    # ========= Aba Notificação =========
    f_notif = ttk.LabelFrame(tab_notif, text="  Exibição  ", padding=16, style="CfgCard.TLabelframe")
    f_notif.pack(fill="x", pady=(0, 12))
    f_notif.columnconfigure(0, weight=1)

    ttk.Label(f_notif, text="Posição na tela", style="CfgCard.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 4))
    row_pos0 = ttk.Frame(f_notif, style="CfgCard.TFrame")
    row_pos0.grid(row=1, column=0, sticky="ew", pady=2)
    ttk.Radiobutton(
        row_pos0, text="Aleatório (inclui centro)",
        variable=pos_var, value="random", style="Cfg.TRadiobutton"
    ).pack(anchor="w")
    row_pos1 = ttk.Frame(f_notif, style="CfgCard.TFrame")
    row_pos1.grid(row=2, column=0, sticky="ew", pady=2)
    row_pos2 = ttk.Frame(f_notif, style="CfgCard.TFrame")
    row_pos2.grid(row=3, column=0, sticky="ew", pady=2)
    ttk.Radiobutton(row_pos1, text="Superior direito", variable=pos_var, value="top-right", style="Cfg.TRadiobutton").pack(side="left", padx=(0, 12))
    ttk.Radiobutton(row_pos1, text="Superior esquerdo", variable=pos_var, value="top-left", style="Cfg.TRadiobutton").pack(side="left", padx=(0, 12))
    ttk.Radiobutton(row_pos2, text="Inferior direito", variable=pos_var, value="bottom-right", style="Cfg.TRadiobutton").pack(side="left", padx=(0, 12))
    ttk.Radiobutton(row_pos2, text="Inferior esquerdo", variable=pos_var, value="bottom-left", style="Cfg.TRadiobutton").pack(side="left", padx=(0, 12))
    ttk.Radiobutton(row_pos2, text="Centro", variable=pos_var, value="center", style="Cfg.TRadiobutton").pack(side="left", padx=(0, 12))

    ttk.Checkbutton(
        f_notif, text="Cobrir toda a tela ao exibir o lembrete",
        variable=fullscreen_var, style="Cfg.TCheckbutton"
    ).grid(row=4, column=0, sticky="w", pady=(10, 0))
    ttk.Checkbutton(
        f_notif, text="Parar áudio ao fechar o popup (recomendado para áudios longos)",
        variable=stop_audio_var, style="Cfg.TCheckbutton"
    ).grid(row=5, column=0, sticky="w", pady=(8, 0))

    f_gif = tk.LabelFrame(
        tab_notif,
        text="  GIFs  ",
        bg=CFG_CARD,
        fg=CFG_ACCENT,
        font=("Segoe UI", 11, "bold"),
        padx=16,
        pady=16,
        relief=tk.SOLID,
        bd=1,
        highlightthickness=0,
    )
    f_gif.pack(fill="both", expand=True)
    f_gif.columnconfigure(0, weight=1)
    f_gif.rowconfigure(7, weight=1)

    ttk.Radiobutton(
        f_gif, text="Usar notificação padrão (texto e cores)",
        variable=visual_mode_var, value="notification", style="Cfg.TRadiobutton"
    ).grid(row=0, column=0, sticky="w", pady=2)
    ttk.Radiobutton(
        f_gif, text="Usar GIF animado",
        variable=visual_mode_var, value="gif", style="Cfg.TRadiobutton"
    ).grid(row=1, column=0, sticky="w", pady=2)

    row_gif_mode = tk.Frame(f_gif, bg=CFG_CARD)
    row_gif_mode.grid(row=2, column=0, sticky="w", pady=(8, 2))
    ttk.Radiobutton(
        row_gif_mode, text="GIF fixo", variable=gif_mode_var, value="single", style="Cfg.TRadiobutton"
    ).pack(side="left", padx=(0, 12))
    ttk.Radiobutton(
        row_gif_mode, text="Aleatório do histórico", variable=gif_mode_var, value="random_history", style="Cfg.TRadiobutton"
    ).pack(side="left", padx=(0, 12))

    row_gif_fit = tk.Frame(f_gif, bg=CFG_CARD)
    row_gif_fit.grid(row=3, column=0, sticky="w", pady=(4, 2))
    tk.Label(
        row_gif_fit,
        text="Ajuste do GIF:",
        bg=CFG_CARD,
        fg=CFG_SUB,
        font=("Segoe UI", 9),
    ).pack(side="left", padx=(0, 8))
    ttk.Radiobutton(
        row_gif_fit, text="Ajustar inteiro", variable=gif_fit_mode_var, value="contain", style="Cfg.TRadiobutton"
    ).pack(side="left", padx=(0, 12))
    ttk.Radiobutton(
        row_gif_fit, text="Preencher área (pode cortar)", variable=gif_fit_mode_var, value="cover", style="Cfg.TRadiobutton"
    ).pack(side="left", padx=(0, 12))

    row_gif_zoom = tk.Frame(f_gif, bg=CFG_CARD)
    row_gif_zoom.grid(row=4, column=0, sticky="w", pady=(2, 2))
    tk.Label(
        row_gif_zoom,
        text="Zoom em tela cheia (%)",
        bg=CFG_CARD,
        fg=CFG_SUB,
        font=("Segoe UI", 9),
    ).pack(side="left", padx=(0, 8))
    ttk.Spinbox(
        row_gif_zoom,
        textvariable=gif_zoom_var,
        from_=100,
        to=300,
        width=6,
        style="Cfg.TSpinbox",
    ).pack(side="left")

    row_gif_path = tk.Frame(f_gif, bg=CFG_CARD)
    row_gif_path.grid(row=5, column=0, sticky="ew", pady=(8, 2))
    row_gif_path.columnconfigure(0, weight=1)
    gif_entry = tk.Entry(
        row_gif_path,
        textvariable=gif_path_var,
        font=("Segoe UI", 9),
        bg="white",
        fg=CFG_TEXTO,
        relief="solid",
        bd=1,
    )
    gif_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

    gif_actions = tk.Frame(f_gif, bg=CFG_CARD)
    gif_actions.grid(row=6, column=0, sticky="ew", pady=(4, 6))

    row_hist = tk.Frame(f_gif, bg=CFG_CARD)
    row_hist.grid(row=7, column=0, sticky="nsew", pady=(4, 0))
    row_hist.columnconfigure(0, weight=1)
    row_hist.rowconfigure(1, weight=1)
    tk.Label(
        row_hist,
        text="Histórico de GIFs salvos",
        bg=CFG_CARD,
        fg=CFG_SUB,
        font=("Segoe UI", 9),
    ).grid(row=0, column=0, sticky="w", pady=(0, 4))
    hist_wrap = tk.Frame(row_hist, bg=CFG_CARD)
    hist_wrap.grid(row=1, column=0, sticky="nsew")
    hist_wrap.columnconfigure(0, weight=1)
    hist_wrap.rowconfigure(0, weight=1)
    sb_hist = tk.Scrollbar(hist_wrap, orient="vertical", width=14)
    lb_hist = tk.Listbox(
        hist_wrap,
        selectmode="extended",
        height=8,
        bg="white",
        fg=CFG_TEXTO,
        selectbackground=CFG_ACCENT,
        selectforeground="white",
        font=("Segoe UI", 9),
        highlightthickness=1,
        highlightbackground=CFG_BORDER,
        relief="solid",
        yscrollcommand=sb_hist.set,
    )
    sb_hist.config(command=lb_hist.yview)
    lb_hist.grid(row=0, column=0, sticky="nsew")
    sb_hist.grid(row=0, column=1, sticky="ns")

    def recarregar_historico_gif(selecao=None):
        lb_hist.delete(0, tk.END)
        for p in gif_history:
            lb_hist.insert(tk.END, p)
        if selecao:
            for i in range(lb_hist.size()):
                if lb_hist.get(i) == selecao:
                    lb_hist.selection_set(i)
                    lb_hist.see(i)
                    break

    recarregar_historico_gif(gif_path_var.get().strip() or None)

    def adicionar_ao_historico(caminho):
        nonlocal gif_history
        item = os.path.normpath(caminho)
        gif_history = normalizar_historico_gifs(gif_history + [item])
        recarregar_historico_gif(item)

    def escolher_gif_explorer():
        path = filedialog.askopenfilename(
            parent=root,
            title="Selecionar GIF animado",
            filetypes=[("GIF animado", "*.gif"), ("GIF", "*.gif"), ("Todos", "*.*")],
        )
        if not path:
            return
        try:
            destino = importar_gif_para_app(path)
        except Exception as e:
            messagebox.showerror("GIF", str(e))
            return
        gif_path_var.set(destino)
        adicionar_ao_historico(destino)

    def adicionar_gifs_explorer():
        paths = filedialog.askopenfilenames(
            parent=root,
            title="Adicionar GIFs ao histórico",
            filetypes=[("GIF animado", "*.gif"), ("GIF", "*.gif"), ("Todos", "*.*")],
        )
        if not paths:
            return
        copiados = 0
        falhas = 0
        ultimo = None
        for src in paths:
            try:
                destino = importar_gif_para_app(src)
                adicionar_ao_historico(destino)
                copiados += 1
                ultimo = destino
            except Exception:
                falhas += 1
        if ultimo:
            gif_path_var.set(ultimo)
        msg = f"GIFs adicionados: {copiados}."
        if falhas:
            msg += f"\nFalhas: {falhas}."
        messagebox.showinfo("GIF", msg)

    def usar_gif_selecionado_hist():
        sel = lb_hist.curselection()
        if not sel:
            return
        gif_path_var.set(lb_hist.get(sel[0]))

    def remover_gif_selecionado_hist():
        nonlocal gif_history
        sel = lb_hist.curselection()
        if not sel:
            return
        remover = {lb_hist.get(i) for i in sel}
        gif_history = [p for p in gif_history if p not in remover]
        if gif_path_var.get().strip() in remover:
            gif_path_var.set("")
        recarregar_historico_gif()

    def limpar_historico_gif():
        nonlocal gif_history
        if not gif_history:
            return
        if messagebox.askyesno("GIF", "Limpar todo o histórico de GIFs?"):
            gif_history = []
            gif_path_var.set("")
            recarregar_historico_gif()

    lb_hist.bind("<Double-Button-1>", lambda _e: usar_gif_selecionado_hist())

    _cfg_btn_sec(gif_actions, text="Escolher GIF…", command=escolher_gif_explorer).pack(side="left", padx=(0, 8), pady=2)
    _cfg_btn_sec(gif_actions, text="+ Adicionar vários…", command=adicionar_gifs_explorer).pack(side="left", padx=8, pady=2)
    _cfg_btn_sec(gif_actions, text="Usar selecionado", command=usar_gif_selecionado_hist).pack(side="left", padx=8, pady=2)
    _cfg_btn_sec(gif_actions, text="Remover do histórico", command=remover_gif_selecionado_hist).pack(side="left", padx=8, pady=2)
    _cfg_btn_sec(gif_actions, text="Limpar histórico", command=limpar_historico_gif).pack(side="left", padx=8, pady=2)

    # ========= Aba Aparência (somente visual da notificação padrão) =========
    f_ap = ttk.LabelFrame(tab_ap, text="  Aparência  ", padding=16, style="CfgCard.TLabelframe")
    f_ap.pack(fill="both", expand=True)
    f_ap.columnconfigure(0, weight=1)

    ttk.Checkbutton(f_ap, text="Cores aleatórias a cada popup", variable=random_colors_var, style="Cfg.TCheckbutton").grid(row=0, column=0, sticky="w")

    ttk.Label(f_ap, text="Paleta de cores", style="CfgCard.TLabel").grid(row=1, column=0, sticky="w", pady=(12, 4))
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
    if pos_saved not in CANTOS_POPUP + ("random",):
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
    ttk.Spinbox(row_font, textvariable=font_var, from_=10, to=24, width=6, style="Cfg.TSpinbox").pack(side="left")

    # ========= Aba Áudio =========
    f_aud = tk.LabelFrame(
        tab_aud,
        text="  Áudio  ",
        bg=CFG_CARD,
        fg=CFG_ACCENT,
        font=("Segoe UI", 11, "bold"),
        padx=16,
        pady=16,
        relief=tk.SOLID,
        bd=1,
        highlightthickness=0,
    )
    f_aud.pack(fill="both", expand=True)
    f_aud.columnconfigure(0, weight=1)
    f_aud.rowconfigure(4, weight=1)

    ttk.Radiobutton(f_aud, text="Aleatório — todos os arquivos da pasta audios", variable=audio_mode_var, value="random", style="Cfg.TRadiobutton").grid(row=0, column=0, sticky="w", pady=2)
    ttk.Radiobutton(f_aud, text="Apenas os selecionados na lista abaixo (Ctrl+clique para vários)", variable=audio_mode_var, value="selected", style="Cfg.TRadiobutton").grid(row=1, column=0, sticky="w", pady=2)

    vol_frame = tk.Frame(f_aud, bg=CFG_CARD)
    vol_frame.grid(row=2, column=0, sticky="ew", pady=(10, 4))
    vol_frame.columnconfigure(0, weight=1)
    tk.Label(vol_frame, text="Volume das notificações", bg=CFG_CARD, fg=CFG_TEXTO, font=("Segoe UI", 10)).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
    vol_pct_label = tk.Label(vol_frame, text=f"{_vol_saved}%", bg=CFG_CARD, fg=CFG_TEXTO, font=("Segoe UI", 10), width=6)
    vol_pct_label.grid(row=1, column=1, sticky="e", padx=(10, 0))

    def atualizar_label_vol(*_a):
        try:
            v = int(round(float(vol_var.get())))
        except tk.TclError:
            return
        vol_pct_label.config(text=f"{v}%")

    vol_var.trace_add("write", atualizar_label_vol)
    ttk.Scale(vol_frame, from_=0, to=100, variable=vol_var, orient="horizontal").grid(row=1, column=0, sticky="ew")
    tk.Label(
        vol_frame,
        text="Afeta o som ao tocar o lembrete e as prévias desta janela (0% = mudo).",
        bg=CFG_CARD,
        fg=CFG_SUB,
        font=("Segoe UI", 9),
    ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))

    def cfg_com_volume_atual():
        c = {**carregar_config()}
        try:
            c["notification_volume"] = int(round(float(vol_var.get())))
        except tk.TclError:
            c["notification_volume"] = CONFIG_PADRAO["notification_volume"]
        return c

    tk.Label(
        f_aud,
        text="Lista de arquivos — use a barra de rolagem à direita se houver mais itens.",
        bg=CFG_CARD,
        fg=CFG_SUB,
        font=("Segoe UI", 9),
    ).grid(row=3, column=0, sticky="w", pady=(6, 2))

    list_wrap = tk.Frame(f_aud, bg=CFG_CARD)
    list_wrap.grid(row=4, column=0, sticky="nsew", pady=4)
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
            tocar_arquivo_audio(path, cfg_com_volume_atual())
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
                    tocar_arquivo_audio(path, cfg_com_volume_atual())
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

    def remover_audios_selecionados():
        sel = lb.curselection()
        if not sel:
            messagebox.showinfo("Áudio", "Selecione um ou mais arquivos na lista para remover.")
            return

        nomes = [lb.get(i) for i in sel]
        if len(nomes) == 1:
            msg_confirm = f'Deseja remover o arquivo "{nomes[0]}" da pasta audios?'
        else:
            preview = ", ".join(nomes[:4])
            if len(nomes) > 4:
                preview += ", ..."
            msg_confirm = (
                f"Deseja remover {len(nomes)} arquivos da pasta audios?\n\n"
                f"Selecionados: {preview}"
            )

        if not messagebox.askyesno("Confirmar remoção", msg_confirm):
            return

        removidos = 0
        falhas = []
        pasta = pasta_audios()
        for nome in nomes:
            path = os.path.join(pasta, nome)
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    removidos += 1
            except Exception as e:
                falhas.append(f"{nome}: {e}")

        recarregar_lista_audios()
        if falhas:
            detalhes = "\n".join(falhas[:6])
            if len(falhas) > 6:
                detalhes += "\n..."
            messagebox.showwarning(
                "Áudio",
                f"Removidos: {removidos}\nFalhas: {len(falhas)}\n\n{detalhes}",
            )
        else:
            messagebox.showinfo("Áudio", f"Arquivos removidos: {removidos}.")

    aud_actions = tk.Frame(f_aud, bg=CFG_CARD)
    aud_actions.grid(row=5, column=0, sticky="ew", pady=(10, 4))
    _cfg_btn_sec(aud_actions, text="▶ Ouvir seleção", command=reproduzir_selecionado).pack(side="left", padx=(0, 8), pady=2)
    _cfg_btn_sec(aud_actions, text="■ Parar som", command=parar_som).pack(side="left", padx=8, pady=2)
    _cfg_btn_sec(aud_actions, text="+ Adicionar arquivos…", command=adicionar_audios_explorer).pack(side="left", padx=8, pady=2)
    _cfg_btn_sec(aud_actions, text="🗑 Remover selecionado(s)", command=remover_audios_selecionados).pack(side="left", padx=8, pady=2)
    _cfg_btn_sec(aud_actions, text="Abrir pasta no Explorer", command=abrir_pasta_audios_cmd).pack(side="left", padx=8, pady=2)

    tk.Label(
        f_aud,
        text="Dica: duplo clique em um item para ouvir a prévia.",
        bg=CFG_CARD,
        fg=CFG_SUB,
        font=("Segoe UI", 9),
    ).grid(row=6, column=0, sticky="w", pady=(2, 0))

    tk.Label(f_aud, text="Pasta: " + pasta_audios(), bg=CFG_CARD, fg=CFG_SUB, font=("Segoe UI", 9)).grid(row=7, column=0, sticky="w", pady=(6, 0))

    # ========= Aba Extras =========
    f_extra = ttk.LabelFrame(tab_extra, text="  Personalização divertida  ", padding=16, style="CfgCard.TLabelframe")
    f_extra.pack(fill="x")
    ttk.Radiobutton(f_extra, text="Sem efeito extra", variable=fun_mode_var, value="none", style="Cfg.TRadiobutton").pack(anchor="w", pady=2)
    ttk.Radiobutton(f_extra, text="Brilhos (✨)", variable=fun_mode_var, value="sparkles", style="Cfg.TRadiobutton").pack(anchor="w", pady=2)
    ttk.Radiobutton(f_extra, text="Tema água (💧🫧🌊)", variable=fun_mode_var, value="water", style="Cfg.TRadiobutton").pack(anchor="w", pady=2)
    ttk.Radiobutton(f_extra, text="Modo festa (🎉🥳)", variable=fun_mode_var, value="party", style="Cfg.TRadiobutton").pack(anchor="w", pady=2)
    ttk.Label(
        f_extra,
        text="Aplica um toque visual na mensagem padrão da notificação.",
        style="Cfg.Subtle.TLabel",
    ).pack(anchor="w", pady=(8, 0))

    def atualizar_estado_controles_notificacao(*_a):
        gif_on = visual_mode_var.get() == "gif"
        state = "normal" if gif_on else "disabled"
        gif_entry.configure(state=state)
        try:
            for child in row_gif_zoom.winfo_children():
                child.configure(state=state)
        except Exception:
            pass
        for child in row_gif_fit.winfo_children():
            try:
                child.configure(state=state)
            except Exception:
                pass
        for child in gif_actions.winfo_children():
            child.configure(state=state)
        lb_hist.configure(state=state)
        if gif_on and gif_mode_var.get() == "random_history":
            gif_entry.configure(state="disabled")
        elif gif_on:
            gif_entry.configure(state="normal")
        else:
            gif_entry.configure(state="disabled")

    visual_mode_var.trace_add("write", atualizar_estado_controles_notificacao)
    gif_mode_var.trace_add("write", atualizar_estado_controles_notificacao)
    atualizar_estado_controles_notificacao()

    # Rodapé fixo
    btn_frame = tk.Frame(main, bg=CFG_FUNDO, highlightthickness=1, highlightbackground=CFG_BORDER)

    def testar():
        try:
            nv = int(round(float(vol_var.get())))
        except (ValueError, tk.TclError):
            nv = CONFIG_PADRAO["notification_volume"]
        nv = max(0, min(100, nv))
        try:
            gif_zoom_pct = int(round(float(gif_zoom_var.get())))
        except (ValueError, tk.TclError):
            gif_zoom_pct = 140
        gif_zoom_pct = max(100, min(300, gif_zoom_pct))

        cfg_teste = {
            "message": msg_var.get().strip() or "Teste de notificação! 🔔",
            "random_colors": random_colors_var.get(),
            "colors": PALETAS.get(palette_var.get(), PALETAS["Pastel"]),
            "popup_animation": anim_var.get(),
            "popup_position": pos_var.get(),
            "font_size": int(font_var.get() or 14),
            "stop_audio_on_close": stop_audio_var.get(),
            "popup_duration_seconds": 4,
            "audio_mode": audio_mode_var.get(),
            "selected_audios": [lb.get(i) for i in lb.curselection()],
            "notification_volume": nv,
            "visual_mode": visual_mode_var.get(),
            "gif_path": gif_path_var.get().strip(),
            "gif_mode": gif_mode_var.get(),
            "gif_fit_mode": gif_fit_mode_var.get(),
            "gif_fullscreen_zoom_percent": gif_zoom_pct,
            "gif_history": normalizar_historico_gifs(gif_history),
            "fullscreen_notification": fullscreen_var.get(),
            "fun_mode": fun_mode_var.get(),
        }
        root.after(100, lambda: mostrar_popup(parent=root, cfg_override=cfg_teste))

    def salvar():
        try:
            interval = int(interval_var.get())
            duration = int(duration_var.get())
            fs = int(font_var.get())
        except ValueError:
            messagebox.showerror("Erro", "Preencha números válidos em intervalo, duração e fonte.")
            return

        visual_mode = visual_mode_var.get()
        gif_mode = gif_mode_var.get()
        try:
            gif_zoom_pct = int(round(float(gif_zoom_var.get())))
        except (ValueError, tk.TclError):
            gif_zoom_pct = 140
        gif_zoom_pct = max(100, min(300, gif_zoom_pct))
        gif_path = os.path.normpath(gif_path_var.get().strip()) if gif_path_var.get().strip() else ""
        hist_normalizado = normalizar_historico_gifs(gif_history)
        if gif_path:
            hist_normalizado = normalizar_historico_gifs(hist_normalizado + [gif_path])

        if visual_mode == "gif":
            if gif_mode == "single":
                if not gif_path:
                    messagebox.showerror("Erro", "Selecione um GIF para usar no modo GIF fixo.")
                    return
                if not os.path.isfile(gif_path):
                    messagebox.showerror("Erro", "O GIF selecionado não foi encontrado.")
                    return
            if gif_mode == "random_history":
                validos = [p for p in hist_normalizado if os.path.isfile(p)]
                if not validos:
                    messagebox.showerror("Erro", "Adicione pelo menos 1 GIF válido no histórico para usar o modo aleatório.")
                    return
            if gif_path and not os.path.isfile(gif_path):
                messagebox.showerror("Erro", "O GIF selecionado não foi encontrado.")
                return

        sel_idx = lb.curselection()
        selected = [lb.get(i) for i in sel_idx]

        try:
            vol_pct = int(round(float(vol_var.get())))
        except (ValueError, tk.TclError):
            vol_pct = CONFIG_PADRAO["notification_volume"]
        vol_pct = max(0, min(100, vol_pct))

        novo_cfg = {
            "message": msg_var.get().strip() or CONFIG_PADRAO["message"],
            "interval_minutes": max(1, min(120, interval)),
            "popup_duration_seconds": max(3, min(60, duration)),
            "fullscreen_notification": fullscreen_var.get(),
            "stop_audio_on_close": stop_audio_var.get(),
            "visual_mode": visual_mode,
            "gif_mode": gif_mode,
            "gif_fit_mode": gif_fit_mode_var.get(),
            "gif_fullscreen_zoom_percent": gif_zoom_pct,
            "gif_path": gif_path,
            "gif_history": hist_normalizado,
            "random_colors": random_colors_var.get(),
            "color_palette": palette_var.get(),
            "colors": PALETAS.get(palette_var.get(), PALETAS["Pastel"]).copy(),
            "popup_animation": anim_var.get(),
            "popup_position": pos_var.get(),
            "font_size": max(10, min(24, fs)),
            "fun_mode": fun_mode_var.get(),
            "audio_mode": audio_mode_var.get(),
            "selected_audios": selected,
            "notification_volume": vol_pct,
        }
        salvar_config(novo_cfg)
        messagebox.showinfo("Salvo", "Configurações salvas! As mudanças valerão no próximo lembrete.")
        root.destroy()

    _cfg_btn_sec(btn_frame, text="Testar popup", command=testar).pack(side="left", padx=10, pady=10)
    _cfg_btn_pri(btn_frame, text="Salvar", command=salvar).pack(side="right", padx=10, pady=10)
    btn_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))

    if is_top_level:
        parent.wait_window(root)
    else:
        root.mainloop()

