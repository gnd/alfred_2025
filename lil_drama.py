# pip install pynput pygame-ce mss screeninfo

import os
import sys
import pathlib
import subprocess
from pynput import keyboard

# import submodules
from desktop_feed.feedback import DesktopFeedback
from meme_deathmatch.player import MemeDeathmatch


HERE = pathlib.Path(__file__).parent

class lil_drama:

	def __init__(self):
		# Subprocesses
		self.memes_proc = None
		self.tunnel_proc = None
		self.subs_proc = None
		self.sludge_proc = None

	def toggle_tunnel(self):
		if self.tunnel_proc and self.tunnel_proc.poll() is None:
			print("Stopping tunnel …")
			self.tunnel_proc.kill()
		else:
			print("Starting tunnel …")
			self.tunnel_proc = subprocess.Popen([sys.executable, "-m", "desktop_feed.feedback"],cwd=HERE)
			
	def run(self):
		try:
			with keyboard.GlobalHotKeys({'t': self.toggle_tunnel}) as hk:
				hk.join()
		finally:
			if self.tunnel_proc and self.tunnel_proc.poll() is None:
				self.tunnel_proc.terminate()

# Lil Drama
if __name__ == "__main__":
    lil_drama().run()