"""窗口与显示管理"""

import ctypes
import ctypes.wintypes
import pygame
from pygame.locals import NOFRAME
from OpenGL.GL import *
import imgui
from imgui.integrations.pygame import PygameRenderer

from config import Config


class WindowManager:
    """管理窗口模式、分辨率和多显示器配置"""

    def __init__(self, display_flags: int):
        self._display_flags = display_flags
        self._current_window_mode = 0

    @property
    def current_window_mode(self) -> int:
        return self._current_window_mode

    @staticmethod
    def enum_monitors() -> list:
        """通过 Win32 API 枚举物理显示器，按主屏优先排序"""
        MONITORINFOF_PRIMARY = 0x00000001

        class MONITORINFOEX(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.wintypes.DWORD),
                ("rcMonitor", ctypes.wintypes.RECT),
                ("rcWork", ctypes.wintypes.RECT),
                ("dwFlags", ctypes.wintypes.DWORD),
                ("szDevice", ctypes.c_wchar * 32),
            ]

        results = []

        def _cb(hMon, _hdc, _lprc, _data):
            info = MONITORINFOEX()
            info.cbSize = ctypes.sizeof(MONITORINFOEX)
            ctypes.windll.user32.GetMonitorInfoW(hMon, ctypes.byref(info))
            m = info.rcMonitor
            results.append({
                "x": m.left, "y": m.top,
                "w": m.right - m.left, "h": m.bottom - m.top,
                "primary": bool(info.dwFlags & MONITORINFOF_PRIMARY),
            })
            return True

        ENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
            ctypes.POINTER(ctypes.wintypes.RECT), ctypes.c_long,
        )
        ctypes.windll.user32.EnumDisplayMonitors(None, None, ENUMPROC(_cb), 0)
        results.sort(key=lambda m: (not m["primary"], m["x"], m["y"]))
        return results

    def get_current_display(self) -> int:
        """返回当前窗口所在的显示器索引"""
        try:
            monitors = self.enum_monitors()
            if len(monitors) <= 1:
                return 0
            hwnd = pygame.display.get_wm_info()["window"]
            rect = ctypes.wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            cx = (rect.left + rect.right) // 2
            cy = (rect.top + rect.bottom) // 2
            for i, m in enumerate(monitors):
                if m["x"] <= cx < m["x"] + m["w"] and m["y"] <= cy < m["y"] + m["h"]:
                    return i
            return 0
        except Exception:
            return 0

    def get_target_display(self, preferred_idx: int) -> int:
        """解析目标显示器索引（-1 表示当前窗口所在屏幕）"""
        if preferred_idx is None or preferred_idx < 0:
            return self.get_current_display()
        monitors = self.enum_monitors()
        return min(preferred_idx, len(monitors) - 1)

    def apply_window_mode(self, mode: int, preferred_display: int = -1) -> None:
        """切换窗口模式：0=窗口，1=无边框全屏"""
        try:
            display_idx = self.get_target_display(preferred_display)
            monitors = self.enum_monitors()

            if mode == 1:
                mon = monitors[display_idx] if display_idx < len(monitors) else monitors[0]
                dw, dh = mon["w"], mon["h"]
                mx, my = mon["x"], mon["y"]
                pygame.display.set_mode((dw, dh), self._display_flags | NOFRAME)
                pygame.event.pump()
                hwnd = pygame.display.get_wm_info()["window"]
                ctypes.windll.user32.SetWindowPos(
                    hwnd, 0, mx, my, dw, dh, 0x0004 | 0x0020,  # SWP_NOZORDER | SWP_FRAMECHANGED
                )
            else:
                pygame.display.set_mode((Config.RENDER_WIDTH, Config.RENDER_HEIGHT), self._display_flags)
                pygame.event.pump()
                cur = self.get_current_display()
                mon = monitors[cur] if cur < len(monitors) else monitors[0]
                cx = mon["x"] + (mon["w"] - Config.RENDER_WIDTH) // 2
                cy = mon["y"] + (mon["h"] - Config.RENDER_HEIGHT) // 2
                hwnd = pygame.display.get_wm_info()["window"]
                ctypes.windll.user32.SetWindowPos(hwnd, 0, cx, cy, 0, 0, 0x0004 | 0x0001)  # NOZORDER | NOSIZE

            pygame.display.set_caption("PIP-Link Ground Unit")
            pygame.event.pump()
            pygame.event.get()
            self._current_window_mode = mode
            print(f"[WindowManager] Mode: {'Fullscreen' if mode == 1 else 'Windowed'} (display {display_idx})")
        except Exception as e:
            print(f"[WindowManager] Mode switch failed: {e}")

    def apply_resolution(self, res_index: int, resolutions: dict) -> None:
        """切换窗口分辨率（仅窗口模式有效）"""
        res = resolutions.get(res_index)
        if not res or self._current_window_mode == 1:
            return
        w, h = res[0], res[1]
        try:
            pygame.display.set_mode((w, h), self._display_flags)
            pygame.display.set_caption("PIP-Link Ground Unit")
            pygame.event.pump()
            pygame.event.get()
            print(f"[WindowManager] Resolution: {w}x{h}")
        except Exception as e:
            print(f"[WindowManager] Resolution change failed: {e}")

    def reinit_gl(self, video_renderer, imgui_renderer: PygameRenderer) -> PygameRenderer:
        """set_mode 后重建 GL 状态和 ImGui renderer"""
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_TEXTURE_2D)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        video_renderer.init_texture()

        w, h = pygame.display.get_window_size()
        glViewport(0, 0, w, h)
        imgui.get_io().display_size = (w, h)

        try:
            if hasattr(imgui_renderer, 'shutdown'):
                imgui_renderer.shutdown()
        except Exception:
            pass
        return PygameRenderer()
