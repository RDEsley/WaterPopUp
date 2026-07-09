"""
Water Popup - Notificação personalizada
Suporta personalização via config.json (na mesma pasta do .exe)
Execute com --config para abrir as configurações.

Ponto de entrada fino: a lógica da aplicação vive no pacote waterpopup/
(config.py, monitors.py, animations.py, popup.py, audio.py, gui_config.py
e main.py).
"""

from waterpopup.main import main

if __name__ == "__main__":
    main()
