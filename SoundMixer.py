"""Independent master, music and game-effects levels using Windows audio."""

import ctypes as Ctypes
from pathlib import Path
from NamingCompatibility import PascalName
import sys as Sys


class SoundMixer:
    def __init__(Self, Session):
        Self.Session = Session
        Self.Channels = {}

    def Command(Self, Text):
        if Sys.platform != "win32":
            return 1
        return Ctypes.windll.winmm.mciSendStringW(Text, None, 0, None)

    def Apply(Self):
        G = Self.Session
        G.Music.Master = G.Settings.Values["master"]
        G.Music.SetVolume(G.Music.Volume)
        Volume = round(G.Settings.Values["master"] * G.Settings.Values["effects"] / 10)
        for Alias in Self.Channels.values():
            Self.Command(f"setaudio {Alias} volume to {Volume}")

    def Play(Self, Kind):
        G = Self.Session
        if not G.SoundEnabled or not G.AudioActive or Sys.platform != "win32":
            return
        if Kind not in Self.Channels:
            FilePath = (
                Path(__file__).resolve().parent
                / "assets"
                / "sounds"
                / f"{PascalName(Kind)}.wav"
            )
            if not FilePath.is_file():
                return
            Alias = f"cup_{id(Self)}_{Kind}"
            if Self.Command(f'open "{FilePath}" type mpegvideo alias {Alias}'):
                return
            Self.Channels[Kind] = Alias
        Alias = Self.Channels[Kind]
        Self.Apply()
        Self.Command(f"play {Alias} from 0")

    def Stop(Self):
        for Alias in Self.Channels.values():
            Self.Command(f"close {Alias}")
        Self.Channels.clear()
