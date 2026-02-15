#!/usr/bin/env python3
"""Voice Claude - Damian的语音编程助手

按住空格键说话，松开后自动识别中文并发送给Claude Code执行。
按ESC退出程序。
"""

import argparse
import os
import subprocess
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
    """Core engine for voice recording, Whisper transcription, and Claude Code interaction.

    Used by both CLI (this file's main()) and GUI (voice_claude_gui.py).
    Core methods (load_model, start/stop_recording, transcribe, call_claude) are
    UI-agnostic — they return data without printing. CLI-specific output lives in
    process_recording(), run(), and the keyboard callbacks.
    """

    def __init__(self, model_size: str = "medium", test_mode: bool = False):
        self.model_size = model_size
        self.test_mode = test_mode
        self.recording = False
        self.frames: list[np.ndarray] = []
        self.stream = None
        self.record_start_time = 0.0
        self.processing = False  # 正在处理中，不接受新录音
        self.whisper_model = None

    # ---- Core engine methods (UI-agnostic) ----

    def load_model(self):
        """加载Whisper模型（阻塞直到完成）"""
        from faster_whisper import WhisperModel

        self.whisper_model = WhisperModel(
            self.model_size,
            device="auto",
            compute_type="auto",
        )

    def audio_callback(self, indata, frames_count, time_info, status):
        """录音回调（在音频线程中运行）"""
        if self.recording:
            self.frames.append(indata.copy())

    def start_recording(self) -> bool:
        """开始录音。如果正在处理中返回False。"""
        if self.processing:
            return False
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
        return True

    def stop_recording(self) -> tuple[str, float] | None:
        """停止录音。

        Returns:
            (wav_path, duration) 成功时返回临时文件路径和录音时长
            None 录音太短或静音时返回
        """
        if not self.recording:
            return None

        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        duration = time.time() - self.record_start_time

        if duration < MIN_DURATION or not self.frames:
            return None

        audio_data = np.concatenate(self.frames, axis=0)

        # 检查是否基本是静音
        if np.abs(audio_data).mean() < 0.005:
            return None

        # 保存到临时文件
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        sf.write(tmp.name, audio_data, SAMPLE_RATE)
        tmp.close()

        return (tmp.name, duration)

    def transcribe(self, wav_path: str) -> str:
        """用Whisper识别音频，返回识别文字"""
        segments, info = self.whisper_model.transcribe(
            wav_path,
            language="zh",
            vad_filter=True,
            beam_size=5,
        )
        text = "".join(seg.text for seg in segments).strip()
        return text

    def call_claude(self, text: str, capture: bool = False) -> tuple[str, int]:
        """调用Claude Code执行命令。

        Args:
            text: 要发送给Claude Code的文字
            capture: True时捕获输出并返回，False时直接输出到终端

        Returns:
            (output, returncode) output在capture=False时为空字符串
        """
        try:
            result = subprocess.run(
                ["claude", "-p", text],
                capture_output=capture,
                text=True,
            )
            if capture:
                return (result.stdout or "", result.returncode)
            return ("", result.returncode)
        except FileNotFoundError:
            return ("找不到claude命令，请确认Claude Code已安装", -1)

    def cancel_recording(self):
        """取消当前录音"""
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    # ---- CLI-specific methods ----

    def show_welcome(self):
        """显示CLI欢迎界面"""
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

    def process_recording(self):
        """CLI: 处理一次录音（带终端输出）"""
        self.processing = True
        try:
            result = self.stop_recording()
            if result is None:
                print(f"\r  {DIM}⏭️  录音太短或无声音，已跳过{RESET}          ")
                return

            wav_path, duration = result
            print(
                f"\r  🟢 {GREEN}识别中... ({duration:.1f}秒录音){RESET}  ",
                end="",
                flush=True,
            )

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
                print(f"\n  {BLUE}🤖 发送给Claude Code...{RESET}\n")
                print(f"{DIM}{'─' * 50}{RESET}")
                _, returncode = self.call_claude(text, capture=False)
                if returncode != 0:
                    print(
                        f"\n  {RED}❌ Claude Code返回错误 (code={returncode}){RESET}"
                    )
                print(f"{DIM}{'─' * 50}{RESET}\n")

            print(f"  {DIM}准备好了，继续说话吧！{RESET}\n")
        finally:
            self.processing = False

    def on_press(self, key):
        """按键按下事件"""
        if key == keyboard.Key.space and not self.recording and not self.processing:
            self.start_recording()
            print(f"\r  🔴 {RED}录音中...{RESET}  ", end="", flush=True)
        elif key == keyboard.Key.esc:
            self.cancel_recording()
            return False  # 停止监听

    def on_release(self, key):
        """按键松开事件"""
        if key == keyboard.Key.space and self.recording:
            # 在新线程中处理，避免阻塞键盘监听
            threading.Thread(target=self.process_recording, daemon=True).start()

    def run(self):
        """CLI主循环"""
        print(f"\n{YELLOW}⏳ 正在加载语音识别模型 ({self.model_size})...{RESET}")
        print(f"{DIM}   首次运行需要下载模型文件，请耐心等待{RESET}\n")
        self.load_model()
        print(f"{GREEN}✅ 模型加载完成！{RESET}\n")

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
