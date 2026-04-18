<div align="center">

<img src="https://cdn-icons-png.flaticon.com/512/3105/3105807.png" width="100" alt="Water Icon"/>

# 💧 Water-Popup

**Um utilitário leve e eficiente em Python para notificações personalizadas no Windows.**

[![Python Version](https://img.shields.io/badge/python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Finalizado-25D366?style=for-the-badge)]()

</div>

---

## 📌 Sobre o Projeto

O **Water-Popup** é um app de notificações personalizadas. Apesar do nome, ele não é limitado a hidratação: você pode configurar mensagens, visual, GIFs, áudio e frequência para qualquer tipo de lembrete pessoal ou profissional.

> 🎯 **Destaque:** Totalmente compatível com empacotamento `.exe` para rodar direto no Windows. Ideal para iniciar junto com o PC.

---

## ✨ Recursos

| Funcionalidade | Descrição |
|---|---|
| 🖼️ **Popups Dinâmicos** | Notificações visuais com cores aleatórias ou paletas temáticas (Pastel, Vibrante, Natureza, Escuro, Clássico). |
| 🎬 **Animações** | Entrada com vários efeitos: aleatório, deslizar (horizontal ou vertical), zoom (escala), bounce, elástico, cair, fade ou nenhum. |
| 📍 **Posição Configurável** | Canto fixo (superior/inferior × esquerdo/direito) ou **aleatório** a cada lembrete. |
| 🔊 **Feedback Sonoro** | Reprodução de arquivos (`.mp3`, `.wav`, `.ogg`) — aleatório ou seleção personalizada. |
| ⏹️ **Áudio Inteligente** | Opção para parar o áudio quando o popup fechar (ideal para músicas longas). |
| ✏️ **Mensagem Personalizada** | Defina sua própria mensagem de notificação. |
| ⏱️ **Temporização** | Intervalo entre notificações (1–120 min) e duração do popup (3–60 seg). |
| 🪶 **Baixo Consumo** | Execução otimizada em segundo plano via *Threading*. |
| 📦 **Portabilidade** | Pronto para conversão em executável via PyInstaller. |
| ⚙️ **Configuração Persistente** | Preferências em `config.json`: pasta do app (ou do `.exe`) quando gravável; caso contrário `%AppData%\WaterPopUp`. Variável `WATERPOPUP_CONFIG_PATH` ou `--config-path` para forçar o arquivo. |

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
pip install -r requirements.txt
```

> Tkinter já vem incluído no Python. O arquivo `requirements.txt` fixa a versão do pygame para builds reproduzíveis.

### Executar com Python

```bash
# Clone o repositório
git clone https://github.com/RDEsley/WaterPopUp.git
cd WaterPopUp

# Instale as dependências
pip install -r requirements.txt

# Execute as notificações (popup no intervalo configurado)
python waterpopup.py

# Abrir configurações
python waterpopup.py --config
```

### Linha de comando (Python e `.exe`)

| Argumento | Descrição |
|-----------|-----------|
| *(nenhum)* | Abre a janela principal com notificações |
| `--config` ou `-c` | Abre só a janela de configurações |
| `--config-path CAMINHO` | Usa esse arquivo como `config.json` (sessão atual) |
| `--print-config-path` | Imprime o caminho do `config.json` em uso e encerra |
| `--print-config` | Imprime o JSON de configuração atual e encerra |
| `--set chave=valor` | Atualiza uma ou mais chaves e grava (pode repetir). Ex.: `--set interval_minutes=15 --set stop_audio_on_close=false` |

Valores em `--set`: números, `true`/`false`, ou JSON para listas/objetos (ex.: `selected_audios=["a.mp3"]`).

Variável de ambiente **`WATERPOPUP_CONFIG_PATH`**: caminho absoluto do `config.json` (útil sem passar `--config-path` em cada execução).

### Gerar executável (.exe)

```bash
pip install pyinstaller
pyinstaller waterpopup.spec
```

O `.exe` fica em `dist/waterpopup.exe`. Para recompilar do zero (limpa o cache do PyInstaller): `pyinstaller waterpopup.spec --clean`.

**Windows — “Permission denied” / `update_exe_pe_checksum`:** o `waterpopup.exe` não pode estar em uso. Feche o app (e atalhos em segundo plano) ou use **`build-exe.bat`** / **`build-exe.ps1`**, que encerram processos `waterpopup` e em seguida rodam o PyInstaller. Se a pasta estiver no OneDrive, aguarde a sincronização ou exclua `dist` da nuvem para reduzir bloqueios.

### Usar o .exe

| Ação | Comando |
|------|---------|
| Iniciar notificações | `waterpopup.exe` |
| Abrir configurações | `waterpopup.exe --config` ou `waterpopup.exe -c` |
| Outras opções | Mesmos argumentos da tabela acima (ex.: `waterpopup.exe --print-config-path`) |

### Iniciar com o Windows

1. Pressione `Win + R`, digite `shell:startup` e Enter.
2. Crie um atalho do `waterpopup.exe` dentro dessa pasta.

---

## ⚙️ Configurações

O app grava preferências em `config.json` (ignorado no Git). Para começar a partir de um modelo, copie `config.example.json` para `config.json` e ajuste.

**Onde o arquivo é salvo:** por padrão, na mesma pasta do `waterpopup.py` ou do `.exe` **se essa pasta for gravável**. Se não for (ex.: `Program Files`), usa-se `%AppData%\WaterPopUp\config.json`. Você pode forçar o caminho com a variável `WATERPOPUP_CONFIG_PATH` ou com `--config-path`.

Execute com `--config` para abrir a interface de personalização:

- **Mensagem** — Texto exibido no popup
- **Intervalo** — Minutos entre cada notificação (1–120)
- **Duração** — Segundos que o popup permanece na tela (3–60)
- **Posição** — Aleatório (incluindo centro) ou posição fixa (cantos + centro)
- **Visual** — Notificação padrão (texto) ou GIF animado
- **GIFs** — Seleção pelo explorador, histórico salvo e opção de GIF aleatório a cada notificação
- **Tela cheia** — Opção para cobrir toda a tela durante o lembrete (inclusive no modo GIF)
- **Parar áudio ao fechar** — Interrompe o som quando o popup fecha
- **Cores** — Aleatórias ou paleta fixa (Pastel, Vibrante, Natureza, Escuro, Clássico)
- **Animação** — Aleatória, Deslizar, Vertical, Zoom, Bounce, Elástico, Cair, Fade ou Nenhuma
- **Fonte** — Tamanho do texto (10–24 px)
- **Extras divertidos** — Efeitos de mensagem (sem efeito, brilho, água e festa)
- **Áudio** — Modo aleatório ou seleção de arquivos específicos da pasta `audios/`
- **Janela principal (opcional, só no JSON)** — `control_window_title`, `control_window_status`, `control_window_hint` personalizam título, texto de estado e dica da janela de controle

### Pasta de áudios

- **Com .exe:** Coloque a pasta `audios/` ao lado do executável para usar seus próprios arquivos.
- **Com Python:** Use a pasta `audios/` na raiz do projeto.

---

## 📁 Estrutura do Projeto

```
WaterPopUp/
├── waterpopup.py              # Aplicação principal
├── waterpopup.spec            # Configuração PyInstaller
├── requirements.txt           # Dependências Python
├── config.example.json        # Modelo de config.json (versionado)
├── Configurar Water Popup.bat # Atalho para abrir configurações
├── audios/                    # Arquivos de áudio (.mp3, .wav, .ogg)
├── config.json                # Configurações (gerado automaticamente; não versionado)
├── .gitignore                 # Artefatos locais e pastas de build
├── LICENSE                    # Licença MIT
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

*⭐ Personalize suas notificações e deixe uma estrela no repositório! ⭐*

</div>
