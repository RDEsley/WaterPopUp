"""Cache persistente em disco dos frames de GIF já decodificados e
redimensionados, e pré-processamento em background — para eliminar o
lag de decodificar/redimensionar GIFs grandes na hora de exibir o popup.

Este módulo é intencionalmente livre de Tkinter: toda a decodificação e
redimensionamento aqui usa só Pillow, o que o torna seguro para rodar
em uma thread de background (Tk não é thread-safe; quem precisar de um
``ImageTk.PhotoImage`` a partir do resultado deve criá-lo na thread
principal — é isso que ``popup.py`` faz).

O cache em disco guarda, por combinação (hash do conteúdo do arquivo
original + resolução alvo + modo de ajuste + zoom + cor de fundo), os
frames já prontos como JPEGs individuais + um `meta.json` com as
durações. JPEG foi escolhido depois de medir: um único WEBP/PNG
animado é 10-300x mais lento de gravar que frames JPEG separados para
um GIF grande (veja o histórico do commit desta frente para os
números), o que importa porque essa gravação roda em background toda
vez que um GIF novo é detectado. Como cada entrada de cache já é
específica para uma cor de fundo, achatar a transparência nessa mesma
cor antes de salvar não muda nada visualmente.
"""

import os
import json
import math
import queue
import shutil
import time
import hashlib
import logging
import threading
from typing import Iterable, List, Optional, Tuple

from PIL import Image, ImageOps

from .config import pasta_config

try:
    PIL_RESAMPLING_LANCZOS = Image.Resampling.LANCZOS
except Exception:
    PIL_RESAMPLING_LANCZOS = Image.LANCZOS

_CACHE_DIR_NOME = ".cache"
_CACHE_MAX_ARQUIVOS = 150
_MAX_FRAMES = 180
_MIN_DELAY_MS = 20
_MAX_DELAY_MS = 300

_lock = threading.Lock()
_em_andamento: set = set()  # chaves sendo processadas agora, evita duplicar trabalho

Alvo = Tuple[int, int, str, int, Tuple[int, int, int]]  # (max_w, max_h, fit_mode, zoom_pct, cor_fundo)


def pasta_cache_gifs() -> str:
    caminho = os.path.join(pasta_config(), _CACHE_DIR_NOME, "gifs")
    os.makedirs(caminho, exist_ok=True)
    return caminho


def _hash_arquivo(caminho_gif: str) -> str:
    h = hashlib.sha256()
    with open(caminho_gif, "rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()[:24]


def chave_cache(caminho_gif: str, max_w: int, max_h: int, fit_mode: str, zoom_pct: int, cor_fundo: Tuple[int, int, int]) -> str:
    hash_arquivo = _hash_arquivo(caminho_gif)
    cor_hex = "%02x%02x%02x" % tuple(int(c) for c in cor_fundo)
    return f"{hash_arquivo}_{max_w}x{max_h}_{fit_mode}_{zoom_pct}_{cor_hex}"


def _pasta_entrada_cache(chave: str) -> str:
    return os.path.join(pasta_cache_gifs(), chave)


def esta_em_cache(caminho_gif: str, max_w: int, max_h: int, fit_mode: str, zoom_pct: int, cor_fundo: Tuple[int, int, int]) -> bool:
    """Verifica se já existe cache em disco, sem disparar processamento."""
    try:
        chave = chave_cache(caminho_gif, max_w, max_h, fit_mode, zoom_pct, cor_fundo)
    except OSError:
        return False
    return os.path.isfile(os.path.join(_pasta_entrada_cache(chave), "meta.json"))


def _carregar_do_disco(chave: str) -> Optional[Tuple[List[Image.Image], List[int]]]:
    entrada = _pasta_entrada_cache(chave)
    meta_path = os.path.join(entrada, "meta.json")
    if not os.path.isfile(meta_path):
        return None
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        duracoes = meta["duracoes"]
        frames = []
        for i in range(len(duracoes)):
            with Image.open(os.path.join(entrada, f"frame_{i:04d}.jpg")) as img:
                frames.append(img.convert("RGB").copy())
        os.utime(meta_path, None)  # marca como usado recentemente (política de eviction)
        return frames, duracoes
    except Exception as e:
        logging.warning("Cache de GIF corrompido, descartando '%s': %s", entrada, e)
        _remover_entrada_cache(entrada)
        return None


def _salvar_no_disco(chave: str, frames: List[Image.Image], duracoes: List[int], cor_fundo: Tuple[int, int, int]) -> None:
    """Grava os frames como JPEGs individuais (formato escolhido por ser ~100x
    mais rápido de codificar que WEBP/PNG animado nesta biblioteca, o que
    importa bastante — é o que roda em background ao adicionar/detectar um
    GIF novo). Como cada entrada de cache já é específica para uma cor de
    fundo, achatar a transparência nessa mesma cor antes de salvar não muda
    nada visualmente (a label é pintada com a cor idêntica por trás).
    """
    if not frames:
        return
    entrada = _pasta_entrada_cache(chave)
    # Sufixo único por chamada: o worker de background e um pedido síncrono
    # (popup precisando do GIF na hora) podem processar a mesma chave ao
    # mesmo tempo. Com um nome de pasta temporária fixo, o segundo a
    # terminar falhava ao gravar (WinError 5) por causa da primeira pasta
    # temporária ainda existir; com sufixo único isso não colide mais.
    tmp = f"{entrada}.tmp-{threading.get_ident()}-{time.monotonic_ns()}"
    try:
        os.makedirs(tmp, exist_ok=True)
        for i, frame in enumerate(frames):
            if frame.mode in ("RGBA", "LA") or "transparency" in frame.info:
                fundo = Image.new("RGB", frame.size, tuple(int(c) for c in cor_fundo))
                fundo.paste(frame.convert("RGBA"), (0, 0), frame.convert("RGBA"))
                frame_final = fundo
            else:
                frame_final = frame.convert("RGB")
            frame_final.save(os.path.join(tmp, f"frame_{i:04d}.jpg"), format="JPEG", quality=90)
        with open(os.path.join(tmp, "meta.json"), "w", encoding="utf-8") as f:
            json.dump({"duracoes": duracoes}, f)

        _remover_entrada_cache(entrada)
        os.replace(tmp, entrada)
        _evitar_cache_grande_demais()
    except Exception as e:
        logging.warning("Não foi possível gravar cache de GIF '%s': %s", entrada, e)
        _remover_entrada_cache(tmp)


def _remover_entrada_cache(caminho_pasta: str) -> None:
    if os.path.isdir(caminho_pasta):
        shutil.rmtree(caminho_pasta, ignore_errors=True)


def _evitar_cache_grande_demais() -> None:
    pasta = pasta_cache_gifs()
    try:
        entradas = [
            os.path.join(pasta, nome) for nome in os.listdir(pasta)
            if os.path.isfile(os.path.join(pasta, nome, "meta.json"))
        ]
    except OSError:
        return
    excedente = len(entradas) - _CACHE_MAX_ARQUIVOS
    if excedente <= 0:
        return
    entradas.sort(key=lambda p: os.path.getmtime(os.path.join(p, "meta.json")))
    for p in entradas[:excedente]:
        _remover_entrada_cache(p)


def _decodificar_e_redimensionar(caminho_gif: str, max_w: int, max_h: int, fit_mode: str, zoom_mult: float, cor_fundo: Tuple[int, int, int]) -> Tuple[List[Image.Image], List[int]]:
    """Decodifica e redimensiona um GIF com Pillow puro (sem Tk/PhotoImage) —
    o trabalho pesado que hoje causa o lag. Sub-amostra frames de GIFs muito
    grandes (no máx. `_MAX_FRAMES`) pra manter o processamento rápido."""
    frames: List[Image.Image] = []
    duracoes: List[int] = []
    try:
        with Image.open(caminho_gif) as img:
            total_frames = max(1, int(getattr(img, "n_frames", 1)))
            step = max(1, math.ceil(total_frames / _MAX_FRAMES))
            for idx in range(0, total_frames, step):
                img.seek(idx)
                frame = img.convert("RGBA")
                if fit_mode == "cover":
                    frame = ImageOps.fit(frame, (max_w, max_h), method=PIL_RESAMPLING_LANCZOS, centering=(0.5, 0.5))
                else:
                    frame = ImageOps.contain(frame, (max_w, max_h), method=PIL_RESAMPLING_LANCZOS)

                if zoom_mult > 1.0:
                    zoom_w = max(1, int(frame.width * zoom_mult))
                    zoom_h = max(1, int(frame.height * zoom_mult))
                    frame = frame.resize((zoom_w, zoom_h), PIL_RESAMPLING_LANCZOS)
                    if zoom_w >= max_w and zoom_h >= max_h:
                        left = (zoom_w - max_w) // 2
                        top = (zoom_h - max_h) // 2
                        frame = frame.crop((left, top, left + max_w, top + max_h))
                    else:
                        fundo = Image.new("RGBA", (max_w, max_h), (*cor_fundo, 255))
                        fundo.paste(frame, ((max_w - zoom_w) // 2, (max_h - zoom_h) // 2), frame)
                        frame = fundo

                frames.append(frame.copy())
                dur = int(img.info.get("duration", 80) or 80)
                duracoes.append(max(_MIN_DELAY_MS, min(_MAX_DELAY_MS, dur * step)))
    except Exception as e:
        logging.warning("Falha ao decodificar GIF '%s': %s", caminho_gif, e)
        return [], []
    return frames, duracoes


def obter_frames(caminho_gif: str, max_w: int, max_h: int, fit_mode: str, zoom_mult: float, cor_fundo: Tuple[int, int, int]) -> Tuple[List[Image.Image], List[int]]:
    """API principal: retorna (frames Pillow, durações em ms) para o GIF na
    resolução/modo pedidos. Usa o cache em disco quando existir; senão,
    decodifica do zero e grava no cache pra próxima vez. Thread-safe (não
    toca em Tk) — pode ser chamada tanto no fluxo síncrono do popup quanto
    na thread de pré-processamento em background.
    """
    zoom_pct = int(round(zoom_mult * 100))
    try:
        chave = chave_cache(caminho_gif, max_w, max_h, fit_mode, zoom_pct, cor_fundo)
    except OSError as e:
        logging.warning("Não foi possível ler '%s' para cache: %s", caminho_gif, e)
        return [], []

    do_disco = _carregar_do_disco(chave)
    if do_disco is not None:
        return do_disco

    frames, duracoes = _decodificar_e_redimensionar(caminho_gif, max_w, max_h, fit_mode, zoom_mult, cor_fundo)
    if frames:
        _salvar_no_disco(chave, frames, duracoes, cor_fundo)
    return frames, duracoes


_fila: Optional[queue.Queue] = None  # criada sob demanda (ver _garantir_worker)
_worker_iniciado = False


def _garantir_worker() -> None:
    """Garante que exista um único worker de background processando a fila —
    em vez de uma thread por GIF, o que poderia disparar dezenas de threads
    de uma vez (uma pasta gifs/ grande) e sobrecarregar a máquina, além de
    arriscar duas threads gravando a mesma chave de cache ao mesmo tempo
    quando dois arquivos diferentes têm conteúdo idêntico (mesmo hash)."""
    global _fila, _worker_iniciado
    with _lock:
        if _worker_iniciado:
            return
        _fila = queue.Queue()
        _worker_iniciado = True
        threading.Thread(target=_loop_worker, daemon=True, name="gif-prefetch").start()


def _loop_worker() -> None:
    while True:
        caminho_gif, chave, max_w, max_h, fit_mode, zoom_pct, cor_fundo = _fila.get()
        try:
            obter_frames(caminho_gif, max_w, max_h, fit_mode, zoom_pct / 100.0, cor_fundo)
        except Exception as e:
            logging.warning("Falha ao pré-processar '%s' em background: %s", caminho_gif, e)
        finally:
            with _lock:
                _em_andamento.discard(chave)
            _fila.task_done()


def preprocessar_em_background(caminho_gif: str, alvos: Iterable[Alvo]) -> None:
    """Enfileira cada (max_w, max_h, fit_mode, zoom_pct, cor_fundo) em `alvos`
    para ficar cacheado em disco para `caminho_gif`, processado por um único
    worker em background — não trava a UI. Combinações já em cache ou já
    enfileiradas não são duplicadas."""
    alvos = list(alvos)
    if not alvos or not os.path.isfile(caminho_gif):
        return

    pendentes = []
    with _lock:
        for max_w, max_h, fit_mode, zoom_pct, cor_fundo in alvos:
            try:
                chave = chave_cache(caminho_gif, max_w, max_h, fit_mode, zoom_pct, cor_fundo)
            except OSError:
                continue
            if chave in _em_andamento or os.path.isfile(os.path.join(_pasta_entrada_cache(chave), "meta.json")):
                continue
            _em_andamento.add(chave)
            pendentes.append((chave, max_w, max_h, fit_mode, zoom_pct, cor_fundo))

    if not pendentes:
        return

    _garantir_worker()
    for chave, max_w, max_h, fit_mode, zoom_pct, cor_fundo in pendentes:
        _fila.put((caminho_gif, chave, max_w, max_h, fit_mode, zoom_pct, cor_fundo))
