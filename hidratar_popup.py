import os, sys, time, tkinter as tk
from threading import Thread
import pygame, random

def caminho_recurso(rel):
    # Localiza o arquivo dentro do bundle PyInstaller (--onefile)
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.abspath(".")
    return os.path.join(base, rel)

# Inicializa o mixer do pygame
pygame.mixer.init()

def tocar_som():
    # lista todos os arquivos da pasta audios
    pasta_audios = caminho_recurso("audios")
    arquivos = [f for f in os.listdir(pasta_audios) if f.lower().endswith((".wav", ".mp3", ".ogg"))]

    if not arquivos:
        print("Nenhum áudio encontrado na pasta audios.")
        return

    # escolhe aleatoriamente
    arquivo_escolhido = random.choice(arquivos)
    wav_path = os.path.join(pasta_audios, arquivo_escolhido)

    try:
        pygame.mixer.music.load(wav_path)
        pygame.mixer.music.play()  # toca em background
    except Exception as e:
        print("Erro ao tocar som:", e)

def mostrar_popup():
    # dispara o som
    tocar_som()

    # configura janela
    root = tk.Tk()
    root.title("Hidrate-se!")
    root.geometry("300x100")
    root.attributes("-topmost", True)
    root.overrideredirect(True)

    # posiciona no canto superior direito
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"300x100+{w-310}+10")

    # paleta de cores possíveis
    cores = ["light pink", "light blue", "light green", "lavender", "peach puff", "light yellow", "plum", "khaki"]
    cor_aleatoria = random.choice(cores)

    tk.Label(root,
             text="🌊🫧 Drink some water! 💧💦",
             font=("Sans Serif",14),
             bg=cor_aleatoria,
             fg="black").pack(expand=True, fill="both")

    root.after(12000, root.destroy)
    root.mainloop()

def iniciar():
    while True:
        mostrar_popup()
        time.sleep(800)  # intervalo 10 minutos

Thread(target=iniciar, daemon=True).start()

# mantém o script vivo
while True:
    time.sleep(1)
