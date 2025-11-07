from ui.components.label import Label
from ui.components.textbox import TextBox
from ui.components.button import Button


class ConnectionTab:
    """连接选项卡"""

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.components = []
        self._build_ui()

    def _build_ui(self):
        """构建UI"""
        self.config_manager = None

        # 状态标签
        self.status_label = Label(10, 10, 510, 25, "Status: Disconnected", "conn_status")
        self.status_label.text_color = (255, 100, 100)
        self.status_label.background_color = (45, 45, 52)
        self.status_label.border_width = 0

        self.duration_label = Label(10, 40, 510, 20, "Duration: --:--:--", "conn_duration")
        self.duration_label.text_color = (200, 200, 200)
        self.duration_label.background_color = (45, 45, 52)
        self.duration_label.border_width = 0

        # IP输入
        ip_label = Label(10, 70, 510, 20, "Server IP:", "ip_label")
        ip_label.text_color = (200, 200, 200)
        ip_label.background_color = (45, 45, 52)
        ip_label.border_width = 0
        ip_label.font_scale = 0.45
        ip_label.align = "left"

        self.ip_textbox = TextBox(10, 95, 510, 36, "ip_textbox")
        self.ip_textbox.placeholder = "192.168.1.100"

        # 端口输入
        port_label = Label(10, 140, 510, 20, "Port:", "port_label")
        port_label.text_color = (200, 200, 200)
        port_label.background_color = (45, 45, 52)
        port_label.border_width = 0
        port_label.font_scale = 0.45
        port_label.align = "left"

        self.port_textbox = TextBox(10, 165, 510, 36, "port_textbox")
        self.port_textbox.placeholder = "8888"

        # 连接按钮
        self.connect_button = Button(10, 215, 510, 40, "Connect", "connect_btn")
        self.connect_button.background_color = (70, 130, 180)

        self.components = [
            self.status_label, self.duration_label,
            ip_label, self.ip_textbox,
            port_label, self.port_textbox,
            self.connect_button
        ]

    def update(self, state):
        """更新状态显示"""
        if state.connection.is_connected:
            self.status_label.text = "Status: Connected"
            self.status_label.text_color = (100, 255, 100)

            # 更新时长显示
            duration = state.connection.connection_duration
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
            self.duration_label.text = f"Duration: {hours:02d}:{minutes:02d}:{seconds:02d}"

            self.connect_button.text = "Disconnect"
            self.connect_button.background_color = (180, 70, 70)
        else:
            self.status_label.text = "Status: Disconnected"
            self.status_label.text_color = (255, 100, 100)
            self.duration_label.text = "Duration: --:--:--"
            self.connect_button.text = "Connect"
            self.connect_button.background_color = (70, 130, 180)

    def set_config(self, config_manager):
        """设置配置管理器并加载配置"""
        self.config_manager = config_manager
        # 加载配置到输入框
        self.ip_textbox.text = config_manager.get('connection', 'server_ip', '192.168.1.100')
        self.port_textbox.text = config_manager.get('connection', 'server_port', '8888')

    def get_components(self):
        """返回UI组件列表"""
        return self.components

    def get_input_values(self):
        """获取输入值"""
        return {
            'ip': self.ip_textbox.text,
            'port': self.port_textbox.text
        }