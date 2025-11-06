from core.config import Config
from core.state import AppState
from utils.events import EventBus, Events
from network.tcp_conn import TCPConnection
from network.udp_conn import UDPReceiver
from network.params_receiver import ParamsReceiver
from network.control_sender import ControlSender


class NetworkManager:
    """网络管理器"""

    def __init__(self, state: AppState, event_bus: EventBus):
        self.state = state
        self.event_bus = event_bus

        self.tcp = TCPConnection(Config.TCP_TIMEOUT)
        self.udp = None
        self.params = None
        self.control = None

        self._setup_tcp_callbacks()

    def _setup_tcp_callbacks(self):
        """设置TCP回调"""
        self.tcp.on_connecting = lambda: self.event_bus.publish(Events.CONNECTING)
        self.tcp.on_success = self._on_tcp_success
        self.tcp.on_disconnected = self._on_tcp_disconnected
        self.tcp.on_timeout = lambda: self.event_bus.publish(Events.CONNECTION_ERROR, "timeout")
        self.tcp.on_refused = lambda: self.event_bus.publish(Events.CONNECTION_ERROR, "refused")
        self.tcp.on_error = lambda e: self.event_bus.publish(Events.CONNECTION_ERROR, str(e))

    def connect(self, ip: str, port: int):
        """连接服务器"""
        self.state.connection.server_ip = ip
        self.state.connection.server_port = str(port)
        self.tcp.udp_port = port + Config.UDP_PORT_OFFSET
        self.tcp.handshake(ip, port, async_mode=True)

    def _on_tcp_success(self):
        """TCP连接成功"""
        self.state.connection.is_connected = True

        port = int(self.state.connection.server_port)
        ip = self.state.connection.server_ip

        # 启动UDP视频流接收
        self.udp = UDPReceiver(port + Config.UDP_PORT_OFFSET)
        self.udp.on_frame_received = self._on_frame_received
        self.udp.start()

        # 启动参数接收
        self.params = ParamsReceiver(port + Config.PARAMS_PORT_OFFSET)
        self.params.on_params_received = self._on_params_received
        self.params.start()

        # 启动控制发送
        self.control = ControlSender(Config.CONTROL_SEND_RATE)
        self.control.event_bus = self.event_bus  # 传递event_bus
        self.control.start(ip, port)

        self.event_bus.publish(Events.CONNECTED)

    def _on_tcp_disconnected(self):
        """TCP连接断开"""
        self.state.connection.is_connected = False

        # 强制转为 Not Ready 状态
        self.state.control.state = 0

        self._cleanup_connections()

        # 发布断开事件和状态变化事件
        self.event_bus.publish(Events.DISCONNECTED)
        self.event_bus.publish(Events.CONTROL_STATE_CHANGED, 0)

    def _on_frame_received(self, frame):
        """视频帧接收回调"""
        self.state.video.video_frame = frame.copy()
        self.state.video.frames_received += 1
        self.event_bus.publish(Events.FRAME_RECEIVED, frame)

    def _on_params_received(self, stream_params, clients):
        """参数接收回调"""
        import time
        self.state.server_params.stream_params = stream_params
        self.state.server_params.clients = clients
        self.state.server_params.last_update_time = time.time()

        # 计算延迟
        if stream_params.timestamp > 0:
            latency = time.time() - stream_params.timestamp
            if 0 < latency < 5.0:
                self.state.video.latency_ms = latency * 1000

        self.event_bus.publish(Events.PARAMS_RECEIVED, stream_params, clients)

    def disconnect(self):
        """断开连接"""
        self.state.connection.is_connected = False
        if self.tcp:
            self.tcp.disconnect()
        self._cleanup_connections()

    def _cleanup_connections(self):
        """清理连接"""
        if self.udp:
            self.udp.stop()
            self.udp = None
        if self.params:
            self.params.stop()
            self.params = None
        if self.control:
            self.control.stop()
            self.control = None

    def send_quality_settings(self, jpeg_quality: int, frame_scale: float):
        """发送质量设置"""
        if self.tcp and self.tcp.socket:
            message = f"QUALITY:{jpeg_quality},{frame_scale:.2f}"
            self.tcp.socket.send(message.encode('utf-8'))

    def send_image_adjustment(self, exposure: float, contrast: float, gamma: float):
        """发送图像调整参数"""
        if self.tcp and self.tcp.socket:
            message = f"IMAGE_ADJUST:{exposure:.2f},{contrast:.2f},{gamma:.2f}"
            self.tcp.socket.send(message.encode('utf-8'))

    def get_statistics(self) -> dict:
        """获取网络统计"""
        stats = {
            'frames_received': self.state.video.frames_received,
            'latency_ms': self.state.video.latency_ms,
            # 添加默认值,防止KeyError
            'recent_packet_loss_rate': 0.0,
            'overall_packet_loss_rate': 0.0,
            'total_packets_received': 0,
            'total_packets_expected': 0,
            'total_packets_lost': 0,
            'total_frames_dropped': 0,
            'buffer_size': 0,
            'total_bytes_received': 0,
            'current_bandwidth_mbps': 0.0,
            'average_bandwidth_mbps': 0.0,
            'peak_bandwidth_mbps': 0.0,
            'bandwidth_history': []
        }

        if self.udp:
            udp_stats = self.udp.get_statistics()
            stats.update(udp_stats)

        if self.control:
            control_stats = self.control.get_statistics()
            stats.update(control_stats)

        return stats