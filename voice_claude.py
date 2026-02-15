#!/usr/bin/env python3
"""Voice Claude - Damian的语音编程助手

按住空格键说话，松开后自动识别中文并发送给Claude Code执行。
按ESC退出程序。
"""

import argparse
import os
import subprocess
import sys
import tempfile
import threading
import time

import numpy as np
import sounddevice as sd
import soundfile as sf
from pynput import keyboard

# ANSI颜色
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

# 录音参数
SAMPLE_RATE = 16000
CHANNELS = 1
MIN_DURATION = 0.5  # 最短录音秒数


class VoiceClaude:
    def __init__(self, model_size: str = "medium", test_mode: bool = False):
        self.model_size = model_size
        self.test_mode = test_mode
        self.recording = False
        self.frames: list[np.ndarray] = []
        self.stream = None
        self.record_start_time = 0.0
        self.running = True
        self.processing = False  # 正在处理中，不接受新录音
        self.whisper_model = None

    def load_model(self):
        """加载Whisper模型"""
        print(f"\n{YELLOW}⏳ 正在加载语音识别模型 ({self.model_size})...{RESET}")
        print(f"{DIM}   首次运行需要下载模型文件，请耐心等待{RESET}\n")

        from faster_whisper import WhisperModel

        self.whisper_model = WhisperModel(
            self.model_size,
            device="auto",
            compute_type="auto",
        )
        print(f"{GREEN}✅ 模型加载完成！{RESET}\n")

    def show_welcome(self):
        """显示欢迎界面"""
        print(f"{BOLD}{CYAN}{'=' * 50}{RESET}")
        print(f"{BOLD}{CYAN}  Voice Claude - Damian的语音编程助手{RESET}")
        print(f"{BOLD}{CYAN}{'=' * 50}{RESET}")
        print()
        print(f"  {BOLD}按住空格键{RESET} 🎤 说话")
        print(f"  {BOLD}松开空格键{RESET} 🚀 发送给Claude")
        print(f"  {BOLD}按ESC键{RESET}    👋 退出程序")
        if self.test_mode:
            print(f"\n  {YELLOW}📋 测试模式：只转文字，不调用Claude Code{RESET}")
        print()
        print(f"{DIM}  准备好了，开始说话吧！{RESET}\n")

    def audio_callback(self, indata, frames_count, time_info, status):
        """录音回调（在音频线程中运行）"""
        if self.recording:
            self.frames.append(indata.copy())

    def start_recording(self):
        """开始录音"""
        if self.processing:
            return
        self.frames = []
        self.recording = True
        self.record_start_time = time.time()
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            callback=self.audio_callback,
        )
        self.stream.start()
        print(f"\r  🔴 {RED}录音中...{RESET}  ", end="", flush=True)

    def stop_recording(self) -> str | None:
        """停止录音，返回临时wav文件路径"""
        if not self.recording:
            return None

        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        duration = time.time() - self.record_start_time

        if duration < MIN_DURATION or not self.frames:
            print(f"\r  {DIM}⏭️  录音太短，已跳过{RESET}          ")
            return None

        audio_data = np.concatenate(self.frames, axis=0)

        # 检查是否基本是静音
        if np.abs(audio_data).mean() < 0.005:
            print(f"\r  {DIM}🔇 未检测到声音，已跳过{RESET}          ")
            return None

        # 保存到临时文件
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        sf.write(tmp.name, audio_data, SAMPLE_RATE)
        tmp.close()

        print(f"\r  🟢 {GREEN}识别中... ({duration:.1f}秒录音){RESET}  ", end="", flush=True)
        return tmp.name

    def transcribe(self, wav_path: str) -> str:
        """用Whisper识别音频"""
        segments, info = self.whisper_model.transcribe(
            wav_path,
            language="zh",
            vad_filter=True,
            beam_size=5,
        )
        text = "".join(seg.text for seg in segments).strip()
        return text

    def call_claude(self, text: str):
        """调用Claude Code执行命令"""
        print(f"\n  {BLUE}🤖 发送给Claude Code...{RESET}\n")
        print(f"{DIM}{'─' * 50}{RESET}")

        try:
            result = subprocess.run(
                ["claude", "-p", text],
                capture_output=False,
                text=True,
            )
            if result.returncode != 0:
                print(f"\n  {RED}❌ Claude Code返回错误 (code={result.returncode}){RESET}")
        except FileNotFoundError:
            print(f"\n  {RED}❌ 找不到claude命令，请确认Claude Code已安装{RESET}")
            print(f"  {DIM}安装方法: npm install -g @anthropic-ai/claude-code{RESET}")

        print(f"{DIM}{'─' * 50}{RESET}\n")

    def process_recording(self):
        """处理一次录音：识别 + 调用Claude"""
        self.processing = True
        try:
            wav_path = self.stop_recording()
            if not wav_path:
                return

            try:
                text = self.transcribe(wav_path)
            finally:
                os.unlink(wav_path)

            if not text:
                print(f"\r  {DIM}🔇 未识别到语音内容{RESET}          \n")
                return

            print(f"\r  📝 {BOLD}识别结果：{RESET}{text}          \n")

            if self.test_mode:
                print(f"  {YELLOW}📋 测试模式，跳过Claude Code调用{RESET}\n")
            else:
                self.call_claude(text)

            print(f"  {DIM}准备好了，继续说话吧！{RESET}\n")
        finally:
            self.processing = False

    def on_press(self, key):
        """按键按下事件"""
        if key == keyboard.Key.space and not self.recording and not self.processing:
            self.start_recording()
        elif key == keyboard.Key.esc:
            self.running = False
            if self.recording:
                self.recording = False
                if self.stream:
                    self.stream.stop()
                    self.stream.close()
            return False  # 停止监听

    def on_release(self, key):
        """按键松开事件"""
        if key == keyboard.Key.space and self.recording:
            # 在新线程中处理，避免阻塞键盘监听
            threading.Thread(target=self.process_recording, daemon=True).start()

    def run(self):
        """主循环"""
        self.load_model()
        self.show_welcome()

        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release,
        ) as listener:
            listener.join()

        print(f"\n{CYAN}👋 再见，Damian！下次再来编程吧！{RESET}\n")


def main():
    parser = argparse.ArgumentParser(description="Voice Claude - Damian的语音编程助手")
    parser.add_argument(
        "--model",
        default="medium",
        help="Whisper模型大小 (默认: medium, 可选: large-v3)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="测试模式，只转文字不调用Claude Code",
    )
    args = parser.parse_args()

    app = VoiceClaude(model_size=args.model, test_mode=args.test)

    try:
        app.run()
    except KeyboardInterrupt:
        print(f"\n\n{CYAN}👋 再见！{RESET}\n")


if __name__ == "__main__":
    main()
