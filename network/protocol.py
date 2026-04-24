"""
协议编解码 - 消息序列化/反序列化和 CRC 校验
"""

import struct
import json
import zlib
from typing import Tuple, Optional
from dataclasses import dataclass


# 协议常量
MAGIC = 0xABCD
VERSION = 0x01

# 消息类型
MSG_TYPE_CONTROL_COMMAND = 0x01
MSG_TYPE_PARAM_UPDATE = 0x02
MSG_TYPE_PARAM_QUERY = 0x03
MSG_TYPE_HEARTBEAT = 0x04
MSG_TYPE_ACK = 0x05
MSG_TYPE_VIDEO_ACK = 0x06
MSG_TYPE_VIDEO_NACK = 0x07


KEYBOARD_STATE_SIZE = 10
MOUSE_DATA_SIZE = 6  # int16 dx + int16 dy + uint8 buttons + int8 scroll


@dataclass
class ControlCommand:
    """控制指令 — 10 字节键盘位图 + 6 字节鼠标数据"""
    seq: int
    t1: float
    keyboard_state: bytes = b'\x00' * KEYBOARD_STATE_SIZE
    mouse_dx: int = 0
    mouse_dy: int = 0
    mouse_buttons: int = 0
    scroll_delta: int = 0

    def to_bytes(self) -> bytes:
        return bytes(self.keyboard_state[:KEYBOARD_STATE_SIZE]).ljust(KEYBOARD_STATE_SIZE, b'\x00')

    @staticmethod
    def from_bytes(data: bytes) -> 'ControlCommand':
        kb = data[:KEYBOARD_STATE_SIZE] if len(data) >= KEYBOARD_STATE_SIZE else data.ljust(KEYBOARD_STATE_SIZE, b'\x00')
        mouse_dx = mouse_dy = mouse_buttons = scroll_delta = 0
        if len(data) >= KEYBOARD_STATE_SIZE + MOUSE_DATA_SIZE:
            mouse_dx, mouse_dy, mouse_buttons, scroll_delta = struct.unpack(
                '=hhBb', data[KEYBOARD_STATE_SIZE:KEYBOARD_STATE_SIZE + MOUSE_DATA_SIZE])
        return ControlCommand(seq=0, t1=0.0, keyboard_state=kb,
                              mouse_dx=mouse_dx, mouse_dy=mouse_dy,
                              mouse_buttons=mouse_buttons, scroll_delta=scroll_delta)


@dataclass
class ACKMessage:
    """ACK 消息"""
    seq: int
    t2: float
    t3: float


class Protocol:
    """协议编解码器

    消息格式（通用）：
    [Magic:2][Version:1][MsgType:1][Reserved:1][Seq:4][...payload...][CRC32:4]
    """

    # -------------------------------------------------------------------------
    # 私有 helper
    # -------------------------------------------------------------------------

    @staticmethod
    def _build_header(msg_type: int, seq: int) -> bytes:
        return struct.pack('=HBBBI', MAGIC, VERSION, msg_type, 0, seq)

    @staticmethod
    def _seal(data: bytes) -> bytes:
        """追加 CRC32 校验尾"""
        return data + struct.pack('=I', zlib.crc32(data) & 0xffffffff)

    @staticmethod
    def _verify_crc(data: bytes) -> None:
        crc_recv = struct.unpack('=I', data[-4:])[0]
        crc_calc = zlib.crc32(data[:-4]) & 0xffffffff
        if crc_recv != crc_calc:
            raise ValueError(f"CRC 校验失败: {hex(crc_recv)} != {hex(crc_calc)}")

    @staticmethod
    def _parse_header(data: bytes, min_len: int, expected_type: int = 0) -> Tuple[int, int]:
        """解析并验证消息头，返回 (msg_type, seq)"""
        if len(data) < min_len:
            raise ValueError(f"消息太短: {len(data)} bytes")
        magic, version, msg_type, _, seq = struct.unpack('=HBBBI', data[:9])
        if magic != MAGIC:
            raise ValueError(f"Magic 错误: {hex(magic)}")
        if version != VERSION:
            raise ValueError(f"Version 错误: {version}")
        if expected_type and msg_type != expected_type:
            raise ValueError(f"消息类型错误: {msg_type}")
        Protocol._verify_crc(data)
        return msg_type, seq

    # -------------------------------------------------------------------------
    # 构建方法
    # -------------------------------------------------------------------------

    @staticmethod
    def build_control_command(
        seq: int,
        t1: float,
        keyboard_state: bytes = b'\x00' * KEYBOARD_STATE_SIZE,
        mouse_dx: int = 0,
        mouse_dy: int = 0,
        mouse_buttons: int = 0,
        scroll_delta: int = 0,
    ) -> bytes:
        """构建控制指令消息（37 字节）
        格式：[Header:9][t1:8][KeyboardState:10][MouseDX:2][MouseDY:2][MouseButtons:1][ScrollDelta:1][CRC32:4]
        """
        kb = bytes(keyboard_state[:KEYBOARD_STATE_SIZE]).ljust(KEYBOARD_STATE_SIZE, b'\x00')
        mouse = struct.pack('=hhBb',
                            max(-32768, min(32767, mouse_dx)),
                            max(-32768, min(32767, mouse_dy)),
                            mouse_buttons & 0xFF,
                            max(-128, min(127, scroll_delta)))
        return Protocol._seal(
            Protocol._build_header(MSG_TYPE_CONTROL_COMMAND, seq) + struct.pack('=d', t1) + kb + mouse
        )

    @staticmethod
    def build_ack(seq: int, t2: float, t3: float) -> bytes:
        """构建 ACK 消息
        格式：[Header:9][t2:8][t3:8][CRC32:4]
        """
        return Protocol._seal(
            Protocol._build_header(MSG_TYPE_ACK, seq) + struct.pack('=dd', t2, t3)
        )

    @staticmethod
    def build_heartbeat(seq: int, t1: float) -> bytes:
        """构建心跳消息
        格式：[Header:9][t1:8][CRC32:4]
        """
        return Protocol._seal(
            Protocol._build_header(MSG_TYPE_HEARTBEAT, seq) + struct.pack('=d', t1)
        )

    @staticmethod
    def build_video_ack(frame_id: int) -> bytes:
        """构建视频帧 ACK
        格式：[Header:9][CRC32:4]
        """
        return Protocol._seal(Protocol._build_header(MSG_TYPE_VIDEO_ACK, frame_id))

    @staticmethod
    def build_video_nack(frame_id: int, missing_chunks: list) -> bytes:
        """构建视频帧 NACK
        格式：[Header:9][NumChunks:2][ChunkIdx:2*N][CRC32:4]
        """
        chunks = struct.pack('=H', len(missing_chunks))
        for idx in missing_chunks:
            chunks += struct.pack('=H', idx)
        return Protocol._seal(Protocol._build_header(MSG_TYPE_VIDEO_NACK, frame_id) + chunks)

    @staticmethod
    def build_param_update(seq: int, t1: float, params: dict) -> bytes:
        """构建参数修改消息（payload 为 JSON）"""
        payload = json.dumps(params).encode('utf-8')
        return Protocol._seal(
            Protocol._build_header(MSG_TYPE_PARAM_UPDATE, seq) + struct.pack('=d', t1) + payload
        )

    @staticmethod
    def build_param_query(seq: int, t1: float) -> bytes:
        """构建参数查询消息"""
        return Protocol._seal(
            Protocol._build_header(MSG_TYPE_PARAM_QUERY, seq) + struct.pack('=d', t1)
        )

    # -------------------------------------------------------------------------
    # 解析方法
    # -------------------------------------------------------------------------

    @staticmethod
    def parse_message(data: bytes) -> Tuple[int, int, float, Optional[bytes]]:
        """解析通用消息，返回 (msg_type, seq, t1, payload)"""
        msg_type, seq = Protocol._parse_header(data, min_len=18)
        t1 = struct.unpack('=d', data[9:17])[0]
        payload = data[17:-4] if len(data) > 21 else None
        return msg_type, seq, t1, payload

    @staticmethod
    def parse_ack(data: bytes) -> Tuple[int, float, float]:
        """解析 ACK 消息，返回 (seq, t2, t3)"""
        _, seq = Protocol._parse_header(data, min_len=25, expected_type=MSG_TYPE_ACK)
        t2, t3 = struct.unpack('=dd', data[9:25])
        return seq, t2, t3

    @staticmethod
    def parse_heartbeat(data: bytes) -> Tuple[int, float]:
        """解析心跳消息，返回 (seq, t1)"""
        _, seq = Protocol._parse_header(data, min_len=21, expected_type=MSG_TYPE_HEARTBEAT)
        t1 = struct.unpack('=d', data[9:17])[0]
        return seq, t1

    @staticmethod
    def parse_video_ack(data: bytes) -> int:
        """解析视频帧 ACK，返回 frame_id"""
        _, frame_id = Protocol._parse_header(data, min_len=13, expected_type=MSG_TYPE_VIDEO_ACK)
        return frame_id

    @staticmethod
    def parse_video_nack(data: bytes) -> tuple:
        """解析视频帧 NACK，返回 (frame_id, [missing_chunk_indices])"""
        _, frame_id = Protocol._parse_header(data, min_len=15, expected_type=MSG_TYPE_VIDEO_NACK)
        num_chunks = struct.unpack('=H', data[9:11])[0]
        missing = [struct.unpack('=H', data[11 + i * 2: 13 + i * 2])[0] for i in range(num_chunks)]
        return frame_id, missing
