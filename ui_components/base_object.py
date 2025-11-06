import cv2
import numpy as np
from typing import Tuple, Optional, Callable


class Object:
    """CV2 UI框架基类"""

    # 类变量：全局焦点管理
    _focused_object = None

    def __init__(self, x: int, y: int, width: int, height: int, name: str = ""):
        """
        初始化UI对象

        Args:
            x: 左上角x坐标
            y: 左上角y坐标
            width: 宽度
            height: 高度
            name: 对象名称
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.name = name

        # 可见性和交互性
        self.visible = True
        self.enabled = True

        # 样式属性
        self.background_color = (255, 255, 255)
        self.border_color = (0, 0, 0)
        self.border_width = 1
        self.alpha = 1.0  # 透明度 0-1

        # 鼠标状态
        self.is_hovered = False
        self.is_pressed = False

        # 事件回调
        self.on_click: Optional[Callable] = None
        self.on_hover: Optional[Callable] = None
        self.on_leave: Optional[Callable] = None

        # 子对象
        self.children = []
        self.parent: Optional[Object] = None

    @classmethod
    def set_focus(cls, obj: Optional['Object']):
        """设置全局焦点"""
        if cls._focused_object and cls._focused_object != obj:
            if hasattr(cls._focused_object, 'on_blur'):
                cls._focused_object.on_blur()
        cls._focused_object = obj

    @classmethod
    def get_focused_object(cls) -> Optional['Object']:
        """获取当前焦点对象"""
        return cls._focused_object

    @property
    def rect(self) -> Tuple[int, int, int, int]:
        """返回矩形区域 (x, y, width, height)"""
        return (self.x, self.y, self.width, self.height)

    @property
    def absolute_position(self) -> Tuple[int, int]:
        """返回绝对坐标（考虑父对象）"""
        if self.parent:
            px, py = self.parent.absolute_position
            return (self.x + px, self.y + py)
        return (self.x, self.y)

    def contains_point(self, px: int, py: int) -> bool:
        """检查点是否在对象内"""
        ax, ay = self.absolute_position
        return (ax <= px <= ax + self.width and
                ay <= py <= ay + self.height)

    def add_child(self, child: 'Object'):
        """添加子对象"""
        child.parent = self
        self.children.append(child)

    def remove_child(self, child: 'Object'):
        """移除子对象"""
        if child in self.children:
            child.parent = None
            self.children.remove(child)

    def handle_mouse_event(self, event: int, x: int, y: int, flags: int, param):
        """处理鼠标事件"""
        if not self.visible or not self.enabled:
            return False

        # 先让子对象处理
        for child in reversed(self.children):  # 从上层往下检查
            if child.handle_mouse_event(event, x, y, flags, param):
                return True

        # 检查是否在当前对象内
        is_inside = self.contains_point(x, y)

        # 处理悬停
        if is_inside and not self.is_hovered:
            self.is_hovered = True
            if self.on_hover:
                self.on_hover(self)
        elif not is_inside and self.is_hovered:
            self.is_hovered = False
            self.is_pressed = False
            if self.on_leave:
                self.on_leave(self)

        # 处理点击
        if event == cv2.EVENT_LBUTTONDOWN and is_inside:
            self.is_pressed = True
            return True
        elif event == cv2.EVENT_LBUTTONUP:
            if self.is_pressed and is_inside:
                if self.on_click:
                    self.on_click(self)
            self.is_pressed = False
            return is_inside

        return is_inside

    def draw(self, canvas: np.ndarray):
        """在画布上绘制对象"""
        if not self.visible:
            return

        ax, ay = self.absolute_position

        # 绘制背景
        # if self.alpha < 1.0:
        #     # 支持透明度
        #     overlay = canvas.copy()
        #     cv2.rectangle(overlay, (ax, ay),
        #                   (ax + self.width, ay + self.height),
        #                   self.background_color, -1)
        #     cv2.addWeighted(overlay, self.alpha, canvas, 1 - self.alpha, 0, canvas)
        # else:
        #     cv2.rectangle(canvas, (ax, ay),
        #                   (ax + self.width, ay + self.height),
        #                   self.background_color, -1)

        # 绘制边框
        if self.border_width > 0:
            cv2.rectangle(canvas, (ax, ay),
                          (ax + self.width, ay + self.height),
                          self.border_color, self.border_width)

        # 绘制子对象
        for child in self.children:
            child.draw(canvas)

    def update(self, dt: float = 0):
        """更新对象状态（用于动画等）"""
        for child in self.children:
            child.update(dt)

    def set_position(self, x: int, y: int):
        """设置位置"""
        self.x = x
        self.y = y

    def set_size(self, width: int, height: int):
        """设置大小"""
        self.width = width
        self.height = height

    def show(self):
        """显示对象"""
        self.visible = True

    def hide(self):
        """隐藏对象"""
        self.visible = False

    def enable(self):
        """启用交互"""
        self.enabled = True

    def disable(self):
        """禁用交互"""
        self.enabled = False







# 使用示例
if __name__ == "__main__":
    import time
    from button import Button
    from label import Label
    from textbox import TextBox
    from panel import Panel

    # 创建画布
    canvas_width, canvas_height = 900, 700
    window_name = "CV2 UI Framework - Complete Demo"

    # 创建根对象
    root = Object(0, 0, canvas_width, canvas_height, "root")
    root.background_color = (240, 240, 240)

    # 创建Panel
    panel = Panel(50, 50, 800, 600, "main_panel")
    panel.title = "UI Component Demo"
    root.add_child(panel)

    # 创建Label
    label1 = Label(20, 50, 760, 40, "Welcome to CV2 UI Framework!", "title_label")
    label1.font_scale = 0.8
    label1.font_thickness = 2
    label1.text_color = (50, 50, 50)
    label1.align = "center"
    panel.add_child(label1)

    # 创建多个按钮
    button1 = Button(20, 110, 150, 50, "Button 1", "btn1")
    button2 = Button(190, 110, 150, 50, "Button 2", "btn2")
    button3 = Button(360, 110, 150, 50, "Disabled", "btn3")
    button3.disable()


    def on_btn1_click(obj):
        print("Button 1 clicked")
        count = getattr(on_btn1_click, 'count', 0) + 1
        on_btn1_click.count = count
        label2.text = f"Button 1 clicks: {count}"


    def on_btn2_click(obj):
        print("Button 2 clicked")
        button3.enabled = not button3.enabled
        status = 'Enabled' if button3.enabled else 'Disabled'
        label2.text = f"Button 3 status: {status}"


    button1.on_click = on_btn1_click
    button2.on_click = on_btn2_click

    panel.add_child(button1)
    panel.add_child(button2)
    panel.add_child(button3)

    # 状态标签
    label2 = Label(20, 180, 760, 30, "Click buttons to see effects", "status_label")
    label2.text_color = (70, 130, 180)
    label2.font_scale = 0.6
    panel.add_child(label2)

    # 创建TextBox
    textbox1 = TextBox(20, 230, 300, 40, "textbox1")
    textbox1.placeholder = "Enter your name..."

    textbox2 = TextBox(340, 230, 300, 40, "textbox2")
    textbox2.placeholder = "Enter email address..."


    def on_text_change(obj):
        label3.text = f"Input: {obj.text}"


    textbox1.on_text_change = on_text_change

    panel.add_child(textbox1)
    panel.add_child(textbox2)

    # 输入提示标签
    label3 = Label(20, 290, 760, 30, "Click textbox to start input...", "input_label")
    label3.text_color = (100, 100, 100)
    label3.font_scale = 0.5
    panel.add_child(label3)

    # 创建嵌套Panel
    sub_panel = Panel(20, 340, 760, 220, "sub_panel")
    sub_panel.title = "Nested Panel Example"
    sub_panel.background_color = (255, 255, 255)
    panel.add_child(sub_panel)

    # 子面板中的组件
    label4 = Label(20, 50, 720, 30, "This is a Label nested in Panel", "nested_label")
    label4.align = "center"
    label4.text_color = (80, 80, 80)
    sub_panel.add_child(label4)

    info_label = Label(20, 100, 720, 80,
                       "Features:\n- Mouse hover and click effects\n- Press ESC or Enter to blur textbox\n- All components support parent-child nesting",
                       "info")
    info_label.font_scale = 0.45
    info_label.text_color = (100, 100, 100)
    info_label.valign = "top"
    sub_panel.add_child(info_label)


    # 鼠标回调
    def mouse_callback(event, x, y, flags, param):
        root.handle_mouse_event(event, x, y, flags, param)


    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_callback)

    print("=== CV2 UI Framework Demo ===")
    print("Press ESC to exit")
    print("Click textbox to input text")

    last_time = time.time()

    while True:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time

        # 创建画布
        canvas = np.ones((canvas_height, canvas_width, 3), dtype=np.uint8) * 255

        # 更新UI状态
        root.update(dt)

        # 绘制UI
        root.draw(canvas)

        # 显示
        cv2.imshow(window_name, canvas)

        # if cv2.getWindowProperty('Window', cv2.WND_PROP_VISIBLE) < 1:
        #     break
        # 按键处理
        key = cv2.waitKey(1) & 0xFF

        # 让TextBox处理键盘输入
        if textbox1.handle_key(key) or textbox2.handle_key(key):
            continue


        prop = cv2.getWindowProperty("CV2 UI Framework - Complete Demo", cv2.WND_PROP_VISIBLE)
        if prop == -1 or prop == 0:  # -1是错误,-0是关闭
            break


    cv2.destroyAllWindows()