from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np
import sounddevice as sd

from .sapi import SapiSynth, VoiceInfo

PREFERRED_VB_KEYWORDS = ("CABLE Input", "VB-Audio", "Virtual Cable")
PREFERRED_SPK_KEYWORDS = ("Speakers", "Headphones", "Realtek", "Audio")


@dataclass(frozen=True)
class OutputDevice:
    index: int
    name: str


class TalkAsMicService:
    """
    High level façade around SapiSynth and sounddevice playback for GUI/CLI use.
    """

    synth: SapiSynth = field(default_factory=SapiSynth)  # type: ignore[assignment]

    def __init__(self) -> None:
        self.synth = SapiSynth()
        self.device_vb: Optional[int] = self._auto_pick_output_device(PREFERRED_VB_KEYWORDS)
        self.device_monitor: Optional[int] = None
        self.voice_token_id: Optional[str] = None
        self.rate: int = 0
        self.volume: int = 100
        self._play_lock = threading.Lock()

    # ---- Device helpers -------------------------------------------------
    def list_output_devices(self) -> List[OutputDevice]:
        devices = sd.query_devices()
        return [
            OutputDevice(index=i, name=d["name"])
            for i, d in enumerate(devices)
            if d.get("max_output_channels", 0) > 0
        ]

    def _auto_pick_output_device(self, keywords: tuple[str, ...]) -> Optional[int]:
        for device in self.list_output_devices():
            name = device.name.lower()
            if any(kw.lower() in name for kw in keywords):
                return device.index

        default = sd.default.device
        if isinstance(default, (list, tuple)) and len(default) == 2:
            return default[1]
        return None

    def set_virtual_mic_device(self, device_index: Optional[int]) -> None:
        self.device_vb = device_index

    def set_monitor_device(self, device_index: Optional[int]) -> None:
        self.device_monitor = device_index

    # ---- Voice helpers --------------------------------------------------
    def list_voices(self) -> List[VoiceInfo]:
        return self.synth.list_voices()

    def set_voice(self, token_id: Optional[str]) -> None:
        self.voice_token_id = token_id or None

    # ---- Parameters -----------------------------------------------------
    def set_rate(self, value: int) -> None:
        self.rate = max(-10, min(10, int(value)))

    def set_volume(self, value: int) -> None:
        self.volume = max(0, min(100, int(value)))

    # ---- Core functionality ---------------------------------------------
    def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        pcm, samplerate = self.synth.synth_pcm16(
            text=text, rate=self.rate, volume=self.volume, voice_token_id=self.voice_token_id
        )
        if pcm.size == 0:
            raise RuntimeError("Speech synthesis returned empty audio.")
        peak = float(np.max(np.abs(pcm)))
        if peak > 0.99:
            pcm = pcm * (0.99 / peak)
        return pcm, samplerate

    def speak(self, text: str) -> None:
        pcm, samplerate = self.synthesize(text)
        if self.device_vb is None:
            raise RuntimeError("No VB-CABLE or virtual microphone output device has been selected.")

        with self._play_lock:
            threads: list[threading.Thread] = []
            results: list[tuple[int, Optional[Exception]]] = []

            threads.append(self._play_async(pcm, samplerate, self.device_vb, results))
            if self.device_monitor is not None:
                threads.append(
                    self._play_async(pcm, samplerate, self.device_monitor, results)
                )

            for thread in threads:
                thread.join()

            errors = [f"#{idx}: {err}" for idx, err in results if err is not None]
            if errors:
                raise RuntimeError(
                    "Failed to play audio on device(s): " + "; ".join(errors)
                )

    def _play_async(
        self,
        pcm: np.ndarray,
        samplerate: int,
        device_index: int,
        results: list[tuple[int, Optional[Exception]]],
    ) -> threading.Thread:
        data = np.array(pcm, copy=False)

        def runner() -> None:
            error: Optional[Exception] = None
            try:
                with sd.OutputStream(
                    samplerate=samplerate,
                    device=device_index,
                    channels=data.shape[1],
                    dtype=data.dtype,
                ) as stream:
                    stream.write(data)
            except Exception as exc:
                error = exc
            finally:
                results.append((device_index, error))

        thread = threading.Thread(target=runner, daemon=True)
        thread.start()
        return thread
