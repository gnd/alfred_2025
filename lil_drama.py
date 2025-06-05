# pip install pynput pygame-ce mss screeninfo mido python-rtmidi

import os
import sys
import signal
import socket
import pathlib
import threading
import subprocess
from pynput import keyboard, mouse

# import submodules
from midi_listener import MidiListener
from desktop_feed.feedback import DesktopFeedback
from meme_deathmatch.player import MemeDeathmatch
from gameplay.player import GameplaySludge
from realtime_subs.display import SubtitleDisplay

HERE = pathlib.Path(__file__).parent

class lil_drama:

	def __init__(self):
		# Subprocesses
		self.deathmatch_proc = None
		self.tunnel_proc = None
		self.subs_proc = None
		self.gameplay_proc = None
		self.subtitle_proc = None

		# Various vars
		self.host = "127.0.0.1"
		self.deathmatch_port = 6666
		self.gameplay_port = 6667
		self.secondary_screen = False

		# Keyboard & Mouse listener
		self.key_listener   = keyboard.GlobalHotKeys({
			'b': self.deathmatch_kill_reel,
			'n': self.deathmatch_new_reel,
			'v': self.deathmatch_kill_all,
			'h': self.gameplay_kill_reel,
			'j': self.gameplay_new_reel,
			'g': self.gameplay_kill_all,
			'r': self.toggle_deathmatch,
			't': self.toggle_tunnel,
			'y': self.toggle_gameplay,
			's': self.toggle_subtitles,
			'q': self.on_exit
        })
		self.mouse_listener = mouse.Listener(
			on_scroll=self.on_scroll,
			on_click =self.on_click,
		)

		# MIDI listener
		self.midi = MidiListener(self, port_name="MIDI Mix:MIDI Mix MIDI 1 28:0")
		self.midi.start()

	def toggle_secondary_screen(self):
		if self.secondary_screen:
			print("Disabling secondary screen")
			self.secondary_screen = False
		else:
			print("Enabling secondary screen")
			self.secondary_screen = True

	def toggle_deathmatch(self):
		if self.deathmatch_proc and self.deathmatch_proc.poll() is None:
			print("Stopping deathmatch ...")
			self.deathmatch_proc.terminate()
		else:
			print("Starting deathmatch ...")
			cmd = [sys.executable, "-m", "meme_deathmatch.player"]
			if self.secondary_screen:
				cmd.append("--secondary")
			self.deathmatch_proc = subprocess.Popen(cmd, cwd=HERE)

	def toggle_tunnel(self):
		if self.tunnel_proc and self.tunnel_proc.poll() is None:
			print("Stopping tunnel ...")
			self.tunnel_proc.kill()
		else:
			print("Starting tunnel ...")
			cmd = [sys.executable, "-m", "desktop_feed.feedback"]
			if self.secondary_screen:
				cmd.append("--secondary")
			self.tunnel_proc = subprocess.Popen(cmd, cwd=HERE)

	def toggle_gameplay(self):
		if self.gameplay_proc and self.gameplay_proc.poll() is None:
			print("Stopping gameplay ...")
			self.gameplay_proc.terminate()
		else:
			print("Starting gameplay ...")
			cmd = [sys.executable, "-m", "gameplay.player"]
			if self.secondary_screen:
				cmd.append("--secondary")
			self.gameplay_proc = subprocess.Popen(cmd, cwd=HERE)

	def toggle_subtitles(self):
		if self.subtitle_proc and self.subtitle_proc.poll() is None:
			print("Stopping subtitles ...")
			self.subtitle_proc.terminate()
		else:
			print("Starting subtitles ...")
			cmd = [sys.executable, "-m", "realtime_subs.display"]
			if self.secondary_screen:
				cmd.append("--secondary")
			self.subtitle_proc = subprocess.Popen(cmd, cwd=HERE)

	def deathmatch_new_reel(self):
		self._send_async(self.deathmatch_port, b"new\n")

	def deathmatch_kill_reel(self):
		self._send_async(self.deathmatch_port, b"kill\n")

	def deathmatch_kill_all(self):
		self._send_async(self.deathmatch_port, b"killall\n")

	def gameplay_new_reel(self):
		self._send_async(self.gameplay_port, b"new\n")

	def gameplay_kill_reel(self):
		self._send_async(self.gameplay_port, b"kill\n")

	def gameplay_kill_all(self):
		self._send_async(self.gameplay_port, b"killall\n")

	def on_scroll(self, x, y, dx, dy):
		if   dy > 0: self._send_async(b"new\n")
		elif dy < 0: self._send_async(b"kill\n")

	def on_click(self, x, y, button, pressed):
		if button is mouse.Button.middle and not pressed:
			self._send_async(b"killall\n")

	def _send_async(self, port, payload: bytes):
		threading.Thread(target=self._send_worker, args=(port, payload), daemon=True).start()

	def _send_worker(self, port, payload: bytes):
		try:
			with socket.create_connection((self.host, port), timeout=1) as sock:
				sock.sendall(payload)
		except OSError as err:
			print(f"Connection failed: {err}")

	def on_exit(self):
		print("Received command to quit.")
		if self.midi:
			print("Stopping MIDI listener ...")
			self.midi.stop()
		if self.deathmatch_proc:
			print("Terminating deathmatch ...")
			self.deathmatch_proc.terminate()
		if self.tunnel_proc:
			print("Killing tunnel ...")
			self.tunnel_proc.kill()
		if self.gameplay_proc:
			print("Killing gameplay ...")
			self.gameplay_proc.kill()
		if self.subtitle_proc:
			print("Terminating subtitles ...")
			self.subtitle_proc.terminate()
		print("Quitting ...")
		sys.exit(0)

	def run(self):
		self.key_listener.start()
		self.mouse_listener.start()
		try:
			self.key_listener.join()
		finally:
			self.mouse_listener.stop()

# Lil Drama
if __name__ == "__main__":
    lil_drama().run()