import pygame
import cv2
import numpy as np
import time
import threading
from core.config import Config
from core.state import AppState
from utils.events import EventBus, Events
from network.manager import NetworkManager
from pygame._sdl2 import Window
from ui.manager import UIManager
from utils.config_manager import ConfigManager

class ApplicationController:
    """应用主控制器"""

    def __init__(self):
        pygame.init()

        # 配置管理器
        self.config_manager = ConfigManager()

        self.icon_img = pygame.image.load("assets/icon.ico")
        self.icon_img.set_colorkey((255, 255, 255))
        pygame.display.set_icon(self.icon_img)  # 可以填img

        display_info = pygame.display.Info()
        self.screen_width = display_info.current_w
        self.screen_height = display_info.current_h
        print(f"[Display] 检测到屏幕分辨率: {self.screen_width}x{self.screen_height}")


        self.screen = None
        self.window_center = (Config.DEFAULT_WIDTH // 2, Config.DEFAULT_HEIGHT // 2)

        self.window_name = Config.WINDOW_NAME


        # 核心组件
        self.state = AppState()
        self.event_bus = EventBus()
        self.network = NetworkManager(self.state, self.event_bus)
        self.ui = UIManager(self.state, self.event_bus)

        # 鼠标追踪
        self.ignore_next_mouse_event = False  # 添加这行
        self.is_switching_mode = False  # ===== 新增：模式切换标志 =====

        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """设置事件处理"""
        # Connection Tab
        self.ui.connection_tab.connect_button.on_click = self._on_connect_click

        # Stream Tab
        self.ui.stream_tab.apply_button.on_click = self._on_apply_quality_click

        # Display Tab
        self.ui.display_tab.windowed_btn.on_click = lambda obj: self._set_window_mode("windowed")
        self.ui.display_tab.fullscreen_btn.on_click = lambda obj: self._set_window_mode("fullscreen")

        for idx, btn in enumerate(self.ui.display_tab.resolution_buttons):
            btn.on_click = lambda obj, i=idx: self._set_resolution(i)

        # Image Tab
        self.ui.image_tab.apply_button.on_click = self._on_apply_image_click
        self.ui.image_tab.reset_button.on_click = self._on_reset_image_click

        # ===== 新增: Control Tab =====
        self.ui.control_tab.apply_button.on_click = self._on_apply_sensitivity_click

        self.event_bus.subscribe(Events.CONTROL_STATE_CHANGED, self._on_control_state_changed)

        # 让UIManager能访问network
        self.ui.set_network_manager(self.network)
        # 传递配置管理器给UI
        self.ui.set_config_manager(self.config_manager)

    def _on_apply_sensitivity_click(self, obj):
        """应用灵敏度设置"""
        values = self.ui.control_tab.get_input_values()
        if values and self.network.control:
            sensitivity = values['sensitivity']
            self.network.control.set_sensitivity(sensitivity)
            self.state.control.mouse_sensitivity = sensitivity
            # 保存控制配置
            self.config_manager.set('control', 'mouse_sensitivity', sensitivity)
            print(f"[App] 鼠标灵敏度已设置为: {sensitivity:.2f}")

    def _on_connect_click(self, obj):
        """连接按钮点击"""
        if self.state.connection.is_connected:
            self.network.disconnect()
        else:
            values = self.ui.connection_tab.get_input_values()
            if values['ip'] and values['port']:
                try:
                    port = int(values['port'])
                    # 保存连接配置
                    self.config_manager.set('connection', 'server_ip', values['ip'])
                    self.config_manager.set('connection', 'server_port', values['port'])
                    self.network.connect(values['ip'], port)
                except ValueError:
                    print("Invalid port")

    def _on_apply_quality_click(self, obj):
        """应用质量设置"""
        if not self.state.connection.is_connected:
            return

        values = self.ui.stream_tab.get_input_values()
        if values:
            self.network.send_quality_settings(
                values['jpeg_quality'],
                values['frame_scale']
            )
            # 保存流配置
            self.config_manager.set('stream', 'jpeg_quality', values['jpeg_quality'])
            self.config_manager.set('stream', 'frame_scale', values['frame_scale'])

    def _on_apply_image_click(self, obj):
        """应用图像调整"""
        if not self.state.connection.is_connected:
            return

        values = self.ui.image_tab.get_input_values()
        if values:
            self.network.send_image_adjustment(
                values['exposure'],
                values['contrast'],
                values['gamma']
            )
            # 保存图像配置
            self.config_manager.set('image', 'exposure', values['exposure'])
            self.config_manager.set('image', 'contrast', values['contrast'])
            self.config_manager.set('image', 'gamma', values['gamma'])

    def _on_reset_image_click(self, obj):
        """重置图像调整"""
        if not self.state.connection.is_connected:
            return

        self.network.send_image_adjustment(1.0, 1.0, 1.0)

        # 更新UI显示
        self.ui.image_tab.exposure_textbox.text = "1.00"
        self.ui.image_tab.contrast_textbox.text = "1.00"
        self.ui.image_tab.gamma_textbox.text = "1.00"

    def _set_window_mode(self, mode: str):
        """设置窗口模式"""
        print(f"[Display] 准备切换到 {mode} 模式...")

        # ===== 暂时停止渲染 =====
        self.is_switching_mode = True

        self.state.ui.window_mode = mode

        if mode == "fullscreen":
            # 保存当前窗口大小
            self.saved_width = self.ui.width if self.ui.width != self.screen_width else self.saved_width
            self.saved_height = self.ui.height if self.ui.height != self.screen_height else self.saved_height

            # 获取屏幕分辨率
            width = self.screen_width
            height = self.screen_height

            try:
                # 切换到无边框全屏
                self.screen = pygame.display.set_mode((width, height), pygame.NOFRAME)

                # 移动到左上角
                self.window.position = (0, 0)

                # 更新UI尺寸
                self.ui.resize(width, height)
                self.window_center = (width // 2, height // 2)
                print(f"[Display] 切换到全屏模式成功: {width}x{height}")

            except Exception as e:
                print(f"[Display] 切换到全屏失败: {e}")
                self.is_switching_mode = False
                return

        else:  # windowed
            # 恢复窗口模式
            if hasattr(self, 'saved_width'):
                width = self.saved_width
                height = self.saved_height
            else:
                width = Config.DEFAULT_WIDTH
                height = Config.DEFAULT_HEIGHT

            try:
                # 切换回可调整大小窗口
                self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)

                self.window.position = (50, 50)

                # 更新UI尺寸
                self.ui.resize(width, height)
                self.window_center = (width // 2, height // 2)
                print(f"[Display] 切换到窗口模式成功: {width}x{height}")

            except Exception as e:
                print(f"[Display] 切换到窗口模式失败: {e}")
                self.is_switching_mode = False
                return

        # ===== 恢复渲染 =====
        self.is_switching_mode = False
        # 保存显示模式
        self.config_manager.set('display', 'window_mode', mode)

        # 刷新Display选项卡
        self.ui.debug_panel._rebuild_content()

    def _set_resolution(self, index: int):
        """设置分辨率"""
        if self.state.ui.window_mode != "windowed":
            return

        self.state.ui.current_resolution_index = index
        res_name, (new_width, new_height) = Config.AVAILABLE_RESOLUTIONS[index]

        # 调整窗口
        self.screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)
        self.ui.resize(new_width, new_height)
        self.window_center = (new_width // 2, new_height // 2)

        # 保存分辨率索引
        self.config_manager.set('display', 'resolution_index', index)

        print(f"[Display] Resolution changed to {res_name}")
        self.ui.debug_panel._rebuild_content()

    def _handle_key(self, key: int) -> bool:
        """处理按键"""
        if key == 27:  # ESC
            # 先检查是否有TextBox聚焦
            from ui.components.base_object import Object
            focused = Object.get_focused_object()
            if focused and hasattr(focused, 'is_focused') and focused.is_focused:
                focused.is_focused = False
                Object.set_focus(None)
            else:
                self.ui.toggle_debug_panel()
            return True

        # 收集所有TextBox
        textboxes = [
            self.ui.connection_tab.ip_textbox,
            self.ui.connection_tab.port_textbox,
            self.ui.stream_tab.jpeg_quality_textbox,
            self.ui.stream_tab.frame_scale_textbox,
            self.ui.image_tab.exposure_textbox,
            self.ui.image_tab.contrast_textbox,
            self.ui.image_tab.gamma_textbox,
            self.ui.control_tab.sensitivity_textbox,
        ]

        for tb in textboxes:
            if tb.handle_key(key):
                return True

        return True

    def _handle_mouse_button(self, button: int, pressed: bool):
        """处理鼠标按键"""
        # pygame button: 1=左键, 2=中键, 3=右键, 4=Mouse4, 5=Mouse5
        button_map = {
            1: 'left',
            2: 'middle',
            3: 'right',
            4: 'mouse4',
            5: 'mouse5'
        }

        if button in button_map:
            self._update_mouse_state(**{button_map[button]: pressed})

    def _update_mouse_state(self, left=None, right=None, middle=None,
                            mouse4=None, mouse5=None, scroll_up=False, scroll_down=False):
        """更新鼠标状态到控制发送器"""
        if not (self.network.control and self.state.control.state == 1):
            return

        # 获取当前状态
        current = getattr(self, '_mouse_button_state', {
            'left': False, 'right': False, 'middle': False,
            'mouse4': False, 'mouse5': False
        })

        # 更新状态
        if left is not None:
            current['left'] = left
        if right is not None:
            current['right'] = right
        if middle is not None:
            current['middle'] = middle
        if mouse4 is not None:
            current['mouse4'] = mouse4
        if mouse5 is not None:
            current['mouse5'] = mouse5

        self._mouse_button_state = current

        # 发送更新
        self.network.control.update_mouse_buttons(
            current['left'], current['right'], current['middle'],
            current['mouse4'], current['mouse5'],
            scroll_up, scroll_down
        )

    def _on_control_state_changed(self, new_state: int):
        """
        控制状态改变事件处理

        Args:
            new_state: 0=Not Ready, 1=Ready
        """
        if new_state == 1:  # Ready
            self._hide_cursor()
        else:  # Not Ready
            self._show_cursor()

    def _hide_cursor(self):
        """隐藏系统光标并锁定到窗口中心"""
        if self.state.ui.cursor_hidden:
            return

        pygame.mouse.set_visible(False)

        # ===== 新增：锁定鼠标到窗口（防止逃逸）=====
        pygame.event.set_grab(True)

        # 将鼠标移到窗口中心
        pygame.mouse.set_pos(self.window_center)

        self.state.ui.cursor_hidden = True
        print("[Cursor] 光标已隐藏并锁定")

    def _show_cursor(self):
        """恢复系统光标并解除锁定"""
        if not self.state.ui.cursor_hidden:
            return

        # ===== 新增：解除鼠标锁定 =====
        pygame.event.set_grab(False)

        pygame.mouse.set_visible(True)
        self.state.ui.cursor_hidden = False
        print("[Cursor] 光标已恢复并解锁")

    def on_mouse_move(self, x, y):
        """鼠标移动 - 只在 Ready 状态下计算速度"""
        if not (self.network.control and self.state.control.state == 1):
            return

        # 跳过重置产生的事件
        if self.ignore_next_mouse_event:
            self.ignore_next_mouse_event = False
            return

        current_time = time.time()
        dt = current_time - getattr(self, 'last_mouse_time', current_time)
        self.last_mouse_time = current_time

        # 计算相对中心的位移
        dx = x - self.window_center[0]
        dy = y - self.window_center[1]

        if dt > 0:  # 忽略微小抖动
            vx = dx / dt
            vy = dy / dt
            # print(dx)
            self.network.control.update_mouse_position(dx, dy, dt)

        # 重置鼠标到中心并设置忽略标志
        self.ignore_next_mouse_event = True
        pygame.mouse.set_pos(self.window_center)


    def run(self):
        """主循环"""
        # 创建pygame窗口
        self.screen = pygame.display.set_mode((self.ui.width, self.ui.height))
        pygame.display.set_caption(self.window_name)
        self.window = Window.from_display_module()

        self.window_center = (self.ui.width // 2, self.ui.height // 2)

        last_time = time.time()

        # 使用独立的时钟，不限制主循环帧率
        clock = pygame.time.Clock()

        # 渲染缓存
        self.last_canvas = None
        self.canvas_lock = threading.Lock()

        while True:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            if self.network.control:
                self.state.control.state = self.network.control.state

            # 更新连接时长
            if self.state.connection.is_connected and self.network.tcp:
                self.state.connection.connection_duration = self.network.tcp.get_connection_duration()

            # 处理pygame事件（这部分必须快速完成）
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._cleanup()
                    return
                elif event.type == pygame.VIDEORESIZE:
                    self.ui.resize(event.w, event.h)
                    self.window_center = (event.w // 2, event.h // 2)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.ui.handle_mouse_event(cv2.EVENT_LBUTTONDOWN, event.pos[0], event.pos[1], 0, None)
                    if self.state.control.state == 1 and self.network.control:
                        self._handle_mouse_button(event.button, True)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.ui.handle_mouse_event(cv2.EVENT_LBUTTONUP, event.pos[0], event.pos[1], 0, None)
                    if self.state.control.state == 1 and self.network.control:
                        self._handle_mouse_button(event.button, False)
                elif event.type == pygame.MOUSEWHEEL:
                    # ===== 新增: 滚轮事件 =====
                    if self.state.control.state == 1 and self.network.control:
                        self.last_wheel_time = current_time
                        scroll_up = event.y > 0
                        scroll_down = event.y < 0
                        self._update_mouse_state(scroll_up=scroll_up, scroll_down=scroll_down)
                elif event.type == pygame.MOUSEMOTION:
                    # 只在光标隐藏时才处理鼠标移动(Ready状态)
                    if self.state.ui.cursor_hidden:
                        self.on_mouse_move(event.pos[0], event.pos[1])
                elif event.type == pygame.KEYDOWN:
                    # 直接传递 pygame 的 key 值
                    key = event.key

                    # 映射特殊键
                    key_map = {
                        pygame.K_ESCAPE: 27,
                        pygame.K_RETURN: 13,
                        pygame.K_BACKSPACE: 8,
                        pygame.K_DELETE: 127,
                        pygame.K_LEFT: 2,
                        pygame.K_RIGHT: 3,
                        pygame.K_HOME: 1,
                        pygame.K_END: 4,
                    }

                    if key in key_map:
                        key = key_map[key]
                    elif 32 <= key <= 126:
                        pass  # 保持原值
                    else:
                        key = -1

                    if key != -1:
                        # 收集所有TextBox
                        textboxes = [
                            self.ui.connection_tab.ip_textbox,
                            self.ui.connection_tab.port_textbox,
                            self.ui.stream_tab.jpeg_quality_textbox,
                            self.ui.stream_tab.frame_scale_textbox,
                            self.ui.image_tab.exposure_textbox,
                            self.ui.image_tab.contrast_textbox,
                            self.ui.image_tab.gamma_textbox,
                            self.ui.control_tab.sensitivity_textbox,
                        ]

                        # 检查是否有TextBox处理
                        handled = False
                        for tb in textboxes:
                            if tb.handle_key(key, is_press=True):
                                handled = True
                                break

                        # 如果没有TextBox处理，交给_handle_key
                        if not handled:
                            self._handle_key(key)

                elif event.type == pygame.KEYUP:
                    # 处理按键释放
                    key = event.key

                    key_map = {
                        pygame.K_ESCAPE: 27,
                        pygame.K_RETURN: 13,
                        pygame.K_BACKSPACE: 8,
                        pygame.K_DELETE: 127,
                        pygame.K_LEFT: 2,
                        pygame.K_RIGHT: 3,
                        pygame.K_HOME: 1,
                        pygame.K_END: 4,
                    }

                    if key in key_map:
                        key = key_map[key]
                    elif 32 <= key <= 126:
                        pass
                    else:
                        key = -1

                    if key != -1:
                        textboxes = [
                            self.ui.connection_tab.ip_textbox,
                            self.ui.connection_tab.port_textbox,
                            self.ui.stream_tab.jpeg_quality_textbox,
                            self.ui.stream_tab.frame_scale_textbox,
                            self.ui.image_tab.exposure_textbox,
                            self.ui.image_tab.contrast_textbox,
                            self.ui.image_tab.gamma_textbox,
                            self.ui.control_tab.sensitivity_textbox,
                        ]

                        for tb in textboxes:
                            tb.handle_key(key, is_press=False)

            # ===== 鼠标静止时归零速度 =====
            if self.network.control and self.state.control.state == 1:
                current_time = time.time()
                time_since_last_move = current_time - getattr(self, 'last_mouse_time', current_time)
                if time_since_last_move > 0.15:  # 增加到150ms，防止慢速移动时误判
                    self.network.control.update_mouse_position(
                        0,
                        0,
                        0.001
                    )
                    self.last_mouse_time = current_time


                time_since_last_wheel_move = current_time - getattr(self, 'last_wheel_time', current_time)
                if time_since_last_wheel_move > 0.15:  # 滚轮也同步增加到150ms
                    self._update_mouse_state(scroll_up=False, scroll_down=False)
                    self.last_mouse_time = current_time

            # ===== 如果正在切换模式，跳过渲染 =====
            if self.is_switching_mode:
                continue

            # ===== 检查窗口是否有效 =====
            if not self.screen:
                print("[Render] 窗口无效，跳过本帧")
                continue

            try:
                # 创建画布
                canvas = self._create_canvas()

                # 更新和绘制UI
                self.ui.update(dt)
                self.ui.draw(canvas)

                # 转换并显示
                canvas_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
                canvas_surface = pygame.surfarray.make_surface(canvas_rgb.swapaxes(0, 1))

                # 检查尺寸是否匹配
                screen_size = self.screen.get_size()
                canvas_size = (canvas_rgb.shape[1], canvas_rgb.shape[0])

                if screen_size != canvas_size:
                    print(f"[Render] 尺寸不匹配: screen={screen_size}, canvas={canvas_size}")
                    continue

                self.screen.blit(canvas_surface, (0, 0))
                pygame.display.flip()

            except pygame.error as e:
                print(f"[Render] Pygame错误: {e}")
                # 不要退出，继续下一帧
            except Exception as e:
                print(f"[Render] 渲染错误: {e}")
                import traceback
                traceback.print_exc()


        self._cleanup()

    def _create_canvas(self) -> np.ndarray:
        """创建画布"""
        if self.state.video.video_frame is not None:
            frame = self.state.video.video_frame.copy()
            frame_h, frame_w = frame.shape[:2]
            scale = min(self.ui.width / frame_w, self.ui.height / frame_h)
            new_w = int(frame_w * scale)
            new_h = int(frame_h * scale)
            resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

            canvas = np.zeros((self.ui.height, self.ui.width, 3), dtype=np.uint8)
            x_offset = (self.ui.width - new_w) // 2
            y_offset = (self.ui.height - new_h) // 2
            canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
        else:
            canvas = np.zeros((self.ui.height, self.ui.width, 3), dtype=np.uint8)
            canvas[:] = (30, 30, 30)

        return canvas

    def _cleanup(self):
        """清理资源"""
        self.network.disconnect()
        pygame.quit()