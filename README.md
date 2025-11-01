# I Can Not Speak

English | [简体中文](README_ZH_CN.md)

## Overview

I Can Not Speak is a Windows-only text-to-speech assistant that uses the system SAPI 5 voices and streams audio through a virtual microphone. The UI is built with [Flet](https://flet.dev/) and targets users who need to play synthesized speech into voice chat or conferencing software.

## Key Features

- Enumerates playback devices and selects a virtual microphone (tested with VB-Audio VB-CABLE).
- Optional local monitor output so you can hear the audio while it streams to the virtual device.
- Adjustable speech rate and volume with instant feedback.
- Asynchronous speech queue powered by Windows SAPI for offline voice synthesis.

## Requirements

- **Operating system:** Windows 10 or later (SAPI 5 is required). The app does not run on macOS or Linux.
- **Virtual microphone:** [VB-Audio VB-CABLE](https://vb-audio.com/Cable/) or another compatible virtual audio device. Install and enable it before launching the app.
- **Python:** 3.12+ (managed via [uv](https://github.com/astral-sh/uv) in this project).

## Initial Setup

Install dependencies with uv (this creates the virtual environment on first run):

```powershell
uv sync
```

Make sure VB-CABLE is installed and that at least one SAPI voice is available in Windows Settings → Time & Language → Speech.

## Running the App

Launch the desktop UI with:

```powershell
uv run i-can-not-speak
```

If you add new SAPI voices or audio devices while the app is open, use the refresh button inside the UI to reload the device list.

## Packaging (Flet Build)

The project follows the structure required by `flet build`. To produce a Windows bundle:

```powershell
flet build windows -v
```

Ensure Visual Studio Build Tools and the Flutter desktop prerequisites are installed, as described in the [Flet publishing guide](https://flet.dev/docs/publish/).

## Troubleshooting

- **No voices available:** install an additional SAPI voice in Windows settings.
- **VB-CABLE missing:** install VB-CABLE and reboot if it does not show up in the device list.
- **Audio clipping:** reduce the speech volume slider inside the app or lower the gain on the destination application.

## License

This project is distributed under the terms specified in the repository. External dependencies retain their respective licenses.
