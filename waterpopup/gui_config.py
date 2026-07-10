"""Janela gráfica de configurações — abas espelhando as seções do config.json
v2 (Geral, Mensagem, Visual/GIF, Posição, Cores, Animação, Áudio, Avançado)."""

import os
import shutil
import logging
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

from . import theme
from . import gif_cache
from .config import carregar_config, salvar_config, CONFIG_PADRAO, PALETAS, POSICOES_POPUP
from .monitors import listar_monitores
from .audio import listar_audios, tocar_arquivo_audio, parar_som, pasta_audios, abrir_pasta_no_explorador
from .popup import normalizar_historico_gifs, importar_gif_para_app, mostrar_popup, carregar_frames_para_preview

_ANIM_OPCOES = [
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

_POS_OPCOES = [
    ("random", "Aleatório (inclui centro)"),
    ("top-right", "Superior direito"),
    ("top-left", "Superior esquerdo"),
    ("bottom-right", "Inferior direito"),
    ("bottom-left", "Inferior esquerdo"),
    ("center", "Centro"),
]

_FUN_MODE_OPCOES = [
    ("none", "Sem efeito extra"),
    ("sparkles", "Brilhos (✨)"),
    ("water", "Tema água (💧🫧🌊)"),
    ("party", "Modo festa (🎉🥳)"),
]


def _card(parent, **kw):
    opts = dict(fg_color=theme.COR_CARD_2, corner_radius=theme.RAIO_BORDA)
    opts.update(kw)
    return ctk.CTkFrame(parent, **opts)


def _rotulo(parent, texto, **kw):
    opts = dict(font=theme.fonte(11), text_color=theme.COR_TEXTO, anchor="w")
    opts.update(kw)
    return ctk.CTkLabel(parent, text=texto, **opts)


def _subtitulo(parent, texto, **kw):
    opts = dict(font=theme.fonte(9), text_color=theme.COR_SUBTEXTO, anchor="w", justify="left")
    opts.update(kw)
    return ctk.CTkLabel(parent, text=texto, **opts)


def _botao_sec(parent, **kw):
    opts = dict(
        fg_color=theme.COR_BOTAO_SEC, hover_color=theme.COR_BOTAO_SEC_HOVER,
        text_color=theme.COR_TEXTO, font=theme.fonte(11), corner_radius=theme.RAIO_BORDA_PEQUENO,
    )
    opts.update(kw)
    return ctk.CTkButton(parent, **opts)


def _botao_pri(parent, **kw):
    opts = dict(
        fg_color=theme.COR_BOTAO, hover_color=theme.COR_BOTAO_HOVER,
        text_color="white", font=theme.fonte(11, "bold"), corner_radius=theme.RAIO_BORDA_PEQUENO,
    )
    opts.update(kw)
    return ctk.CTkButton(parent, **opts)


def abrir_configuracoes(parent=None):
    is_top_level = parent is not None
    root = ctk.CTkToplevel(parent) if is_top_level else ctk.CTk()
    root.title("🔔 Water Popup — Configurações")
    root.geometry("940x740")
    root.minsize(780, 620)
    root.configure(fg_color=theme.COR_FUNDO)
    if is_top_level:
        root.transient(parent)
        root.grab_set()

    cfg = carregar_config()

    main = ctk.CTkFrame(root, fg_color="transparent")
    main.pack(fill="both", expand=True, padx=16, pady=14)

    header = ctk.CTkFrame(main, fg_color="transparent")
    header.pack(fill="x", pady=(0, 10))
    ctk.CTkLabel(
        header, text="Configurações", font=theme.fonte_titulo(20), text_color=theme.COR_TEXTO, anchor="w",
    ).pack(anchor="w")
    _subtitulo(
        header, "Personalize suas notificações. As alterações são salvas no arquivo de configuração.",
    ).pack(anchor="w", pady=(4, 0))

    # ========= Variáveis =========
    msg_var = ctk.StringVar(value=cfg.get("message", CONFIG_PADRAO["message"]))
    font_var = ctk.StringVar(value=str(cfg.get("font_size", 14)))
    fun_mode_saved = str(cfg.get("fun_mode", "none")).lower().strip()
    if fun_mode_saved not in dict(_FUN_MODE_OPCOES):
        fun_mode_saved = "none"
    fun_mode_var = ctk.StringVar(value=fun_mode_saved)

    interval_var = ctk.StringVar(value=str(cfg.get("interval_minutes", 10)))
    duration_var = ctk.StringVar(value=str(cfg.get("popup_duration_seconds", 12)))

    visual_mode_saved = str(cfg.get("visual_mode", "notification")).lower().strip()
    if visual_mode_saved not in ("notification", "gif"):
        visual_mode_saved = "notification"
    visual_mode_var = ctk.StringVar(value=visual_mode_saved)
    fullscreen_var = ctk.BooleanVar(value=cfg.get("fullscreen_notification", False))
    stop_audio_var = ctk.BooleanVar(value=cfg.get("stop_audio_on_close", True))

    gif_fit_mode_saved = str(cfg.get("gif_fit_mode", "contain")).lower().strip()
    if gif_fit_mode_saved not in ("contain", "cover"):
        gif_fit_mode_saved = "contain"
    gif_fit_mode_var = ctk.StringVar(value=gif_fit_mode_saved)
    gif_zoom_saved = cfg.get("gif_fullscreen_zoom_percent", 140)
    try:
        gif_zoom_saved = max(100, min(300, int(round(float(gif_zoom_saved)))))
    except (TypeError, ValueError):
        gif_zoom_saved = 140
    gif_zoom_var = ctk.StringVar(value=str(gif_zoom_saved))

    gif_mode_saved = str(cfg.get("gif_mode", "single")).lower().strip()
    if gif_mode_saved not in ("single", "random_history"):
        gif_mode_saved = "single"
    gif_mode_var = ctk.StringVar(value=gif_mode_saved)
    gif_path_var = ctk.StringVar(value=(cfg.get("gif_path") or "").strip())
    gif_history = normalizar_historico_gifs(cfg.get("gif_history", []))

    pos_saved = cfg.get("popup_position", "top-right")
    if pos_saved not in POSICOES_POPUP + ("random",):
        pos_saved = "top-right"
    pos_var = ctk.StringVar(value=pos_saved)  # única variável de posição (antes existia duplicada)

    random_colors_var = ctk.BooleanVar(value=cfg.get("random_colors", True))
    palette_var = ctk.StringVar(value=cfg.get("color_palette", "Pastel"))

    anim_var = ctk.StringVar(value=cfg.get("popup_animation", "slide"))

    audio_mode_var = ctk.StringVar(value=cfg.get("audio_mode", "random"))
    _vol_saved = cfg.get("notification_volume", CONFIG_PADRAO["notification_volume"])
    try:
        _vol_saved = max(0, min(100, int(round(float(_vol_saved)))))
    except (TypeError, ValueError):
        _vol_saved = 100
    vol_var = ctk.DoubleVar(value=_vol_saved)

    title_var = ctk.StringVar(value=cfg.get("control_window_title", CONFIG_PADRAO["control_window_title"]))
    status_txt_var = ctk.StringVar(value=cfg.get("control_window_status", CONFIG_PADRAO["control_window_status"]))
    hint_var = ctk.StringVar(value=cfg.get("control_window_hint", CONFIG_PADRAO["control_window_hint"]))

    # ========= Validação inline compartilhada =========
    campos_invalidos = set()
    _botao_salvar_ref = {"widget": None}

    def _atualizar_estado_salvar():
        # O botão Salvar só existe depois que todas as abas são montadas;
        # até lá, esta função é um no-op seguro (os campos numéricos das
        # primeiras abas já disparam validação ao serem criados).
        if _botao_salvar_ref["widget"] is not None:
            _botao_salvar_ref["widget"].configure(state="disabled" if campos_invalidos else "normal")

    def _campo_numerico(parent, chave, var, minimo, maximo, largura=80):
        """Campo numérico com feedback de erro inline; enquanto o valor
        estiver fora da faixa aceita, o botão Salvar fica desabilitado."""
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        entry = ctk.CTkEntry(wrapper, textvariable=var, width=largura, font=theme.fonte(11))
        entry.pack(anchor="w")
        erro_lbl = ctk.CTkLabel(wrapper, text="", font=theme.fonte(9), text_color=theme.COR_ERRO, anchor="w")
        erro_lbl.pack(anchor="w")

        def validar(*_a):
            valido = False
            try:
                v = int(float(var.get()))
                valido = minimo <= v <= maximo
            except (ValueError, TypeError):
                valido = False
            if valido:
                campos_invalidos.discard(chave)
                entry.configure(border_color=theme.COR_BORDA)
                erro_lbl.configure(text="")
            else:
                campos_invalidos.add(chave)
                entry.configure(border_color=theme.COR_ERRO)
                erro_lbl.configure(text=f"Use um número entre {minimo} e {maximo}.")
            _atualizar_estado_salvar()

        var.trace_add("write", validar)
        validar()
        return wrapper

    # ========= Abas =========
    tabview = ctk.CTkTabview(
        main, fg_color=theme.COR_CARD,
        segmented_button_fg_color=theme.COR_CARD_2,
        segmented_button_selected_color=theme.COR_BOTAO,
        segmented_button_selected_hover_color=theme.COR_BOTAO_HOVER,
        segmented_button_unselected_color=theme.COR_CARD_2,
        text_color=theme.COR_TEXTO,
    )
    tabview.pack(fill="both", expand=True, pady=(0, 10))

    tab_geral = tabview.add("Geral")
    tab_msg = tabview.add("Mensagem")
    tab_visual = tabview.add("Visual/GIF")
    tab_pos = tabview.add("Posição")
    tab_cores = tabview.add("Cores")
    tab_anim = tabview.add("Animação")
    tab_audio = tabview.add("Áudio")
    tab_avancado = tabview.add("Avançado")

    # ---- Geral (general: interval_minutes, popup_duration_seconds) ----
    f_geral = _card(tab_geral)
    f_geral.pack(fill="x", padx=4, pady=4)
    inner = ctk.CTkFrame(f_geral, fg_color="transparent")
    inner.pack(fill="x", padx=16, pady=16)
    linha = ctk.CTkFrame(inner, fg_color="transparent")
    linha.pack(fill="x")
    col1 = ctk.CTkFrame(linha, fg_color="transparent")
    col1.pack(side="left", padx=(0, 32))
    _rotulo(col1, "Intervalo entre lembretes (min)").pack(anchor="w")
    _campo_numerico(col1, "interval", interval_var, 1, 120).pack(anchor="w", pady=(4, 0))
    col2 = ctk.CTkFrame(linha, fg_color="transparent")
    col2.pack(side="left")
    _rotulo(col2, "Duração do popup na tela (seg)").pack(anchor="w")
    _campo_numerico(col2, "duration", duration_var, 3, 60).pack(anchor="w", pady=(4, 0))

    # ---- Mensagem (message: text, font_size, effect) ----
    f_msg = _card(tab_msg)
    f_msg.pack(fill="x", padx=4, pady=4)
    inner = ctk.CTkFrame(f_msg, fg_color="transparent")
    inner.pack(fill="x", padx=16, pady=16)
    _rotulo(inner, "Mensagem principal").pack(anchor="w")
    ctk.CTkEntry(inner, textvariable=msg_var, font=theme.fonte(11)).pack(fill="x", pady=(6, 4))
    _subtitulo(inner, "Mensagem exibida em todas as notificações.").pack(anchor="w")

    linha_fonte = ctk.CTkFrame(inner, fg_color="transparent")
    linha_fonte.pack(fill="x", pady=(16, 0))
    _rotulo(linha_fonte, "Tamanho da fonte").pack(anchor="w")
    _campo_numerico(linha_fonte, "font_size", font_var, 10, 24).pack(anchor="w", pady=(4, 0))

    f_efeito = _card(tab_msg)
    f_efeito.pack(fill="x", padx=4, pady=(8, 4))
    inner2 = ctk.CTkFrame(f_efeito, fg_color="transparent")
    inner2.pack(fill="x", padx=16, pady=16)
    _rotulo(inner2, "Efeito na mensagem").pack(anchor="w", pady=(0, 8))
    for val, lbl in _FUN_MODE_OPCOES:
        ctk.CTkRadioButton(inner2, text=lbl, variable=fun_mode_var, value=val, font=theme.fonte(11)).pack(anchor="w", pady=2)

    # ---- Visual/GIF (visual: mode, fullscreen, fit_mode, gif_zoom_percent + gifs) ----
    f_visual = _card(tab_visual)
    f_visual.pack(fill="x", padx=4, pady=4)
    inner = ctk.CTkFrame(f_visual, fg_color="transparent")
    inner.pack(fill="x", padx=16, pady=16)
    ctk.CTkRadioButton(inner, text="Usar notificação padrão (texto e cores)", variable=visual_mode_var, value="notification", font=theme.fonte(11)).pack(anchor="w", pady=2)
    ctk.CTkRadioButton(inner, text="Usar GIF animado", variable=visual_mode_var, value="gif", font=theme.fonte(11)).pack(anchor="w", pady=2)
    ctk.CTkCheckBox(inner, text="Cobrir toda a tela ao exibir o lembrete (multi-monitor se houver 2+ telas)", variable=fullscreen_var, font=theme.fonte(11)).pack(anchor="w", pady=(10, 2))
    ctk.CTkCheckBox(inner, text="Parar áudio ao fechar o popup (recomendado para áudios longos)", variable=stop_audio_var, font=theme.fonte(11)).pack(anchor="w", pady=2)

    f_gif = _card(tab_visual)
    f_gif.pack(fill="both", expand=True, padx=4, pady=(8, 4))
    corpo_gif = ctk.CTkFrame(f_gif, fg_color="transparent")
    corpo_gif.pack(fill="both", expand=True, padx=16, pady=16)
    corpo_gif.grid_columnconfigure(0, weight=1)
    corpo_gif.grid_columnconfigure(1, weight=0)

    coluna_gif = ctk.CTkFrame(corpo_gif, fg_color="transparent")
    coluna_gif.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

    linha_modo_gif = ctk.CTkFrame(coluna_gif, fg_color="transparent")
    linha_modo_gif.pack(anchor="w", pady=(0, 8))
    ctk.CTkRadioButton(linha_modo_gif, text="GIF fixo", variable=gif_mode_var, value="single", font=theme.fonte(11)).pack(side="left", padx=(0, 16))
    ctk.CTkRadioButton(linha_modo_gif, text="Aleatório do histórico", variable=gif_mode_var, value="random_history", font=theme.fonte(11)).pack(side="left")

    linha_fit = ctk.CTkFrame(coluna_gif, fg_color="transparent")
    linha_fit.pack(anchor="w", pady=(0, 8))
    _rotulo(linha_fit, "Ajuste:", font=theme.fonte(10), text_color=theme.COR_SUBTEXTO).pack(side="left", padx=(0, 8))
    ctk.CTkRadioButton(linha_fit, text="Ajustar inteiro", variable=gif_fit_mode_var, value="contain", font=theme.fonte(11)).pack(side="left", padx=(0, 16))
    ctk.CTkRadioButton(linha_fit, text="Preencher (pode cortar)", variable=gif_fit_mode_var, value="cover", font=theme.fonte(11)).pack(side="left")

    linha_zoom = ctk.CTkFrame(coluna_gif, fg_color="transparent")
    linha_zoom.pack(anchor="w", pady=(0, 10))
    _rotulo(linha_zoom, "Zoom em tela cheia (%)", font=theme.fonte(10), text_color=theme.COR_SUBTEXTO).pack(side="left", padx=(0, 8))
    zoom_entry = ctk.CTkEntry(linha_zoom, textvariable=gif_zoom_var, width=60, font=theme.fonte(11))
    zoom_entry.pack(side="left")

    linha_path = ctk.CTkFrame(coluna_gif, fg_color="transparent")
    linha_path.pack(fill="x", pady=(0, 8))
    gif_entry = ctk.CTkEntry(linha_path, textvariable=gif_path_var, font=theme.fonte(10))
    gif_entry.pack(fill="x")

    gif_actions = ctk.CTkFrame(coluna_gif, fg_color="transparent")
    gif_actions.pack(fill="x", pady=(0, 10))

    _rotulo(coluna_gif, "Histórico de GIFs salvos", font=theme.fonte(10), text_color=theme.COR_SUBTEXTO).pack(anchor="w", pady=(0, 4))
    hist_wrap = ctk.CTkFrame(coluna_gif, fg_color="transparent")
    hist_wrap.pack(fill="both", expand=True)
    sb_hist = tk.Scrollbar(hist_wrap, orient="vertical", width=14)
    lb_hist = tk.Listbox(
        hist_wrap, selectmode="extended", height=6,
        bg=theme.COR_FUNDO, fg=theme.COR_TEXTO,
        selectbackground=theme.COR_BOTAO, selectforeground="white",
        font=(theme.FONTE_FAMILIA, 9), highlightthickness=1,
        highlightbackground=theme.COR_BORDA, relief="flat",
        yscrollcommand=sb_hist.set, bd=0,
    )
    sb_hist.config(command=lb_hist.yview)
    lb_hist.pack(side="left", fill="both", expand=True)
    sb_hist.pack(side="left", fill="y")

    # Coluna de pré-visualização animada do GIF selecionado.
    coluna_preview = ctk.CTkFrame(corpo_gif, fg_color=theme.COR_FUNDO, corner_radius=theme.RAIO_BORDA, width=240, height=180)
    coluna_preview.grid(row=0, column=1, sticky="n")
    coluna_preview.grid_propagate(False)
    preview_label = tk.Label(coluna_preview, bg=theme.COR_FUNDO, bd=0, highlightthickness=0)
    preview_label.place(relx=0.5, rely=0.42, anchor="center")
    preview_status_var = ctk.StringVar(value="Nenhum GIF selecionado.")
    ctk.CTkLabel(
        coluna_preview, textvariable=preview_status_var, font=theme.fonte(9),
        text_color=theme.COR_SUBTEXTO, wraplength=210, justify="center",
    ).place(relx=0.5, rely=0.86, anchor="center")
    prefetch_status_var = ctk.StringVar(value="")
    ctk.CTkLabel(
        coluna_preview, textvariable=prefetch_status_var, font=theme.fonte(8),
        text_color=theme.COR_SUBTEXTO, wraplength=210, justify="center",
    ).place(relx=0.5, rely=0.97, anchor="s")

    _preview_after_id = {"id": None}
    _prefetch_after_id = {"id": None}

    def _parar_preview():
        if _preview_after_id["id"] is not None:
            try:
                preview_label.after_cancel(_preview_after_id["id"])
            except Exception:
                pass
            _preview_after_id["id"] = None

    def _parar_monitoramento_prefetch():
        if _prefetch_after_id["id"] is not None:
            try:
                root.after_cancel(_prefetch_after_id["id"])
            except Exception:
                pass
            _prefetch_after_id["id"] = None

    def _checar_prefetch(caminho, alvos, tentativas=0):
        if not root.winfo_exists():
            return
        pendentes = [a for a in alvos if not gif_cache.esta_em_cache(caminho, *a)]
        if not pendentes or tentativas > 60:  # ~30s de tolerância
            prefetch_status_var.set("")
            return
        prefetch_status_var.set("Preparando para suas telas…")
        _prefetch_after_id["id"] = root.after(500, lambda: _checar_prefetch(caminho, alvos, tentativas + 1))

    def disparar_prefetch_gif(caminho: str) -> None:
        """Prepara em background o cache do GIF na resolução de cada monitor
        detectado, assim que o usuário escolhe/adiciona o GIF — pra quando
        clicar em "Testar agora" ou o próximo lembrete disparar, o cache já
        estar pronto (GIF plug-and-play, sem ajuste manual)."""
        _parar_monitoramento_prefetch()
        if not caminho or not os.path.isfile(caminho):
            return
        try:
            fit_mode = gif_fit_mode_var.get()
            try:
                zoom_pct = max(100, min(300, int(round(float(gif_zoom_var.get())))))
            except (ValueError, tk.TclError):
                zoom_pct = 140
            cores = PALETAS.get(palette_var.get(), PALETAS["Pastel"])
            cor_hex = cores[0] if cores else "#87CEEB"
            r, g, b = root.winfo_rgb(cor_hex)
            cor_fundo = (r // 256, g // 256, b // 256)
            monitores = listar_monitores(root)
            resolucoes = {(max(160, m.width - 80), max(120, m.height - 120)) for m in monitores}
            resolucoes.add((260, 130))  # tamanho aproximado do popup normal
            alvos = [(w, h, fit_mode, zoom_pct, cor_fundo) for (w, h) in resolucoes]
            gif_cache.preprocessar_em_background(caminho, alvos)
            _checar_prefetch(caminho, alvos)
        except Exception as e:
            logging.warning("Falha ao preparar pré-processamento do GIF '%s': %s", caminho, e)

    def atualizar_preview_gif(*_a):
        _parar_preview()
        caminho = gif_path_var.get().strip()
        try:
            preview_label.configure(image="")
        except tk.TclError:
            return
        if not caminho or not os.path.isfile(caminho):
            preview_status_var.set("Nenhum GIF selecionado.")
            prefetch_status_var.set("")
            return
        preview_status_var.set("Carregando pré-visualização…")
        root.update_idletasks()
        frames, duracoes = carregar_frames_para_preview(caminho, 220, 130, root, theme.COR_FUNDO)
        if not frames:
            preview_status_var.set("Não foi possível pré-visualizar este GIF.")
            return
        preview_status_var.set("")
        disparar_prefetch_gif(caminho)

        def tick(i=0):
            if not preview_label.winfo_exists():
                return
            i = i % len(frames)
            try:
                preview_label.configure(image=frames[i])
                preview_label.image = frames[i]
            except tk.TclError:
                return
            delay = duracoes[i] if i < len(duracoes) else 80
            _preview_after_id["id"] = preview_label.after(delay, lambda: tick(i + 1))

        tick(0)

    gif_path_var.trace_add("write", atualizar_preview_gif)

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
            parent=root, title="Selecionar GIF animado",
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
            parent=root, title="Adicionar GIFs ao histórico",
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

    _botao_sec(gif_actions, text="Escolher GIF…", command=escolher_gif_explorer, width=110).pack(side="left", padx=(0, 6), pady=2)
    _botao_sec(gif_actions, text="+ Adicionar vários…", command=adicionar_gifs_explorer, width=130).pack(side="left", padx=6, pady=2)
    _botao_sec(gif_actions, text="Usar selecionado", command=usar_gif_selecionado_hist, width=120).pack(side="left", padx=6, pady=2)
    _botao_sec(gif_actions, text="Remover", command=remover_gif_selecionado_hist, width=90).pack(side="left", padx=6, pady=2)
    _botao_sec(gif_actions, text="Limpar histórico", command=limpar_historico_gif, width=120).pack(side="left", padx=6, pady=2)

    def atualizar_estado_controles_gif(*_a):
        gif_on = visual_mode_var.get() == "gif"
        estado = "normal" if gif_on else "disabled"
        for w in (zoom_entry,):
            w.configure(state=estado)
        for child in linha_fit.winfo_children():
            if isinstance(child, ctk.CTkRadioButton):
                child.configure(state=estado)
        for child in gif_actions.winfo_children():
            child.configure(state=estado)
        lb_hist.configure(state=estado)
        if gif_on and gif_mode_var.get() == "random_history":
            gif_entry.configure(state="disabled")
        elif gif_on:
            gif_entry.configure(state="normal")
        else:
            gif_entry.configure(state="disabled")

    visual_mode_var.trace_add("write", atualizar_estado_controles_gif)
    gif_mode_var.trace_add("write", atualizar_estado_controles_gif)
    atualizar_estado_controles_gif()
    atualizar_preview_gif()

    # ---- Posição (position: value) — variável única ----
    f_pos = _card(tab_pos)
    f_pos.pack(fill="x", padx=4, pady=4)
    inner = ctk.CTkFrame(f_pos, fg_color="transparent")
    inner.pack(fill="x", padx=16, pady=16)
    _rotulo(inner, "Posição do popup na tela").pack(anchor="w", pady=(0, 8))
    for val, lbl in _POS_OPCOES:
        ctk.CTkRadioButton(inner, text=lbl, variable=pos_var, value=val, font=theme.fonte(11)).pack(anchor="w", pady=2)
    _subtitulo(inner, "Vale tanto para a notificação normal quanto para o modo tela cheia (sem GIF).").pack(anchor="w", pady=(8, 0))

    # ---- Cores (colors: random, palette) ----
    f_cores = _card(tab_cores)
    f_cores.pack(fill="x", padx=4, pady=4)
    inner = ctk.CTkFrame(f_cores, fg_color="transparent")
    inner.pack(fill="x", padx=16, pady=16)
    ctk.CTkCheckBox(inner, text="Cores aleatórias a cada popup", variable=random_colors_var, font=theme.fonte(11)).pack(anchor="w")

    _rotulo(inner, "Paleta de cores", font=theme.fonte(11)).pack(anchor="w", pady=(14, 6))
    linha_paletas = ctk.CTkFrame(inner, fg_color="transparent")
    linha_paletas.pack(anchor="w")
    for nome in PALETAS:
        ctk.CTkRadioButton(linha_paletas, text=nome, variable=palette_var, value=nome, font=theme.fonte(11)).pack(side="left", padx=(0, 14))

    _rotulo(inner, "Pré-visualização", font=theme.fonte(11)).pack(anchor="w", pady=(14, 6))
    preview_frame = ctk.CTkFrame(inner, fg_color="transparent")
    preview_frame.pack(anchor="w")

    def atualizar_preview_cor():
        for w in preview_frame.winfo_children():
            w.destroy()
        cores = PALETAS.get(palette_var.get(), PALETAS["Pastel"])
        for c in cores[:12]:
            ctk.CTkFrame(preview_frame, fg_color=c, width=26, height=26, corner_radius=theme.RAIO_BORDA_PEQUENO).pack(side="left", padx=3)

    atualizar_preview_cor()
    palette_var.trace_add("write", lambda *a: atualizar_preview_cor())

    # ---- Animação (animation: type) ----
    f_anim = _card(tab_anim)
    f_anim.pack(fill="x", padx=4, pady=4)
    inner = ctk.CTkFrame(f_anim, fg_color="transparent")
    inner.pack(fill="x", padx=16, pady=16)
    _rotulo(inner, "Animação de entrada (popup não-fullscreen)").pack(anchor="w", pady=(0, 8))
    grade_anim = ctk.CTkFrame(inner, fg_color="transparent")
    grade_anim.pack(anchor="w")
    for idx, (val, lbl) in enumerate(_ANIM_OPCOES):
        ctk.CTkRadioButton(grade_anim, text=lbl, variable=anim_var, value=val, font=theme.fonte(11)).grid(
            row=idx // 3, column=idx % 3, sticky="w", padx=(0, 20), pady=4
        )

    # ---- Áudio (audio: mode, selected, volume, stop_on_close) ----
    f_audio = _card(tab_audio)
    f_audio.pack(fill="both", expand=True, padx=4, pady=4)
    inner = ctk.CTkFrame(f_audio, fg_color="transparent")
    inner.pack(fill="both", expand=True, padx=16, pady=16)

    ctk.CTkRadioButton(inner, text="Aleatório — todos os arquivos da pasta audios", variable=audio_mode_var, value="random", font=theme.fonte(11)).pack(anchor="w", pady=2)
    ctk.CTkRadioButton(inner, text="Apenas os selecionados na lista abaixo (Ctrl+clique para vários)", variable=audio_mode_var, value="selected", font=theme.fonte(11)).pack(anchor="w", pady=2)

    vol_frame = ctk.CTkFrame(inner, fg_color="transparent")
    vol_frame.pack(fill="x", pady=(12, 6))
    linha_vol = ctk.CTkFrame(vol_frame, fg_color="transparent")
    linha_vol.pack(fill="x")
    _rotulo(linha_vol, "Volume das notificações").pack(side="left")
    vol_pct_label = _rotulo(linha_vol, f"{int(_vol_saved)}%", anchor="e")
    vol_pct_label.pack(side="right")

    def atualizar_label_vol(*_a):
        try:
            v = int(round(float(vol_var.get())))
        except (tk.TclError, ValueError):
            return
        vol_pct_label.configure(text=f"{v}%")

    vol_var.trace_add("write", atualizar_label_vol)
    ctk.CTkSlider(vol_frame, from_=0, to=100, variable=vol_var, number_of_steps=100).pack(fill="x", pady=(6, 0))
    _subtitulo(vol_frame, "Afeta o som ao tocar o lembrete e as prévias desta janela (0% = mudo).").pack(anchor="w", pady=(6, 0))

    def cfg_com_volume_atual():
        c = {**carregar_config()}
        try:
            c["notification_volume"] = int(round(float(vol_var.get())))
        except tk.TclError:
            c["notification_volume"] = CONFIG_PADRAO["notification_volume"]
        return c

    _subtitulo(inner, "Lista de arquivos — use a barra de rolagem se houver mais itens.").pack(anchor="w", pady=(10, 4))
    list_wrap = ctk.CTkFrame(inner, fg_color="transparent")
    list_wrap.pack(fill="both", expand=True, pady=4)
    sb_aud = tk.Scrollbar(list_wrap, orient="vertical", width=16)
    lb = tk.Listbox(
        list_wrap, selectmode="extended", height=10,
        bg=theme.COR_FUNDO, fg=theme.COR_TEXTO,
        selectbackground=theme.COR_BOTAO, selectforeground="white",
        font=(theme.FONTE_FAMILIA, 10), highlightthickness=1,
        highlightbackground=theme.COR_BORDA, relief="flat",
        activestyle="dotbox", yscrollcommand=sb_aud.set, bd=0,
    )
    sb_aud.config(command=lb.yview)
    lb.pack(side="left", fill="both", expand=True)
    sb_aud.pack(side="left", fill="y")

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
            parent=root, title="Copiar áudios para a pasta do app",
            filetypes=[
                ("Áudio", "*.wav *.mp3 *.ogg"), ("Wave", "*.wav"),
                ("MP3", "*.mp3"), ("Ogg", "*.ogg"), ("Todos", "*.*"),
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
                        "Substituir?", f'Já existe "{nome}" na pasta audios.\n\nSubstituir pelo arquivo escolhido?',
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
            msg_confirm = f"Deseja remover {len(nomes)} arquivos da pasta audios?\n\nSelecionados: {preview}"
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
            messagebox.showwarning("Áudio", f"Removidos: {removidos}\nFalhas: {len(falhas)}\n\n{detalhes}")
        else:
            messagebox.showinfo("Áudio", f"Arquivos removidos: {removidos}.")

    aud_actions = ctk.CTkFrame(inner, fg_color="transparent")
    aud_actions.pack(fill="x", pady=(10, 4))
    _botao_sec(aud_actions, text="▶ Ouvir", command=reproduzir_selecionado, width=90).pack(side="left", padx=(0, 6), pady=2)
    _botao_sec(aud_actions, text="■ Parar", command=parar_som, width=90).pack(side="left", padx=6, pady=2)
    _botao_sec(aud_actions, text="+ Adicionar…", command=adicionar_audios_explorer, width=110).pack(side="left", padx=6, pady=2)
    _botao_sec(aud_actions, text="🗑 Remover", command=remover_audios_selecionados, width=100).pack(side="left", padx=6, pady=2)
    _botao_sec(aud_actions, text="Abrir pasta", command=abrir_pasta_audios_cmd, width=100).pack(side="left", padx=6, pady=2)

    _subtitulo(inner, "Dica: duplo clique em um item para ouvir a prévia. Pasta: " + pasta_audios()).pack(anchor="w", pady=(4, 0))

    # ---- Avançado (window: control_window_title/status/hint) ----
    f_avancado = _card(tab_avancado)
    f_avancado.pack(fill="x", padx=4, pady=4)
    inner = ctk.CTkFrame(f_avancado, fg_color="transparent")
    inner.pack(fill="x", padx=16, pady=16)
    _rotulo(inner, "Janela principal").pack(anchor="w")
    _subtitulo(inner, "Textos da janela de controle (status/lembretes). Antes só dava pra mudar editando o config.json.").pack(anchor="w", pady=(2, 10))

    _rotulo(inner, "Título da janela").pack(anchor="w", pady=(6, 2))
    ctk.CTkEntry(inner, textvariable=title_var, font=theme.fonte(11)).pack(fill="x")
    _rotulo(inner, "Texto de status").pack(anchor="w", pady=(10, 2))
    ctk.CTkEntry(inner, textvariable=status_txt_var, font=theme.fonte(11)).pack(fill="x")
    _rotulo(inner, "Dica exibida abaixo do status").pack(anchor="w", pady=(10, 2))
    ctk.CTkEntry(inner, textvariable=hint_var, font=theme.fonte(11)).pack(fill="x")

    # ========= Rodapé =========
    btn_frame = ctk.CTkFrame(main, fg_color=theme.COR_CARD, corner_radius=theme.RAIO_BORDA)
    btn_frame.pack(fill="x", pady=(0, 0))
    rodape = ctk.CTkFrame(btn_frame, fg_color="transparent")
    rodape.pack(fill="x", padx=10, pady=10)

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
        if campos_invalidos:
            messagebox.showerror("Erro", "Corrija os campos destacados em vermelho antes de salvar.")
            return
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
            "control_window_title": title_var.get().strip() or CONFIG_PADRAO["control_window_title"],
            "control_window_status": status_txt_var.get().strip() or CONFIG_PADRAO["control_window_status"],
            "control_window_hint": hint_var.get().strip() or CONFIG_PADRAO["control_window_hint"],
        }
        salvar_config(novo_cfg)
        _parar_preview()
        _parar_monitoramento_prefetch()
        messagebox.showinfo("Salvo", "Configurações salvas! As mudanças valerão no próximo lembrete.")
        root.destroy()

    def _ao_fechar_config():
        _parar_preview()
        _parar_monitoramento_prefetch()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _ao_fechar_config)

    _botao_sec(rodape, text="Testar popup", command=testar, width=140).pack(side="left")
    btn_salvar = _botao_pri(rodape, text="Salvar", command=salvar, width=140)
    btn_salvar.pack(side="right")
    _botao_salvar_ref["widget"] = btn_salvar
    _atualizar_estado_salvar()

    if is_top_level:
        parent.wait_window(root)
    else:
        root.mainloop()
