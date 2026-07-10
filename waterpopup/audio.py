"""Reprodução de áudio (pygame) para os lembretes e prévias da tela de configuração."""

import os
import sys
import logging
import subprocess
import random
from typing import Any, Dict, List, Optional

import pygame

from .config import CONFIG_PADRAO, caminho_recurso, pasta_base, carregar_config

pygame.mixer.init()

def pasta_audios() -> str:
    externa = os.path.join(pasta_base(), "audios")
    if os.path.isdir(externa):
        return externa
    return caminho_recurso("audios")

def _volume_pygame_de_cfg(cfg: Optional[Dict[str, Any]]) -> float:
    """0.0–1.0 a partir de notification_volume (0–100) no dict cfg."""
    if cfg is None:
        cfg = carregar_config()
    try:
        pct = float(cfg.get("notification_volume", CONFIG_PADRAO["notification_volume"]))
    except (TypeError, ValueError):
        pct = 100.0
    return max(0.0, min(1.0, pct / 100.0))

def listar_audios() -> List[str]:
    p = pasta_audios()
    if not os.path.isdir(p):
        return []
    return [f for f in os.listdir(p) if f.lower().endswith((".wav", ".mp3", ".ogg"))]

def tocar_arquivo_audio(caminho: str, cfg: Optional[Dict[str, Any]] = None) -> None:
    """Reproduz um arquivo específico (prévia na config ou lembrete). cfg opcional para volume."""
    try:
        pygame.mixer.music.set_volume(_volume_pygame_de_cfg(cfg))
        pygame.mixer.music.load(caminho)
        pygame.mixer.music.play()
    except Exception as e:
        raise RuntimeError(str(e)) from e

def tocar_som(cfg: Optional[Dict[str, Any]] = None) -> None:
    if cfg is None:
        cfg = carregar_config()
    if not cfg.get("audio_enabled", True):
        return
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
        tocar_arquivo_audio(wav_path, cfg)
    except Exception as e:
        logging.warning("Erro ao tocar som '%s': %s", wav_path, e)

def parar_som() -> None:
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass

def abrir_pasta_no_explorador(pasta: str) -> None:
    os.makedirs(pasta, exist_ok=True)
    pasta = os.path.normpath(pasta)
    if sys.platform == "win32":
        os.startfile(pasta)
    elif sys.platform == "darwin":
        subprocess.run(["open", pasta], check=False)
    else:
        subprocess.run(["xdg-open", pasta], check=False)
