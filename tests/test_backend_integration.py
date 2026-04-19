"""集成测试：完整后端系统"""

import sys
import time
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from network.session import SessionManager, SessionState
from logic.status_monitor import StatusMonitor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_backend_integration():
    """测试完整后端系统"""
    print("=" * 60)
    print("集成测试：完整后端系统")
    print("=" * 60)

    # 创建会话管理器
    session = SessionManager()
    status_monitor = StatusMonitor()

    # 设置回调
    def on_state_changed(state):
        logger.info(f"Session state changed: {state.value}")

    def on_error(error):
        logger.error(f"Session error: {error}")

    session.on_state_changed = on_state_changed
    session.on_error = on_error

    # 启动服务发现
    logger.info("Starting service discovery...")
    try:
        session.start_discovery("air_unit")
    except Exception as e:
        logger.error(f"Service discovery failed: {e}")
        return

    # 等待连接
    logger.info("Waiting for connection...")
    for i in range(30):  # 30秒超时
        if session.state == SessionState.CONNECTED:
            logger.info("Connected!")
            break
        time.sleep(1)
        logger.info(f"State: {session.state.value}")
    else:
        logger.warning("Connection timeout")
        session.disconnect()
        return

    # 运行10秒
    logger.info("Running for 10 seconds...")
    for i in range(10):
        # 获取统计
        stats = session.get_statistics()
        status_monitor.update(stats)
        status = status_monitor.get_status()

        logger.info(f"[{i+1}s] FPS: {status['fps']:.1f}, RTT: {status['rtt_ms']:.2f}ms, "
                   f"Frames: {status['frames_received']}, Loss: {status['packet_loss_rate']:.1f}%")

        time.sleep(1)

    # 断开连接
    logger.info("Disconnecting...")
    session.disconnect()

    logger.info("Test completed")


if __name__ == "__main__":
    test_backend_integration()
