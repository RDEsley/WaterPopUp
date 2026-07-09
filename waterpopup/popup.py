"""Janelas de notificação (popup): texto ou GIF animado, com suporte a
tela cheia multi-monitor sincronizada."""

import os
import math
import random
import shutil
import logging
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple
import tkinter as tk

try:
    from PIL import Image, ImageTk, ImageOps
    PIL_DISPONIVEL = True
except Exception:
    Image = ImageTk = ImageOps = None
    PIL_DISPONIVEL = False

if PIL_DISPONIVEL:
    try:
        PIL_RESAMPLING_LANCZOS = Image.Resampling.LANCZOS
    except Exception:
        PIL_RESAMPLING_LANCZOS = Image.LANCZOS
else:
    PIL_RESAMPLING_LANCZOS = None

from .config import PALETAS, CONFIG_PADRAO, pasta_base, pasta_config, carregar_config
from .monitors import listar_monitores
from .animations import resolver_posicao_popup, pos_inicial, animar_entrada
from .audio import tocar_som, parar_som

# ============ GIFs: pasta, importação e histórico ============

def pasta_gifs() -> str:
    externa = os.path.join(pasta_base(), "gifs")
    if os.path.isdir(externa):
        return externa
    interna = os.path.join(pasta_config(), "gifs")
    os.makedirs(interna, exist_ok=True)
    return interna

def importar_gif_para_app(origem: str) -> str:
    origem_abs = os.path.abspath(origem)
    if not origem_abs.lower().endswith(".gif"):
        raise ValueError("Selecione um arquivo .gif")
    if not os.path.isfile(origem_abs):
        raise FileNotFoundError("Arquivo GIF não encontrado")

    destino_dir = pasta_gifs()
    os.makedirs(destino_dir, exist_ok=True)
    destino = os.path.join(destino_dir, os.path.basename(origem_abs))

    if os.path.normcase(origem_abs) == os.path.normcase(os.path.abspath(destino)):
        return destino

    shutil.copy2(origem_abs, destino)
    return destino

def normalizar_historico_gifs(lista: Optional[List[str]]) -> List[str]:
    vistos = set()
    normalizados = []
    for item in lista or []:
        p = os.path.normpath(str(item).strip())
        if not p or not p.lower().endswith(".gif"):
            continue
        chave = os.path.normcase(p)
        if chave in vistos:
            continue
        vistos.add(chave)
        normalizados.append(p)
    return normalizados

def resolver_gif_do_popup(cfg: Dict[str, Any]) -> str:
    gif_mode = str(cfg.get("gif_mode", "single")).lower().strip()
    gif_atual = (cfg.get("gif_path") or "").strip()
    historico = normalizar_historico_gifs(cfg.get("gif_history", []))
    validos = [p for p in historico if os.path.isfile(p)]
    if gif_mode == "random_history" and validos:
        return random.choice(validos)
    if gif_atual and os.path.isfile(gif_atual):
        return gif_atual
    if validos:
        return validos[-1]
    return gif_atual

# ============ Renderização do popup ============

_CACHE_FRAMES_GIF = OrderedDict()
_CACHE_FRAMES_GIF_MAX = 8

def _tk_cor_para_rgb(widget, cor: str) -> Tuple[int, int, int]:
    """Resolve uma cor do Tk (hex '#RRGGBB' ou nome como 'light pink') para uma
    tupla RGB 0-255. O Pillow não entende nomes de cor do Tk, então usamos o
    próprio Tk (winfo_rgb) pra resolver qualquer cor válida de forma genérica."""
    try:
        r, g, b = widget.winfo_rgb(cor)
        return (r // 256, g // 256, b // 256)
    except Exception:
        return (0, 0, 0)

def _carregar_frames_gif(caminho_gif, max_w=None, max_h=None, fit_mode="contain", fullscreen_zoom=1.0, cor_fundo=(0, 0, 0)):
    """
    Carrega GIF animado com Pillow para evitar artefatos visuais do tk.PhotoImage
    (borrões pretos / transparência) e reduzir risco de crash por memória.

    Redimensiona mantendo a proporção original (LANCZOS). GIFs com muitos
    frames são sub-amostrados (no máximo `max_frames` quadros) para manter o
    carregamento rápido mesmo em arquivos grandes. Os frames já processados
    (por caminho + tamanho + modo + zoom + cor) ficam em cache em memória
    durante a sessão, então reexibir o mesmo GIF não reprocessa nada.

    Retorna (frames, duracoes_ms).
    """
    if not PIL_DISPONIVEL:
        return [], []

    try:
        mtime = os.path.getmtime(caminho_gif)
    except OSError:
        mtime = 0
    cor_fundo = tuple(cor_fundo)
    chave = (os.path.normcase(os.path.abspath(caminho_gif)), mtime, max_w, max_h, fit_mode, round(fullscreen_zoom, 3), cor_fundo)
    if chave in _CACHE_FRAMES_GIF:
        _CACHE_FRAMES_GIF.move_to_end(chave)
        return _CACHE_FRAMES_GIF[chave]

    frames = []
    duracoes = []
    max_frames = 180
    min_delay = 20
    max_delay = 300

    try:
        with Image.open(caminho_gif) as img:
            total_frames = max(1, int(getattr(img, "n_frames", 1)))
            step = max(1, math.ceil(total_frames / max_frames))

            for idx in range(0, total_frames, step):
                img.seek(idx)
                frame = img.convert("RGBA")
                if max_w and max_h:
                    if fit_mode == "cover":
                        frame = ImageOps.fit(
                            frame,
                            (max_w, max_h),
                            method=PIL_RESAMPLING_LANCZOS,
                            centering=(0.5, 0.5),
                        )
                    else:
                        frame = ImageOps.contain(frame, (max_w, max_h), method=PIL_RESAMPLING_LANCZOS)

                    # Zoom extra (somente para tela cheia). Depois corta no centro para manter composição.
                    if fullscreen_zoom > 1.0:
                        zoom_w = max(1, int(frame.width * fullscreen_zoom))
                        zoom_h = max(1, int(frame.height * fullscreen_zoom))
                        frame = frame.resize((zoom_w, zoom_h), PIL_RESAMPLING_LANCZOS)
                        if zoom_w >= max_w and zoom_h >= max_h:
                            left = (zoom_w - max_w) // 2
                            top = (zoom_h - max_h) // 2
                            frame = frame.crop((left, top, left + max_w, top + max_h))
                        else:
                            fundo = Image.new("RGBA", (max_w, max_h), (*cor_fundo, 255))
                            paste_x = (max_w - zoom_w) // 2
                            paste_y = (max_h - zoom_h) // 2
                            fundo.paste(frame, (paste_x, paste_y), frame)
                            frame = fundo
                tk_frame = ImageTk.PhotoImage(frame)
                frames.append(tk_frame)
                dur = int(img.info.get("duration", 80) or 80)
                duracoes.append(max(min_delay, min(max_delay, dur * step)))
    except Exception as e:
        logging.warning("Falha ao decodificar GIF '%s': %s", caminho_gif, e)
        return [], []

    resultado = (frames, duracoes)
    _CACHE_FRAMES_GIF[chave] = resultado
    _CACHE_FRAMES_GIF.move_to_end(chave)
    while len(_CACHE_FRAMES_GIF) > _CACHE_FRAMES_GIF_MAX:
        _CACHE_FRAMES_GIF.popitem(last=False)
    return resultado

def _aplicar_modo_divertido(msg: str, cfg: Dict[str, Any]) -> str:
    modo = str(cfg.get("fun_mode", "none")).strip().lower()
    if modo == "sparkles":
        return f"✨ {msg} ✨"
    if modo == "party":
        return f"🎉 {msg} 🥳"
    if modo == "water":
        gotas = "".join(random.choice(["💧", "🫧", "🌊"]) for _ in range(3))
        return f"{gotas}  {msg}  {gotas}"
    return msg

def _preparar_conteudo_notificacao(janela, popup_w, fullscreen, cor, txt, font_size, fechar_popup):
    """Cria o Label de texto padrão (modo não-GIF) dentro de uma janela de popup."""
    lbl = tk.Label(
        janela,
        text=txt,
        font=("Segoe UI", font_size, "bold"),
        bg=cor,
        fg="#1a1a2e",
        wraplength=max(300, popup_w - 80),
        cursor="hand2",
        relief="flat",
        padx=16 if not fullscreen else 40,
        pady=16 if not fullscreen else 40,
        justify="center",
    )
    lbl.pack(expand=True, fill="both")
    lbl.bind("<Button-1>", lambda e: fechar_popup())
    return lbl

def _preparar_janela_gif(janela, fullscreen, cor, fechar_popup):
    """Monta o container + Label de imagem de uma janela de popup em modo GIF.

    O fundo (que aparece como letterbox/pillarbox ao redor do GIF quando a
    proporção não bate com a da tela) usa a cor escolhida para o popup, em
    vez de preto fixo.
    """
    janela.configure(bg=cor)
    bg_container = tk.Frame(janela, bg=cor)
    bg_container.pack(expand=True, fill="both")
    bg_container.bind("<Button-1>", lambda e: fechar_popup())

    gif_label = tk.Label(
        bg_container,
        bg=cor,
        cursor="hand2",
        bd=0,
        highlightthickness=0,
        relief="flat",
    )
    gif_label.place(relx=0.5, rely=0.5, anchor="center")
    gif_label.bind("<Button-1>", lambda e: fechar_popup())

    if fullscreen:
        hint = tk.Label(
            bg_container,
            text="Clique para fechar",
            bg="#000000",
            fg="#f8fafc",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=6,
        )
        hint.place(relx=0.5, rely=0.96, anchor="s")
        hint.bind("<Button-1>", lambda e: fechar_popup())

    return gif_label

def _iniciar_animacao_gif_sincronizada(janela_mestre, grupos):
    """Anima várias janelas (uma por monitor) com o MESMO frame ao mesmo tempo.

    `grupos` é uma lista de (gif_label, frames, duracoes) — um por janela. Um
    único laço `after`, preso à janela mestre, avança o índice de frame e
    atualiza todos os labels no mesmo tick, evitando que loops independentes
    percam a sincronia entre monitores.
    """
    duracoes_ref = grupos[0][2]
    total = len(duracoes_ref)

    def tick(i=0):
        if not janela_mestre.winfo_exists():
            return
        i = i % total
        for gif_label, frames, _duracoes in grupos:
            try:
                if not gif_label.winfo_exists():
                    continue
                frame = frames[i % len(frames)]
                gif_label.configure(image=frame)
                gif_label.image = frame
            except tk.TclError:
                continue
        delay = duracoes_ref[i] if i < len(duracoes_ref) else 80
        janela_mestre._gif_after_id = janela_mestre.after(delay, lambda: tick(i + 1))

    tick(0)

def mostrar_popup(parent=None, cfg_override: Optional[Dict[str, Any]] = None) -> None:
    """Exibe um popup de notificação (texto ou GIF), respeitando tela cheia
    multi-monitor quando configurada."""
    base = cfg_override or carregar_config()
    cfg = resolver_posicao_popup(base)
    tocar_som(base)

    root = tk.Toplevel(parent) if parent is not None else tk.Tk()
    root.title("Notificação")
    root.attributes("-topmost", True)
    root.overrideredirect(True)
    root.configure(bg="white")

    fullscreen = bool(cfg.get("fullscreen_notification", False))
    monitores = listar_monitores(root) if fullscreen else None

    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    if fullscreen:
        popup_w, popup_h = monitores[0].width, monitores[0].height
        x1, y1 = monitores[0].x, monitores[0].y
    else:
        popup_w, popup_h = 340, 130
        x1, y1 = pos_inicial(cfg, w, h, popup_w, popup_h)

    root.geometry(f"{popup_w}x{popup_h}+{x1}+{y1}")

    if cfg.get("random_colors", True):
        cores = cfg.get("colors", PALETAS["Pastel"])
        cor = random.choice(cores) if cores else "#87CEEB"
    else:
        cores = cfg.get("colors", PALETAS["Pastel"])
        cor = cores[0] if cores else "#87CEEB"

    msg = _aplicar_modo_divertido(cfg.get("message", CONFIG_PADRAO["message"]), cfg)
    duracao_ms = int(cfg.get("popup_duration_seconds", 12)) * 1000
    stop_audio = cfg.get("stop_audio_on_close", True)
    font_size = int(cfg.get("font_size", 14))
    visual_mode = str(cfg.get("visual_mode", "notification")).lower().strip()
    if visual_mode not in ("notification", "gif"):
        visual_mode = "notification"
    gif_fit_mode = str(cfg.get("gif_fit_mode", "contain")).strip().lower()
    if gif_fit_mode not in ("contain", "cover"):
        gif_fit_mode = "contain"
    try:
        gif_zoom_pct = int(round(float(cfg.get("gif_fullscreen_zoom_percent", 140))))
    except (TypeError, ValueError):
        gif_zoom_pct = 140
    gif_zoom_pct = max(100, min(300, gif_zoom_pct))
    gif_zoom_mult = gif_zoom_pct / 100.0
    gif_path = resolver_gif_do_popup(cfg).strip()
    root._gif_after_id = None

    # Em fullscreen com 2+ monitores, cria uma Toplevel borderless extra por
    # monitor além do próprio `root` (que cobre o monitor[0]). Todas fecham
    # juntas e exibem o mesmo conteúdo, sincronizado no caso de GIF.
    janelas_extra = []
    if fullscreen and monitores and len(monitores) > 1:
        for m in monitores[1:]:
            extra = tk.Toplevel(root)
            extra.title("Notificação")
            extra.attributes("-topmost", True)
            extra.overrideredirect(True)
            extra.configure(bg="white")
            extra.geometry(f"{m.width}x{m.height}+{m.x}+{m.y}")
            janelas_extra.append(extra)

    janelas_geo = [(root, popup_w, popup_h)] + [
        (j, m.width, m.height) for j, m in zip(janelas_extra, (monitores[1:] if monitores else []))
    ]

    def fechar_popup():
        if getattr(root, "_gif_after_id", None) is not None:
            try:
                root.after_cancel(root._gif_after_id)
            except Exception:
                pass
            root._gif_after_id = None
        if stop_audio:
            parar_som()
        for j in janelas_extra:
            try:
                if j.winfo_exists():
                    j.destroy()
            except Exception:
                pass
        if root.winfo_exists():
            root.destroy()

    for j in janelas_extra:
        j.bind("<Button-1>", lambda e: fechar_popup())

    if visual_mode == "gif" and os.path.isfile(gif_path):
        if not PIL_DISPONIVEL:
            visual_mode = "notification"
            msg = "Pillow não instalado para renderizar GIF. Usando notificação padrão.\n\n" + msg
        else:
            cor_fundo_gif = _tk_cor_para_rgb(root, cor)
            grupos_gif = []
            falhou = False
            for janela, jw, jh in janelas_geo:
                area_w = max(160, jw - (80 if fullscreen else 20))
                area_h = max(120, jh - (120 if fullscreen else 20))
                gif_label = _preparar_janela_gif(janela, fullscreen, cor, fechar_popup)
                frames, duracoes = _carregar_frames_gif(
                    gif_path,
                    area_w,
                    area_h,
                    gif_fit_mode,
                    gif_zoom_mult if fullscreen else 1.0,
                    cor_fundo_gif,
                )
                if not frames:
                    falhou = True
                    break
                grupos_gif.append((gif_label, frames, duracoes))

            if not falhou and grupos_gif:
                root._gif_grupos = grupos_gif  # mantém referência viva (evita garbage collection)
                _iniciar_animacao_gif_sincronizada(root, grupos_gif)
            else:
                visual_mode = "notification"
                msg = "Não foi possível decodificar o GIF. Usando notificação padrão.\n\n" + msg
                for janela, _jw, _jh in janelas_geo:
                    for child in janela.winfo_children():
                        child.destroy()

    if visual_mode != "gif":
        txt = msg
        if cfg.get("visual_mode") == "gif" and gif_path and not os.path.isfile(gif_path):
            txt = f"GIF não encontrado, exibindo notificação padrão.\n\n{msg}"
        for janela, jw, _jh in janelas_geo:
            _preparar_conteudo_notificacao(janela, jw, fullscreen, cor, txt, font_size, fechar_popup)

    def agendar_fechar():
        root.after(duracao_ms, fechar_popup)

    if fullscreen:
        agendar_fechar()
    else:
        animar_entrada(root, cfg, x1, y1, agendar_fechar)
    if parent is None:
        root.mainloop()
