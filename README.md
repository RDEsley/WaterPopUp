<div align="center">

<img src="https://cdn-icons-png.flaticon.com/512/3105/3105807.png" width="100" alt="Water Icon"/>

# 💧 Water-Popup

**Um utilitário leve e eficiente em Python para cuidar da sua saúde enquanto você trabalha.**

[![Python Version](https://img.shields.io/badge/python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Finalizado-25D366?style=for-the-badge)]()

</div>

---

## 📌 Sobre o Projeto

O **Water-Popup** (ou Hidratar Popup) foi projetado para garantir que você nunca esqueça de se hidratar durante longas sessões de foco. Ele exibe lembretes visuais e sonoros periódicos de forma não intrusiva, com interface de personalização completa.

> 🎯 **Destaque:** Totalmente compatível com empacotamento `.exe` para rodar direto no Windows. Ideal para iniciar junto com o PC.

---

## ✨ Recursos

| Funcionalidade | Descrição |
|---|---|
| 🖼️ **Popups Dinâmicos** | Notificações visuais com cores aleatórias ou paletas temáticas (Pastel, Vibrante, Natureza, Escuro, Clássico). |
| 🎬 **Animações** | Entrada do popup com efeito deslizar ou fade in. |
| 📍 **Posição Configurável** | Escolha o canto da tela: superior/inferior, esquerdo/direito. |
| 🔊 **Feedback Sonoro** | Reprodução de arquivos (`.mp3`, `.wav`, `.ogg`) — aleatório ou seleção personalizada. |
| ⏹️ **Áudio Inteligente** | Opção para parar o áudio quando o popup fechar (ideal para músicas longas). |
| ✏️ **Mensagem Personalizada** | Defina sua própria mensagem de lembrete. |
| ⏱️ **Temporização** | Intervalo entre lembretes (1–120 min) e duração do popup (3–60 seg). |
| 🪶 **Baixo Consumo** | Execução otimizada em segundo plano via *Threading*. |
| 📦 **Portabilidade** | Pronto para conversão em executável via PyInstaller. |
| ⚙️ **Configuração Persistente** | Todas as preferências salvas em `config.json` na pasta do app. |

---

## 🛠️ Tecnologias Utilizadas

<div align="center">

| Tecnologia | Papel no Projeto |
|---|---|
| 🐍 **Python 3.8+** | Core do sistema e lógica de automação |
| 🎮 **Pygame** | Motor de áudio |
| 🪟 **Tkinter** | Interface gráfica (popup e configurações) |
| 🧵 **Threading** | Gerenciamento de processos em background |

</div>

---

## 🚀 Instalação e Uso

### Dependências

```bash
pip install pygame
```

> Tkinter já vem incluído no Python.

### Executar com Python

```bash
# Clone o repositório
git clone https://github.com/RDEsley/WaterPopUp.git
cd WaterPopUp

# Instale as dependências
pip install pygame

# Execute o lembrete (popup a cada 10 min)
python waterpopup.py

# Abrir configurações
python waterpopup.py --config
```

### Gerar executável (.exe)

```bash
pip install pyinstaller
pyinstaller waterpopup.spec
```

O `.exe` será criado em `dist/waterpopup.exe`.

### Usar o .exe

| Ação | Comando |
|------|---------|
| Iniciar lembretes | `waterpopup.exe` |
| Abrir configurações | `waterpopup.exe --config` ou `waterpopup.exe -c` |

### Iniciar com o Windows

1. Pressione `Win + R`, digite `shell:startup` e Enter.
2. Crie um atalho do `waterpopup.exe` dentro dessa pasta.

---

## ⚙️ Configurações

Execute com `--config` para abrir a interface de personalização:

- **Mensagem** — Texto exibido no popup
- **Intervalo** — Minutos entre cada lembrete (1–120)
- **Duração** — Segundos que o popup permanece na tela (3–60)
- **Parar áudio ao fechar** — Interrompe o som quando o popup fecha
- **Cores** — Aleatórias ou paleta fixa (Pastel, Vibrante, Natureza, Escuro, Clássico)
- **Animação** — Aleatória, Deslizar, Zoom, Bounce, Elástico, Cair, Fade ou Nenhuma
- **Posição** — Canto da tela onde o popup aparece
- **Fonte** — Tamanho do texto (10–24 px)
- **Áudio** — Modo aleatório ou seleção de arquivos específicos da pasta `audios/`

### Pasta de áudios

- **Com .exe:** Coloque a pasta `audios/` ao lado do executável para usar seus próprios arquivos.
- **Com Python:** Use a pasta `audios/` na raiz do projeto.

---

## 📁 Estrutura do Projeto

```
WaterPopUp/
├── waterpopup.py              # Aplicação principal
├── waterpopup.spec            # Configuração PyInstaller
├── Configurar Water Popup.bat # Atalho para abrir configurações
├── audios/                    # Arquivos de áudio (.mp3, .wav, .ogg)
├── config.json                # Configurações (gerado automaticamente)
└── README.md
```

---

## ⚖️ Licença

Este projeto está sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👨‍💻 Desenvolvedor

<div align="center">

<img src="https://github.com/RDEsley.png" width="100" style="border-radius:50%" alt="Richard Esley"/>

💻 **Richard Esley**

*Desenvolvedor Full Stack | UI/UX*

[![Portfólio](https://img.shields.io/badge/Portfólio-25D366?style=for-the-badge&logo=vercel&logoColor=white)](https://richardesley-dev.vercel.app/)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/RDEsley)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/richardesley/)

</div>

---

<div align="center">

*⭐ Beba água e deixe uma estrela no repositório! ⭐*

</div>
