# Voice Claude - Damian的语音编程助手

## 项目目标

构建一个Python CLI工具，让5岁的Damian通过中文语音与Claude Code交互，用说话的方式构建小程序。

## 技术方案

- **语音录制**：sounddevice + soundfile，16kHz单声道
- **语音识别**：faster-whisper（本地离线，完全免费），默认medium模型
- **CLI调用**：通过subprocess调用 `claude -p "<识别文字>"` 把语音内容发送给Claude Code
- **键盘监听**：pynput，按住空格录音，松开识别发送，ESC退出

## 运行环境

- macOS Apple Silicon，24GB内存（可用约8GB）
- 默认用medium模型（~1.5GB内存），可选large-v3（~3GB，更精准但内存紧张）
- Python 3.10+

## 依赖

```
brew install portaudio
pip install faster-whisper sounddevice soundfile numpy pynput
```

## 核心文件

- `voice_claude.py` — 主程序，包含录音、识别、调用Claude Code的完整逻辑

## 交互流程

1. 启动程序，加载Whisper模型（首次需下载约1.5GB）
2. 显示欢迎界面，等待用户按空格键
3. 用户按住空格键 → 开始录音（显示🔴）
4. 用户松开空格键 → 停止录音 → Whisper识别中文 → 显示识别结果
5. 将识别文字通过 `claude -p` 发送给Claude Code执行
6. Claude Code输出完毕后，回到步骤2等待下一次输入

## Whisper配置要点

- `language="zh"` 强制指定中文，提高儿童语音识别准确率
- `vad_filter=True` 过滤静音段
- `beam_size=5` 提高准确度
- `device="auto"` 自动选择Apple Silicon最佳后端
- 录音最短0.5秒，低于阈值的静音自动跳过

## macOS权限需求

首次运行需授权：
- 麦克风权限：终端app需要访问麦克风
- 辅助功能权限：系统设置 → 隐私与安全 → 辅助功能 → 添加终端app（用于pynput监听键盘）

## 命令行参数

```
python voice_claude.py                     # 默认medium模型
python voice_claude.py --model large-v3    # 更高精度
python voice_claude.py --test              # 测试模式，只转文字不调用Claude Code
```

## 代码规范

- 终端输出用ANSI颜色，对儿童友好（🔴录音中、🟢识别中、📝结果）
- 错误提示用中文，简洁明了
- 临时wav文件用完即删
- 录音回调线程安全，用frames列表收集音频块

## 后续可扩展方向

- 添加一个简易GUI（大按钮界面），Damian不需要记键盘操作
- 支持语音反馈（TTS），让Claude Code的输出也能读出来
- 添加"连续对话"模式，调用 `claude` 的交互模式而非 `-p` 单次模式
- 支持自动打开Claude Code生成的HTML/游戏文件
