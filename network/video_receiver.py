"""视频接收线程"""

import threading
import socket
import queue
import logging
from typing import Optional, Callable, Dict
from config import Config
from network.protocol import Protocol


logger = logging.getLogger(__name__)


class VideoReceiver:
    """视频接收线程 - 接收视频分片并重组"""

    def __init__(self, port: int):
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.is_running = False
        self.render_queue = queue.Queue(maxsize=Config.RENDER_QUEUE_MAX_SIZE)

        # 分片缓冲 {frame_id: {seq: data}}
        self._frame_buffer: Dict[int, Dict[int, bytes]] = {}
        self._buffer_lock = threading.Lock()

        # 回调
        self.on_frame_received: Optional[Callable] = None
        self.on_error: Optional[Callable] = None

        # 统计
        self._stats_lock = threading.Lock()
        self.frames_received = 0
        self.packets_received = 0
        self.bytes_received = 0
        self.frames_dropped = 0
        self.packets_lost = 0

    def start(self):
        """启动接收"""
        if self.is_running:
            return

        self.is_running = True
        thread = threading.Thread(target=self._rx_thread, daemon=True)
        thread.start()
        logger.info(f"VideoReceiver started (port: {self.port})")

    def stop(self):
        """停止接收"""
        self.is_running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        logger.info("VideoReceiver stopped")

    def _rx_thread(self):
        """接收线程"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2 * 1024 * 1024)
            self.socket.bind(("0.0.0.0", self.port))
            self.socket.settimeout(1.0)

            logger.info(f"VideoReceiver UDP bind: 0.0.0.0:{self.port}")

            while self.is_running:
                try:
                    data, addr = self.socket.recvfrom(Config.UDP_BUFFER_SIZE)
                    self._process_packet(data, addr)

                except socket.timeout:
                    continue
                except Exception as e:
                    if self.is_running:
                        logger.error(f"Receive error: {e}")
                        if self.on_error:
                            self.on_error(str(e))

        except Exception as e:
            logger.error(f"RX thread error: {e}")
            if self.on_error:
                self.on_error(str(e))

    def _process_packet(self, data: bytes, addr: tuple):
        """处理接收的分片包"""
        try:
            with self._stats_lock:
                self.packets_received += 1
                self.bytes_received += len(data)

            # 解析消息头
            if len(data) < 13:
                return

            seq, t2, t3 = Protocol.parse_ack(data)

            # 这里假设视频数据也使用Protocol格式
            # 实际应用中可能需要自定义视频分片格式
            # 简化处理：直接将数据放入渲染队列

            try:
                self.render_queue.put_nowait(data)
                with self._stats_lock:
                    self.frames_received += 1

                if self.on_frame_received:
                    self.on_frame_received(data, addr)

            except queue.Full:
                with self._stats_lock:
                    self.frames_dropped += 1

        except Exception as e:
            logger.debug(f"Packet parse error: {e}")

    def get_latest_frame(self):
        """获取最新帧"""
        try:
            return self.render_queue.get_nowait()
        except queue.Empty:
            return None

    def get_statistics(self) -> dict:
        """获取统计"""
        with self._stats_lock:
            return {
                "frames_received": self.frames_received,
                "packets_received": self.packets_received,
                "bytes_received": self.bytes_received,
                "frames_dropped": self.frames_dropped,
                "packets_lost": self.packets_lost,
            }
