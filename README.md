# KidsPrograming

Voice Claude - 让小朋友用中文语音和Claude Code对话编程。

## 快速开始

```bash
# 安装系统依赖
brew install portaudio

# 创建虚拟环境并安装
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 运行
python voice_claude.py              # 默认medium模型
python voice_claude.py --test       # 测试模式（只转文字）
python voice_claude.py --model large-v3  # 更高精度
```

## 使用方法

- **按住空格键** 说话
- **松开空格键** 自动识别并发送给Claude Code
- **按ESC** 退出
