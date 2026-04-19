"""
ServiceDiscovery 单元测试
"""

import pytest
import time
import logging
from network.service_discovery import ServiceDiscovery, ServiceDiscoveryThread


logging.basicConfig(level=logging.DEBUG)


class TestServiceDiscovery:
    """ServiceDiscovery 基础测试"""

    def test_initialization(self):
        """测试初始化"""
        discovery = ServiceDiscovery()
        assert discovery.service_type == "_pip_vision._udp.local."
        assert len(discovery.discovered_services) == 0

    def test_start_stop(self):
        """测试启动和停止"""
        discovery = ServiceDiscovery()
        discovery.start()
        time.sleep(0.5)
        discovery.stop()

    def test_get_all_services_empty(self):
        """测试获取空服务列表"""
        discovery = ServiceDiscovery()
        services = discovery.get_all_services()
        assert isinstance(services, dict)
        assert len(services) == 0

    def test_get_service_not_found(self):
        """测试获取不存在的服务"""
        discovery = ServiceDiscovery()
        service = discovery.get_service("nonexistent")
        assert service is None


class TestServiceDiscoveryThread:
    """ServiceDiscoveryThread 线程测试"""

    def test_thread_initialization(self):
        """测试线程初始化"""
        thread = ServiceDiscoveryThread()
        assert not thread.is_running

    def test_thread_start_stop(self):
        """测试线程启动和停止"""
        thread = ServiceDiscoveryThread()
        thread.start()
        time.sleep(0.5)
        assert thread.is_running
        thread.stop()
        time.sleep(0.5)
        assert not thread.is_running

    def test_thread_get_services(self):
        """测试线程获取服务"""
        thread = ServiceDiscoveryThread()
        thread.start()
        time.sleep(0.5)

        services = thread.get_all_services()
        assert isinstance(services, dict)

        thread.stop()

    def test_thread_callbacks(self):
        """测试线程回调"""
        found_services = []
        lost_services = []

        def on_found(name, info):
            found_services.append(name)

        def on_lost(name):
            lost_services.append(name)

        thread = ServiceDiscoveryThread(
            on_service_found=on_found,
            on_service_lost=on_lost
        )
        thread.start()
        time.sleep(1.0)
        thread.stop()

        # 注意：这个测试可能不会发现任何服务（取决于网络环境）
        # 但我们可以验证回调函数被正确设置


class TestServiceDiscoveryWaitForService:
    """等待服务测试"""

    def test_wait_for_service_timeout(self):
        """测试等待服务超时"""
        discovery = ServiceDiscovery()
        discovery.start()

        # 等待一个不存在的服务（应该超时）
        service = discovery.wait_for_service("nonexistent", timeout=1.0)
        assert service is None

        discovery.stop()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
