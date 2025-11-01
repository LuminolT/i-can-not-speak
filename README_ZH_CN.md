# 我不好说（I Can Not Speak）

简体中文 | [English](README.md)

## 项目简介

I Can Not Speak 是一个仅支持 Windows 的文本转语音助手，使用系统内置的 SAPI 5 语音合成，并通过虚拟麦克风输出音频。界面基于 [Flet](https://flet.dev/) 构建，适用于需要在语音聊天或会议软件中播放合成语音的场景。

## 核心特性

- 自动枚举输出设备，可优先选择虚拟麦克风（已用 VB-Audio VB-CABLE 测试）。
- 支持可选的本地监听输出，方便同时监听与推流。
- 可调节语速、音量并实时生效。
- 使用 Windows SAPI 进行异步语音合成，无需联网。

## 环境要求

- **操作系统：** Windows 10 及以上版本（需要 SAPI 5）。本项目不支持 macOS 或 Linux。
- **虚拟麦克风：** 请先安装 [VB-Audio VB-CABLE](https://vb-audio.com/Cable/) 或其它兼容的虚拟音频设备，并确保其处于启用状态。
- **Python：** 3.12 及以上版本（项目通过 [uv](https://github.com/astral-sh/uv) 管理依赖）。

## 安装步骤

首次部署时运行：

```powershell
uv sync
```

该命令会创建虚拟环境并安装所需依赖（如 `comtypes`、`sounddevice`、`flet` 等）。此外，请在 Windows 设置 → 时间和语言 → 语音 中安装至少一种 SAPI 语音。

## 运行应用

```powershell
uv run i-can-not-speak
```

如果在应用运行期间新增了语音或音频设备，可通过界面右上角的刷新按钮重新加载设备列表。

## 打包发布

项目已按照 `flet build` 的目录结构整理。要构建 Windows 安装包，可执行：

```powershell
flet build windows -v
```

请确保已安装 Visual Studio Build Tools 及 Flutter 桌面环境等依赖，详细说明可参考 [Flet 发布文档](https://flet.dev/docs/publish/)。

## 常见问题

- **未检测到语音包：** 请在 Windows 设置中安装额外的 SAPI 语音。
- **虚拟麦克风缺失：** 确认 VB-CABLE 已安装并启用；必要时重启系统。
- **声音失真或爆音：** 在应用内调低音量滑块，或在目标软件中降低增益。

## 许可

本仓库的代码遵循仓库中声明的许可协议，第三方依赖遵循各自的授权条款。
