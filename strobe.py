# quick-and-dirty 20 Hz strobe in Pygame
import mido 
import time
import pygame
from screeninfo import get_monitors

# import submodules
from midi_listener import MidiListener


class Strobe():
    def __init__(self):
        # Some configuration
        self.secondary_screen = False
        self.strobe = True
        self.screen_offset = 0
        self.screen_width = 0
        self.screen_height = 0
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
        self.clock = pygame.time.Clock()

        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.color   = self.BLACK

        # MIDI listener
        port_name = self.open_default_port()
        print(f"Opening {port_name}")
        midi = MidiListener(self, port_name)
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

    def run(self):
        last_switch = pygame.time.get_ticks()
        while True:
            if self.strobe:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                now = pygame.time.get_ticks()
                self.TOGGLE_MS = 1000 / self.freq
                if now - last_switch >= self.TOGGLE_MS:
                    
                    self.screen.fill(self.WHITE)
                    pygame.display.flip()
                    time.sleep(0.01)
                    self.screen.fill(self.BLACK)
                    pygame.display.flip()
                    last_switch = now

                
                self.clock.tick(240)  # keep the loop fast enough for precise timing

# Strobe
if __name__ == "__main__":
    Strobe().run()