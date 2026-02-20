# quick-and-dirty 20 Hz strobe in Pygame
import mido 
import time
import pygame
import select
import socket
import argparse
import threading
from pygame._sdl2 import Window
from screeninfo import get_monitors

# import submodules
from midi_listener import MidiListener


class Strobe(threading.Thread):
    def __init__(self, lil_drama=None, secondary_screen=False):
        super().__init__(daemon=True)

        # The main app
        self.lil_drama = lil_drama

        # Threading stuff
        self.active  = threading.Event()  # cleared = paused
        self.stopper = threading.Event()  # set = terminate thread

        # Some configuration
        self.listen_host = 'localhost'
        self.listen_port = 6669
        self.secondary_screen = True
        self.strobe = True
        self.screen_offset = 0
        self.screen_width = 0
        self.screen_height = 0
        self.opacity = 1
        self.greenblue = 0
        self.freq = 5

        # Get screen dimensions
        if (self.secondary_screen):
            print("[strobe] Running on secondary screen")
            monitor = get_monitors()[1]
            self.screen_width = monitor.width
            self.screen_height = monitor.height
            self.screen_offset = get_monitors()[0].width
        else:
            monitor = get_monitors()[0]
            self.screen_offset = 0
            self.screen_width = monitor.width
            self.screen_height = monitor.height
        print(f"[strobe] width: {self.screen_width}, height: {self.screen_height}")

        # Create screen
        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.NOFRAME)
        pygame.display.set_window_position((0 + self.screen_offset, 0))
        self.sdl_window = Window.from_display_module()  
        self.sdl_window.opacity = self.opacity
        self.clock = pygame.time.Clock()

        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.color   = self.BLACK

        # MIDI listener
        port_name = self.open_default_port()
        print(f"Opening {port_name}")
        midi = MidiListener(self, "strobe", port_name)
        midi.start()

    def open_default_port(self):
        names = mido.get_input_names()
        print(names)
        if not names:
            sys.exit("No MIDI input ports detected.")
        for name in names:
            if "MIDI Mix" in name:
                return name

    def toggle_strobe(self):
        if self.strobe:
            self.strobe = False
        else:
            self.strobe = True

    def adjust_strobe_freq(self, freq):
        if freq > 0:
            self.freq = freq

    def adjust_strobe_opacity(self, opacity):
        self.opacity = opacity
        self.sdl_window.opacity = self.opacity

    def adjust_greenblue(self, greenblue):
        self.greenblue = greenblue

    def pause(self):
        self.active.clear()

    def resume(self):
        self.active.set()

    def shutdown(self):
        self.stopper.set()
        self.active.set()    

    def on_exit(self, signum, frame):
        print("[strobe] Cleaning up ...")
        self.strobe = False
        self.midi.stop()
        pygame.display.quit()
        pygame.quit()
        sys.exit(0)

    def run(self):
        last_switch = pygame.time.get_ticks()

        while self.strobe:
            now = pygame.time.get_ticks()
            toggle_ms = 1000 / self.freq                 # period per half-cycle

            if now - last_switch >= toggle_ms:
                self.screen.fill((255,self.greenblue, self.greenblue))
                pygame.display.flip()
                time.sleep(0.01)                           # optional flash length
                self.screen.fill(self.BLACK)
                pygame.display.flip()
                last_switch = now

# Start Strobe
def main():
    # Parse some arguments
    p = argparse.ArgumentParser()
    p.add_argument("--secondary", action="store_true", help="Run on the secondary screen")
    args = p.parse_args()
    strobe = Strobe(secondary_screen=args.secondary)
    strobe.resume()
    try:
        strobe.run()
    except KeyboardInterrupt:
        strobe.shutdown()

if __name__ == "__main__":
    main()