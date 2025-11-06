"""
键盘编码器 - 使用 pynput 实现多键同时检测
"""

from pynput import keyboard
import threading
from typing import Set, Optional


class KeyboardEncoder:
    """键盘状态编码器 - 支持多键同时按下"""

    # pynput 键码映射到位索引
    KEY_MAP = {
        # Byte 0: 功能键 (0-7)
        keyboard.Key.esc: 0,
        keyboard.Key.f1: 1,
        keyboard.Key.f2: 2,
        keyboard.Key.f3: 3,
        keyboard.Key.f4: 4,
        keyboard.Key.f5: 5,
        keyboard.Key.f6: 6,
        keyboard.Key.f7: 7,

        # Byte 1: 功能键 + 数字 (8-15)
        keyboard.Key.f8: 8,
        keyboard.Key.f9: 9,
        keyboard.Key.f10: 10,
        keyboard.Key.f11: 11,
        keyboard.Key.f12: 12,
        keyboard.KeyCode.from_char('`'): 13,
        keyboard.KeyCode.from_char('1'): 14,
        keyboard.KeyCode.from_char('2'): 15,

        # Byte 2: 数字键 (16-23)
        keyboard.KeyCode.from_char('3'): 16,
        keyboard.KeyCode.from_char('4'): 17,
        keyboard.KeyCode.from_char('5'): 18,
        keyboard.KeyCode.from_char('6'): 19,
        keyboard.KeyCode.from_char('7'): 20,
        keyboard.KeyCode.from_char('8'): 21,
        keyboard.KeyCode.from_char('9'): 22,
        keyboard.KeyCode.from_char('0'): 23,

        # Byte 3: 符号 + 字母 (24-31)
        keyboard.KeyCode.from_char('-'): 24,
        keyboard.KeyCode.from_char('='): 25,
        keyboard.Key.backspace: 26,
        keyboard.Key.tab: 27,
        keyboard.KeyCode.from_char('q'): 28,
        keyboard.KeyCode.from_char('w'): 29,
        keyboard.KeyCode.from_char('e'): 30,
        keyboard.KeyCode.from_char('r'): 31,

        # Byte 4: 字母 (32-39)
        keyboard.KeyCode.from_char('t'): 32,
        keyboard.KeyCode.from_char('y'): 33,
        keyboard.KeyCode.from_char('u'): 34,
        keyboard.KeyCode.from_char('i'): 35,
        keyboard.KeyCode.from_char('o'): 36,
        keyboard.KeyCode.from_char('p'): 37,
        keyboard.KeyCode.from_char('['): 38,
        keyboard.KeyCode.from_char(']'): 39,

        # Byte 5: 符号 + 字母 (40-47)
        keyboard.KeyCode.from_char('\\'): 40,
        keyboard.Key.caps_lock: 41,
        keyboard.KeyCode.from_char('a'): 42,
        keyboard.KeyCode.from_char('s'): 43,
        keyboard.KeyCode.from_char('d'): 44,
        keyboard.KeyCode.from_char('f'): 45,
        keyboard.KeyCode.from_char('g'): 46,
        keyboard.KeyCode.from_char('h'): 47,

        # Byte 6: 字母 (48-55)
        keyboard.KeyCode.from_char('j'): 48,
        keyboard.KeyCode.from_char('k'): 49,
        keyboard.KeyCode.from_char('l'): 50,
        keyboard.KeyCode.from_char(';'): 51,
        keyboard.KeyCode.from_char('\''): 52,
        keyboard.Key.enter: 53,
        keyboard.Key.shift_l: 54,
        keyboard.KeyCode.from_char('z'): 55,

        # Byte 7: 字母 (56-63)
        keyboard.KeyCode.from_char('x'): 56,
        keyboard.KeyCode.from_char('c'): 57,
        keyboard.KeyCode.from_char('v'): 58,
        keyboard.KeyCode.from_char('b'): 59,
        keyboard.KeyCode.from_char('n'): 60,
        keyboard.KeyCode.from_char('m'): 61,
        keyboard.KeyCode.from_char(','): 62,
        keyboard.KeyCode.from_char('.'): 63,

        # Byte 8: 符号 + 修饰键 (64-70)
        keyboard.KeyCode.from_char('/'): 64,
        keyboard.Key.shift_r: 65,
        keyboard.Key.ctrl_l: 66,
        keyboard.Key.alt_l: 67,
        keyboard.Key.space: 68,
        keyboard.Key.alt_r: 69,
        keyboard.Key.ctrl_r: 70,
    }

    def __init__(self):
        """初始化键盘编码器"""
        self.keyboard_state = bytearray(10)  # 10字节
        self.pressed_keys: Set[int] = set()  # 当前按下的键位索引
        self.state_lock = threading.Lock()

        # pynput 监听器
        self.listener: Optional[keyboard.Listener] = None
        self.is_running = False

        # F5 切换回调
        self.on_f5_pressed: Optional[callable] = None

    def start(self):
        """启动键盘监听"""
        if self.is_running:
            return

        self.is_running = True
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()
        print("[KeyboardEncoder] 键盘监听已启动")

    def stop(self):
        """停止键盘监听"""
        self.is_running = False
        if self.listener:
            self.listener.stop()
        print("[KeyboardEncoder] 键盘监听已停止")

    def _on_press(self, key):
        """按键按下事件"""
        # F5 特殊处理
        if key == keyboard.Key.f5:
            if self.on_f5_pressed:
                self.on_f5_pressed()
            return

        bit_index = self._get_bit_index(key)
        if bit_index is not None:
            with self.state_lock:
                self.pressed_keys.add(bit_index)
                self._update_state()

    def _on_release(self, key):
        """按键释放事件"""
        bit_index = self._get_bit_index(key)
        if bit_index is not None:
            with self.state_lock:
                self.pressed_keys.discard(bit_index)
                self._update_state()

    def _get_bit_index(self, key) -> Optional[int]:
        """获取键对应的位索引"""
        return self.KEY_MAP.get(key)

    def _update_state(self):
        """更新编码状态"""
        self.keyboard_state = bytearray(10)  # 清零

        for bit_index in self.pressed_keys:
            byte_index = bit_index // 8
            bit_offset = bit_index % 8
            self.keyboard_state[byte_index] |= (1 << bit_offset)

    def get_state(self) -> bytes:
        """获取当前编码状态"""
        with self.state_lock:
            return bytes(self.keyboard_state)

    def get_pressed_count(self) -> int:
        """获取当前按下的键数量"""
        with self.state_lock:
            return len(self.pressed_keys)