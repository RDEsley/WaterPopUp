# 💧 Hydrate-Popup

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](#contribuindo)

Um utilitário leve e eficiente em Python projetado para cuidar da sua saúde enquanto você trabalha. O **Hydrate-Popup** exibe lembretes visuais e sonoros periódicos, garantindo que você nunca esqueça de se hidratar.

---

## ✨ Recursos

* **Notificações Visuais:** Popups dinâmicos no canto superior direito com cores de fundo aleatórias.
* **Feedback Sonoro:** Reprodução aleatória de arquivos de áudio (`.mp3`, `.wav`, `.ogg`) da pasta `audios/`.
* **Leveza:** Execução em segundo plano com baixo consumo de recursos.
* **Portabilidade:** Totalmente compatível com empacotamento `.exe` via PyInstaller para Windows.

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.8+
* **Interface/Áudio:** Pygame (para manipulação de áudio e janelas).
* **Automação:** Threading para execução em segundo plano.

## 🚀 Instalação e Configuração

### Pré-requisitos
* Python instalado (versão 3.8 ou superior).
* Ambiente virtual (recomendado).

### Passo a passo
1. **Clone o repositório:**
   git clone https://github.com/RDEsley/hydrate-popup.git
   cd hydrate-popup

2. **Configure o ambiente virtual:**
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # macOS / Linux
   source .venv/bin/activate

3. **Instale as dependências:**
   pip install -r requirements.txt

4. **Prepare os áudios:**
   Adicione seus arquivos de som favoritos na pasta `audios/` na raiz do projeto.

---

## 💻 Como Usar

Para iniciar o monitor de hidratação, execute:
python hidratar_popup.py

> **Dica de Infra:** Para criar um executável para Windows, você pode usar o comando:
> pyinstaller --noconsole --onefile hidratar_popup.py

---

## 🤝 Contribuindo

Contribuições tornam a comunidade open source um lugar incrível!
1. Faça um **Fork** do projeto.
2. Crie uma **Branch** para sua feature (git checkout -b feature/NovaFeature).
3. Dê um **Commit** em suas mudanças (git commit -m 'Add: Nova Feature').
4. Faça um **Push** para a Branch (git push origin feature/NovaFeature).
5. Abra um **Pull Request**.

---

## ⚖️ Licença

Este projeto está sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👨‍💻 Contato

**Richard Esley** - *Full Stack Developer*
* **GitHub:** [RDEsley](https://github.com/RDEsley)
* **Portfólio:** [certificates-richard-oliveira.vercel.app](https://certificates-richard-oliveira.vercel.app)
