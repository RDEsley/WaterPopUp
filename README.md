One-liner:
Hydrate-Popup — Pequeno utilitário Python que mostra um popup de lembrete para beber água e toca áudios aleatórios; facilmente empacotável com PyInstaller.

README - Hydrate-Popup

Hydrate-Popup

Pequeno utilitário em Python que exibe um popup periódico com lembrete para beber água e reproduz um áudio aleatório da pasta `audios/`. Ideal como app leve para desktop (suporta empacotamento com PyInstaller).

Recursos
- Mostra um popup no canto superior direito com mensagem de lembrete.
- Reproduz aleatoriamente arquivos de áudio da pasta `audios/` (`.mp3`, `.wav`, `.ogg`).
- Popups com cor de fundo aleatória.
- Fácil de empacotar em `.exe` (Windows) via PyInstaller.

Pré-requisitos
- Python 3.8+
- Recomendado criar um ambiente virtual (venv).

Instalação (desenvolvimento)
1. Clone o repositório:
   git clone https://github.com/RDEsley/hydrate-popup.git
   cd hydrate-popup

2. Crie e ative um ambiente virtual (opcional mas recomendado):
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate

3. Instale dependências:
   pip install -r requirements.txt

   Exemplo do requirements.txt mínimo:
   pygame

4. Coloque seus arquivos de áudio na pasta `audios/` (formatos suportados: `.mp3`, `.wav`, `.ogg`).

Execução
Rode localmente com:
   python hidratar_popup.py

O app roda em segundo plano; ele exibirá o popup periodicamente (conforme configurado no código).

Contribuições
Contribuições são bem-vindas. Abra uma issue para discutir mudanças e depois envie um pull request com commits pequenos e claros.

Licença
Este projeto está licenciado sob a MIT License — veja o ficheiro LICENSE para detalhes.

Contato
Desenvolvedor: Richard Esley — perfil: https://github.com/RDEsley
