import time
from utils import concat

class DisplayManager:
    def __init__(self, app, display, align="center", padding=None):
        self.app = app
        self.d = display
        self.align = align
        self.padding_top = padding[0]
        self.padding_left = padding[1]

    def display(self):
        msg = self.app.text_buffer_window if self.app.text_buffer_window is not None else self.app.text_buffer
        self.d.send(
            original=msg,
            fill=True,
            align=self.align,
            padding_top=self.padding_top,
            padding_left=self.padding_left,
        )
        self.app.last_sent_time = time.time()

    def display_intermediate(self, text):
        buf = self.app.text_buffer_window if self.app.text_buffer_window is not None else self.app.text_buffer
        msg = (concat(buf, text)).strip()
        self.d.send(
            original=msg,
            fill=True,
            align=self.align,
            padding_top=self.padding_top,
            padding_left=self.padding_left,
        )
        self.app.last_sent_time = time.time()

    def display_translation(self):
        msg = self.app.trans_buffer_window if self.app.trans_buffer_window is not None else self.app.trans_buffer
        self.d.send(
            translation=msg,
            fill=True,
            align=self.align,
            padding_top=self.padding_top,
            padding_left=self.padding_left,
        )

    def clear(self):
        self.d.send(text=None, fill=True)
