"""
参数接收器 - 客户端
接收服务端发送的流参数和客户端列表
"""

import socket
import threading
from typing import Optional, Callable
from web_conn.params_packet import ParamsPacket


class ParamsReceiver:
    """参数接收器"""

    def __init__(self, local_port: int = 10000):
        """
        初始化参数接收器

        Args:
            local_port: 本地监听端口
        """
        self.local_port = local_port
        self.is_running = False
        self.socket = None
        self.receive_thread = None

        # 回调函数
        self.on_params_received: Optional[Callable] = None

        # 统计
        self.total_packets_received = 0
        self.decode_errors = 0

    def start(self):
        """启动参数接收器"""
        if self.is_running:
            return

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('0.0.0.0', self.local_port))

            self.is_running = True
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            print(f"[ParamsReceiver] 已启动，监听端口 {self.local_port}")
        except Exception as e:
            print(f"[ParamsReceiver] 启动失败: {e}")

    def stop(self):
        """停止参数接收器"""
        self.is_running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        print("[ParamsReceiver] 已停止")

    def _receive_loop(self):
        """接收循环"""
        while self.is_running:
            try:
                data, addr = self.socket.recvfrom(65507)
                self.total_packets_received += 1

                # 解码参数包
                result = ParamsPacket.decode(data)

                if result:
                    stream_params, clients = result

                    # 触发回调
                    if self.on_params_received:
                        self.on_params_received(stream_params, clients)

                    # 每 10 个包打印一次日志
                    if self.total_packets_received % 10 == 0:
                        print(f"[ParamsReceiver] 已接收 {self.total_packets_received} 个参数包")
                else:
                    self.decode_errors += 1
                    if self.decode_errors % 10 == 0:
                        print(f"[ParamsReceiver] 解码错误累计: {self.decode_errors}")

            except Exception as e:
                if self.is_running:
                    print(f"[ParamsReceiver] 接收错误: {e}")


# ==================== 测试代码 ====================
if __name__ == '__main__':
    def on_params(stream, clients):
        print(f"\n收到参数:")
        print(f"  分辨率: {stream.resolution_w}x{stream.resolution_h}")
        print(f"  JPEG质量: {stream.jpeg_quality}%")
        print(f"  帧率: {stream.actual_fps:.1f} FPS")
        print(f"  客户端数量: {len(clients)}")
        for client in clients:
            print(f"    - ID {client.client_id}: {client.ip}:{client.udp_port}")


    receiver = ParamsReceiver(10000)
    receiver.on_params_received = on_params
    receiver.start()

    print("参数接收器测试 - 按 Ctrl+C 退出")

    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止接收")
        receiver.stop()