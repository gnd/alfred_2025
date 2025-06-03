import os
import sys
import fire
import ptext
import pygame
import socket
import configparser
from msg_decoder import decode_msg 
from screeninfo import get_monitors
from pygame._sdl2 import Window

# Load variables from config
settings = os.path.join(sys.path[0], 'config.ini')
config = configparser.ConfigParser()
config.read(settings)

# Assign config variables
DISPLAY_HOST = config.get('display', 'DISPLAY_HOST')
DISPLAY_PORT = int(config.get('display', 'DISPLAY_PORT'))
PADDING_TOP = int(config.get('display', 'PADDING_TOP'))
PADDING_LEFT = int(config.get('display', 'PADDING_LEFT'))
DISPLAY_HEIGHT = int(config.get('display', 'DISPLAY_HEIGHT'))
FONT_FILE = config.get('display', 'FONT')
FONT_SIZE = int(config.get('display', 'FONT_SIZE'))
MAX_WORDS = int(config.get('display', 'MAX_WORDS'))
PAUSE_LENGTH = int(config.get('display', 'PAUSE_LENGTH'))
SHOW_TRANSLATION = config.get('display', 'SHOW_TRANSLATION')
ONCE = True

# Screen dimensions
monitor = get_monitors()[0]
screen_width, screen_height = monitor.width, monitor.height

def main(port=DISPLAY_PORT, host=DISPLAY_HOST):
    # setup listening socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)

    # init pygame
    pygame.init()
    screen = pygame.display.set_mode((screen_width, DISPLAY_HEIGHT), pygame.NOFRAME|pygame.SRCALPHA)
    pygame.display.set_window_position((0, screen_height - DISPLAY_HEIGHT))
    window = Window.from_display_module()  
    window.opacity = 0.5
    font = pygame.font.Font(FONT_FILE, FONT_SIZE)
    screen.fill((255,255,255))
    pygame.display.flip()

    running =  True   
    while running:
        # get data from socket - blocking
        # TODO - do a threaded non-blocking version
        client_socket, address = server_socket.accept()
        msg = client_socket.recv(1024).decode()
        msg_dict = decode_msg(msg)
        print("RX: {}".format(msg_dict))

        if SHOW_TRANSLATION:
            text = msg_dict.get("translation")
        else:
            text = msg_dict.get("original")
        
        fill = msg_dict.get("fill")
        font_fname = msg_dict.get("font") if msg_dict.get("font") else pygame.font.get_default_font()
        align = msg_dict.get("align")
        padding_top = int(msg_dict.get("padding_top")) if msg_dict.get("padding_top") else PADDING_TOP
        padding_left = int(msg_dict.get("padding_left")) if msg_dict.get("padding_left") else PADDING_LEFT
        font_size = msg_dict.get("font_size")
        font_size = int(font_size) if font_size else FONT_SIZE
        fc = (255,255,255)

        if fill:
            screen.fill(fc, (0, 0, screen_width, screen_height))
    
        if text:
            ptext.draw(
                text,
                (padding_left, padding_top),
                color=(0,0,0),
                width=screen_width-2*padding_left,
                fontname=font_fname,
                lineheight=1,
                fontsize=font_size,
                align=align,
                alpha=0.5
            )

        # handle some events
        # This will work properly once non-blocking socket is done
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    print("Esc key press detected")
                    running = False
   
        pygame.display.flip()

    server_socket.close()
    pygame.quit()


if __name__ == "__main__":
    fire.Fire(main)
