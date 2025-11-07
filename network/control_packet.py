"""
控制数据包编解码器
"""

import struct
import time


class ControlPacket:
    """控制数据包编解码器"""

    MAGIC = b'CTRL'
    HEADER_SIZE = 20
    DATA_SIZE = 22  # 鼠标速度(8) + 鼠标按键(2) + 键盘状态(10) + 保留(2)
    TOTAL_SIZE = 42  # 从40改为42

    @staticmethod
    def encode(state: int, mouse_vx: float, mouse_vy: float,
               mouse_buttons: bytes, keyboard_state: bytes, seq: int) -> bytes:
        """
        编码控制包

        Args:
            state: 0=Not Ready, 1=Ready
            mouse_vx: 鼠标X速度 (像素/秒)
            mouse_vy: 鼠标Y速度 (像素/秒)
            keyboard_state: 键盘状态 (10字节)
            seq: 序列号

        Returns:
            编码后的数据包
        """
        timestamp = time.time()

        # 包头 (20字节)
        header = (
                ControlPacket.MAGIC +  # 4字节
                struct.pack('!I', seq) +  # 4字节
                struct.pack('!d', timestamp) +  # 8字节
                struct.pack('B', state) +  # 1字节
                bytes(3)  # 3字节保留
        )

        if state == 1:  # Ready状态
            # 数据部分 (20字节)
            data = (
                    struct.pack('!f', mouse_vx) +  # 4字节
                    struct.pack('!f', mouse_vy) +  # 4字节
                    mouse_buttons +  # 2字节 (新增)
                    keyboard_state +  # 10字节
                    bytes(2)  # 2字节对齐
            )
            return header + data
        else:
            # Not Ready 只发包头
            return header

    @staticmethod
    def decode(packet: bytes) -> dict:
        """
        解码控制包

        Returns:
            {
                'seq': int,
                'timestamp': float,
                'state': int,
                'mouse_vx': float,
                'mouse_vy': float,
                'keyboard_state': bytes
            }
        """
        if len(packet) < ControlPacket.HEADER_SIZE:
            return None

        # 验证魔数
        if packet[0:4] != ControlPacket.MAGIC:
            return None

        # 解析包头
        seq = struct.unpack('!I', packet[4:8])[0]
        timestamp = struct.unpack('!d', packet[8:16])[0]
        state = packet[16]

        result = {
            'seq': seq,
            'timestamp': timestamp,
            'state': state,
            'mouse_vx': 0.0,
            'mouse_vy': 0.0,
            'mouse_buttons': bytes(2),  # 新增
            'keyboard_state': bytes(10)
        }

        if state == 1 and len(packet) >= ControlPacket.TOTAL_SIZE:
            result['mouse_vx'] = struct.unpack('!f', packet[20:24])[0]
            result['mouse_vy'] = struct.unpack('!f', packet[24:28])[0]
            result['mouse_buttons'] = packet[28:30]  # 新增
            result['keyboard_state'] = packet[30:40]  # 从28:38改为30:40

        return result