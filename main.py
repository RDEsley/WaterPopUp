"""Ponto de entrada da aplicação: CLI, janela de controle principal e
agendamento dos lembretes periódicos."""

import sys
import json
import time
import logging
import argparse
from typing import Optional
import tkinter as tk

from config import (
    carregar_config,
    salvar_config,
    caminho_config,
    definir_caminho_override,
    aninhar_flat,
    MAPA_NESTED_PARA_FLAT,
)
from monitors import habilitar_dpi_awareness
from popup import mostrar_popup
from gui_config import abrir_configuracoes

# ============ TEMA DA JANELA PRINCIPAL (escuro) ============

COR_FUNDO = "#0f172a"
COR_CARD = "#111827"
COR_CARD_2 = "#1f2937"
COR_TEXTO = "#e5e7eb"
COR_SUBTEXTO = "#94a3b8"
COR_DESTAQUE = "#38bdf8"
COR_BOTAO = "#0ea5e9"
COR_BOTAO_HOVER = "#0284c7"

# ============ AGENDAMENTO DOS LEMBRETES ============

_lembretes_ativos = False
_lembrete_after_id = None
_proximo_lembrete_ts: Optional[float] = None

def _agendar_proximo_lembrete(root, delay_ms: int) -> None:
    global _lembrete_after_id, _proximo_lembrete_ts
    _proximo_lembrete_ts = time.time() + (delay_ms / 1000.0)
    _lembrete_after_id = root.after(delay_ms, lambda: _mostrar_e_reagendar(root))

def _mostrar_e_reagendar(root) -> None:
    if not _lembretes_ativos or not root.winfo_exists():
        return
    mostrar_popup(parent=root)
    cfg = carregar_config()
    interval_ms = int(cfg.get("interval_minutes", 10)) * 60 * 1000
    _agendar_proximo_lembrete(root, max(1000, interval_ms))

def _iniciar_lembretes(root) -> bool:
    global _lembretes_ativos
    if _lembretes_ativos:
        return False
    _lembretes_ativos = True
    _agendar_proximo_lembrete(root, 1000)
    return True

def _parar_lembretes(root=None) -> bool:
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

# ============ JANELA PRINCIPAL ============

def janela_app() -> None:
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
        text=cfg.get("control_window_status", "Notificações ativas"),
        font=("Segoe UI", 14, "bold"),
        fg=COR_TEXTO,
        bg=COR_CARD,
    ).pack(anchor="w")
    tk.Label(
        card,
        text=cfg.get("control_window_hint", "Feche esta janela para encerrar as notificações"),
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

# ============ CLI ============

def _configurar_logging(debug: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

def _parse_valor_set(s: str):
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

def _reconfigurar_saida_utf8() -> None:
    """Evita UnicodeEncodeError ao imprimir texto com emoji (mensagem, títulos)
    em consoles Windows que não usam UTF-8 por padrão (ex.: cp1252/850)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

def main() -> None:
    _reconfigurar_saida_utf8()

    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--config", "-c", action="store_true", help="Abrir janela de configurações")
    parser.add_argument("--set", action="append", default=[], help="Define config: chave=valor ou secao.campo=valor (pode repetir)")
    parser.add_argument("--config-path", default=None, help="Caminho do config.json (opcional)")
    parser.add_argument("--print-config-path", action="store_true", help="Mostra onde o config está sendo usado")
    parser.add_argument("--print-config", action="store_true", help="Imprime o config atual e sai")
    parser.add_argument("--debug", action="store_true", help="Ativa logs de depuração (nível DEBUG)")
    args = parser.parse_args()

    _configurar_logging(args.debug)
    habilitar_dpi_awareness()

    if args.config_path:
        definir_caminho_override(args.config_path)

    if args.print_config_path:
        print(caminho_config())
        sys.exit(0)

    if args.print_config:
        print(json.dumps(aninhar_flat(carregar_config()), indent=2, ensure_ascii=False))
        sys.exit(0)

    if args.set:
        atual = carregar_config()

        updates = {}
        for item in args.set:
            if "=" not in item:
                raise SystemExit(f"--set inválido: {item}. Use chave=valor ou secao.campo=valor")
            k, v = item.split("=", 1)
            k = k.strip()
            if "." in k:
                chave_flat = MAPA_NESTED_PARA_FLAT.get(k)
                if chave_flat is None:
                    raise SystemExit(f"--set: chave aninhada desconhecida '{k}'.")
                k = chave_flat
            updates[k] = _parse_valor_set(v)

        salvar_config({**atual, **updates})
        print("OK: config atualizado em", caminho_config())
        sys.exit(0)

    if args.config:
        abrir_configuracoes()
        sys.exit(0)

    janela_app()

if __name__ == "__main__":
    main()
