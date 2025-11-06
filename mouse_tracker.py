from typing import Callable, Optional
from pynput import mouse
import pyautogui
import time
import threading

class MouseTracker:
    def __init__(
        self,
        on_move: Optional[Callable[[int, int], None]] = None,
        poll_interval: float = 0.05
    ):
        self.on_move_callback = on_move
        self.poll_interval = poll_interval
        self.last_mouse_update_time = time.time()
        self._stop_flag = False

    def _on_move_internal(self, x, y):
        """内部触发：事件监听器调用"""
        pass

    def _poll_mouse_position(self):
        """定时轮询鼠标位置，即使没有事件也能更新"""
        while not self._stop_flag:
            x, y = pyautogui.position()
            self.on_move_callback(x, y)

            time.sleep(self.poll_interval)

    def start(self):
        # 启动 pynput 的事件监听器
        listener = mouse.Listener(on_move=self._on_move_internal)
        listener.daemon = True
        listener.start()

        # 启动轮询线程
        threading.Thread(target=self._poll_mouse_position, daemon=True).start()

    def stop(self):
        self._stop_flag = True