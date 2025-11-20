class Config:
    """全局配置"""
    # 窗口
    DEFAULT_WIDTH = 1024
    DEFAULT_HEIGHT = 768
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

    # 鼠标灵敏度范围
    MIN_SENSITIVITY = 0.1
    MAX_SENSITIVITY = 10.0
    DEFAULT_SENSITIVITY = 1.0

    # 鼠标速度缩放因子(固定,用户不可修改)
    MOUSE_SCALE_FACTOR = 0.4

    # 鼠标速度限幅(像素/秒)
    MAX_MOUSE_VELOCITY = 720.0
    MIN_MOUSE_VELOCITY = -720.0

    # 分辨率列表
    AVAILABLE_RESOLUTIONS = [
        ("1920x1080 (16:9)", (1920, 1080)),
        ("1600x900 (16:9)", (1600, 900)),
        ("1280x720 (16:9)", (1280, 720)),
        ("1680x1050 (16:10)", (1680, 1050)),
        ("1440x900 (16:10)", (1440, 900)),
        ("1280x800 (16:10)", (1280, 800)),
        ("1024x768 (4:3)", (1024, 768)),
        ("800x600 (4:3)", (800, 600)),
    ]
    DEFAULT_RESOLUTION_INDEX = 6