from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass
class ConnectionState:
    """连接状态"""
    is_connected: bool = False
    server_ip: str = ""
    server_port: str = ""
    connection_duration: int = 0

@dataclass
class UIState:
    """UI状态"""
    debug_panel_visible: bool = True
    window_mode: str = "windowed"  # "windowed" or "fullscreen"
    current_resolution_index: int = 6
    cursor_hidden: bool = False

@dataclass
class ControlState:
    """控制状态"""
    state: int = 0  # 0=Not Ready, 1=Ready
    last_state: int = 0

@dataclass
class VideoState:
    """视频流状态"""
    video_frame: Optional[np.ndarray] = None
    frames_received: int = 0
    latency_ms: float = 0.0

@dataclass
class ServerParams:
    """服务端参数"""
    stream_params: Optional[object] = None
    clients: list = None
    last_update_time: float = 0.0

class AppState:
    """应用总状态"""
    def __init__(self):
        self.connection = ConnectionState()
        self.ui = UIState()
        self.control = ControlState()
        self.video = VideoState()
        self.server_params = ServerParams()