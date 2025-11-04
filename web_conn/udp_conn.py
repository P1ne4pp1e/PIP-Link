import socket
import threading
import cv2
import numpy as np
from typing import Optional, Callable
from collections import defaultdict


class UDPReceiver:
    """UDP 视频流接收器"""

    def __init__(self, local_port: int = 9999):
        """
        初始化 UDP 接收器

        Args:
            local_port: 本地监听端口
        """
        self.local_port = local_port
        self.is_running = False
        self.socket = None
        self.receive_thread = None

        # 帧重组缓冲
        self.frame_buffer = defaultdict(dict)  # {frame_id: {packet_id: data}}
        self.frame_lock = threading.Lock()

        # 当前完整帧
        self.current_frame = None
        self.on_frame_received: Optional[Callable[[np.ndarray], None]] = None

        # 统计
        self.total_packets_received = 0
        self.total_frames_received = 0

    def start(self):
        """启动 UDP 接收器"""
        if self.is_running:
            return

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('0.0.0.0', self.local_port))

            self.is_running = True
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            print(f"[UDP Receiver] 已启动，监听端口 {self.local_port}")
        except Exception as e:
            print(f"[UDP Receiver] 启动失败: {e}")

    def stop(self):
        """停止 UDP 接收器"""
        self.is_running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        print("[UDP Receiver] 已停止")

    def get_frame(self) -> Optional[np.ndarray]:
        """获取当前接收到的完整帧"""
        with self.frame_lock:
            return self.current_frame.copy() if self.current_frame is not None else None

    def _receive_loop(self):
        """接收循环"""
        while self.is_running:
            try:
                data, addr = self.socket.recvfrom(65507)  # UDP 最大包大小

                # 解析包头
                if len(data) < 8:
                    continue

                frame_id = int.from_bytes(data[0:4], 'big')
                packet_idx = int.from_bytes(data[4:6], 'big')
                total_packets = int.from_bytes(data[6:8], 'big')
                packet_data = data[8:]

                self.total_packets_received += 1

                # 每 100 个包打印一次日志
                if self.total_packets_received % 100 == 0:
                    print(f"[UDP Receiver] 已接收 {self.total_packets_received} 个包")

                # 保存包数据
                with self.frame_lock:
                    self.frame_buffer[frame_id][packet_idx] = packet_data

                    # 检查是否接收完整
                    if len(self.frame_buffer[frame_id]) == total_packets:
                        # 重组帧
                        frame_data = self._reassemble_frame(frame_id, total_packets)

                        if frame_data:
                            # 解码 JPEG
                            frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
                            if frame is not None:
                                self.current_frame = frame
                                self.total_frames_received += 1

                                if self.on_frame_received:
                                    self.on_frame_received(frame)

                        # 清除缓冲
                        del self.frame_buffer[frame_id]

                        print(f"[UDP Receiver] ✓ 接收完整帧 {frame_id} "
                              f"({self.total_frames_received} 总帧数)")

            except Exception as e:
                if self.is_running:
                    print(f"[UDP Receiver] 接收错误: {e}")

    def _reassemble_frame(self, frame_id: int, total_packets: int) -> Optional[bytes]:
        """
        重组帧数据

        Args:
            frame_id: 帧 ID
            total_packets: 总包数

        Returns:
            重组后的帧数据或 None
        """
        try:
            frame_data = b''
            for i in range(total_packets):
                if i not in self.frame_buffer[frame_id]:
                    return None  # 缺少包
                frame_data += self.frame_buffer[frame_id][i]
            return frame_data
        except:
            return None