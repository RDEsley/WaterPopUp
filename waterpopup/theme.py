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

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ============ CORES — paleta outono (fundo claro, alto contraste) ============

COR_FUNDO = "#f4ead9"        # creme quente
COR_CARD = "#fbf3e7"         # creme mais claro (cards sobre o fundo)
COR_CARD_2 = "#ecdcc4"       # bege mais escuro (botões secundários, listas)
COR_TEXTO = "#3d2817"        # marrom escuro (alto contraste sobre o creme)
COR_SUBTEXTO = "#6b4f3a"     # marrom médio
COR_DESTAQUE = "#c2410c"     # terracota
COR_BOTAO = "#d97706"        # âmbar/laranja
COR_BOTAO_HOVER = "#b45309"  # âmbar mais escuro
COR_BOTAO_SEC = "#ecdcc4"    # bege (botão secundário)
COR_BOTAO_SEC_HOVER = "#e0c9a6"
COR_BORDA = "#d9c4a3"        # bege acinzentado

COR_ATIVO = "#4d7c0f"        # verde-oliva: indicador de lembretes ativos
COR_PAUSADO = "#a8927c"      # bege acinzentado: indicador de lembretes pausados

COR_ERRO = "#b91c1c"         # vermelho escuro (contraste sobre fundo claro)

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
