# Voice Claude - Kids Programming by Voice

让小朋友用中文语音和 Claude Code 对话编程 — 说出想法，AI 帮你写代码。

## Why

5 岁的 Damian 想编程，但还不会打字。Voice Claude 让他按住按钮说中文，语音自动转文字后发送给 [Claude Code](https://docs.anthropic.com/en/docs/claude-code)，由 AI 生成代码、创建游戏、画图……一切只需要一张嘴。

## How It Works

```
🎤 按住说话 → 🟢 Whisper 识别中文 → 🤖 Claude Code 执行 → ✅ 代码/游戏生成
```

1. 按住按钮（GUI）或空格键（CLI）开始录音
2. 松开后 [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 在本地离线识别中文语音
3. 识别结果通过 `claude -p` 发送给 Claude Code
4. Claude Code 理解意图并执行 — 写代码、生成网页、做小游戏等

## Two Interfaces

| | CLI (`voice_claude.py`) | GUI (`voice_claude_gui.py`) |
|---|---|---|
| 交互方式 | 空格键录音，ESC 退出 | 鼠标按住大按钮录音 |
| 适合人群 | 开发者 / 大孩子 | 小朋友（无需记键盘） |
| macOS 权限 | 麦克风 + 辅助功能 | 仅麦克风 |
| 输出位置 | 终端 | 窗口内滚动文本区 |

## Quick Start

```bash
# 前置条件：已安装 Claude Code (npm install -g @anthropic-ai/claude-code)

# 系统依赖
brew install portaudio

# Python 环境
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# GUI 版额外依赖
brew install python-tk@3.12
```

### Run

```bash
# GUI 版 — 推荐给小朋友
python voice_claude_gui.py

# CLI 版
python voice_claude.py

# 测试模式（只转文字，不调用 Claude Code）
python voice_claude_gui.py --test
python voice_claude.py --test

# 使用更高精度的模型（需要 ~3GB 内存）
python voice_claude_gui.py --model large-v3
```

## Tech Stack

- **语音录制** — sounddevice + soundfile, 16kHz 单声道
- **语音识别** — faster-whisper, 本地离线, 完全免费
- **AI 编程** — Claude Code (`claude -p`)
- **GUI** — tkinter, 大红按钮, 深色主题
- **平台** — macOS Apple Silicon (M1/M2/M3/M4)

## macOS Permissions

首次运行需授权：

- **麦克风** — 终端 app (CLI) 或 Python (GUI) 需要录音权限
- **辅助功能**（仅 CLI）— 系统设置 → 隐私与安全 → 辅助功能 → 添加终端 app

GUI 版不需要辅助功能权限。

## Project Structure

```
voice_claude.py      # 核心引擎 (VoiceClaude class) + CLI 入口
voice_claude_gui.py  # GUI 入口 (tkinter)
requirements.txt     # Python 依赖
CLAUDE.md            # Claude Code 项目指引
```
