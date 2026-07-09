"""Localização de arquivos, esquema de configuração (dataclasses), migração
automática do formato antigo (flat) para o novo (v2, aninhado) e leitura/
gravação de config.json.

O restante do app sempre lê/grava um dict "flat" (as mesmas chaves de
sempre, ex.: ``cfg.get("interval_minutes")``) — só este módulo conhece o
formato aninhado gravado em disco.
"""

import os
import sys
import json
import time
import shutil
import logging
from dataclasses import dataclass, field, fields, asdict
from typing import Any, Dict, List, Optional
import tkinter as tk
from tkinter import messagebox

# ============ PATHS ============

def pasta_base() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # Este arquivo vive em <projeto>/waterpopup/config.py — sobe dois níveis
    # (o arquivo em si e a pasta do pacote) para achar a raiz do projeto.
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_config_path_override: Optional[str] = None

def definir_caminho_override(path: Optional[str]) -> None:
    """Força um caminho de config.json específico para a sessão atual (--config-path)."""
    global _config_path_override
    _config_path_override = path

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

def pasta_config() -> str:
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

def caminho_config() -> str:
    if _config_path_override:
        return _config_path_override
    env_path = os.environ.get("WATERPOPUP_CONFIG_PATH")
    if env_path:
        return env_path
    return os.path.join(pasta_config(), "config.json")

def caminho_recurso(rel: str) -> str:
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = pasta_base()
    return os.path.join(base, rel)

# ============ PALETAS DE CORES ============

PALETAS: Dict[str, List[str]] = {
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

# Valores válidos usados tanto pela validação do config quanto pela lógica
# de posicionamento/animação do popup.
CANTOS_POPUP = ("top-right", "top-left", "bottom-right", "bottom-left")
POSICOES_POPUP = CANTOS_POPUP + ("center",)
ANIMACOES = ["slide", "slide-vertical", "scale", "bounce", "elastic", "drop", "fade"]

# ============ CONFIG ============

CONFIG_PADRAO: Dict[str, Any] = {
    "message": "Hora da sua notificação personalizada! 🔔",
    "interval_minutes": 10,
    "popup_duration_seconds": 5,
    "fullscreen_notification": False,
    "stop_audio_on_close": True,
    "visual_mode": "notification",
    "gif_mode": "single",
    "gif_fit_mode": "contain",
    "gif_fullscreen_zoom_percent": 140,
    "gif_path": "",
    "gif_history": [],
    "random_colors": True,
    "color_palette": "Pastel",
    "colors": PALETAS["Pastel"].copy(),
    "popup_animation": "slide",
    "popup_position": "top-right",
    "font_size": 14,
    "fun_mode": "none",
    "audio_mode": "random",
    "selected_audios": [],
    "notification_volume": 100,
    "control_window_title": "🔔 Water Popup",
    "control_window_status": "Notificações ativas",
    "control_window_hint": "Feche esta janela para encerrar as notificações",
}

_config_cache: Optional[Dict[str, Any]] = None
_config_mtime: float = 0

# ---- Estrutura v2 (aninhada, gravada em disco) ----
#
# O restante do app continua lendo/gravando um dict "flat" (as mesmas chaves
# de sempre, ex.: cfg.get("interval_minutes")) — só esta seção conhece o
# formato aninhado. Isso reduz muito o risco de quebrar popup/GUI durante a
# reorganização do config.json.

def _coagir_int(valor, padrao, minimo=None, maximo=None) -> int:
    try:
        v = int(round(float(valor)))
    except (TypeError, ValueError):
        v = padrao
    if minimo is not None:
        v = max(minimo, v)
    if maximo is not None:
        v = min(maximo, v)
    return v

def _coagir_bool(valor, padrao) -> bool:
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        low = valor.strip().lower()
        if low in ("true", "1", "sim"):
            return True
        if low in ("false", "0", "não", "nao"):
            return False
    return padrao

def _coagir_str(valor, padrao) -> str:
    return valor if isinstance(valor, str) else padrao

def _coagir_lista_str(valor, padrao) -> list:
    if isinstance(valor, list) and all(isinstance(x, str) for x in valor):
        return list(valor)
    return list(padrao)

@dataclass
class GeneralCfg:
    """Intervalo entre lembretes e duração do popup na tela."""
    interval_minutes: int = 10
    duration_seconds: int = 5
    def __post_init__(self):
        self.interval_minutes = _coagir_int(self.interval_minutes, 10, 1, 120)
        self.duration_seconds = _coagir_int(self.duration_seconds, 5, 3, 60)

@dataclass
class MessageCfg:
    """Texto da notificação, tamanho de fonte e efeito divertido aplicado."""
    text: str = "Hora da sua notificação personalizada! 🔔"
    font_size: int = 14
    effect: str = "none"
    def __post_init__(self):
        self.text = _coagir_str(self.text, MessageCfg.text) or MessageCfg.text
        self.font_size = _coagir_int(self.font_size, 14, 10, 24)
        if self.effect not in ("none", "sparkles", "water", "party"):
            self.effect = "none"

@dataclass
class VisualCfg:
    """Modo de exibição (texto/GIF), tela cheia e ajuste do GIF."""
    mode: str = "notification"
    fullscreen: bool = False
    fit_mode: str = "contain"
    gif_zoom_percent: int = 140
    def __post_init__(self):
        if self.mode not in ("notification", "gif"):
            self.mode = "notification"
        self.fullscreen = _coagir_bool(self.fullscreen, False)
        if self.fit_mode not in ("contain", "cover"):
            self.fit_mode = "contain"
        self.gif_zoom_percent = _coagir_int(self.gif_zoom_percent, 140, 100, 300)

@dataclass
class PositionCfg:
    """Posição do popup na tela (canto fixo, centro ou aleatório)."""
    value: str = "top-right"
    def __post_init__(self):
        if self.value not in POSICOES_POPUP + ("random",):
            self.value = "top-right"

@dataclass
class ColorsCfg:
    """Cor de fundo do popup: aleatória ou fixa, a partir de uma paleta nomeada."""
    random: bool = True
    palette: str = "Pastel"
    values: list = field(default_factory=lambda: PALETAS["Pastel"].copy())
    def __post_init__(self):
        self.random = _coagir_bool(self.random, True)
        if self.palette not in PALETAS:
            self.palette = "Pastel"
        # A paleta nomeada é sempre a fonte da verdade das cores (mesma regra
        # que o app já seguia antes da reorganização do config).
        self.values = PALETAS[self.palette].copy()

@dataclass
class AnimationCfg:
    """Animação de entrada do popup (deslizar, zoom, bounce etc.)."""
    type: str = "slide"
    def __post_init__(self):
        if self.type not in set(ANIMACOES) | {"none"}:
            self.type = "slide"

@dataclass
class AudioCfg:
    """Modo de seleção de áudio, arquivos escolhidos, volume e parar-ao-fechar."""
    mode: str = "random"
    selected: list = field(default_factory=list)
    volume: int = 100
    stop_on_close: bool = True
    def __post_init__(self):
        if self.mode not in ("random", "selected"):
            self.mode = "random"
        self.selected = _coagir_lista_str(self.selected, [])
        self.volume = _coagir_int(self.volume, 100, 0, 100)
        self.stop_on_close = _coagir_bool(self.stop_on_close, True)

@dataclass
class GifsCfg:
    """GIF atual, modo (fixo/aleatório do histórico) e histórico salvo."""
    mode: str = "single"
    current: str = ""
    history: list = field(default_factory=list)
    def __post_init__(self):
        if self.mode not in ("single", "random_history"):
            self.mode = "single"
        self.current = _coagir_str(self.current, "")
        self.history = _coagir_lista_str(self.history, [])

@dataclass
class WindowCfg:
    """Textos da janela de controle principal."""
    control_window_title: str = "🔔 Water Popup"
    control_window_status: str = "Notificações ativas"
    control_window_hint: str = "Feche esta janela para encerrar as notificações"
    def __post_init__(self):
        self.control_window_title = _coagir_str(self.control_window_title, WindowCfg.control_window_title)
        self.control_window_status = _coagir_str(self.control_window_status, WindowCfg.control_window_status)
        self.control_window_hint = _coagir_str(self.control_window_hint, WindowCfg.control_window_hint)

@dataclass
class ConfigV2:
    """Estrutura v2 completa, gravada em config.json."""
    version: int = 2
    general: GeneralCfg = field(default_factory=GeneralCfg)
    message: MessageCfg = field(default_factory=MessageCfg)
    visual: VisualCfg = field(default_factory=VisualCfg)
    position: PositionCfg = field(default_factory=PositionCfg)
    colors: ColorsCfg = field(default_factory=ColorsCfg)
    animation: AnimationCfg = field(default_factory=AnimationCfg)
    audio: AudioCfg = field(default_factory=AudioCfg)
    gifs: GifsCfg = field(default_factory=GifsCfg)
    window: WindowCfg = field(default_factory=WindowCfg)

# Mapeamento chave-flat <-> (seção, campo) aninhado. Única fonte de verdade
# usada por: migração, salvar, --print-config e --set com chave aninhada.
_MAPA_FLAT_PARA_NESTED = {
    "message": ("message", "text"),
    "font_size": ("message", "font_size"),
    "fun_mode": ("message", "effect"),
    "interval_minutes": ("general", "interval_minutes"),
    "popup_duration_seconds": ("general", "duration_seconds"),
    "visual_mode": ("visual", "mode"),
    "fullscreen_notification": ("visual", "fullscreen"),
    "gif_fit_mode": ("visual", "fit_mode"),
    "gif_fullscreen_zoom_percent": ("visual", "gif_zoom_percent"),
    "popup_position": ("position", "value"),
    "random_colors": ("colors", "random"),
    "color_palette": ("colors", "palette"),
    "colors": ("colors", "values"),
    "popup_animation": ("animation", "type"),
    "audio_mode": ("audio", "mode"),
    "selected_audios": ("audio", "selected"),
    "notification_volume": ("audio", "volume"),
    "stop_audio_on_close": ("audio", "stop_on_close"),
    "gif_mode": ("gifs", "mode"),
    "gif_path": ("gifs", "current"),
    "gif_history": ("gifs", "history"),
    "control_window_title": ("window", "control_window_title"),
    "control_window_status": ("window", "control_window_status"),
    "control_window_hint": ("window", "control_window_hint"),
}
MAPA_NESTED_PARA_FLAT = {f"{secao}.{campo}": chave for chave, (secao, campo) in _MAPA_FLAT_PARA_NESTED.items()}

def aninhar_flat(flat: dict) -> dict:
    """Converte um dict flat (chaves como 'interval_minutes') para a estrutura
    aninhada v2 (seções general/message/visual/...)."""
    nested = {"version": 2}
    for chave_flat, (secao, campo) in _MAPA_FLAT_PARA_NESTED.items():
        valor = flat.get(chave_flat, CONFIG_PADRAO.get(chave_flat))
        nested.setdefault(secao, {})[campo] = valor
    return nested

def _achatar_nested(nested: dict) -> dict:
    """Converte a estrutura aninhada v2 de volta para o dict flat usado
    internamente pelo resto do app."""
    flat = CONFIG_PADRAO.copy()
    for chave_flat, (secao, campo) in _MAPA_FLAT_PARA_NESTED.items():
        secao_dict = nested.get(secao)
        if isinstance(secao_dict, dict) and campo in secao_dict:
            flat[chave_flat] = secao_dict[campo]
    return flat

def _construir_config_v2(dados: dict) -> ConfigV2:
    """Constrói um ConfigV2 validado a partir de um dict aninhado bruto
    (possivelmente incompleto ou com tipos/valores inválidos)."""
    def secao(nome, cls):
        bruto = dados.get(nome) if isinstance(dados, dict) else None
        if not isinstance(bruto, dict):
            bruto = {}
        campos_validos = {f.name for f in fields(cls)}
        bruto = {k: v for k, v in bruto.items() if k in campos_validos}
        try:
            return cls(**bruto)
        except Exception as e:
            logging.warning("Seção de config '%s' inválida (%s); usando padrão.", nome, e)
            return cls()

    return ConfigV2(
        version=2,
        general=secao("general", GeneralCfg),
        message=secao("message", MessageCfg),
        visual=secao("visual", VisualCfg),
        position=secao("position", PositionCfg),
        colors=secao("colors", ColorsCfg),
        animation=secao("animation", AnimationCfg),
        audio=secao("audio", AudioCfg),
        gifs=secao("gifs", GifsCfg),
        window=secao("window", WindowCfg),
    )

def _config_tem_versao_atual(dados) -> bool:
    return isinstance(dados, dict) and dados.get("version") == 2

def _fazer_backup_config(path: str, sufixo: str, somente_se_ausente: bool = False) -> None:
    """Copia o config.json atual para um arquivo de backup antes de sobrescrevê-lo."""
    if not os.path.isfile(path):
        return
    if sufixo == "bak":
        destino = path + ".bak"
        if somente_se_ausente and os.path.exists(destino):
            return
    else:
        ts = time.strftime("%Y%m%d-%H%M%S")
        destino = f"{path}.{sufixo}-{ts}.bak"
    try:
        shutil.copy2(path, destino)
        logging.info("Backup do config.json anterior salvo em %s", destino)
    except OSError as e:
        logging.warning("Falha ao gerar backup do config.json: %s", e)

def _avisar_config_restaurado() -> None:
    """Mostra um aviso ao usuário quando há uma janela Tk ativa (fluxo GUI);
    em fluxos puramente CLI, o aviso já foi registrado via logging."""
    try:
        if tk._default_root is not None:
            messagebox.showwarning(
                "Configuração",
                "O arquivo config.json estava corrompido ou em formato inválido.\n"
                "As configurações foram restauradas para o padrão (um backup do "
                "arquivo anterior foi salvo ao lado dele).",
            )
    except Exception:
        pass

def carregar_config() -> Dict[str, Any]:
    """Lê o config.json (migrando/validando se necessário) e retorna o dict
    flat usado internamente pelo resto do app."""
    global _config_cache, _config_mtime
    path = caminho_config()
    if not os.path.exists(path):
        cfg_inicial = CONFIG_PADRAO.copy()
        salvar_config(cfg_inicial)
        return cfg_inicial

    try:
        mtime = os.path.getmtime(path)
    except OSError as e:
        logging.error("Não foi possível acessar config.json: %s", e)
        return CONFIG_PADRAO.copy()

    if mtime == _config_mtime and _config_cache:
        return _config_cache

    try:
        with open(path, "r", encoding="utf-8") as f:
            dados = json.load(f)
        if not isinstance(dados, dict):
            raise ValueError(f"formato inesperado ({type(dados).__name__})")
    except (json.JSONDecodeError, ValueError, OSError) as e:
        logging.error("config.json inválido/corrompido (%s). Restaurando valores padrão.", e)
        _fazer_backup_config(path, sufixo="corrompido")
        cfg_inicial = CONFIG_PADRAO.copy()
        salvar_config(cfg_inicial)
        _avisar_config_restaurado()
        return cfg_inicial

    migrando = not _config_tem_versao_atual(dados)
    if migrando:
        logging.info("config.json em formato antigo (v1); migrando para a estrutura v2.")
        _fazer_backup_config(path, sufixo="bak", somente_se_ausente=True)
        nested = aninhar_flat(dados)
    else:
        nested = dados

    cfg_v2 = _construir_config_v2(nested)
    nested_validado = asdict(cfg_v2)
    flat = _achatar_nested(nested_validado)

    if migrando:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(nested_validado, f, indent=2, ensure_ascii=False)
            mtime = os.path.getmtime(path)
        except OSError as e:
            logging.warning("Não foi possível gravar config.json migrado: %s", e)

    _config_cache = flat
    _config_mtime = mtime
    return _config_cache

def salvar_config(cfg: Dict[str, Any]) -> None:
    """Valida/clampa `cfg` (dict flat) e grava a estrutura v2 em config.json."""
    global _config_cache, _config_mtime
    path = caminho_config()
    os.makedirs(os.path.dirname(path), exist_ok=True)

    nested = aninhar_flat({**CONFIG_PADRAO, **cfg})
    cfg_v2 = _construir_config_v2(nested)
    nested_validado = asdict(cfg_v2)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(nested_validado, f, indent=2, ensure_ascii=False)

    _config_cache = _achatar_nested(nested_validado)
    _config_mtime = os.path.getmtime(path)
