"""Ponto de entrada da aplicação: CLI, janela de controle principal e
agendamento dos lembretes periódicos."""

import sys
import json
import time
import logging
import argparse
from typing import Optional
import customtkinter as ctk

from . import theme
from .config import (
    carregar_config,
    salvar_config,
    caminho_config,
    definir_caminho_override,
    aninhar_flat,
    MAPA_NESTED_PARA_FLAT,
)
from .monitors import habilitar_dpi_awareness
from .popup import mostrar_popup
from .gui_config import abrir_configuracoes

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
    root = ctk.CTk()
    root.title(cfg.get("control_window_title", "💧 Water Popup"))
    root.geometry("560x360")
    root.minsize(520, 330)
    root.configure(fg_color=theme.COR_FUNDO)
    root.attributes("-topmost", False)

    container = ctk.CTkFrame(root, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=18, pady=16)

    card = ctk.CTkFrame(container, fg_color=theme.COR_CARD, corner_radius=theme.RAIO_BORDA)
    card.pack(fill="both", expand=True)
    conteudo = ctk.CTkFrame(card, fg_color="transparent")
    conteudo.pack(fill="both", expand=True, padx=18, pady=16)

    ctk.CTkLabel(
        conteudo,
        text=cfg.get("control_window_status", "Notificações ativas"),
        font=theme.fonte(15, "bold"),
        text_color=theme.COR_TEXTO,
        anchor="w",
    ).pack(anchor="w", fill="x")
    ctk.CTkLabel(
        conteudo,
        text=cfg.get("control_window_hint", "Feche esta janela para encerrar as notificações"),
        font=theme.fonte(10),
        text_color=theme.COR_SUBTEXTO,
        anchor="w",
    ).pack(anchor="w", fill="x", pady=(2, 12))

    # Indicador de estado (bolinha colorida + texto): fica verde quando os
    # lembretes estão ativos e cinza quando pausados, pra dar um feedback
    # visual imediato do estado sem precisar ler o texto.
    linha_status = ctk.CTkFrame(conteudo, fg_color="transparent")
    linha_status.pack(anchor="w", fill="x")
    indicador_var = ctk.StringVar(value="●")
    status_var = ctk.StringVar(value="Lembretes: iniciando...")
    ctk.CTkLabel(
        linha_status, textvariable=indicador_var, font=theme.fonte(12),
        text_color=theme.COR_PAUSADO, width=16,
    ).pack(side="left")
    ctk.CTkLabel(
        linha_status, textvariable=status_var, font=theme.fonte(11, "bold"),
        text_color=theme.COR_DESTAQUE, anchor="w",
    ).pack(side="left")

    timer_var = ctk.StringVar(value="Próximo lembrete em: --:--")
    ctk.CTkLabel(
        conteudo, textvariable=timer_var, font=theme.fonte_mono(12),
        text_color=theme.COR_TEXTO, anchor="w",
    ).pack(anchor="w", fill="x", pady=(4, 12))
    ctk.CTkLabel(
        conteudo,
        text="Config em uso: " + caminho_config(),
        font=theme.fonte(9),
        text_color=theme.COR_SUBTEXTO,
        anchor="w",
        justify="left",
        wraplength=480,
    ).pack(anchor="w", fill="x", pady=(0, 14))

    btns = ctk.CTkFrame(conteudo, fg_color="transparent")
    btns.pack(anchor="w")

    def _formatar_tempo(segundos):
        segundos = max(0, int(segundos))
        m, s = divmod(segundos, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def atualizar_status():
        ativo = _lembretes_ativos
        status_var.set("Lembretes: ativos" if ativo else "Lembretes: pausados")
        indicador_var.set("●")
        indicador_label = linha_status.winfo_children()[0]
        indicador_label.configure(text_color=theme.COR_ATIVO if ativo else theme.COR_PAUSADO)
        if ativo and _proximo_lembrete_ts:
            restante = _proximo_lembrete_ts - time.time()
            timer_var.set(f"Próximo lembrete em: {_formatar_tempo(restante)}")
        else:
            timer_var.set("Próximo lembrete em: --:--")
        btn_iniciar.configure(state="disabled" if ativo else "normal")
        btn_pausar.configure(state="normal" if ativo else "disabled")
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

    botao_secundario = dict(
        width=140, fg_color=theme.COR_BOTAO_SEC, hover_color=theme.COR_BOTAO_SEC_HOVER,
        text_color=theme.COR_TEXTO, font=theme.fonte(11), corner_radius=theme.RAIO_BORDA_PEQUENO,
    )
    ctk.CTkButton(btns, text="Configurar", command=abrir_cfg, **botao_secundario).grid(row=0, column=0, padx=4, pady=4)
    ctk.CTkButton(btns, text="Testar agora", command=testar_agora, **botao_secundario).grid(row=0, column=1, padx=4, pady=4)
    btn_iniciar = ctk.CTkButton(
        btns, text="Iniciar", command=iniciar, width=140, font=theme.fonte(11, "bold"),
        fg_color=theme.COR_BOTAO, hover_color=theme.COR_BOTAO_HOVER, corner_radius=theme.RAIO_BORDA_PEQUENO,
    )
    btn_iniciar.grid(row=1, column=0, padx=4, pady=4)
    btn_pausar = ctk.CTkButton(btns, text="Pausar", command=pausar, **botao_secundario)
    btn_pausar.grid(row=1, column=1, padx=4, pady=4)

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
