#!/usr/bin/env python3
"""Voice Claude GUI - Damian的语音编程助手（图形界面版）

大按钮界面，按住说话，松开发送给Claude Code。
专为5岁小朋友设计，无需记忆键盘操作。

依赖：brew install python-tk@3.12
"""

import argparse
import os
import sys
import threading

try:
    import tkinter as tk
except ImportError:
    print("错误：找不到tkinter模块")
    print("请运行: brew install python-tk@3.12")
    print("然后使用brew安装的Python运行此脚本")
    sys.exit(1)

from voice_claude import VoiceClaude

# 颜色主题
BG_COLOR = "#1B1B2F"
BTN_IDLE = "#EF233C"
BTN_RECORDING = "#FF1744"
BTN_DISABLED = "#555555"
BTN_OUTLINE = "#D90429"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#8D99AE"
OUTPUT_BG = "#0F0F23"
OUTPUT_FG = "#E0E0E0"


class VoiceClaudeGUI:
    def __init__(self, model_size: str = "medium", test_mode: bool = False):
        self.engine = VoiceClaude(model_size=model_size, test_mode=test_mode)
        self.root = tk.Tk()
        self._button_enabled = False
        self._setup_window()
        self._setup_widgets()

    def _setup_window(self):
        self.root.title("Voice Claude")
        self.root.geometry("800x600")
        self.root.minsize(600, 500)
        self.root.configure(bg=BG_COLOR)
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

    def _setup_widgets(self):
        # 标题
        tk.Label(
            self.root,
            text="Voice Claude",
            font=("Helvetica", 36, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_COLOR,
        ).pack(pady=(30, 2))

        tk.Label(
            self.root,
            text="Damian的语音编程助手",
            font=("Helvetica", 16),
            fg=TEXT_SECONDARY,
            bg=BG_COLOR,
        ).pack(pady=(0, 20))

        # 大按钮（Canvas绘制圆形）
        self.canvas = tk.Canvas(
            self.root,
            width=200,
            height=200,
            bg=BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack(pady=10)

        self._btn_circle = self.canvas.create_oval(
            10,
            10,
            190,
            190,
            fill=BTN_DISABLED,
            outline="#444444",
            width=4,
        )
        self._btn_icon = self.canvas.create_text(
            100, 80, text="\U0001f3a4", font=("Helvetica", 50)
        )
        self._btn_label = self.canvas.create_text(
            100,
            145,
            text="加载中...",
            font=("Helvetica", 16, "bold"),
            fill=TEXT_PRIMARY,
        )

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        # 状态文字
        self._status_var = tk.StringVar(value="正在加载语音识别模型...")
        tk.Label(
            self.root,
            textvariable=self._status_var,
            font=("Helvetica", 16),
            fg=TEXT_SECONDARY,
            bg=BG_COLOR,
        ).pack(pady=(5, 10))

        # 输出区域
        output_frame = tk.Frame(self.root, bg=BG_COLOR)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 10))

        self._output = tk.Text(
            output_frame,
            wrap=tk.WORD,
            font=("Menlo", 13),
            bg=OUTPUT_BG,
            fg=OUTPUT_FG,
            insertbackground=OUTPUT_FG,
            relief=tk.FLAT,
            padx=15,
            pady=15,
            state=tk.DISABLED,
        )
        scrollbar = tk.Scrollbar(output_frame, command=self._output.yview)
        self._output.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 文字颜色标签
        self._output.tag_configure("user", foreground="#4FC3F7")
        self._output.tag_configure("claude", foreground="#A5D6A7")
        self._output.tag_configure("error", foreground="#EF5350")
        self._output.tag_configure("info", foreground="#FFD54F")

        # 退出按钮
        tk.Button(
            self.root,
            text="退出",
            command=self._quit,
            font=("Helvetica", 13),
            bg="#333333",
            fg=TEXT_SECONDARY,
            activebackground="#555555",
            activeforeground=TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=15,
            pady=4,
        ).pack(pady=(0, 15))

    # ---- 状态更新 ----

    def _set_status(self, text: str):
        self._status_var.set(text)

    def _append_output(self, text: str, tag: str = ""):
        self._output.configure(state=tk.NORMAL)
        if tag:
            self._output.insert(tk.END, text + "\n", tag)
        else:
            self._output.insert(tk.END, text + "\n")
        self._output.see(tk.END)
        self._output.configure(state=tk.DISABLED)

    def _set_button_state(self, state: str):
        """state: 'idle', 'recording', 'disabled'"""
        if state == "idle":
            self.canvas.itemconfig(
                self._btn_circle, fill=BTN_IDLE, outline=BTN_OUTLINE
            )
            self.canvas.itemconfig(self._btn_label, text="按住说话")
            self._button_enabled = True
        elif state == "recording":
            self.canvas.itemconfig(
                self._btn_circle, fill=BTN_RECORDING, outline="#FF0000"
            )
            self.canvas.itemconfig(self._btn_label, text="录音中...")
        elif state == "disabled":
            self.canvas.itemconfig(
                self._btn_circle, fill=BTN_DISABLED, outline="#444444"
            )
            self.canvas.itemconfig(self._btn_label, text="请等待...")
            self._button_enabled = False

    # ---- 事件处理 ----

    def _on_press(self, event):
        if not self._button_enabled or self.engine.processing:
            return
        started = self.engine.start_recording()
        if started:
            self._set_button_state("recording")
            self._set_status("🔴 录音中... 松开按钮结束录音")

    def _on_release(self, event):
        if self.engine.recording:
            self._set_button_state("disabled")
            self._set_status("🟢 识别中...")
            threading.Thread(target=self._process_recording, daemon=True).start()

    def _process_recording(self):
        self.engine.processing = True
        try:
            result = self.engine.stop_recording()
            if result is None:
                self.root.after(0, self._set_status, "录音太短或没有声音，再试一次吧！")
                self.root.after(0, self._set_button_state, "idle")
                return

            wav_path, duration = result
            self.root.after(0, self._set_status, f"🟢 识别中... ({duration:.1f}秒)")

            try:
                text = self.engine.transcribe(wav_path)
            finally:
                os.unlink(wav_path)

            if not text:
                self.root.after(0, self._set_status, "没有听清楚，再说一次吧！")
                self.root.after(0, self._set_button_state, "idle")
                return

            self.root.after(
                0, self._append_output, f"🎤 Damian说: {text}", "user"
            )

            if self.engine.test_mode:
                self.root.after(
                    0, self._append_output, "📋 测试模式，跳过Claude Code调用\n", "info"
                )
                self.root.after(0, self._set_status, "准备好了，按住按钮说话吧！")
            else:
                self.root.after(0, self._set_status, "🤖 Claude正在思考...")
                output, returncode = self.engine.call_claude(text, capture=True)
                if returncode == 0:
                    self.root.after(
                        0, self._append_output, f"🤖 Claude:\n{output}\n", "claude"
                    )
                else:
                    error_msg = output or f"Claude Code返回错误 (code={returncode})"
                    self.root.after(
                        0, self._append_output, f"❌ {error_msg}\n", "error"
                    )
                self.root.after(0, self._set_status, "准备好了，按住按钮说话吧！")

            self.root.after(0, self._set_button_state, "idle")
        except Exception as e:
            self.root.after(0, self._append_output, f"❌ 出错了: {e}", "error")
            self.root.after(0, self._set_status, "出错了，再试一次吧！")
            self.root.after(0, self._set_button_state, "idle")
        finally:
            self.engine.processing = False

    # ---- 生命周期 ----

    def _load_model_async(self):
        def _load():
            try:
                self.engine.load_model()
                self.root.after(0, self._set_status, "准备好了，按住按钮说话吧！")
                self.root.after(0, self._set_button_state, "idle")
            except Exception as e:
                self.root.after(0, self._set_status, f"模型加载失败: {e}")

        threading.Thread(target=_load, daemon=True).start()

    def _quit(self):
        self.engine.cancel_recording()
        self.root.destroy()

    def run(self):
        self._load_model_async()
        self.root.mainloop()


def main():
    parser = argparse.ArgumentParser(
        description="Voice Claude GUI - Damian的语音编程助手"
    )
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

    app = VoiceClaudeGUI(model_size=args.model, test_mode=args.test)
    app.run()


if __name__ == "__main__":
    main()
