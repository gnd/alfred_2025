import time
try:
    from utils import concat
except:
    from .utils import concat

class DisplayManager:
    def __init__(self, app, display):
        self.app = app
        self.d = display

    def display(self):
        msg = self.app.text_buffer_window if self.app.text_buffer_window is not None else self.app.text_buffer
        self.d.send(
            original=msg,
            fill=True
        )
        self.app.last_sent_time = time.time()

    def display_intermediate(self, text):
        buf = self.app.text_buffer_window if self.app.text_buffer_window is not None else self.app.text_buffer
        msg = (concat(buf, text)).strip()
        self.d.send(
            original=msg,
            fill=True
        )
        self.app.last_sent_time = time.time()

    def display_intermediate_translation(self, text):
        self.d.send(
            translation=text,
            fill=True
        )
        self.app.last_sent_time = time.time()

    def display_translation(self):
        msg = self.app.trans_buffer_window if self.app.trans_buffer_window is not None else self.app.trans_buffer
        self.d.send(
            translation=msg,
            fill=True
        )

    def clear(self):
        self.d.send(text=None, fill=True)
