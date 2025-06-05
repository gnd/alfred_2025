import os
import sys
import ptext
import pygame
import signal
import socket
import argparse
import threading
import configparser
from pathlib import Path
from .msg_decoder import decode_msg 
from screeninfo import get_monitors
from pygame._sdl2 import Window

class SubtitleDisplay(threading.Thread):
    
    def __init__(self, lil_drama=None, secondary_screen=False):
        super().__init__(daemon=True)

        # The main app
        self.lil_drama = lil_drama

        # Threading stuff
        self.active  = threading.Event()
        self.stopper = threading.Event()

        # Signal handling
        signal.signal(signal.SIGTERM, self.on_exit)
        signal.signal(signal.SIGINT, self.on_exit)

        # Configuration - load variables from config
        self.work_dir = Path(__file__).resolve().parent
        settings = os.path.join(self.work_dir, 'config.ini')
        config = configparser.ConfigParser()
        config.read(settings)

        # Assign config variables
        self.listen_host = config.get('display', 'DISPLAY_HOST')
        self.listen_port = int(config.get('display', 'DISPLAY_PORT'))
        self.padding_top = int(config.get('display', 'PADDING_TOP'))
        self.padding_left = int(config.get('display', 'PADDING_LEFT'))
        self.display_height = int(config.get('display', 'DISPLAY_HEIGHT'))
        self.font_file = config.get('display', 'FONT')
        self.font_size = int(config.get('display', 'FONT_SIZE'))
        self.pause_length = int(config.get('display', 'PAUSE_LENGTH'))
        self.show_translation = config.get('display', 'SHOW_TRANSLATION')
        self.once = True
        self.secondary_screen = secondary_screen
        self.screen_offset = 0

        # Socket stuff
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.listen_host, self.listen_port))
        self.sock.listen(5)

        # Get screen dimensions
        if (self.secondary_screen):
            print("[subs-display] Running on secondary screen")
            monitor = get_monitors()[1]
            self.screen_offset = get_monitors()[0].width
        else:
            monitor = get_monitors()[0]
            self.screen_offset = 0
        self.screen_width = monitor.width
        self.screen_height = monitor.height
        print(f"[subs-display] width: {self.screen_width}, height: {self.screen_height}")

        # Init pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_width, self.display_height), pygame.NOFRAME|pygame.SRCALPHA)
        pygame.display.set_window_position((0 + self.screen_offset, self.screen_height - self.display_height))
        window = Window.from_display_module()  
        window.opacity = 0.5
        self.font = pygame.font.Font(self.work_dir / self.font_file, self.font_size)
        self.font_fname = pygame.font.get_default_font()
        self.black = (0,0,0)
        self.white = (255,255,255)

        # blank screen
        self.screen.fill(self.black)
        pygame.display.flip()


    def resume(self):
        self.active.set()

    def pause(self):
        self.active.clear()

    def shutdown(self):
        self.stopper.set()
        self.active.set()  

    def on_exit(self, signum, frame):
        print("[subs-display] Cleaning up ...")
        self.sock.close()
        sys.exit(0)

    def run(self):
        # endless loop
        while not self.stopper.is_set():
            if not self.active.wait(timeout=0.1):
                continue 
            try:
                self.sock.settimeout(0.5)
                conn, addr = self.sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            with conn:
                #print(f"[subs-display] Connected by {addr}")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    msg = data.decode().strip()
                    msg_dict = decode_msg(msg)
                    #print("[subs-display] RX: {}".format(msg_dict))

                    if self.show_translation:
                        text = msg_dict.get("translation")
                    else:
                        text = msg_dict.get("original")

                    if msg_dict.get("fill"):
                        self.screen.fill(self.black, (0, 0, self.screen_width, self.screen_height))
                
                    if text:
                        ptext.draw(
                            text,
                            (self.padding_left, self.padding_top),
                            color=self.white,
                            width=self.screen_width-2*self.padding_left,
                            fontname=self.font_fname,
                            lineheight=1,
                            fontsize=self.font_size,
                            align="left",
                            alpha=1
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



# Start Subtitle Display
def main():
    # Parse some arguments
    p = argparse.ArgumentParser()
    p.add_argument("--secondary", action="store_true", help="Run on the secondary screen")
    args = p.parse_args()
    subs_display = SubtitleDisplay(secondary_screen=args.secondary)
    subs_display.resume()
    try:
        subs_display.run()
    except KeyboardInterrupt:
        subs_display.shutdown()

if __name__ == "__main__":
    main()