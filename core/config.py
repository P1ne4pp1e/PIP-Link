class Config:
    """全局配置"""
    # 窗口
    DEFAULT_WIDTH = 1920
    DEFAULT_HEIGHT = 1080
    WINDOW_NAME = 'PIP-Link'

    # 网络端口偏移
    UDP_PORT_OFFSET = 1  # 视频流端口
    PARAMS_PORT_OFFSET = 2  # 参数端口
    CONTROL_PORT_OFFSET = 3  # 控制端口

    # 网络参数
    TCP_TIMEOUT = 3
    HEARTBEAT_INTERVAL = 2
    BUFFER_TIMEOUT = 2.0
    CONTROL_SEND_RATE = 100

    # UI尺寸
    TAB_HEIGHT = 35
    CONTENT_PADDING = 12

    # 分辨率列表 (最低1024x768, 最高2.5K)
    AVAILABLE_RESOLUTIONS = [
        ("2560x1440 (16:9)", (2560, 1440)),  # 2.5K
        ("2560x1600 (16:10)", (2560, 1600)), # 2.5K
        ("1920x1080 (16:9)", (1920, 1080)),  # Full HD
        ("1920x1200 (16:10)", (1920, 1200)),
        ("1680x1050 (16:10)", (1680, 1050)),
        ("1600x900 (16:9)", (1600, 900)),
        ("1440x900 (16:10)", (1440, 900)),
        ("1366x768 (16:9)", (1366, 768)),
        ("1280x800 (16:10)", (1280, 800)),
        ("1280x720 (16:9)", (1280, 720)),   # HD
        ("1024x768 (4:3)", (1024, 768)),    # 最低分辨率
    ]
    DEFAULT_RESOLUTION_INDEX = 3  # 1920x1080