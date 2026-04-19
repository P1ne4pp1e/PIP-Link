"""
UDP Socket 单元测试
"""

import pytest
import time
import socket
from network.udp_socket import UDPSocket, UDPReceiver, UDPSender


class TestUDPSocket:
    """UDPSocket 基础测试"""

    def test_bind(self):
        """测试绑定"""
        udp = UDPSocket(local_port=0)
        port = udp.bind()

        assert port > 0
        assert udp.socket is not None

        udp.close()

    def test_send_recv_loopback(self):
        """测试本地回环收发"""
        # 创建发送和接收 Socket
        sender = UDPSocket(timeout=0.1)
        receiver = UDPSocket(timeout=0.1)

        sender_port = sender.bind()
        receiver_port = receiver.bind()

        # 发送数据
        test_data = b"Hello, UDP!"
        sender.send(test_data, ('127.0.0.1', receiver_port))

        # 接收数据
        result = receiver.recv()
        assert result is not None
        data, address = result
        assert data == test_data
        assert address[0] == '127.0.0.1'

        sender.close()
        receiver.close()

    def test_multiple_packets(self):
        """测试多个数据包"""
        sender = UDPSocket(timeout=0.1)
        receiver = UDPSocket(timeout=0.1)

        sender_port = sender.bind()
        receiver_port = receiver.bind()

        # 发送 10 个数据包
        for i in range(10):
            test_data = f"Packet {i}".encode()
            sender.send(test_data, ('127.0.0.1', receiver_port))

        # 接收 10 个数据包
        received_count = 0
        for i in range(10):
            result = receiver.recv()
            if result:
                received_count += 1

        assert received_count == 10

        sender.close()
        receiver.close()

    def test_recv_timeout(self):
        """测试接收超时"""
        receiver = UDPSocket(timeout=0.1)
        receiver.bind()

        # 不发送数据，直接接收（应该超时）
        result = receiver.recv()
        assert result is None

        receiver.close()

    def test_close(self):
        """测试关闭"""
        udp = UDPSocket()
        udp.bind()
        udp.close()

        assert udp.socket is None


class TestUDPReceiver:
    """UDPReceiver 线程测试"""

    def test_receiver_thread(self):
        """测试接收线程"""
        received_data = []

        def on_receive(data, address):
            received_data.append((data, address))

        receiver = UDPReceiver(local_port=0, on_receive=on_receive)
        receiver.start()

        # 等待线程启动
        time.sleep(0.1)

        # 发送数据
        sender = UDPSocket(timeout=0.1)
        sender.bind()
        test_data = b"Test message"
        sender.send(test_data, ('127.0.0.1', receiver.local_port))

        # 等待接收
        time.sleep(0.2)

        # 停止接收线程
        receiver.stop()

        # 验证接收
        assert len(received_data) > 0
        assert received_data[0][0] == test_data

        sender.close()

    def test_receiver_multiple_packets(self):
        """测试接收多个数据包"""
        received_count = [0]

        def on_receive(data, address):
            received_count[0] += 1

        receiver = UDPReceiver(local_port=0, on_receive=on_receive)
        receiver.start()

        time.sleep(0.1)

        # 发送 5 个数据包
        sender = UDPSocket(timeout=0.1)
        sender.bind()
        for i in range(5):
            sender.send(f"Packet {i}".encode(), ('127.0.0.1', receiver.local_port))

        time.sleep(0.2)

        receiver.stop()

        assert received_count[0] == 5

        sender.close()


class TestUDPSender:
    """UDPSender 测试"""

    def test_sender_bind(self):
        """测试发送器绑定"""
        sender = UDPSender()
        port = sender.bind()

        assert port > 0

        sender.close()

    def test_sender_send(self):
        """测试发送器发送"""
        sender = UDPSender()
        sender.bind()

        receiver = UDPSocket(timeout=0.1)
        receiver_port = receiver.bind()

        # 发送数据
        test_data = b"Sender test"
        bytes_sent = sender.send(test_data, ('127.0.0.1', receiver_port))

        assert bytes_sent == len(test_data)

        # 接收数据
        result = receiver.recv()
        assert result is not None
        data, address = result
        assert data == test_data

        sender.close()
        receiver.close()


class TestUDPDataIntegrity:
    """数据完整性测试"""

    def test_large_packet(self):
        """测试大数据包"""
        sender = UDPSocket(timeout=0.1)
        receiver = UDPSocket(timeout=0.1)

        sender_port = sender.bind()
        receiver_port = receiver.bind()

        # 创建 1KB 数据包
        test_data = b"X" * 1024
        sender.send(test_data, ('127.0.0.1', receiver_port))

        result = receiver.recv(buffer_size=2048)
        assert result is not None
        data, address = result
        assert data == test_data

        sender.close()
        receiver.close()

    def test_binary_data(self):
        """测试二进制数据"""
        sender = UDPSocket(timeout=0.1)
        receiver = UDPSocket(timeout=0.1)

        sender_port = sender.bind()
        receiver_port = receiver.bind()

        # 创建二进制数据
        test_data = bytes(range(256))
        sender.send(test_data, ('127.0.0.1', receiver_port))

        result = receiver.recv()
        assert result is not None
        data, address = result
        assert data == test_data

        sender.close()
        receiver.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
