from __future__ import annotations

import os
import tempfile
import wave
from contextlib import contextmanager
from dataclasses import dataclass
import threading
from typing import List, Optional, Tuple

import numpy as np

try:
    from comtypes import CoInitialize, CoUninitialize  # type: ignore
    from comtypes.client import CreateObject, GetModule  # type: ignore
except Exception as exc:  # pragma: no cover - import guard for non-Windows platforms
    CoInitialize = None  # type: ignore
    CoUninitialize = None  # type: ignore
    CreateObject = None  # type: ignore
    GetModule = None  # type: ignore
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

SpeechLib = None  # type: ignore
_SPEECHLIB_ERROR: Optional[Exception] = None
_COM_STATE = threading.local()


VoiceList = List["VoiceInfo"]


@dataclass(frozen=True)
class VoiceInfo:
    """Metadata about an installed SAPI voice."""

    index: int
    description: str
    language: str
    token_id: str


class SapiSynth:
    """Minimal wrapper around Windows SAPI5 speech synthesis."""

    def __init__(self) -> None:
        _ensure_windows()
        self._speechlib = _load_speechlib()
        self.default_samplerate = 16000

    def list_voices(self) -> VoiceList:
        """List available SAPI voices."""
        with _com_scope():
            voice = self._create_voice()
            tokens = voice.GetVoices()
            items: VoiceList = []
            for i in range(tokens.Count):
                token = tokens.Item(i)
                desc = token.GetDescription()
                lang = token.GetAttribute("Language") or ""
                token_id = token.Id
                items.append(VoiceInfo(i, desc, lang, token_id))
            return items

    def synth_pcm16(
        self,
        text: str,
        *,
        rate: int = 0,
        volume: int = 100,
        voice_token_id: Optional[str] = None,
    ) -> Tuple[np.ndarray, int]:
        """
        Synthesize text to a mono float32 numpy array (PCM, range [-1, 1]).

        Returns (pcm, samplerate). pcm has shape (N, 1).
        """
        text = (text or "").strip()
        if not text:
            return np.zeros((0, 1), dtype=np.float32), self.default_samplerate

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".wav")
        os.close(tmp_fd)
        try:
            with _com_scope():
                voice = self._create_voice(voice_token_id=voice_token_id)
                tokens = voice.GetVoices()
                if tokens.Count == 0:
                    raise RuntimeError(
                        "Windows SAPI does not have any voices installed. "
                        "Install a voice pack from Windows settings."
                    )

                voice.Rate = _clamp(rate, -10, 10)
                voice.Volume = _clamp(volume, 0, 100)

                stream = CreateObject("SAPI.SpFileStream")  # type: ignore[arg-type]
                fmt = CreateObject("SAPI.SpAudioFormat")  # type: ignore[arg-type]
                fmt.Type = self._speechlib.SAFT16kHz16BitMono  # type: ignore[attr-defined]
                stream.Format = fmt
                stream.Open(tmp_path, self._speechlib.SSFMCreateForWrite)  # type: ignore[attr-defined]

                voice.AudioOutputStream = stream
                voice.Speak(text, 0)
                stream.Close()
                voice.AudioOutputStream = None

            with wave.open(tmp_path, "rb") as wf:
                frames = wf.readframes(wf.getnframes())
                samplerate = wf.getframerate()

            pcm = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            if pcm.ndim == 1:
                pcm = pcm.reshape(-1, 1)
            return pcm, samplerate
        finally:
            try:
                os.remove(tmp_path)
            except FileNotFoundError:
                pass

    def export_wav(
        self,
        text: str,
        *,
        path: str,
        rate: int = 0,
        volume: int = 100,
        voice_token_id: Optional[str] = None,
    ) -> None:
        """Synthesize text and persist it to a WAV file."""
        pcm, samplerate = self.synth_pcm16(
            text, rate=rate, volume=volume, voice_token_id=voice_token_id
        )
        if pcm.size == 0:
            raise RuntimeError("No audio was generated for the provided text.")

        pcm16 = np.clip(pcm * 32767.0, -32768.0, 32767.0).astype(np.int16)

        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(samplerate)
            wf.writeframes(pcm16.tobytes())

    @staticmethod
    def _create_voice(*, voice_token_id: Optional[str] = None):
        _ensure_windows()

        voice = CreateObject("SAPI.SpVoice")  # type: ignore[arg-type]
        if voice_token_id:
            try:
                token = CreateObject("SAPI.SpObjectToken")  # type: ignore[arg-type]
                token.SetId(voice_token_id)
                voice.Voice = token
            except Exception as exc:  # pragma: no cover - comtypes error path
                raise RuntimeError(f"Failed to select voice: {voice_token_id}") from exc
        return voice


def _ensure_windows() -> None:
    import sys

    if sys.platform != "win32":
        raise OSError("Windows SAPI speech synthesis is only available on Windows.")
    if _IMPORT_ERROR is not None:
        raise ImportError(
            "Failed to import comtypes. Install the dependency first."
        ) from _IMPORT_ERROR
    if _SPEECHLIB_ERROR is not None:
        raise ImportError("Failed to load SAPI type library.") from _SPEECHLIB_ERROR


def _clamp(value: int, lo: int, hi: int) -> int:
    return int(max(lo, min(hi, value)))


def _load_speechlib():
    global SpeechLib, _SPEECHLIB_ERROR
    if SpeechLib is not None:
        return SpeechLib
    if _SPEECHLIB_ERROR is not None:
        raise _SPEECHLIB_ERROR
    if _IMPORT_ERROR is not None:
        raise ImportError("comtypes is not available.") from _IMPORT_ERROR

    with _com_scope():
        try:
            from comtypes.gen import SpeechLib as speech_lib  # type: ignore
        except ImportError as err:
            if GetModule is None:
                _SPEECHLIB_ERROR = err
                raise
            windows_dir = os.environ.get("SystemRoot", r"C:\Windows")
            candidates = [
                os.path.join(windows_dir, "System32", "Speech", "Common", "sapi.dll"),
                os.path.join(windows_dir, "SysWOW64", "Speech", "Common", "sapi.dll"),
            ]
            for path in candidates:
                if not os.path.exists(path):
                    continue
                try:
                    GetModule(path)
                except Exception:
                    continue
                else:
                    break
            else:
                _SPEECHLIB_ERROR = err
                raise
            from comtypes.gen import SpeechLib as speech_lib  # type: ignore

    SpeechLib = speech_lib  # type: ignore
    return SpeechLib


@contextmanager
def _com_scope():
    if CoInitialize is None or CoUninitialize is None:
        raise ImportError("comtypes CoInitialize is unavailable.")

    count = getattr(_COM_STATE, "count", 0)
    if count > 0:
        _COM_STATE.count = count + 1
        try:
            yield
        finally:
            _COM_STATE.count -= 1
        return

    CoInitialize()  # type: ignore[misc]
    _COM_STATE.count = 1
    try:
        yield
    finally:
        _COM_STATE.count = 0
        CoUninitialize()  # type: ignore[misc]
