import cv2
import numpy as np
from core.config import Config
from core.state import AppState
from utils.events import EventBus, Events

from ui.components.base_object import Object
from ui.components.tabbed_panel import TabbedPanel
from ui.components.label import Label
from ui.components.state_indicator import StateIndicator

from ui.tabs.connection import ConnectionTab
from ui.tabs.stream import StreamTab
from ui.tabs.clients import ClientsTab
from ui.tabs.statistics import StatisticsTab
from ui.tabs.display import DisplayTab
from ui.tabs.image import ImageTab
from ui.tabs.control import ControlTab


class UIManager:
    """UI管理器"""

    def __init__(self, state: AppState, event_bus: EventBus):
        self.state = state
        self.event_bus = event_bus

        self.width = Config.DEFAULT_WIDTH
        self.height = Config.DEFAULT_HEIGHT

        # 创建根UI对象
        self.root = Object(0, 0, self.width, self.height, "root")
        self.root.background_color = (30, 30, 30)

        # 创建选项卡
        self.connection_tab = ConnectionTab(event_bus)
        self.stream_tab = StreamTab(event_bus)
        self.clients_tab = ClientsTab(event_bus)
        self.statistics_tab = StatisticsTab(event_bus)
        self.display_tab = DisplayTab(event_bus)
        self.image_tab = ImageTab(event_bus)
        self.control_tab = ControlTab(event_bus)  # ===== 新增 =====

        self._build_ui()
        self._setup_event_listeners()

    def _build_ui(self):
        """构建UI"""
        self.debug_panel = TabbedPanel(20, 20, 550, 600, "debug_panel")
        self.debug_panel.add_tab("Connect", self._get_connection_content)
        self.debug_panel.add_tab("Stream", self._get_stream_content)
        self.debug_panel.add_tab("Clients", self._get_clients_content)
        self.debug_panel.add_tab("Statistics", self._get_statistics_content)
        self.debug_panel.add_tab("Display", self._get_display_content)
        self.debug_panel.add_tab("Image", self._get_image_content)
        self.debug_panel.add_tab("Control", self._get_control_content)  # ===== 新增 =====

        self.root.add_child(self.debug_panel)

        # 信息标签
        self.info_label = Label(
            self.width - 320, self.height - 80,
            300, 60, "Press ESC to toggle Debug Panel", "info_display"
        )
        self.info_label.text_color = (200, 200, 200)
        self.info_label.background_color = (50, 50, 55)
        self.info_label.border_color = (100, 100, 110)
        self.info_label.border_width = 1
        self.info_label.alpha = 0.85
        self.info_label.font_scale = 0.45
        self.info_label.align = "center"
        self.info_label.valign = "center"

        self.root.add_child(self.info_label)

        # 状态指示器
        self.state_indicator = StateIndicator(20, self.height - 20)

    def _setup_event_listeners(self):
        """设置事件监听"""
        self.event_bus.subscribe(Events.CONNECTED, self._on_connected)
        self.event_bus.subscribe(Events.DISCONNECTED, self._on_disconnected)
        self.event_bus.subscribe(Events.PARAMS_RECEIVED, self._on_params_received)
        self.event_bus.subscribe(Events.CONTROL_STATE_CHANGED, self._on_control_state_changed)

    def _get_connection_content(self):
        """获取连接选项卡内容"""
        self.connection_tab.update(self.state)
        return self.connection_tab.get_components()

    def _get_stream_content(self):
        """获取流选项卡内容"""
        self.stream_tab.update(self.state.server_params.stream_params)
        return self.stream_tab.get_components()

    def _get_clients_content(self):
        """获取客户端列表选项卡内容"""
        clients = self.state.server_params.clients
        self.clients_tab.update(clients)
        return self.clients_tab.get_components()

    def _get_statistics_content(self):
        """获取统计信息选项卡内容"""
        stats = self.network.get_statistics() if hasattr(self, 'network') else None
        self.statistics_tab.update(
            stats,
            self.state.video.frames_received,
            self.state.video.latency_ms,
            self.state.server_params.last_update_time
        )
        return self.statistics_tab.get_components()

    def _get_display_content(self):
        """获取显示设置选项卡内容"""
        self.display_tab.update(
            self.state.ui.window_mode,
            self.state.ui.current_resolution_index
        )
        return self.display_tab.get_components()

    def _get_image_content(self):
        """获取图像调整选项卡内容"""
        self.image_tab.update(self.state.server_params.stream_params)
        return self.image_tab.get_components()

    def _get_control_content(self):
        """获取控制选项卡内容"""
        self.control_tab.update(self.state.control.mouse_sensitivity)
        return self.control_tab.get_components()

    def _on_connected(self):
        """连接成功"""
        self.info_label.text = f"Connected to {self.state.connection.server_ip}:{self.state.connection.server_port}"
        self.debug_panel._rebuild_content()

    def _on_disconnected(self):
        """连接断开"""
        self.info_label.text = "Connection lost"
        self.debug_panel._rebuild_content()

    def _on_params_received(self, stream_params, clients):
        """参数接收"""
        self.debug_panel._rebuild_content()

    def _on_control_state_changed(self, new_state):
        """控制状态改变"""
        if new_state == 1:
            self.state_indicator.trigger_animation("Ready", (0, 255, 0))
        else:
            self.state_indicator.trigger_animation("Not Ready", (100, 100, 255))

    def toggle_debug_panel(self):
        """切换调试面板"""
        self.state.ui.debug_panel_visible = not self.state.ui.debug_panel_visible
        self.debug_panel.visible = self.state.ui.debug_panel_visible

    def handle_mouse_event(self, event, x, y, flags, param):
        """处理鼠标事件"""
        self.root.handle_mouse_event(event, x, y, flags, param)

    # 设置network引用（在ApplicationController中调用）
    def set_network_manager(self, network):
        """设置网络管理器引用"""
        self.network = network

    def set_config_manager(self, config_manager):
        """设置配置管理器引用"""
        self.config_manager = config_manager
        # 传递给各个选项卡
        self.connection_tab.set_config(config_manager)
        self.stream_tab.set_config(config_manager)
        self.image_tab.set_config(config_manager)
        self.control_tab.set_config(config_manager)

    def update(self, dt: float):
        """更新UI"""
        self.root.update(dt)
        self.state_indicator.update(dt)

    def draw(self, canvas: np.ndarray):
        """绘制UI"""
        self.root.draw(canvas)
        self.state_indicator.draw(canvas)

    def resize(self, width: int, height: int):
        """调整窗口大小"""
        self.width = width
        self.height = height
        self.root.width = width
        self.root.height = height

        # 更新组件位置
        self.info_label.x = width - 320
        self.info_label.y = height - 80
        self.state_indicator.x = 20
        self.state_indicator.y = height - 20