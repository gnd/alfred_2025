# pip install pygame-ce mss screeninfo
import os
import subprocess
import pygame, mss
from screeninfo import get_monitors

class DesktopFeedback:

    def __init__(self, lil_drama):
        # The main app
        self.lil_drama = lil_drama

        # Get screen dimensions
        monitor = get_monitors()[0]
        self.screen_width = monitor.width
        self.screen_height = monitor.height
        print(f"width: {self.screen_width}, height: {self.screen_height}")

        # Init pygame window
        pygame.init()
        pygame.display.set_caption('lil_feed')

        # create a hidden window so mss won't see it
        self.window = pygame.display.set_mode((1, 1), pygame.HIDDEN)

    def make_screenshot(self):
        with mss.mss() as sct:
            monitor = sct.monitors[0]          # 0 == virtual “all monitors”
            shot = sct.grab(monitor)
            # mss gives RGB in BGRA byte order → convert
            screenshot = pygame.image.frombuffer(shot.rgb, shot.size, "RGB")
            return screenshot

    def run(self):
        screenshot = self.make_screenshot()
        # resize the shot for feedback to work
        smaller_shot = pygame.transform.smoothscale(screenshot, (self.screen_width - 40, self.screen_height - 50))

        # replace the hidden window with a real one after the capture
        self.window = pygame.display.set_mode((self.screen_width - 40, self.screen_height - 50), pygame.NOFRAME)
        pygame.display.set_window_position((20, 0))

        # endless loop
        running = True
        self.window.blit(smaller_shot, (0, 0))
        pygame.display.flip()
        frame = 0
        while running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
            
            screenshot = self.make_screenshot()
            smaller_shot = pygame.transform.smoothscale(screenshot, (1880, 1030))
            self.window.blit(smaller_shot, (0, 0))
            pygame.display.flip()

            frame = (frame + 1) % 100
            if (frame > 50):
                wmctrl_cmd = ["wmctrl", "-a", 'lil_feed']
                subprocess.run(wmctrl_cmd, check=True)
        
        pygame.quit()

# Desktop Feedback
if __name__ == "__main__":
    DesktopFeedback(None).run()