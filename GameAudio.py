"""Windows background music, independent of the short sound-effect channel."""

import ctypes as Ctypes
from pathlib import Path
import sys as Sys
import wave as Wave

DefaultMusicVolume = 20


class BackgroundMusic:
    """Loop a quiet WAV without blocking Tk or interrupting sound effects."""

    def __init__(Self, Root):
        Self.Root = Root
        Self.Timer = None
        Self.Opened = False
        Self.Error = None
        Self.Volume = DefaultMusicVolume
        Self.Master = 100
        Self.Alias = f"lantern_music_{id(Self)}"

    def Command(Self, Text):
        Result = Ctypes.windll.winmm.mciSendStringW(Text, None, 0, None)
        if Result:
            Self.Error = Result
        return Result

    def Start(Self):
        if Sys.platform != "win32" or Self.Opened:
            return
        FilePath = Path(__file__).resolve().parent / "assets/sounds/LanternParty.wav"
        with Wave.open(str(FilePath), "rb") as Audio:
            Self.DurationMs = round(1000 * Audio.getnframes() / Audio.getframerate())
        if Self.Command(f'open "{FilePath}" type mpegvideo alias {Self.Alias}'):
            return
        Self.Opened = True
        Self.SetVolume(Self.Volume)
        Self.Loop()

    def SetVolume(Self, Percent):
        """Set this music channel only; never change the Windows master volume."""
        Self.Volume = max(0, min(100, int(Percent)))
        if Self.Opened:
            Self.Command(
                f"setaudio {Self.Alias} volume to {round(Self.Volume * Self.Master / 10)}"
            )

    def Loop(Self):
        # MCI starts playback asynchronously. Tk schedules only the next loop.
        if Self.Command(f"play {Self.Alias} from 0"):
            Self.Stop()
            return
        Self.Timer = Self.Root.after(Self.DurationMs, Self.Loop)

    def Stop(Self):
        if Self.Timer is not None:
            Self.Root.after_cancel(Self.Timer)
            Self.Timer = None
        if Self.Opened:
            Self.Command(f"close {Self.Alias}")
            Self.Opened = False
