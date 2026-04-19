"""控制发送线程"""

import threading
import socket
import time
import logging
from typing import Optional, Callable, Dict
from config import Config
from network.protocol import Protocol
from network.keyboard_encoder import KeyboardEncoder
from logic.latency_calculator import LatencyCalculator


logger = logging.getLogger(__name__)


class ControlSender:
    """控制发送线程 - 发送控制指令并等待ACK"""

    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.remote_addr: Optional[tuple] = None
        self.is_running = False

        # 键盘编码器
        self.keyboard = KeyboardEncoder()

        # 延迟计算
        self.latency_calc = LatencyCalculator()

        # 待确认的消息 {seq: (send_time, retry_count)}
        self._pending_acks: Dict[int, tuple] = {}
        self._pending_lock = threading.Lock()

        # 回调
        self.on_error: Optional[Callable] = None

        # 统计
        self._stats_lock = threading.Lock()
        self.commands_sent = 0
        self.acks_received = 0
        self.retransmits = 0

    def start(self, server_ip: str, server_port: int):
        """启动发送"""
        if self.is_running:
            return

        self.remote_addr = (server_ip, server_port)
        self.is_running = True

        # 启动键盘监听
        self.keyboard.start()

        # 启动发送线程
        tx_thread = threading.Thread(target=self._tx_thread, daemon=True)
        tx_thread.start()

        # 启动接收线程（接收ACK）
        rx_thread = threading.Thread(target=self._rx_thread, daemon=True)
        rx_thread.start()

        logger.info(f"ControlSender started ({server_ip}:{server_port})")

    def stop(self):
        """停止发送"""
        self.is_running = False
        self.keyboard.stop()
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        logger.info("ControlSender stopped")

    def _tx_thread(self):
        """发送线程"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('0.0.0.0', 0))
            self.socket.settimeout(0.1)

            seq = 0
            interval = 1.0 / Config.TX_SEND_RATE
            last_send_time = time.time()

            while self.is_running:
                current_time = time.time()
                elapsed = current_time - last_send_time

                # 定期发送控制指令
                if elapsed >= interval:
                    seq += 1
                    self._send_control_command(seq)
                    last_send_time = current_time

                # 检查超时重传
                self._check_retransmit()

                time.sleep(0.001)

        except Exception as e:
            logger.error(f"TX thread error: {e}")
            if self.on_error:
                self.on_error(str(e))

    def _rx_thread(self):
        """接收线程 - 接收ACK"""
        try:
            while self.is_running:
                if not self.socket:
                    time.sleep(0.01)
                    continue

                try:
                    data, addr = self.socket.recvfrom(4096)
                    if len(data) >= 13:  # ACK最小长度
                        self._process_ack(data)
                except socket.timeout:
                    pass
                except Exception as e:
                    if self.is_running:
                        logger.error(f"RX error: {e}")

        except Exception as e:
            logger.error(f"RX thread error: {e}")

    def _send_control_command(self, seq: int):
        """发送控制指令"""
        try:
            if not self.socket or not self.remote_addr:
                return

            # 获取键盘状态
            keyboard_state = self.keyboard.get_state()

            # 解析键盘状态为控制参数
            forward, turn, action = self._parse_keyboard_state(keyboard_state)

            # 构建消息
            t1 = time.perf_counter()
            message = Protocol.build_control_command(
                seq=seq,
                t1=t1,
                forward=forward,
                turn=turn,
                action=action
            )

            # 发送
            self.socket.sendto(message, self.remote_addr)

            # 记录待确认
            with self._pending_lock:
                self._pending_acks[seq] = (time.time(), 0)
                self.latency_calc.record_send(seq, t1)

            with self._stats_lock:
                self.commands_sent += 1

        except Exception as e:
            if self.is_running:
                logger.error(f"Send error: {e}")
                if self.on_error:
                    self.on_error(str(e))

    def _process_ack(self, data: bytes):
        """处理ACK"""
        try:
            seq, t2, t3 = Protocol.parse_ack(data)

            # 记录ACK时间
            t4 = time.perf_counter()
            self.latency_calc.record_ack(seq, t2, t3, t4)

            # 移除待确认
            with self._pending_lock:
                if seq in self._pending_acks:
                    del self._pending_acks[seq]

            with self._stats_lock:
                self.acks_received += 1

        except Exception as e:
            logger.debug(f"ACK parse error: {e}")

    def _check_retransmit(self):
        """检查超时重传"""
        current_time = time.time()
        to_retransmit = []

        with self._pending_lock:
            for seq, (send_time, retry_count) in list(self._pending_acks.items()):
                elapsed = current_time - send_time

                # 100ms超时，最多重传3次
                if elapsed > 0.1 and retry_count < 3:
                    to_retransmit.append((seq, retry_count))

        for seq, retry_count in to_retransmit:
            self._retransmit_command(seq, retry_count)

    def _retransmit_command(self, seq: int, retry_count: int):
        """重传控制指令"""
        try:
            if not self.socket or not self.remote_addr:
                return

            # 获取键盘状态
            keyboard_state = self.keyboard.get_state()
            forward, turn, action = self._parse_keyboard_state(keyboard_state)

            # 重新构建消息（使用新的t1）
            t1 = time.perf_counter()
            message = Protocol.build_control_command(
                seq=seq,
                t1=t1,
                forward=forward,
                turn=turn,
                action=action
            )

            # 发送
            self.socket.sendto(message, self.remote_addr)

            # 更新待确认
            with self._pending_lock:
                if seq in self._pending_acks:
                    self._pending_acks[seq] = (time.time(), retry_count + 1)

            with self._stats_lock:
                self.retransmits += 1

            logger.debug(f"Retransmit seq={seq}, retry={retry_count + 1}")

        except Exception as e:
            logger.error(f"Retransmit error: {e}")

    def _parse_keyboard_state(self, keyboard_state: bytes) -> tuple:
        """解析键盘状态为控制参数"""
        # 简单映射：W/S -> forward, A/D -> turn
        # keyboard_state 格式由 KeyboardEncoder 定义
        forward = 0.0
        turn = 0.0
        action = 0

        if len(keyboard_state) >= 10:
            # 假设格式: [w, a, s, d, space, ...]
            w, a, s, d = keyboard_state[0], keyboard_state[1], keyboard_state[2], keyboard_state[3]

            if w:
                forward = 1.0
            elif s:
                forward = -1.0

            if a:
                turn = -1.0
            elif d:
                turn = 1.0

            if keyboard_state[4]:  # space
                action = 1

        return forward, turn, action

    def get_statistics(self) -> dict:
        """获取统计"""
        with self._stats_lock:
            return {
                "commands_sent": self.commands_sent,
                "acks_received": self.acks_received,
                "retransmits": self.retransmits,
                "rtt_avg": self.latency_calc.get_average_rtt(),
            }
