## i-can-not-speak

Windows 本地 SAPI 文本转语音演示，输出到虚拟麦克风（VB-CABLE 等），并提供 Flet 编写的图形界面。

### 主要功能

- 列出系统中的输出设备，优先选择虚拟麦克风（VB-CABLE）。
- 可选本地监听设备，方便同时听到播报。
- 管理语速、音量与发音人。
- 使用 Windows SAPI5 离线合成语音，无需联网。

### 环境准备

项目使用 [uv](https://github.com/astral-sh/uv) 管理依赖：

```powershell
uv sync
```

首次运行会创建虚拟环境并安装依赖（包含 `comtypes`、`sounddevice`、`flet` 等）。

### 运行图形界面

```powershell
uv run i-can-not-speak
# 或者
uv run python -m i_can_not_speak
```

请确保系统已安装 VB-CABLE（或其他虚拟麦克风）以及至少一个 SAPI 语音包。

### 常见问题

- **未检测到语音包**：在 Windows 设置 → 时间和语言 → 语音 中安装中文或英文语音包。
- **未找到输出设备**：确认 VB-CABLE 已安装并启用；必要时点击界面中的刷新按钮重新加载设备列表。
