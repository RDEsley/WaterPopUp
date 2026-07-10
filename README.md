<div align="center">

<img src="https://cdn-icons-png.flaticon.com/512/3105/3105807.png" width="100" alt="Water Icon"/>

# 💧 Water-Popup

**Um utilitário leve e eficiente em Python para notificações personalizadas no Windows.**

[![Python Version](https://img.shields.io/badge/python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Finalizado-25D366?style=for-the-badge)]()
[![Releases](https://img.shields.io/badge/Download-Releases-0969da?style=for-the-badge&logo=github)](https://github.com/RDEsley/WaterPopUp/releases)
[![Última Versão](https://img.shields.io/github/v/release/RDEsley/WaterPopUp?style=for-the-badge&label=%C3%9Altima%20vers%C3%A3o)](https://github.com/RDEsley/WaterPopUp/releases/latest)
[![Plataforma](https://img.shields.io/badge/Plataforma-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)]()

</div>

---

## 📚 Sumário

- [Sobre o Projeto](#sobre)
- [Recursos](#recursos)
- [Tecnologias Utilizadas](#tecnologias)
- [Instalação e Uso](#instalacao)
- [Configurações](#configuracoes)
- [Multi-monitor](#multimonitor)
- [Estrutura do Projeto](#estrutura)
- [Contribuindo](#contribuindo)
- [Licença](#licenca)
- [Desenvolvedor](#desenvolvedor)

---

<a id="sobre"></a>
## 📌 Sobre o Projeto

O **Water-Popup** é um utilitário de notificações personalizadas para Windows. Apesar do nome, ele não se limita a lembretes de hidratação: você define mensagem, visual, GIFs, áudio e frequência para qualquer tipo de lembrete pessoal ou profissional — desde "beba água" até "hora da pausa" ou "levante e alongue".

> 🎯 **Destaque:** empacotamento nativo em `.exe`, suporte real a múltiplos monitores e configuração 100% via interface gráfica. Ideal para deixar rodando junto com a inicialização do Windows.

### ⚡ Teste rápido (recomendado)

Para testar sem configurar ambiente Python, baixe o executável na página de Releases:

👉 **[Baixar Water Popup (.exe)](https://github.com/RDEsley/WaterPopUp/releases)**

👉 **[Baixar última versão (releases/latest)](https://github.com/RDEsley/WaterPopUp/releases/latest)**

Depois:
1. Abra a release mais recente.
2. Baixe o arquivo `.zip` ou `.exe`.
3. Extraia (se for `.zip`) e execute `waterpopup.exe`.

---

<a id="recursos"></a>
## ✨ Recursos

| Funcionalidade | Descrição |
|---|---|
| 🖼️ **Popups Dinâmicos** | Notificações visuais com cores aleatórias ou paletas temáticas (Pastel, Vibrante, Natureza, Escuro, Clássico). |
| 🎬 **Animações** | Entrada com vários efeitos: aleatório, deslizar (horizontal ou vertical), zoom (escala), bounce, elástico, cair, fade ou nenhum. |
| 📍 **Posição Configurável** | Canto fixo (superior/inferior × esquerdo/direito) ou **aleatório** a cada notificação. |
| 🔊 **Feedback Sonoro** | Reprodução de arquivos (`.mp3`, `.wav`, `.ogg`) — aleatório ou seleção personalizada. |
| ⏹️ **Áudio Inteligente** | Opção para parar o áudio quando o popup fechar (ideal para músicas longas). |
| ✏️ **Mensagem Personalizada** | Defina sua própria mensagem de notificação. |
| ⏱️ **Temporização** | Intervalo entre notificações (1–120 min) e duração do popup (3–60 seg). |
| 🪶 **Baixo Consumo** | Execução otimizada em segundo plano via *Threading*. |
| 📦 **Portabilidade** | Pronto para conversão em executável via PyInstaller. |
| ⚙️ **Configuração Persistente** | Preferências em `config.json`: pasta do app (ou do `.exe`) quando gravável; caso contrário `%AppData%\WaterPopUp`. Variável `WATERPOPUP_CONFIG_PATH` ou `--config-path` para forçar o arquivo. |

---

<a id="tecnologias"></a>
## 🛠️ Tecnologias Utilizadas

<div align="center">

| Tecnologia | Papel no Projeto |
|---|---|
| 🐍 **Python 3.8+** | Core do sistema e lógica de automação |
| 🎮 **Pygame** | Motor de áudio |
| 🪟 **Tkinter** | Janelas de notificação (popup) — texto e GIF |
| 🎨 **CustomTkinter** | Janela principal e tela de configurações |
| 🖼️ **Pillow** | Decodificação e redimensionamento de GIFs animados |
| 🖥️ **screeninfo** | Detecção de monitores para o modo tela cheia multi-monitor |
| 🧵 **Threading** | Cache de GIFs em disco preparado em segundo plano |

</div>

---

<a id="instalacao"></a>
## 🚀 Instalação e Uso

> Se seu objetivo é apenas testar/usar o app, prefira baixar em **[Releases](https://github.com/RDEsley/WaterPopUp/releases)**.

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
python run.py

# Abrir configurações
python run.py --config
```

### Linha de comando (Python e `.exe`)

| Argumento | Descrição |
|-----------|-----------|
| *(nenhum)* | Abre a janela principal com notificações |
| `--config` ou `-c` | Abre só a janela de configurações |
| `--config-path CAMINHO` | Usa esse arquivo como `config.json` (sessão atual) |
| `--print-config-path` | Imprime o caminho do `config.json` em uso e encerra |
| `--print-config` | Imprime o JSON de configuração atual (estrutura aninhada) e encerra |
| `--set secao.campo=valor` | Atualiza uma ou mais chaves e grava (pode repetir). Ex.: `--set general.interval_minutes=15 --set audio.stop_on_close=false` |
| `--debug` | Ativa logs de depuração (nível DEBUG) no console |

Valores em `--set`: números, `true`/`false`, ou JSON para listas/objetos (ex.: `audio.selected=["a.mp3"]`). As chaves aceitam tanto o formato aninhado (`secao.campo`, recomendado) quanto as chaves antigas sem seção, por compatibilidade.

Variável de ambiente **`WATERPOPUP_CONFIG_PATH`**: caminho absoluto do `config.json` (útil sem passar `--config-path` em cada execução).

### Gerar executável (.exe)

```bash
pip install pyinstaller
pyinstaller waterpopup.spec
```

O `.exe` fica em `dist/waterpopup.exe`. Para recompilar do zero (limpa o cache do PyInstaller): `pyinstaller waterpopup.spec --clean`.

**Windows — “Permission denied” / `update_exe_pe_checksum`:** o `waterpopup.exe` não pode estar em uso. Feche o app (e atalhos em segundo plano) ou use **`scripts\build-exe.bat`** / **`scripts\build-exe.ps1`**, que encerram processos `waterpopup` e em seguida rodam o PyInstaller. Se a pasta estiver no OneDrive, aguarde a sincronização ou exclua `dist` da nuvem para reduzir bloqueios.

### GitHub Releases (segurança e verificação)

Use o script pronto do projeto (pasta `scripts/`) para empacotar e gerar o hash da release:

Exemplo:

```powershell
# 1) Gere o executavel
.\scripts\build-exe.bat

# 2) Gere assets da release + hash
.\scripts\generate-release-assets.ps1 -Version v1.0.0
```

Arquivos gerados:

- pasta `release/` com `waterpopup.exe` e `SHA256.txt`
- `waterpopup-win64-v1.0.0.zip` na raiz

No GitHub Releases, anexe o `.zip` e o `SHA256.txt`.

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

<a id="configuracoes"></a>
## ⚙️ Configurações

O app grava preferências em `config.json` (ignorado no Git). Para começar a partir de um modelo, copie `config.example.json` para `config.json` e ajuste.

**Estrutura do arquivo:** o `config.json` é gravado em seções (`general`, `message`, `visual`, `position`, `colors`, `animation`, `audio`, `gifs`, `window`) com valores validados (intervalos, tipos e faixas aceitáveis). Um `config.json` no formato antigo (versão anterior, com chaves soltas) é migrado automaticamente na primeira execução, com backup do arquivo anterior salvo como `config.json.bak`. Se o arquivo estiver corrompido/ilegível, o app restaura os valores padrão automaticamente e também guarda um backup do arquivo problemático. Veja `config.example.json` para um exemplo completo.

**Onde o arquivo é salvo:** por padrão, na pasta raiz do projeto (onde fica `run.py`) ou do `.exe` **se essa pasta for gravável**. Se não for (ex.: `Program Files`), usa-se `%AppData%\WaterPopUp\config.json`. Você pode forçar o caminho com a variável `WATERPOPUP_CONFIG_PATH` ou com `--config-path`.

Execute com `--config` para abrir a interface de personalização — organizada
em abas que espelham as seções do `config.json` (veja [Configurações](#configuracoes)
acima), com validação inline nos campos numéricos e pré-visualização animada
do GIF selecionado:

- **Geral** — Intervalo entre lembretes (1–120 min) e duração do popup na tela (3–60 seg)
- **Mensagem** — Texto exibido no popup, tamanho da fonte (10–24 px) e efeito extra (sem efeito, brilho, água ou festa)
- **Visual/GIF** — Notificação padrão (texto) ou GIF animado; tela cheia (cobre **todos** os monitores conectados ao mesmo tempo, veja [Multi-monitor](#multimonitor)); modo de ajuste do GIF, zoom em tela cheia, seleção pelo explorador e histórico salvo — veja também [GIFs plug-and-play](#configuracoes)
- **Posição** — Aleatório (incluindo centro) ou posição fixa (cantos + centro)
- **Cores** — Aleatórias ou paleta fixa (Pastel, Vibrante, Natureza, Escuro, Clássico), com pré-visualização
- **Animação** — Aleatória, Deslizar, Vertical, Zoom, Bounce, Elástico, Cair, Fade ou Nenhuma
- **Áudio** — Ativar/desativar o som das notificações, modo aleatório ou seleção de arquivos específicos da pasta `audios/`, controle de volume
- **Avançado** — Título, texto de status e dica da janela principal (antes só dava pra mudar editando o `config.json` ou via `--set`)

### Pasta de áudios

- **Com .exe:** Coloque a pasta `audios/` ao lado do executável para usar seus próprios arquivos.
- **Com Python:** Use a pasta `audios/` na raiz do projeto.

### GIFs — basta colocar o arquivo, sem ajuste manual

Qualquer GIF na pasta `gifs/` (ou escolhido pelo seletor de arquivos na tela
de Configurações) funciona sem precisar editar/redimensionar nada antes:
o redimensionamento é automático (modo "contain" por padrão) e um cache em
disco é preparado sozinho, em segundo plano, para a resolução de cada
monitor detectado.

- Assim que você escolhe ou adiciona um GIF na aba **Visual/GIF**, o app já
  dispara esse preparo em background (indicador discreto "Preparando para
  suas telas…" enquanto isso). Ao clicar em "Testar agora" logo em seguida,
  a exibição já sai rápida.
- O mesmo preparo roda automaticamente ao abrir o app, para os GIFs já
  salvos na pasta `gifs/` e no histórico — então reabrir o app não volta a
  reprocessar GIFs que você já usou antes.
- **Resolução mínima recomendada:** 1280x720 — abaixo disso o GIF fica
  borrado ao ser ampliado para preencher a tela (isso é uma limitação do
  arquivo original, não algo que o redimensionamento automático resolva).
- **Proporção:** próxima de 16:9 (a mesma da maioria dos monitores) evita
  barras grandes de letterbox/pillarbox — mas qualquer proporção funciona.
- **Tamanho de arquivo:** até 10MB é o ideal; arquivos bem maiores demoram
  mais na primeira preparação (que roda em segundo plano, sem travar o
  app) — depois de pronto, fica em cache e a exibição é instantânea.
- **Onde encontrar:** bancos como Giphy ou Tenor, filtrando por GIFs de uso
  livre/licença aberta, ou GIFs de sua própria autoria.
- O modo de ajuste (`gif_fit_mode`) controla como o GIF se encaixa na tela:
  **"contain"** (padrão) mostra o GIF inteiro com barras da cor do popup ao
  redor; **"cover"** preenche a tela cortando as bordas do GIF.

---

<a id="multimonitor"></a>
## 🖥️🖥️ Multi-monitor

Quando **Tela cheia** está ativa e o Windows detecta 2 ou mais monitores conectados, o Water-Popup cobre todos eles ao mesmo tempo:

- Cada monitor recebe sua própria janela, posicionada exatamente na geometria daquele monitor (funciona com monitores de resoluções diferentes, sem distorcer o conteúdo).
- O mesmo conteúdo (texto ou GIF) aparece em todas as telas, com o GIF **sincronizado** — mesmo frame, ao mesmo tempo, em todos os monitores.
- Clicar em qualquer uma das janelas (ou aguardar a duração configurada) fecha todas juntas.
- A detecção de monitores usa a biblioteca `screeninfo`. Se ela não estiver disponível ou a detecção falhar por algum motivo, o app cai automaticamente para o comportamento de 1 monitor, sem travar.

Não há configuração adicional: basta ativar "Cobrir toda a tela ao exibir o lembrete" com os monitores conectados.

---

<a id="estrutura"></a>
## 📁 Estrutura do Projeto

```
WaterPopUp/
├── run.py                      # Ponto de entrada fino (chama waterpopup.main.main())
├── waterpopup/                 # Pacote com a aplicação
│   ├── main.py                 # CLI, janela principal e agendamento dos lembretes
│   ├── config.py                # Paths, esquema/validação (dataclasses) e migração do config.json
│   ├── theme.py                 # Cores/fontes centralizadas da UI (CustomTkinter)
│   ├── popup.py                 # Janelas de notificação (texto/GIF, multi-monitor)
│   ├── gui_config.py            # Janela de configurações (abas espelhando o config v2)
│   ├── gif_cache.py             # Cache em disco de frames de GIF + pré-processamento em background
│   ├── animations.py            # Posicionamento e animações de entrada do popup
│   ├── audio.py                 # Reprodução de áudio (pygame)
│   ├── monitors.py              # Detecção de monitores e DPI awareness
│   └── __init__.py
├── scripts/                    # Scripts de build e atalhos
│   ├── build-exe.bat / .ps1     # Geram dist\waterpopup.exe (PyInstaller)
│   ├── generate-release-assets.ps1  # Empacota release + SHA256.txt
│   └── Configurar Water Popup.bat   # Atalho para abrir configurações
├── waterpopup.spec             # Configuração PyInstaller
├── requirements.txt            # Dependências Python
├── config.example.json         # Modelo de config.json (versionado)
├── audios/                     # Arquivos de áudio (.mp3, .wav, .ogg)
├── config.json                 # Configurações (gerado automaticamente; não versionado)
├── .gitignore                  # Artefatos locais e pastas de build
├── LICENSE                     # Licença MIT
└── README.md
```

---

<a id="contribuindo"></a>
## 🤝 Contribuindo

Contribuições são muito bem-vindas! Se você tem uma ideia, encontrou um bug ou quer melhorar algo:

1. Faça um **fork** do repositório.
2. Crie uma branch para sua alteração: `git checkout -b feature/minha-melhoria`.
3. Commit suas mudanças: `git commit -m "feat: descreva sua melhoria"`.
4. Envie para o seu fork: `git push origin feature/minha-melhoria`.
5. Abra um **Pull Request** explicando o que foi feito.

🐛 **Encontrou um bug ou tem uma sugestão?** Abra uma [issue](https://github.com/RDEsley/WaterPopUp/issues) descrevendo o problema ou a ideia com o máximo de detalhes possível.

---

<a id="licenca"></a>
## ⚖️ Licença

Este projeto está sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<a id="desenvolvedor"></a>
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

*⭐ Se este projeto foi útil pra você, considere deixar uma estrela no repositório! ⭐*

Feito com 💙 e bastante café por [Richard Esley](https://github.com/RDEsley)

</div>
