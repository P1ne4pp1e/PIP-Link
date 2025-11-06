import socket
import threading
import cv2
import numpy as np
import time
from typing import Optional, Callable, Dict
from collections import defaultdict, deque


class UDPReceiver:
    """UDP 视频流接收器 - 增强版（支持丢包统计、带宽统计和内存保护）"""

    def __init__(self, local_port: int = 9999, buffer_timeout: float = 2.0):
        """
        初始化 UDP 接收器

        Args:
            local_port: 本地监听端口
            buffer_timeout: 帧缓冲超时时间（秒），超时未完成的帧将被清理
        """
        self.local_port = local_port
        self.buffer_timeout = buffer_timeout
        self.is_running = False
        self.socket = None
        self.receive_thread = None
        self.cleanup_thread = None

        # 帧重组缓冲
        self.frame_buffer: Dict[int, dict] = defaultdict(dict)  # {frame_id: {packet_id: data}}
        self.frame_metadata: Dict[int, dict] = {}  # {frame_id: {total_packets, received_time, expected_packets}}
        self.frame_lock = threading.Lock()

        # 当前完整帧
        self.current_frame = None
        self.on_frame_received: Optional[Callable[[np.ndarray], None]] = None

        # 统计信息
        self.total_packets_received = 0
        self.total_frames_received = 0
        self.total_packets_expected = 0
        self.total_packets_lost = 0
        self.total_frames_dropped = 0  # 超时丢弃的不完整帧

        # 丢包率统计（最近1秒）
        self.recent_packets_received = 0
        self.recent_packets_expected = 0
        self.recent_packet_loss_rate = 0.0
        self.last_stats_time = time.time()

        # ===== 新增：带宽统计 =====
        self.total_bytes_received = 0  # 总接收字节数
        self.recent_bytes_received = 0  # 最近1秒接收字节数
        self.current_bandwidth_mbps = 0.0  # 当前带宽 (Mbps)
        self.average_bandwidth_mbps = 0.0  # 平均带宽 (Mbps)
        self.peak_bandwidth_mbps = 0.0  # 峰值带宽 (Mbps)

        # 带宽历史记录（最近10秒）
        self.bandwidth_history = deque(maxlen=10)  # 存储最近10秒的带宽数据

        # 启动时间（用于计算平均带宽）
        self.start_time = None

    def start(self):
        """启动 UDP 接收器"""
        if self.is_running:
            return

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('0.0.0.0', self.local_port))

            self.is_running = True
            self.start_time = time.time()

            # 启动接收线程
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()

            # 启动清理线程
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()

            print(f"[UDP Receiver] Started on port {self.local_port}")
            print(f"[UDP Receiver] Buffer timeout: {self.buffer_timeout}s")
        except Exception as e:
            print(f"[UDP Receiver] Failed to start: {e}")

    def stop(self):
        """停止 UDP 接收器"""
        self.is_running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        print("[UDP Receiver] Stopped")

    def get_frame(self) -> Optional[np.ndarray]:
        """获取当前接收到的完整帧"""
        with self.frame_lock:
            return self.current_frame.copy() if self.current_frame is not None else None

    def get_packet_loss_rate(self) -> float:
        """
        获取丢包率（最近1秒）

        Returns:
            丢包率 (0.0 - 1.0)
        """
        return self.recent_packet_loss_rate

    def get_overall_packet_loss_rate(self) -> float:
        """
        获取总体丢包率

        Returns:
            总体丢包率 (0.0 - 1.0)
        """
        if self.total_packets_expected == 0:
            return 0.0
        return self.total_packets_lost / self.total_packets_expected

    def get_bandwidth_mbps(self) -> float:
        """
        获取当前带宽 (Mbps)

        Returns:
            当前带宽 (Mbps)
        """
        return self.current_bandwidth_mbps

    def get_average_bandwidth_mbps(self) -> float:
        """
        获取平均带宽 (Mbps)

        Returns:
            平均带宽 (Mbps)
        """
        return self.average_bandwidth_mbps

    def get_peak_bandwidth_mbps(self) -> float:
        """
        获取峰值带宽 (Mbps)

        Returns:
            峰值带宽 (Mbps)
        """
        return self.peak_bandwidth_mbps

    def get_bandwidth_history(self) -> list:
        """
        获取带宽历史记录（最近10秒）

        Returns:
            带宽历史列表
        """
        return list(self.bandwidth_history)

    def get_statistics(self) -> dict:
        """
        获取详细统计信息

        Returns:
            统计字典
        """
        overall_loss_rate = self.get_overall_packet_loss_rate()

        return {
            'total_packets_received': self.total_packets_received,
            'total_packets_expected': self.total_packets_expected,
            'total_packets_lost': self.total_packets_lost,
            'total_frames_received': self.total_frames_received,
            'total_frames_dropped': self.total_frames_dropped,
            'recent_packet_loss_rate': self.recent_packet_loss_rate,
            'overall_packet_loss_rate': overall_loss_rate,
            'buffer_size': len(self.frame_buffer),
            # 新增带宽统计
            'total_bytes_received': self.total_bytes_received,
            'current_bandwidth_mbps': self.current_bandwidth_mbps,
            'average_bandwidth_mbps': self.average_bandwidth_mbps,
            'peak_bandwidth_mbps': self.peak_bandwidth_mbps,
            'bandwidth_history': self.get_bandwidth_history()
        }

    def _receive_loop(self):
        """接收循环"""
        while self.is_running:
            try:
                data, addr = self.socket.recvfrom(65507)  # UDP 最大包大小

                # 统计接收字节数
                bytes_received = len(data)
                self.total_bytes_received += bytes_received
                self.recent_bytes_received += bytes_received

                # 解析包头
                if len(data) < 8:
                    continue

                frame_id = int.from_bytes(data[0:4], 'big')
                packet_idx = int.from_bytes(data[4:6], 'big')
                total_packets = int.from_bytes(data[6:8], 'big')
                packet_data = data[8:]

                self.total_packets_received += 1
                self.recent_packets_received += 1

                # 保存包数据
                with self.frame_lock:
                    # 如果是该帧的第一个包，初始化元数据
                    if frame_id not in self.frame_metadata:
                        self.frame_metadata[frame_id] = {
                            'total_packets': total_packets,
                            'received_time': time.time(),
                            'expected_packets': set(range(total_packets))
                        }
                        self.total_packets_expected += total_packets
                        self.recent_packets_expected += total_packets

                    # 保存包数据
                    if packet_idx not in self.frame_buffer[frame_id]:
                        self.frame_buffer[frame_id][packet_idx] = packet_data

                        # 从期望集合中移除
                        if packet_idx in self.frame_metadata[frame_id]['expected_packets']:
                            self.frame_metadata[frame_id]['expected_packets'].remove(packet_idx)

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
                        del self.frame_metadata[frame_id]

                # 定期更新统计（每秒）
                current_time = time.time()
                if current_time - self.last_stats_time >= 1.0:
                    self._update_statistics()
                    self.last_stats_time = current_time

            except Exception as e:
                if self.is_running:
                    print(f"[UDP Receiver] Receive error: {e}")

    def _cleanup_loop(self):
        """清理循环 - 定期清理超时的不完整帧"""
        while self.is_running:
            try:
                time.sleep(0.5)  # 每0.5秒检查一次

                current_time = time.time()
                frames_to_remove = []

                with self.frame_lock:
                    for frame_id, metadata in self.frame_metadata.items():
                        # 检查是否超时
                        if current_time - metadata['received_time'] > self.buffer_timeout:
                            frames_to_remove.append(frame_id)

                            # 统计丢失的包数
                            lost_packets = len(metadata['expected_packets'])
                            self.total_packets_lost += lost_packets
                            self.total_frames_dropped += 1

                    # 清理超时帧
                    for frame_id in frames_to_remove:
                        if frame_id in self.frame_buffer:
                            del self.frame_buffer[frame_id]
                        if frame_id in self.frame_metadata:
                            del self.frame_metadata[frame_id]

                    if frames_to_remove:
                        print(f"[UDP Receiver] Cleaned {len(frames_to_remove)} timeout frames, "
                              f"buffer size: {len(self.frame_buffer)}")

            except Exception as e:
                if self.is_running:
                    print(f"[UDP Receiver] Cleanup error: {e}")

    def _update_statistics(self):
        """更新统计信息（每秒调用）"""
        # 计算最近1秒的丢包率
        if self.recent_packets_expected > 0:
            packets_lost_recent = self.recent_packets_expected - self.recent_packets_received
            self.recent_packet_loss_rate = packets_lost_recent / self.recent_packets_expected
        else:
            self.recent_packet_loss_rate = 0.0

        # ===== 计算带宽 =====
        # 当前带宽 (Mbps) = (最近1秒接收字节数 * 8) / 1,000,000
        self.current_bandwidth_mbps = (self.recent_bytes_received * 8) / 1_000_000

        # 更新峰值带宽
        if self.current_bandwidth_mbps > self.peak_bandwidth_mbps:
            self.peak_bandwidth_mbps = self.current_bandwidth_mbps

        # 计算平均带宽
        if self.start_time:
            elapsed_time = time.time() - self.start_time
            if elapsed_time > 0:
                self.average_bandwidth_mbps = (self.total_bytes_received * 8) / (elapsed_time * 1_000_000)

        # 添加到历史记录
        self.bandwidth_history.append(self.current_bandwidth_mbps)

        # 重置计数器
        self.recent_packets_received = 0
        self.recent_packets_expected = 0
        self.recent_bytes_received = 0

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


# ==================== 测试代码 ====================
if __name__ == '__main__':
    def on_frame(frame):
        print(f"Received frame: {frame.shape}")
        cv2.imshow('UDP Receiver Test', frame)


    receiver = UDPReceiver(9999)
    receiver.on_frame_received = on_frame
    receiver.start()

    print("UDP Receiver Test - Press 'q' to quit")

    try:
        while True:
            stats = receiver.get_statistics()

            print(f"\r[Stats] Frames: {stats['total_frames_received']} | "
                  f"Packets: {stats['total_packets_received']}/{stats['total_packets_expected']} | "
                  f"Loss Rate: {stats['recent_packet_loss_rate'] * 100:.2f}% (recent) / "
                  f"{stats['overall_packet_loss_rate'] * 100:.2f}% (overall) | "
                  f"Bandwidth: {stats['current_bandwidth_mbps']:.2f} Mbps (current) / "
                  f"{stats['average_bandwidth_mbps']:.2f} Mbps (avg) / "
                  f"{stats['peak_bandwidth_mbps']:.2f} Mbps (peak) | "
                  f"Dropped: {stats['total_frames_dropped']} | "
                  f"Buffer: {stats['buffer_size']}", end='')

            key = cv2.waitKey(100) & 0xFF
            if key == ord('q'):
                break

    except KeyboardInterrupt:
        print("\nStopping receiver...")
    finally:
        receiver.stop()
        cv2.destroyAllWindows()