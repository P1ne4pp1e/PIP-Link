from typing import Callable, Dict, List


class EventBus:
    """事件总线"""

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event: str, callback: Callable):
        """订阅事件"""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def publish(self, event: str, *args, **kwargs):
        """发布事件"""
        if event in self._listeners:
            for callback in self._listeners[event]:
                callback(*args, **kwargs)

    def unsubscribe(self, event: str, callback: Callable):
        """取消订阅"""
        if event in self._listeners:
            self._listeners[event].remove(callback)


# 全局事件定义
class Events:
    # 连接事件
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTION_ERROR = "connection_error"

    # 数据事件
    FRAME_RECEIVED = "frame_received"
    PARAMS_RECEIVED = "params_received"

    # UI事件
    RESOLUTION_CHANGED = "resolution_changed"
    WINDOW_MODE_CHANGED = "window_mode_changed"

    # 控制事件
    CONTROL_STATE_CHANGED = "control_state_changed"