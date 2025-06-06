# pip install pygame-ce mss screeninfo
import os
import argparse
import threading
import subprocess
import pygame, mss
import socket
from pygame._sdl2 import Window
from screeninfo import get_monitors

class DesktopFeedback(threading.Thread):

    def __init__(self, lil_drama=None, secondary_screen=False):
        super().__init__(daemon=True)

        # The main app
        self.lil_drama = lil_drama

        # Threading stuff
        self.active  = threading.Event()  # cleared = paused
        self.stopper = threading.Event()  # set = terminate thread

        # Various vars
        self.window = None
        self.screenshot = None
        self.smaller_shot = None
        self.frame = 0
        self.secondary_screen = secondary_screen
        self.screen_offset = 0
        self.screen_offset_y = 0
        self.opacity = 0.0
        self.listen_host = 'localhost'
        self.listen_port = 6668

        # Socket stuff
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.listen_host, self.listen_port))
        self.sock.listen(5)

        # Get screen dimensions
        if (self.secondary_screen):
            print("[tunnel] Running on secondary screen")
            monitor = get_monitors()[1]
            self.screen_offset = get_monitors()[0].width
            self.screen_offset_y = 29
        else:
            monitor = get_monitors()[0]
            self.screen_offset = 0
        self.screen_width = monitor.width
        self.screen_height = monitor.height
        print(f"[tunnel] width: {self.screen_width}, height: {self.screen_height}")

        # Init pygame window
        pygame.init()
        pygame.display.set_caption('lil_feed')

    def resume(self):
        # create a hidden window so mss won't see it
        self.window = pygame.display.set_mode((1, 1), pygame.HIDDEN)

        self.screenshot = self.make_screenshot()
        # resize the shot for feedback to work
        self.smaller_shot = pygame.transform.smoothscale(self.screenshot, (self.screen_width - 40, self.screen_height - 50))

        # replace the hidden window with a real one after the capture
        self.window = pygame.display.set_mode((self.screen_width - 40, self.screen_height - 50), pygame.NOFRAME|pygame.SRCALPHA)
        pygame.display.set_window_position((20 + self.screen_offset, 0 + self.screen_offset_y))
        self.sdl_window = Window.from_display_module()  
        self.sdl_window.opacity = self.opacity

        self.window.blit(self.smaller_shot, (0, 0))
        pygame.display.flip()

        self.active.set()

    def pause(self):
        self.active.clear()

    def shutdown(self):
        self.stopper.set()
        self.active.set()    

    def on_exit(self, signum, frame):
        print("[tunnel] Cleaning up ...")
        pygame.display.quit()
        pygame.quit()
        self.sock.close()
        sys.exit(0)

    def make_screenshot(self):
        with mss.mss() as sct:
            if self.secondary_screen:
                if len(sct.monitors) < 3:
                    raise RuntimeError("[tunnel] Only one monitor detected!")
                monitor = sct.monitors[2]
            else:
                monitor = sct.monitors[0]
            shot = sct.grab(monitor)
            # mss gives RGB in BGRA byte order → convert
            screenshot = pygame.image.frombuffer(shot.rgb, shot.size, "RGB")
            return screenshot

    def raise_window(self, name="lil_feed"):
        try:
            subprocess.run(
                ["wmctrl", "-a", name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
        except subprocess.CalledProcessError:
            pass

    def run(self):
        # endless loop
        while not self.stopper.is_set():
            if not self.active.wait(timeout=0.1):
                continue  
            self.frame = (self.frame + 1) % 100
            if (self.opacity < 0.95):
                self.opacity = self.opacity + 0.01
            self.sdl_window.opacity = self.opacity
            self.screenshot = self.make_screenshot()
            self.smaller_shot = pygame.transform.smoothscale(self.screenshot, (1880, 1030))
            self.window.blit(self.smaller_shot, (0, 0))
            # if (self.frame > 95):
            #     self.window.fill((30, 0, 0))
            pygame.display.flip()
            
            if (self.frame > 50):
                self.raise_window()                

        pygame.quit()
        print("[tunnel] shutting down")

# Start Feedback Tunnel
def main():
    # Parse some arguments
    p = argparse.ArgumentParser()
    p.add_argument("--secondary", action="store_true", help="Run on the secondary screen")
    args = p.parse_args()
    tunnel = DesktopFeedback(secondary_screen=args.secondary)
    tunnel.resume()
    try:
        tunnel.run()
    except KeyboardInterrupt:
        tunnel.shutdown()

if __name__ == "__main__":
    main()