"""Tema centralizado (cores, fontes, raio de borda) para as janelas
CustomTkinter da aplicação — janela principal e tela de configurações.
Um único lugar para essas constantes evita ter cada janela com sua
própria paleta hardcoded e dessincronizada da outra.

Decisão de arquitetura (Frente 0 — UI em CustomTkinter, não pywebview):
prototipei as duas opções (pywebview e CustomTkinter) empacotadas com
PyInstaller nesta mesma máquina (Windows 11, WebView2 Runtime nativo)
antes de decidir:

                    pywebview                      CustomTkinter
tempo até           1.2-1.9s                        0.5-0.6s (~igual ao
renderizar                                           Tkinter puro, 0.3s)
dependências        pythonnet, clr_loader,           nenhuma (Python/
extras puxadas      interop .NET, cryptography       Tkinter puro)
runtime externo     exige WebView2 Runtime na        nenhum
                     máquina do usuário (presente
                     por padrão no Win11/via Edge
                     no Win10, mas é suposição,
                     não garantia)
estabilidade         1 falha de inicialização         0 falhas em todas
observada            (E_ABORT) em ~6 execuções        as execuções

CustomTkinter venceu: o requisito inegociável é o usuário só baixar e
rodar o .exe, com o mínimo de risco e latência possível. pywebview
mediu 2-3x mais lento para abrir uma janela de status simples e teve
uma falha real de inicialização do WebView2 durante o teste — o tipo de
risco que justifica reverter para CustomTkinter em vez de insistir.
"""

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ============ CORES ============

COR_FUNDO = "#0f172a"
COR_CARD = "#111827"
COR_CARD_2 = "#1f2937"
COR_TEXTO = "#e5e7eb"
COR_SUBTEXTO = "#94a3b8"
COR_DESTAQUE = "#38bdf8"
COR_BOTAO = "#0ea5e9"
COR_BOTAO_HOVER = "#0284c7"
COR_BOTAO_SEC = "#1f2937"
COR_BOTAO_SEC_HOVER = "#334155"
COR_BORDA = "#243244"

COR_ATIVO = "#22c55e"       # indicador: lembretes ativos
COR_PAUSADO = "#64748b"     # indicador: lembretes pausados

COR_ERRO = "#f87171"
COR_ERRO_FUNDO = "#3b1f22"

# ============ FONTES ============

FONTE_FAMILIA = "Segoe UI"
FONTE_MONO = "Consolas"

def fonte(tamanho: int = 13, peso: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONTE_FAMILIA, size=tamanho, weight=peso)

def fonte_titulo(tamanho: int = 18) -> ctk.CTkFont:
    return fonte(tamanho, "bold")

def fonte_mono(tamanho: int = 12) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONTE_MONO, size=tamanho)

# ============ FORMATO ============

RAIO_BORDA = 10
RAIO_BORDA_PEQUENO = 6
