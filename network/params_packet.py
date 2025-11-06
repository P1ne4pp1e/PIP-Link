"""
参数传输协议
服务端将流参数和客户端列表通过 UDP 发送给客户端
"""

import json
import struct
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class StreamParams:
    """流参数"""
    jpeg_quality: int
    frame_scale: float
    target_fps: int
    actual_fps: float
    resolution_w: int
    resolution_h: int
    timestamp: float  # 服务端时间戳
    # 新增图像调整参数
    exposure: float = 1.0
    contrast: float = 1.0
    gamma: float = 1.0


@dataclass
class ClientInfoData:
    """客户端信息"""
    client_id: int
    ip: str
    tcp_port: int
    udp_port: int
    connected_time: str


class ParamsPacket:
    """参数包编解码器"""

    # 包头标识
    MAGIC = b'PRM1'
    HEADER_SIZE = 8  # 魔数(4) + 数据长度(4)

    @staticmethod
    def encode(stream_params: StreamParams, clients: List[ClientInfoData]) -> bytes:
        """
        编码参数包

        Args:
            stream_params: 流参数
            clients: 客户端列表

        Returns:
            编码后的字节数据
        """
        # 构建 JSON 数据
        data = {
            'stream': asdict(stream_params),
            'clients': [asdict(client) for client in clients]
        }

        json_data = json.dumps(data).encode('utf-8')
        data_length = len(json_data)

        # 包头: 魔数(4字节) + 数据长度(4字节)
        header = ParamsPacket.MAGIC + struct.pack('!I', data_length)

        return header + json_data

    @staticmethod
    def decode(data: bytes) -> Optional[tuple]:
        """
        解码参数包

        Args:
            data: 原始字节数据

        Returns:
            (stream_params, clients) 元组，解码失败返回 None
        """
        try:
            # 验证包头
            if len(data) < ParamsPacket.HEADER_SIZE:
                return None

            magic = data[0:4]
            if magic != ParamsPacket.MAGIC:
                return None

            # 读取数据长度
            data_length = struct.unpack('!I', data[4:8])[0]

            # 读取 JSON 数据
            json_data = data[8:8 + data_length].decode('utf-8')
            parsed = json.loads(json_data)

            # 解析流参数
            stream_dict = parsed['stream']
            stream_params = StreamParams(**stream_dict)

            # 解析客户端列表
            clients = [ClientInfoData(**client) for client in parsed['clients']]

            return stream_params, clients

        except Exception as e:
            print(f"[ParamsPacket] 解码错误: {e}")
            return None

    @staticmethod
    def create_stream_params(
            jpeg_quality: int,
            frame_scale: float,
            target_fps: int,
            actual_fps: float,
            resolution: tuple,
            exposure: float = 1.0,
            contrast: float = 1.0,
            gamma: float = 1.0
    ) -> StreamParams:
        """创建流参数对象"""
        return StreamParams(
            jpeg_quality=jpeg_quality,
            frame_scale=frame_scale,
            target_fps=target_fps,
            actual_fps=actual_fps,
            resolution_w=resolution[0],
            resolution_h=resolution[1],
            timestamp=time.time(),
            exposure=exposure,
            contrast=contrast,
            gamma=gamma
        )

    @staticmethod
    def create_client_info(
            client_id: int,
            ip: str,
            tcp_port: int,
            udp_port: int,
            connected_time: str
    ) -> ClientInfoData:
        """创建客户端信息对象"""
        return ClientInfoData(
            client_id=client_id,
            ip=ip,
            tcp_port=tcp_port,
            udp_port=udp_port,
            connected_time=connected_time
        )


# ==================== 测试代码 ====================
if __name__ == '__main__':
    # 创建测试数据
    stream_params = ParamsPacket.create_stream_params(
        jpeg_quality=80,
        frame_scale=1.0,
        target_fps=30,
        actual_fps=29.5,
        resolution=(1280, 720)
    )

    clients = [
        ParamsPacket.create_client_info(1, "192.168.1.100", 8888, 9999, "2025-01-10 12:00:00"),
        ParamsPacket.create_client_info(2, "192.168.1.101", 8888, 9999, "2025-01-10 12:05:00"),
    ]

    # 编码
    packet = ParamsPacket.encode(stream_params, clients)
    print(f"编码后大小: {len(packet)} 字节")

    # 解码
    result = ParamsPacket.decode(packet)
    if result:
        decoded_stream, decoded_clients = result
        print(f"\n解码成功:")
        print(f"  JPEG质量: {decoded_stream.jpeg_quality}%")
        print(f"  帧率: {decoded_stream.actual_fps:.1f} FPS")
        print(f"  客户端数量: {len(decoded_clients)}")
        for client in decoded_clients:
            print(f"    - ID {client.client_id}: {client.ip}:{client.udp_port}")
    else:
        print("解码失败")