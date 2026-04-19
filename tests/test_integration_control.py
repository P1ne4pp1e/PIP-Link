"""集成测试：控制指令发送和ACK接收"""

import sys
import time
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from network.control_sender import ControlSender
from network.protocol import Protocol
from network.udp_socket import UDPReceiver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_control_sender_with_ack():
    """测试控制发送和ACK接收"""
    print("=" * 60)
    print("集成测试：控制指令发送和ACK接收")
    print("=" * 60)

    # 启动模拟ACK服务器
    ack_server = UDPReceiver(
        local_port=6001,
        on_receive=lambda data, addr: _handle_control_command(data, addr),
        timeout=0.1
    )
    ack_server.start()
    time.sleep(0.5)

    # 启动控制发送器
    sender = ControlSender()
    sender.start("127.0.0.1", 6001)

    # 运行10秒
    print("\n发送控制指令中...")
    time.sleep(10)

    # 获取统计
    stats = sender.get_statistics()
    print(f"\n统计信息：")
    print(f"  发送指令数: {stats['commands_sent']}")
    print(f"  接收ACK数: {stats['acks_received']}")
    print(f"  重传次数: {stats['retransmits']}")
    print(f"  平均RTT: {stats['rtt_avg']:.2f}ms")

    # 停止
    sender.stop()
    ack_server.stop()

    print("\n✓ 测试完成")


def _handle_control_command(data: bytes, addr: tuple):
    """处理控制指令并发送ACK"""
    try:
        if len(data) < 13:
            return

        # 解析控制指令
        msg_type, seq, t1, payload = Protocol.parse_message(data)

        # 构建ACK
        t2 = time.perf_counter()
        t3 = time.perf_counter()
        ack_message = Protocol.build_ack(seq=seq, t2=t2, t3=t3)

        # 发送ACK回复
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(ack_message, addr)
        sock.close()

    except Exception as e:
        logger.error(f"Handle control command error: {e}")


if __name__ == "__main__":
    test_control_sender_with_ack()
