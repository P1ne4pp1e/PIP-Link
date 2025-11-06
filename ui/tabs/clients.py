from ui.components.label import Label


class ClientsTab:
    """客户端列表选项卡"""

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.components = []
        self.client_labels = []  # 动态客户端标签

    def update(self, clients):
        """更新客户端列表"""
        self.components = []

        if not clients:
            no_clients_label = Label(10, 10, 510, 25, "No clients connected", "no_clients")
            no_clients_label.text_color = (150, 150, 150)
            no_clients_label.background_color = (45, 45, 52)
            no_clients_label.font_scale = 0.5
            self.components.append(no_clients_label)
            return

        y_offset = 10
        for idx, client in enumerate(clients, 1):
            # 客户端标题
            title = Label(10, y_offset, 510, 25,
                          f"Client #{idx} (ID {client.client_id})",
                          f"client_{idx}_title")
            title.text_color = (100, 200, 255)
            title.background_color = (45, 45, 52)
            title.font_scale = 0.5
            title.font_thickness = 2
            title.align = "left"
            self.components.append(title)
            y_offset += 30

            # TCP信息
            tcp_info = Label(20, y_offset, 490, 20,
                             f"TCP: {client.ip}:{client.tcp_port}",
                             f"client_{idx}_tcp")
            tcp_info.text_color = (220, 220, 225)
            tcp_info.background_color = (45, 45, 52)
            tcp_info.font_scale = 0.45
            tcp_info.align = "left"
            self.components.append(tcp_info)
            y_offset += 25

            # UDP信息
            udp_info = Label(20, y_offset, 490, 20,
                             f"UDP: :{client.udp_port}",
                             f"client_{idx}_udp")
            udp_info.text_color = (220, 220, 225)
            udp_info.background_color = (45, 45, 52)
            udp_info.font_scale = 0.45
            udp_info.align = "left"
            self.components.append(udp_info)
            y_offset += 25

            # 连接时间
            time_info = Label(20, y_offset, 490, 20,
                              f"Connected: {client.connected_time}",
                              f"client_{idx}_time")
            time_info.text_color = (150, 150, 155)
            time_info.background_color = (45, 45, 52)
            time_info.font_scale = 0.4
            time_info.align = "left"
            self.components.append(time_info)
            y_offset += 35

    def get_components(self):
        """返回UI组件列表"""
        return self.components