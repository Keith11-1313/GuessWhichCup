"""Windows background music, independent of the short sound-effect channel."""

import ctypes
from pathlib import Path
import sys
import wave

DEFAULT_MUSIC_VOLUME = 20


class BackgroundMusic:
    """Loop a quiet WAV without blocking Tk or interrupting sound effects."""

    def __init__(self, root):
        self.root = root
        self.timer = None
        self.opened = False
        self.error = None
        self.volume = DEFAULT_MUSIC_VOLUME
        self.alias = f"lantern_music_{id(self)}"

    def command(self, text):
        result = ctypes.windll.winmm.mciSendStringW(text, None, 0, None)
        if result:
            self.error = result
        return result

    def start(self):
        if sys.platform != "win32" or self.opened:
            return
        path = Path(__file__).resolve().parent / "assets/sounds/lantern_party.wav"
        with wave.open(str(path), "rb") as audio:
            self.duration_ms = round(1000 * audio.getnframes() / audio.getframerate())
        if self.command(f'open "{path}" type mpegvideo alias {self.alias}'):
            return
        self.opened = True
        self.set_volume(self.volume)
        self.loop()

    def set_volume(self, percent):
        """Set this music channel only; never change the Windows master volume."""
        self.volume = max(0, min(100, int(percent)))
        if self.opened:
            self.command(f"setaudio {self.alias} volume to {self.volume * 10}")

    def loop(self):
        # MCI starts playback asynchronously. Tk schedules only the next loop.
        if self.command(f"play {self.alias} from 0"):
            self.stop()
            return
        self.timer = self.root.after(self.duration_ms, self.loop)

    def stop(self):
        if self.timer is not None:
            self.root.after_cancel(self.timer)
            self.timer = None
        if self.opened:
            self.command(f"close {self.alias}")
            self.opened = False
