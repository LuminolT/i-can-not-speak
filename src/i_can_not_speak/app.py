from __future__ import annotations

import asyncio
import sys
from datetime import datetime

import flet as ft

from .service import OutputDevice, TalkAsMicService, VoiceInfo


def main(page: ft.Page) -> None:
    page.title = "I Can Not Speak!"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(font_family="Microsoft YaHei")
    page.window.icon = "E:\\GitHub\\i-can-not-speak\\src\\assets\\icon.ico"
    page.update()

    page.window_width = 720
    page.window_height = 640

    if sys.platform != "win32":
        page.add(
            ft.Container(
                content=ft.Text(
                    "此应用需要在 Windows 上运行，因为依赖于系统的 SAPI 语音接口。",
                    selectable=True,
                ),
                padding=24,
            )
        )
        return

    service = TalkAsMicService()
    devices = service.list_output_devices()
    voices = service.list_voices()

    status_text = ft.Text("", size=12, selectable=True)
    log_list = ft.ListView(expand=1, spacing=6, auto_scroll=True)

    def add_log(message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_list.controls.append(ft.Text(f"[{timestamp}] {message}", size=12))
        page.update()

    def show_toast(message: str) -> None:
        page.snack_bar = ft.SnackBar(ft.Text(message))
        page.snack_bar.open = True
        page.update()

    def show_error(message: str) -> None:
        status_text.value = f"⚠️ {message}"
        status_text.color = ft.Colors.RED_400
        page.update()
        show_toast(message)

    def clear_status() -> None:
        status_text.value = ""
        status_text.color = ft.Colors.ON_SURFACE
        page.update()

    def device_option(device: OutputDevice) -> ft.dropdown.Option:
        return ft.dropdown.Option(
            key=str(device.index), text=f"#{device.index} · {device.name}"
        )

    def voice_option(voice: VoiceInfo) -> ft.dropdown.Option:
        lang = voice.language or "默认"
        return ft.dropdown.Option(
            key=voice.token_id, text=f"{voice.description} · {lang}"
        )

    vb_dropdown = ft.Dropdown(
        label="虚拟麦克风输出",
        options=[device_option(d) for d in devices],
        value=str(service.device_vb) if service.device_vb is not None else None,
        dense=False,
        on_change=lambda e: service.set_virtual_mic_device(
            int(e.control.value) if e.control.value not in (None, "") else None
        ),
    )

    monitor_dropdown = ft.Dropdown(
        label="本地监听设备",
        options=[ft.dropdown.Option(key="", text="不开启监听")] + [device_option(d) for d in devices],
        value="",
        on_change=lambda e: service.set_monitor_device(
            int(e.control.value) if e.control.value not in (None, "") else None
        ),
    )

    voice_dropdown = ft.Dropdown(
        label="发音人",
        options=[voice_option(v) for v in voices] or None,
        value=voices[0].token_id if voices else None,
        on_change=lambda e: service.set_voice(e.control.value),
    )
    if voices:
        service.set_voice(voice_dropdown.value)
    else:
        status_text.value = "⚠️ 系统中未找到任何 SAPI 语音，请先安装语音包。"
        status_text.color = ft.Colors.RED_400

    rate_value = ft.Text(str(service.rate))
    volume_value = ft.Text(str(service.volume))

    def on_rate_change(e: ft.ControlEvent) -> None:
        clear_status()
        value = int(float(e.control.value))
        service.set_rate(value)
        rate_value.value = str(service.rate)
        page.update()

    def on_volume_change(e: ft.ControlEvent) -> None:
        clear_status()
        value = int(float(e.control.value))
        service.set_volume(value)
        volume_value.value = str(service.volume)
        page.update()

    rate_slider = ft.Slider(
        min=-10,
        max=10,
        value=service.rate,
        divisions=20,
        label="{value}",
        on_change=on_rate_change,
    )

    volume_slider = ft.Slider(
        min=0,
        max=100,
        value=service.volume,
        divisions=20,
        label="{value}",
        on_change=on_volume_change,
    )

    text_input = ft.TextField(
        label="要朗读的文字",
        multiline=True,
        min_lines=4,
        max_lines=10,
        autofocus=True,
        expand=False,
        height=50,
    )

    busy_ring = ft.ProgressRing(width=20, height=20, visible=False)

    def finish_busy_state() -> None:
        busy_ring.visible = False
        speak_button.disabled = False
        page.update()

    async def speak_task(text: str) -> None:
        try:
            await asyncio.to_thread(service.speak, text)
        except Exception as exc:
            show_error(str(exc))
        finally:
            finish_busy_state()

    def on_speak_click(_: ft.ControlEvent) -> None:
        clear_status()
        text = (text_input.value or "").strip()
        if not text:
            show_error("请输入需要朗读的文字。")
            return
        speak_button.disabled = True
        busy_ring.visible = True
        page.update()
        add_log(f"{text[:40]}{'...' if len(text) > 40 else ''}")
        page.run_task(speak_task, text)

    def on_test_click(_: ft.ControlEvent) -> None:
        text_input.value = "这是一个测试。Hello, this is a test message."
        page.update()
        on_speak_click(_)

    speak_button = ft.ElevatedButton("开始播放", icon=ft.Icons.PLAY_ARROW, on_click=on_speak_click)

    refresh_button = ft.IconButton(
        icon=ft.Icons.REFRESH,
        tooltip="刷新输出设备列表",
        on_click=lambda _: refresh_devices(),
    )

    def refresh_devices() -> None:
        clear_status()
        latest = service.list_output_devices()
        vb_options = [device_option(d) for d in latest]
        monitor_options = [ft.dropdown.Option(key="", text="不开启监听")] + vb_options
        vb_dropdown.options = vb_options
        monitor_dropdown.options = monitor_options
        if service.device_vb is not None:
            vb_dropdown.value = str(service.device_vb)
        monitor_dropdown.value = "" if service.device_monitor is None else str(service.device_monitor)
        page.update()
        add_log("已刷新输出设备列表。")

    controls = [
        ft.Container(height=8),
        ft.Row([ft.Container(vb_dropdown), refresh_button], alignment=ft.MainAxisAlignment.START, spacing=16),
        monitor_dropdown,
        voice_dropdown,
        ft.Row(
            [
                ft.Text("语速 [-10~10]"),
                rate_slider,
                rate_value,
            ],
            alignment=ft.MainAxisAlignment.START,
        ),
        ft.Row(
            [
                ft.Text("音量 [0~100]"),
                volume_slider,
                volume_value,
            ],
            alignment=ft.MainAxisAlignment.START,
        ),
        text_input,
        ft.Row(
            [
                speak_button,
                ft.ElevatedButton("播放测试语音", icon=ft.Icons.RECORD_VOICE_OVER, on_click=on_test_click),
                busy_ring,
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=16,
        ),
        ft.Row(
            [
                ft.Text("播放记录", weight=ft.FontWeight.BOLD),
                status_text,
            ],
            spacing=8,
        ),
        ft.Container(log_list, height=160, border=ft.border.all(1, ft.Colors.GREY_300), padding=8),
    ]

    page.add(
        ft.Container(
            ft.Column(controls, spacing=16, expand=True, scroll=ft.ScrollMode.AUTO),
            padding=24,
            expand=True,
        )
    )


def run() -> None:
    ft.app(target=main, assets_dir="assets")
