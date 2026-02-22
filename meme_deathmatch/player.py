import os
import sys
import time
import random
import socket
import signal
import random
import argparse
import threading
import subprocess
from pathlib import Path, os
from screeninfo import get_monitors

class MemeDeathmatch(threading.Thread):
    
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
        self.max_reels = 60
        self.reel_width = 300
        self.reel_anomaly = 100
        self.reels_folder = (Path(__file__).resolve().parent / "downloaded" / "smol")
        # when 9:16 / for teaser
        #self.reels_folder = (Path(__file__).resolve().parent / "downloaded")

        self.listen_port = 6666
        self.listen_host = 'localhost'
        self.loudness = "10"
        self.kill_timeout = 3
        self.secondary_screen = secondary_screen
        self.screen_offset = 0

        # Socket stuff
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.listen_host, self.listen_port))
        self.sock.listen()
        print(f"[deathmatch] Ready on {self.listen_host}:{self.listen_port}")

        # List of processes
        self.process_list = []

        # Load all reels
        self.current_reel_index = 0
        self.reel_files = [f for f in os.listdir(self.reels_folder) if f.endswith('.mp4')]
        random.shuffle(self.reel_files)
        # when 9:16 screen / for teaser
        # self.reel_files[1] = 'reel_251.mp4'
        # my jsme petr fiala lololol
        # remove block after perfo (02/2026)
        fiala_force = 10
        random_fiala = int(random.random() * 10)
        self.reel_files[random_fiala] = 'reel_fiala_1.mp4'
        random_fiala = int(random.random() * 10)
        self.reel_files[random_fiala] = 'reel_fiala_2.mp4'
        random_klempir = int(random.random() * 10)
        self.reel_files[random_klempir] = 'reel_klempir.mp4'
        # end of block
        self.reel_count = len(self.reel_files)
        if self.reel_count == 0:
            print("[deathmatch] No reels found in folder.")
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
        print(f"[deathmatch] width: {self.screen_width}, height: {self.screen_height}")


    def launch_reel(self, file_path):
        random_size = random.randint(0, self.reel_anomaly) - int(self.reel_anomaly / 2)
        actual_reel_width = self.reel_width + random_size
        random_x = random.randint(0, max(0, self.screen_width - actual_reel_width)) - 100
        random_y = random.randint(0, max(0, self.screen_height - 200)) - 100
        # when 9:16 screen
        #random_x = random.randint(int(self.screen_width/3)-50, max(0, (self.screen_width - actual_reel_width)-int(self.screen_width/3))+50)
        #random_y = random.randint(0, max(0, self.screen_height - 200)) - 100

        cmd = [
            "nice", "-n", "19",
            "mplayer",
            "-fixed-vo",
            "-xy", str(actual_reel_width),
            #"-geometry", f"{random_x+self.screen_offset}:{random_y}",
            "-geometry", f"+{random_x+self.screen_offset}+{random_y}",
            "-loop", "0",
            "-really-quiet",
            "-noborder",
            "-nomouseinput",
            # some stuff to speed up
            #"-vo", "xv",
            "-hardframedrop",
            "-double",
            "-nosub",
            # more quiet
            "-af", f"volume=-{self.loudness}",
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


    def kill_reel(self, proc):
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
        print("[deathmatch] Cleaning up ...")
        self.sock.close()
        while self.process_list:
            self.kill_reel(self.process_list.pop())
        sys.exit(0)

    # Thread entrypoint here
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
                print(f"[deathmatch] Connected by {addr}")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    command = data.decode().strip()
                    if command == 'new':
                        if (len(self.process_list) < self.max_reels):
                            print("[deathmatch] Launching new reel.")
                            self.current_reel_index = (self.current_reel_index + 1) % self.reel_count
                            self.launch_reel(os.path.join(self.reels_folder, self.reel_files[self.current_reel_index]))
                            print(f"[deathmatch] {len(self.process_list)} reels running..")
                        else:
                            print(f"[deathmatch] Max reels running: ({len(self.process_list)})")
                    if command == 'kill' and self.process_list:
                        self.kill_reel(self.process_list.pop())
                        print("[deathmatch] Killing last reel.")
                        print(f"[deathmatch] {len(self.process_list)} reels left..")
                    if command == 'killall':
                        print("[deathmatch] Killing all reels.")
                        while self.process_list:
                            self.kill_reel(self.process_list.pop())
                        print(f"[deathmatch] {len(self.process_list)} reels left..")

# Start Meme Deathmatch
def main():
    # Parse some arguments
    p = argparse.ArgumentParser()
    p.add_argument("--secondary", action="store_true", help="Run on the secondary screen")
    args = p.parse_args()
    deathmatch = MemeDeathmatch(secondary_screen=args.secondary)
    deathmatch.resume()
    try:
        deathmatch.run()
    except KeyboardInterrupt:
        deathmatch.shutdown()

if __name__ == "__main__":
    main()