import os
import subprocess
import random
import time
import socket
from screeninfo import get_monitors

# Configuration
REEL_WIDTH = 600
REEL_ANOMALY = 100
REELS_FOLDER = 'gameplay'
PORT = 6666
HOST = 'localhost'
LOUD = "10"
KILL_TIMEOUT = 3
PLAYER = "mplayer"  # Options: 'mplayer' or 'ffplay'

# List of processes
process_list = []

reel_files = [f for f in os.listdir(REELS_FOLDER) if (f.endswith('sludge.mp4') and f)]
reel_count = len(reel_files)

if reel_count == 0:
    print("No reels found in folder.")
    exit(1)

# Screen dimensions
monitor = get_monitors()[0]
screen_width, screen_height = monitor.width, monitor.height

current_reel_index = 0

def launch_mainvid(file_path):
    
    cmd = [
        "mplayer",
        "-fs",
        "-loop", "0",
        "-really-quiet",
        "-noborder",
        "-nomouseinput",
        "-hardframedrop",
        "-double",
        "-nosub",
        # more quiet
        "-af", f"volume=-{LOUD}",
        file_path
    ]

    print(" ".join(cmd))
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True
    )

    process_list.append(proc)

def launch_player(file_path):
    actual_reel_width = REEL_WIDTH
    random_x = random.randint(0, max(0, screen_width - actual_reel_width))
    random_y = random.randint(0, max(0, screen_height - 500))

    cmd = [
        "nice", "-n", "19",
        "mplayer",
        "-xy", str(actual_reel_width),
        "-geometry", f"{random_x}:{random_y}",
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
        "-af", f"volume=-{LOUD}",
        file_path
    ]

    #print(" ".join(cmd))
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True
    )

    process_list.append(proc)


def kill_player(proc):
    if proc:
        try:
            proc.terminate()
            proc.wait(timeout=KILL_TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
        finally:
            proc = None


# Socket server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    launch_mainvid(os.path.join(REELS_FOLDER, 'gameplay.mp4'))

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"Player ready. Listening on {HOST}:{PORT} using {PLAYER}...")

    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            data = conn.recv(1024)
            if not data:
                break
            command = data.decode().strip()
            if command == 'new':
                print("Launching new process.")
                current_reel_index = (current_reel_index + 1) % reel_count
                launch_player(os.path.join(REELS_FOLDER, reel_files[current_reel_index]))
                print(f"{len(process_list)} processes running..")
            if command == 'kill' and process_list:
                kill_player(process_list.pop())
                print("Killing last process.")
                print(f"{len(process_list)} processes left..")
            if command == 'killall':
                print("Killing all processes.")
                while process_list:
                    kill_player(process_list.pop())
                print(f"{len(process_list)} processes left..")
