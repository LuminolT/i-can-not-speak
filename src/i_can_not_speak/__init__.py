"""Utilities for speaking typed text through a virtual microphone on Windows."""

from .sapi import SapiSynth  # noqa: F401
from .service import TalkAsMicService  # noqa: F401

__all__ = ["SapiSynth", "TalkAsMicService"]
