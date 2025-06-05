import os
import sys
import time
import signal
import socket
import random
import argparse
import threading
import subprocess
from pathlib import Path, os
from screeninfo import get_monitors

class GameplaySludge(threading.Thread):

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

        # Configuration
        self.reel_width = 600
        self.reels_folder = (Path(__file__).resolve().parent / "gameplay")
        self.listen_port = 6667
        self.listen_host = 'localhost'
        self.kill_timeout = 3
        self.loudness = -100
        self.secondary_screen = secondary_screen
        self.screen_offset = 0

        # List of processes
        self.process_list = []

        # Load all reels
        self.current_reel_index = 0
        self.reel_files = [f for f in os.listdir(self.reels_folder) if (f.endswith('sludge.mp4') and f)]
        self.reel_count = len(self.reel_files)
        self.reel_files.sort()
        if self.reel_count == 0:
            print("[gameplay] No reels found in folder.")
            exit(1)

        # Get screen dimensions
        if (self.secondary_screen):
            print("[gameplay] Running on secondary screen")
            monitor = get_monitors()[1]
            self.screen_offset = get_monitors()[0].width
        else:
            monitor = get_monitors()[0]
            self.screen_offset = 0
        self.screen_width = monitor.width
        self.screen_height = monitor.height
        print(f"[gameplay] width: {self.screen_width}, height: {self.screen_height}")
        self.main_vid_fullscreen = True

        # Video dimensions
        self.width_half = int(self.screen_width / 2)
        self.width_smaller = int(self.screen_width / 2.66666)
        self.height_half = int(self.screen_height / 2)

        # Launch first vid
        self.launch_mainvid(os.path.join(self.reels_folder, 'gameplay.mp4'))

    def launch_mainvid(self, file_path):
        window_title = f"mplayer_main"
        
        cmd = [
            "mplayer",
            "-xy", f"{self.screen_width},{self.screen_height}",
            "-geometry", f"{self.screen_offset}:0",
            "-vo", "x11",
            "-loop", "0",
            "-really-quiet",
            "-noborder",
            "-nomouseinput",
            "-hardframedrop",
            "-double",
            "-nosub",
            # more quiet
            "-af", f"volume=-{self.loudness}",
            "-title",
            window_title,
            file_path
        ]

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True
        )

        self.process_list.append(proc)

    def launch_sidevid(self, file_path, index, x, y, width, height):
        window_title = f"mplayer_{index}"

        cmd = [
            "nice", "-n", "19",
            "mplayer",
            "-xy", f"{width},{height}",
            "-geometry", f"{x+self.screen_offset}:{y}",
            "-loop", "0",
            "-really-quiet",
            "-noborder",
            "-nomouseinput",
            "-hardframedrop",
            "-double",
            "-nosub",
            # more quiet
            "-af", f"volume=-{self.loudness}",
            "-title",
            window_title,
            file_path
        ]

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True
        )

        self.process_list.append(proc)


    def toggle_fullscreen(self, title, fullscreen):
        if (fullscreen):
            # Remove fullscreen
            wmctrl_cmd = ["wmctrl", "-r", title, "-b", "remove,fullscreen"]
            subprocess.run(wmctrl_cmd, check=True)
        else:
            # Add fullscreen
            wmctrl_cmd = ["wmctrl", "-r", title, "-b", "add,fullscreen"]
            subprocess.run(wmctrl_cmd, check=True)


    def move_window(self, title, x, y, width, height):
        try:
            # Make it a bit smaller to make place for other videos
            wmctrl_cmd = ["wmctrl", "-r", title, "-e", f"0,{x+self.screen_offset},{y},{width},{height}"]
            subprocess.run(wmctrl_cmd, check=True)
            print(f"[gameplay] Moved and resized '{title}' to {x+self.screen_offset},{y} ({width}x{height})")
        except subprocess.CalledProcessError as e:
            print(f"[gameplay] wmctrl failed: {e}")

    def kill_player(self, proc):
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=self.kill_timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
            finally:
                proc = None

    def resume(self):
        self.active.set()

    def pause(self):
        self.active.clear()

    def shutdown(self):
        self.stopper.set()
        self.active.set()  

    def on_exit(self, signum, frame):
        print("[gameplay] Cleaning up ...")
        while self.process_list:
            self.kill_player(self.process_list.pop())
        sys.exit(0)

    # Thread entrypoint here
    def run(self):
        # endless loop
        while not self.stopper.is_set():
            if not self.active.wait(timeout=0.1):
                continue 
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((self.listen_host, self.listen_port))
                s.listen()
                print(f"[gameplay] Ready. Listening on {self.listen_host}:{self.listen_port} ...")

                conn, addr = s.accept()
                with conn:
                    print(f"Connected by {addr}")
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            break
                        command = data.decode().strip()
                        if command == 'new':
                            print("[gameplay] Launching new video.")
                            match len(self.process_list):
                                # Second video layer
                                case 1:
                                    self.launch_sidevid(os.path.join(self.reels_folder, self.reel_files[self.current_reel_index]), self.current_reel_index, 0, 0, self.width_smaller, self.screen_height)
                                    print(f"[gameplay] {len(self.process_list)} videos running..")
                                # Third video layer
                                case 2:
                                    self.toggle_fullscreen("mplayer_main", self.main_vid_fullscreen)
                                    self.main_vid_fullscreen = not self.main_vid_fullscreen
                                    self.move_window("mplayer_main", self.width_half, 0, self.width_half, self.screen_height)
                                    self.move_window("mplayer_0", 0, 0, self.width_half, self.height_half)
                                    # launch third video
                                    self.launch_sidevid(os.path.join(self.reels_folder, self.reel_files[self.current_reel_index]), self.current_reel_index, 0, self.height_half, self.width_half, self.height_half)
                                    print(f"[gameplay] {len(self.process_list)} videos running..")
                                # All others
                                case _:
                                    pos_x = random.randint(0, max(0, self.screen_width - self.reel_width))
                                    pos_y = random.randint(0, max(0, self.screen_height - 500))
                                    self.launch_sidevid(os.path.join(self.reels_folder, self.reel_files[self.current_reel_index]), self.current_reel_index, pos_x, pos_y, self.reel_width, 0)
                                    print(f"[gameplay] {len(self.process_list)} videos running..")
                            # increase reel index
                            self.current_reel_index = (self.current_reel_index + 1) % self.reel_count
                        if command == 'kill' and self.process_list:
                            self.kill_player(self.process_list.pop())
                            if (len(self.process_list) == 1):
                                self.toggle_fullscreen("mplayer_main", self.main_vid_fullscreen)
                                self.main_vid_fullscreen = not self.main_vid_fullscreen
                                self.move_window("mplayer_main", 0, 0, self.screen_width, self.screen_height)
                            print("[gameplay] Killing last video.")
                            print(f"[gameplay] {len(self.process_list)} videos left..")
                        if command == 'killall':
                            print("[gameplay] Killing all videos.")
                            while self.process_list:
                                self.kill_player(self.process_list.pop())
                            print(f"[gameplay] {len(self.process_list)} videos left..")


# Start Gameplay Sludge
def main():
    # Parse some arguments
    p = argparse.ArgumentParser()
    p.add_argument("--secondary", action="store_true", help="Run on the secondary screen")
    args = p.parse_args()
    gameplay = GameplaySludge(secondary_screen=args.secondary)
    gameplay.resume()
    try:
        gameplay.run()
    except KeyboardInterrupt:
        gameplay.shutdown()

if __name__ == "__main__":
    main()