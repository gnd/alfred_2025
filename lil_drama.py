# pip install pynput pygame-ce mss screeninfo

import os
import sys
import socket
import pathlib
import threading
import subprocess
from pynput import keyboard, mouse

# import submodules
from desktop_feed.feedback import DesktopFeedback
from meme_deathmatch.player import MemeDeathmatch

HERE = pathlib.Path(__file__).parent

class lil_drama:

	def __init__(self):
		# Subprocesses
		self.deathmatch_proc = None
		self.tunnel_proc = None
		self.subs_proc = None
		self.sludge_proc = None

		# Various vars
		self.deathmatch_port = 6666
		self.deathmatch_host = "127.0.0.1"

		# Keyboard & Mouse listener
		self.key_listener   = keyboard.GlobalHotKeys({
			'b': self.deathmatch_kill_reel,
			'n': self.deathmatch_new_reel,
			'v': self.deathmatch_kill_all,
			'r': self.toggle_deathmatch,
			't': self.toggle_tunnel
        })
		self.mouse_listener = mouse.Listener(
			on_scroll=self.on_scroll,
			on_click =self.on_click,
		)

	def toggle_tunnel(self):
		if self.tunnel_proc and self.tunnel_proc.poll() is None:
			print("Stopping tunnel ...")
			self.tunnel_proc.kill()
		else:
			print("Starting tunnel ...")
			self.tunnel_proc = subprocess.Popen([sys.executable, "-m", "desktop_feed.feedback"], cwd=HERE)

	def toggle_deathmatch(self):
		if self.deathmatch_proc and self.deathmatch_proc.poll() is None:
			print("Stopping deathmatch ...")
			self.deathmatch_proc.terminate()
			#self.deathmatch_proc.kill()
		else:
			print("Starting deathmatch ...")
			self.deathmatch_proc = subprocess.Popen([sys.executable, "-m", "meme_deathmatch.player"], cwd=HERE)

	def deathmatch_new_reel(self):
		self._send_async(b"new\n")

	def deathmatch_kill_reel(self):
		self._send_async(b"kill\n")

	def deathmatch_kill_all(self):
		self._send_async(b"killall\n")

	def _deathmatch_new_reel_worker(self):
		try:
			with socket.create_connection((self.deathmatch_host, self.deathmatch_port), timeout=1) as sock:
				sock.sendall(b"new\n")
		except OSError as err:
			print(f"[deathmatch] connection failed: {err}")

	def _deathmatch_kill_reel_worker(self):
		try:
			with socket.create_connection((self.deathmatch_host, self.deathmatch_port), timeout=1) as sock:
				sock.sendall(b"kill\n")
		except OSError as err:
			print(f"[deathmatch] connection failed: {err}")

	def _deathmatch_kill_all_worker(self):
		try:
			with socket.create_connection((self.deathmatch_host, self.deathmatch_port), timeout=1) as sock:
				sock.sendall(b"killall\n")
		except OSError as err:
			print(f"[deathmatch] connection failed: {err}")

	def on_scroll(self, x, y, dx, dy):
		if   dy > 0: self._send_async(b"new\n")
		elif dy < 0: self._send_async(b"kill\n")

	def on_click(self, x, y, button, pressed):
		if button is mouse.Button.middle and not pressed:
			self._send_async(b"killall\n")

	def _send_async(self, payload: bytes):
		threading.Thread(target=self._send_worker, args=(payload,), daemon=True).start()

	def _send_worker(self, payload: bytes):
		try:
			with socket.create_connection((self.deathmatch_host, self.deathmatch_port), timeout=1) as sock:
				sock.sendall(payload)
		except OSError as err:
			print(f"Connection failed: {err}")

	def run(self):
		# try:
		# 	with keyboard.GlobalHotKeys({
		# 			'b': self.deathmatch_kill_reel,
		# 			'n': self.deathmatch_new_reel,
		# 			'v': self.deathmatch_kill_all,
		# 			'r': self.toggle_deathmatch,
		# 			't': self.toggle_tunnel
		# 		}) as hk:
		# 		hk.join()
		# finally:
		# 	if self.tunnel_proc and self.tunnel_proc.poll() is None:
		# 		self.tunnel_proc.terminate()
		# 	if self.deathmatch_proc and self.deathmatch_proc.poll() is None:
		# 		self.deathmatch_proc.terminate()
		self.key_listener.start()
		self.mouse_listener.start()
		try:
			self.key_listener.join()
		finally:
			self.mouse_listener.stop()

# Lil Drama
if __name__ == "__main__":
    lil_drama().run()