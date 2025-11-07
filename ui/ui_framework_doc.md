# CV2 UI Framework

<div align="center">

**基于OpenCV的轻量级GUI框架**

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-green.svg)](https://opencv.org/)[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*纯Python实现，无需Qt/Tkinter等重型GUI库*

---

## 📖 简介

CV2 UI Framework 是一个基于OpenCV (`cv2`) 实现的轻量级GUI框架，专为需要在视频流上叠加交互式UI的应用场景设计。框架提供了完整的组件体系、事件系统和焦点管理机制。

### 为什么选择CV2 UI Framework？

- ✅ **轻量级**: 仅依赖OpenCV和NumPy，无需额外GUI库
- ✅ **视频友好**: 直接在NumPy数组上绘制，完美集成视频流
- ✅ **事件驱动**: 完整的鼠标事件和焦点管理系统
- ✅ **模块化**: 组件化设计，易于扩展和复用
- ✅ **易用性**: 简洁的API，类似传统GUI框架的使用方式

### 适用场景

- 远程桌面客户端UI
- 视频监控系统的控制面板
- 计算机视觉应用的调试界面
- 需要轻量级GUI的嵌入式系统

## 🏗️ 架构设计

### 核心概念

```
Object (基类)
  ├─ 位置和尺寸管理
  ├─ 鼠标事件处理
  ├─ 焦点管理
  ├─ 父子关系
  └─ 绘制和更新

Component (组件)
  ├─ Button (按钮)
  ├─ Label (标签)
  ├─ TextBox (文本框)
  ├─ Panel (面板)
  └─ TabbedPanel (选项卡面板)
```

### 类层次结构

```
Object
├── Button
├── Label
├── TextBox
├── Panel
└── TabbedPanel
    └── Tab
```

## 🎨 核心组件

### Object (基类)

所有UI组件的基类，提供基础功能。

#### 核心属性

```python
# 位置和尺寸
x: int              # X坐标
y: int              # Y坐标
width: int          # 宽度
height: int         # 高度

# 可见性和交互性
visible: bool       # 是否可见
enabled: bool       # 是否启用

# 样式
background_color: tuple  # 背景色 (B, G, R)
border_color: tuple      # 边框色
border_width: int        # 边框宽度
alpha: float             # 透明度 (0-1)

# 状态
is_hovered: bool    # 鼠标悬停
is_pressed: bool    # 鼠标按下

# 层次关系
parent: Object      # 父对象
children: list      # 子对象列表
```

#### 核心方法

```python
def add_child(self, child: Object)
    """添加子对象"""

def remove_child(self, child: Object)
    """移除子对象"""

def contains_point(self, px: int, py: int) -> bool
    """检查点是否在对象内"""

def handle_mouse_event(self, event, x, y, flags, param) -> bool
    """处理鼠标事件"""

def draw(self, canvas: np.ndarray)
    """绘制对象"""

def update(self, dt: float)
    """更新对象状态"""
```

#### 事件回调

```python
on_click: Callable      # 点击事件
on_hover: Callable      # 悬停事件
on_leave: Callable      # 离开事件
```

#### 焦点管理

```python
@classmethod
def set_focus(cls, obj: Optional['Object'])
    """设置全局焦点"""

@classmethod
def get_focused_object(cls) -> Optional['Object']
    """获取当前焦点对象"""
```

---

### Button (按钮)

交互式按钮组件。

#### 特有属性

```python
text: str               # 按钮文本
text_color: tuple       # 文本颜色
font_scale: float       # 字体大小
font_thickness: int     # 字体粗细

# 状态颜色
background_color: tuple  # 正常颜色
hover_color: tuple       # 悬停颜色
pressed_color: tuple     # 按下颜色
disabled_color: tuple    # 禁用颜色
```

#### 使用示例

```python
# 创建按钮
button = Button(10, 10, 150, 40, "Click Me", "my_button")
button.background_color = (70, 130, 180)
button.on_click = lambda obj: print("Button clicked!")

# 添加到父容器
parent.add_child(button)

# 禁用按钮
button.disable()
```

---

### Label (标签)

文本显示组件，支持多行文本。

#### 特有属性

```python
text: str           # 显示文本 (支持\n换行)
text_color: tuple   # 文本颜色
font_scale: float   # 字体大小
font_thickness: int # 字体粗细

# 对齐方式
align: str   # 水平对齐: "left", "center", "right"
valign: str  # 垂直对齐: "top", "center", "bottom"
```

#### 使用示例

```python
# 单行文本
label = Label(10, 10, 300, 30, "Hello World", "my_label")
label.text_color = (255, 255, 255)
label.align = "center"

# 多行文本
multi_label = Label(10, 50, 300, 80, 
    "Line 1\nLine 2\nLine 3", 
    "multi_label")
multi_label.valign = "top"
```

---

### TextBox (文本输入框)

支持文本输入和编辑的组件。

#### 特有属性

```python
text: str              # 当前文本
placeholder: str       # 占位符文本
max_length: int        # 最大长度
cursor_position: int   # 光标位置
is_focused: bool       # 是否获得焦点

# 光标闪烁
cursor_visible: bool          # 光标可见性
cursor_blink_interval: float  # 闪烁间隔
```

#### 核心功能

```python
def handle_key(self, key: int, is_press: bool = True) -> bool
    """处理键盘输入"""
    # 支持的按键:
    # - Enter (13): 失去焦点
    # - ESC (27): 失去焦点
    # - Backspace (8): 删除前一个字符
    # - Delete (127): 删除当前字符
    # - Left Arrow (2): 光标左移
    # - Right Arrow (3): 光标右移
    # - Home (1): 光标移到开头
    # - End (4): 光标移到末尾
    # - 可打印字符 (32-126): 插入字符
```

#### 高级特性

**长按重复**
```python
key_repeat_delay: float = 0.5      # 首次重复延迟
key_repeat_interval: float = 0.03  # 重复间隔
```

**光标移动检测**
```python
cursor_moving: bool              # 光标是否在快速移动
cursor_move_timeout: float = 0.15  # 移动停止判定时间
```

#### 使用示例

```python
# 创建文本框
textbox = TextBox(10, 10, 300, 40, "my_textbox")
textbox.placeholder = "Enter text..."
textbox.max_length = 50

# 文本变化回调
def on_text_changed(obj):
    print(f"Text: {obj.text}")

textbox.on_text_change = on_text_changed

# 处理键盘输入
key = cv2.waitKey(1) & 0xFF
if textbox.handle_key(key):
    print("Key handled by textbox")
```

---

### Panel (面板)

容器组件，可以包含其他组件。

#### 特有属性

```python
title: str           # 面板标题
title_height: int    # 标题栏高度
title_color: tuple   # 标题背景色
title_text_color: tuple  # 标题文字色
```

#### 使用示例

```python
# 创建面板
panel = Panel(50, 50, 400, 300, "my_panel")
panel.title = "Settings"
panel.background_color = (245, 245, 245)

# 添加子组件
label = Label(10, 40, 380, 30, "Option 1", "label1")
button = Button(10, 80, 180, 40, "Save", "save_btn")

panel.add_child(label)
panel.add_child(button)
```

---

### TabbedPanel (选项卡面板)

支持多个选项卡的高级容器。

#### 特有属性

```python
tabs: List[Tab]              # 选项卡列表
active_tab_index: int        # 当前激活的选项卡索引
tab_height: int              # 选项卡高度
tab_spacing: int             # 选项卡间距

# 样式
active_tab_color: tuple      # 激活选项卡颜色
inactive_tab_color: tuple    # 非激活选项卡颜色
```

#### Tab 类

```python
class Tab:
    name: str                           # 选项卡名称
    content_builder: Callable           # 内容构建函数
    is_active: bool                     # 是否激活
```

#### 核心方法

```python
def add_tab(self, name: str, content_builder: Callable)
    """添加选项卡"""

def switch_tab(self, index: int)
    """切换选项卡"""
```

#### 使用示例

```python
# 创建选项卡面板
panel = TabbedPanel(20, 20, 550, 600, "debug_panel")

# 定义选项卡内容
def create_settings_content():
    items = []
    label = Label(10, 10, 510, 30, "Settings", "title")
    button = Button(10, 50, 200, 40, "Apply", "apply_btn")
    items.extend([label, button])
    return items

def create_stats_content():
    items = []
    label = Label(10, 10, 510, 30, "Statistics", "title")
    items.append(label)
    return items

# 添加选项卡
panel.add_tab("Settings", create_settings_content)
panel.add_tab("Statistics", create_stats_content)

# 切换选项卡
panel.switch_tab(1)
```

---

## 🎯 事件系统

### 鼠标事件

框架支持完整的鼠标事件处理。

#### 事件类型

```python
cv2.EVENT_LBUTTONDOWN    # 左键按下
cv2.EVENT_LBUTTONUP      # 左键释放
cv2.EVENT_MOUSEMOVE      # 鼠标移动
```

#### 事件传播机制

1. **自顶向下传播**: 事件从父对象传递到子对象
2. **事件捕获**: 子对象优先处理事件
3. **事件停止**: 返回True停止传播

#### 实现示例

```python
def mouse_callback(event, x, y, flags, param):
    root.handle_mouse_event(event, x, y, flags, param)

cv2.namedWindow("Window")
cv2.setMouseCallback("Window", mouse_callback)
```

### 键盘事件

使用pygame的键盘事件系统。

#### 按键映射

```python
# 特殊键映射
key_map = {
    pygame.K_ESCAPE: 27,      # ESC
    pygame.K_RETURN: 13,      # Enter
    pygame.K_BACKSPACE: 8,    # Backspace
    pygame.K_DELETE: 127,     # Delete
    pygame.K_LEFT: 2,         # Left Arrow
    pygame.K_RIGHT: 3,        # Right Arrow
    pygame.K_HOME: 1,         # Home
    pygame.K_END: 4,          # End
}
```

#### 处理示例

```python
for event in pygame.event.get():
    if event.type == pygame.KEYDOWN:
        key = event.key
        
        # 映射特殊键
        if key in key_map:
            key = key_map[key]
        
        # 处理按键
        if textbox.handle_key(key, is_press=True):
            print("Key handled")
```

---

## 🎨 样式系统

### 颜色定义

OpenCV使用BGR格式 (注意不是RGB)。

```python
# 常用颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (0, 0, 255)
GREEN = (0, 255, 0)
BLUE = (255, 0, 0)
YELLOW = (0, 255, 255)
CYAN = (255, 255, 0)
MAGENTA = (255, 0, 255)
```

### 透明度

```python
# 半透明背景
obj.alpha = 0.7

# 绘制实现
overlay = canvas.copy()
cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)
```

### 字体

OpenCV支持的字体类型：

```python
cv2.FONT_HERSHEY_SIMPLEX        # 正常大小的sans-serif字体
cv2.FONT_HERSHEY_PLAIN          # 小号字体
cv2.FONT_HERSHEY_DUPLEX         # 正常大小，比SIMPLEX复杂
cv2.FONT_HERSHEY_COMPLEX        # 正常大小，更复杂
cv2.FONT_HERSHEY_TRIPLEX        # 正常大小，更复杂
```

---

## 📐 布局管理

### 绝对定位

```python
# 直接指定位置
button = Button(100, 50, 150, 40, "Button")
```

### 相对定位

```python
# 相对于父容器
panel = Panel(50, 50, 400, 300)
button = Button(10, 10, 100, 30, "Button")  # 相对于panel
panel.add_child(button)

# 绝对位置自动计算
ax, ay = button.absolute_position  # (60, 60)
```

### 动态布局示例

```python
def create_vertical_layout(items, x, y, spacing=10):
    """创建垂直布局"""
    current_y = y
    for item in items:
        item.x = x
        item.y = current_y
        current_y += item.height + spacing
    return items
```

---

## 🔄 更新循环

### 标准更新循环

```python
import time
import cv2
import numpy as np

# 创建根对象
root = Object(0, 0, 800, 600, "root")

# 添加组件...

# 设置鼠标回调
def mouse_callback(event, x, y, flags, param):
    root.handle_mouse_event(event, x, y, flags, param)

cv2.namedWindow("Window")
cv2.setMouseCallback("Window", mouse_callback)

last_time = time.time()

while True:
    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time
    
    # 创建画布
    canvas = np.zeros((600, 800, 3), dtype=np.uint8)
    
    # 更新UI状态
    root.update(dt)
    
    # 绘制UI
    root.draw(canvas)
    
    # 显示
    cv2.imshow("Window", canvas)
    
    # 处理按键
    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC
        break
    
    # 检查窗口是否关闭
    if cv2.getWindowProperty("Window", cv2.WND_PROP_VISIBLE) < 1:
        break

cv2.destroyAllWindows()
```

---

## 📝 完整示例

### 简单的设置面板

```python
import cv2
import numpy as np
import time
from ui.components.base_object import Object
from ui.components.panel import Panel
from ui.components.label import Label
from ui.components.button import Button
from ui.components.textbox import TextBox

# 创建窗口
width, height = 800, 600
window_name = "Settings Panel"

# 创建根对象
root = Object(0, 0, width, height, "root")
root.background_color = (240, 240, 240)

# 创建面板
panel = Panel(50, 50, 700, 500, "settings_panel")
panel.title = "Settings"
root.add_child(panel)

# 添加标签
label = Label(20, 50, 660, 30, "Server Configuration", "title")
label.text_color = (50, 50, 50)
label.font_scale = 0.6
label.font_thickness = 2
panel.add_child(label)

# IP地址输入
ip_label = Label(20, 100, 200, 25, "Server IP:", "ip_label")
ip_label.text_color = (80, 80, 80)
ip_label.align = "left"
panel.add_child(ip_label)

ip_textbox = TextBox(230, 100, 250, 35, "ip_textbox")
ip_textbox.text = "192.168.1.100"
panel.add_child(ip_textbox)

# 端口输入
port_label = Label(20, 150, 200, 25, "Port:", "port_label")
port_label.text_color = (80, 80, 80)
port_label.align = "left"
panel.add_child(port_label)

port_textbox = TextBox(230, 150, 250, 35, "port_textbox")
port_textbox.text = "8888"
panel.add_child(port_textbox)

# 连接按钮
def on_connect_click(obj):
    ip = ip_textbox.text
    port = port_textbox.text
    print(f"Connecting to {ip}:{port}")
    obj.text = "Connected!"

connect_button = Button(20, 200, 460, 45, "Connect", "connect_btn")
connect_button.background_color = (70, 130, 180)
connect_button.on_click = on_connect_click
panel.add_child(connect_button)

# 鼠标回调
def mouse_callback(event, x, y, flags, param):
    root.handle_mouse_event(event, x, y, flags, param)

cv2.namedWindow(window_name)
cv2.setMouseCallback(window_name, mouse_callback)

last_time = time.time()

while True:
    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time
    
    # 创建画布
    canvas = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # 更新和绘制
    root.update(dt)
    root.draw(canvas)
    
    cv2.imshow(window_name, canvas)
    
    # 处理按键
    key = cv2.waitKey(1) & 0xFF
    
    # 让TextBox处理键盘输入
    if ip_textbox.handle_key(key) or port_textbox.handle_key(key):
        continue
    
    if key == 27:  # ESC
        break
    
    # 检查窗口是否关闭
    if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
        break

cv2.destroyAllWindows()
```

---

## 🚀 高级技巧

### 自定义组件

```python
class ProgressBar(Object):
    """进度条组件"""
    
    def __init__(self, x, y, width, height, name=""):
        super().__init__(x, y, width, height, name)
        self.progress = 0.0  # 0.0 - 1.0
        self.bar_color = (0, 255, 0)
        self.background_color = (200, 200, 200)
    
    def set_progress(self, value: float):
        """设置进度"""
        self.progress = max(0.0, min(1.0, value))
    
    def draw(self, canvas: np.ndarray):
        if not self.visible:
            return
        
        ax, ay = self.absolute_position
        
        # 绘制背景
        cv2.rectangle(canvas, (ax, ay),
                     (ax + self.width, ay + self.height),
                     self.background_color, -1)
        
        # 绘制进度
        bar_width = int(self.width * self.progress)
        if bar_width > 0:
            cv2.rectangle(canvas, (ax, ay),
                         (ax + bar_width, ay + self.height),
                         self.bar_color, -1)
        
        # 绘制边框
        cv2.rectangle(canvas, (ax, ay),
                     (ax + self.width, ay + self.height),
                     (100, 100, 100), 2)
```

### 动画效果

```python
class AnimatedButton(Button):
    """带动画的按钮"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.animation_time = 0.0
        self.animation_duration = 0.3
        self.is_animating = False
    
    def on_click(self, obj):
        """点击动画"""
        self.is_animating = True
        self.animation_time = 0.0
    
    def update(self, dt: float):
        super().update(dt)
        
        if self.is_animating:
            self.animation_time += dt
            
            if self.animation_time >= self.animation_duration:
                self.is_animating = False
                self.animation_time = 0.0
    
    def draw(self, canvas: np.ndarray):
        # 缩放动画
        if self.is_animating:
            progress = self.animation_time / self.animation_duration
            scale = 1.0 + 0.1 * (1.0 - progress)
            
            # 临时调整尺寸
            original_width = self.width
            original_height = self.height
            
            self.width = int(original_width * scale)
            self.height = int(original_height * scale)
            
            super().draw(canvas)
            
            self.width = original_width
            self.height = original_height
        else:
            super().draw(canvas)
```

### 主题系统

```python
class Theme:
    """主题配置"""
    
    # 深色主题
    DARK = {
        'background': (45, 45, 52),
        'panel_bg': (55, 55, 62),
        'text': (240, 240, 245),
        'primary': (70, 130, 180),
        'border': (100, 100, 110),
    }
    
    # 浅色主题
    LIGHT = {
        'background': (240, 240, 240),
        'panel_bg': (255, 255, 255),
        'text': (50, 50, 50),
        'primary': (70, 130, 180),
        'border': (180, 180, 180),
    }

def apply_theme(obj: Object, theme: dict):
    """应用主题到对象"""
    if hasattr(obj, 'background_color'):
        obj.background_color = theme['panel_bg']
    if hasattr(obj, 'text_color'):
        obj.text_color = theme['text']
    if hasattr(obj, 'border_color'):
        obj.border_color = theme['border']
    
    # 递归应用到子对象
    for child in obj.children:
        apply_theme(child, theme)
```

---

## 🐛 调试技巧

### 可视化调试

```python
def draw_debug_info(obj: Object, canvas: np.ndarray):
    """绘制调试信息"""
    ax, ay = obj.absolute_position
    
    # 绘制边界框
    cv2.rectangle(canvas, (ax, ay),
                 (ax + obj.width, ay + obj.height),
                 (0, 255, 0), 1)
    
    # 显示对象名称
    cv2.putText(canvas, obj.name, (ax, ay - 5),
               cv2.FONT_HERSHEY_SIMPLEX, 0.4,
               (0, 255, 0), 1)
    
    # 递归绘制子对象
    for child in obj.children:
        draw_debug_info(child, canvas)
```

### 事件日志

```python
class LoggingObject(Object):
    """带日志的对象"""
    
    def handle_mouse_event(self, event, x, y, flags, param):
        event_name = {
            cv2.EVENT_LBUTTONDOWN: "LBUTTONDOWN",
            cv2.EVENT_LBUTTONUP: "LBUTTONUP",
            cv2.EVENT_MOUSEMOVE: "MOUSEMOVE",
        }.get(event, "UNKNOWN")
        
        print(f"[{self.name}] {event_name} at ({x}, {y})")
        
        return super().handle_mouse_event(event, x, y, flags, param)
```

---

## 📊 性能优化

### 减少重绘

```python
class CachedPanel(Panel):
    """带缓存的面板"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = None
        self.cache_dirty = True
    
    def draw(self, canvas: np.ndarray):
        if self.cache_dirty or self.cache is None:
            # 创建缓存
            self.cache = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            super().draw(self.cache)
            self.cache_dirty = False
        
        # 从缓存绘制
        ax, ay = self.absolute_position
        canvas[ay:ay+self.height, ax:ax+self.width] = self.cache
    
    def invalidate_cache(self):
        """标记缓存失效"""
        self.cache_dirty = True
```

### 事件过滤

```python
def handle_mouse_event(self, event, x, y, flags, param):
    # 只处理感兴趣的事件
    if event not in [cv2.EVENT_LBUTTONDOWN, cv2.EVENT_LBUTTONUP]:
        return False
    
    return super().handle_mouse_event(event, x, y, flags, param)
```

---

## 🔗 与Pygame集成

本框架在PIP-Link项目中与Pygame集成使用。

### 集成要点

```python
import pygame
import cv2
import numpy as np

# 初始化Pygame
pygame.init()
screen = pygame.display.set_mode((width, height))

# 创建UI
root = Object(0, 0, width, height)

# 主循环
while True:
    # Pygame事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            root.handle_mouse_event(cv2.EVENT_LBUTTONDOWN, 
                                   event.pos[0], event.pos[1], 0, None)
    
    # 创建OpenCV画布
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    
    # 绘制UI
    root.draw(canvas)
    
    # 转换并显示
    canvas_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
    canvas_surface = pygame.surfarray.make_surface(canvas_rgb.swapaxes(0, 1))
    screen.blit(canvas_surface, (0, 0))
    pygame.display.flip()
```

---

## 📚 API参考

### Object

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `__init__` | x, y, width, height, name | - | 构造函数 |
| `add_child` | child: Object | - | 添加子对象 |
| `remove_child` | child: Object | - | 移除子对象 |
| `contains_point` | px: int, py: int | bool | 检查点是否在对象内 |
| `handle_mouse_event` | event, x, y, flags, param | bool | 处理鼠标事件 |
| `draw` | canvas: np.ndarray | - | 绘制对象 |
| `update` | dt: float | - | 更新对象状态 |
| `show` | - | - | 显示对象 |
| `hide` | - | - | 隐藏对象 |
| `enable` | - | - | 启用交互 |
| `disable` | - | - | 禁用交互 |
| `set_position` | x: int, y: int | - | 设置位置 |
| `set_size` | width: int, height: int | - | 设置大小 |
| `set_focus` | obj: Object (classmethod) | - | 设置全局焦点 |
| `get_focused_object` | - (classmethod) | Object | 获取焦点对象 |

### Button

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `__init__` | x, y, width, height, text, name | - | 构造函数 |
| `draw` | canvas: np.ndarray | - | 绘制按钮 |

| 属性 | 类型 | 说明 |
|------|------|------|
| `text` | str | 按钮文本 |
| `text_color` | tuple | 文本颜色 |
| `font_scale` | float | 字体大小 |
| `font_thickness` | int | 字体粗细 |
| `background_color` | tuple | 正常背景色 |
| `hover_color` | tuple | 悬停背景色 |
| `pressed_color` | tuple | 按下背景色 |
| `disabled_color` | tuple | 禁用背景色 |

### Label

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `__init__` | x, y, width, height, text, name | - | 构造函数 |
| `draw` | canvas: np.ndarray | - | 绘制标签 |

| 属性 | 类型 | 说明 |
|------|------|------|
| `text` | str | 显示文本(支持\n) |
| `text_color` | tuple | 文本颜色 |
| `font_scale` | float | 字体大小 |
| `font_thickness` | int | 字体粗细 |
| `align` | str | 水平对齐 |
| `valign` | str | 垂直对齐 |

### TextBox

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `__init__` | x, y, width, height, name | - | 构造函数 |
| `handle_key` | key: int, is_press: bool | bool | 处理键盘输入 |
| `handle_mouse_event` | event, x, y, flags, param | bool | 处理鼠标事件 |
| `draw` | canvas: np.ndarray | - | 绘制文本框 |
| `update` | dt: float | - | 更新状态 |
| `on_blur` | - | - | 失去焦点回调 |

| 属性 | 类型 | 说明 |
|------|------|------|
| `text` | str | 当前文本 |
| `placeholder` | str | 占位符 |
| `max_length` | int | 最大长度 |
| `cursor_position` | int | 光标位置 |
| `is_focused` | bool | 焦点状态 |
| `on_text_change` | Callable | 文本改变回调 |

### Panel

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `__init__` | x, y, width, height, name | - | 构造函数 |
| `draw` | canvas: np.ndarray | - | 绘制面板 |

| 属性 | 类型 | 说明 |
|------|------|------|
| `title` | str | 面板标题 |
| `title_height` | int | 标题栏高度 |
| `title_color` | tuple | 标题背景色 |
| `title_text_color` | tuple | 标题文字色 |

### TabbedPanel

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `__init__` | x, y, width, height, name | - | 构造函数 |
| `add_tab` | name: str, content_builder: Callable | - | 添加选项卡 |
| `switch_tab` | index: int | - | 切换选项卡 |
| `draw` | canvas: np.ndarray | - | 绘制面板 |
| `handle_mouse_event` | event, x, y, flags, param | bool | 处理鼠标事件 |

| 属性 | 类型 | 说明 |
|------|------|------|
| `tabs` | List[Tab] | 选项卡列表 |
| `active_tab_index` | int | 当前激活索引 |
| `tab_height` | int | 选项卡高度 |
| `active_tab_color` | tuple | 激活颜色 |
| `inactive_tab_color` | tuple | 非激活颜色 |

---

## 🎓 最佳实践

### 1. 组件命名规范

```python
# 使用描述性名称
button = Button(10, 10, 100, 30, "Save", "save_button")  # Good
button = Button(10, 10, 100, 30, "Save", "btn1")        # Bad

# 使用分类前缀
ip_textbox = TextBox(10, 10, 200, 30, "ip_textbox")
port_textbox = TextBox(10, 50, 200, 30, "port_textbox")
```

### 2. 事件处理

```python
# 使用命名函数而非lambda (便于调试)
def on_save_click(obj):
    print("Saving...")

button.on_click = on_save_click  # Good
button.on_click = lambda obj: print("Saving...")  # Bad (调试困难)
```

### 3. 资源管理

```python
# 在适当时机清理资源
def cleanup():
    """清理UI资源"""
    root.children.clear()
    cv2.destroyAllWindows()
```

### 4. 状态同步

```python
# 定期更新UI状态
def update_ui_state(state):
    """根据应用状态更新UI"""
    if state.is_connected:
        connect_button.text = "Disconnect"
        connect_button.background_color = (180, 70, 70)
    else:
        connect_button.text = "Connect"
        connect_button.background_color = (70, 130, 180)
```

### 5. 错误处理

```python
try:
    root.draw(canvas)
except Exception as e:
    print(f"Draw error: {e}")
    import traceback
    traceback.print_exc()
```

---

## ⚠️ 常见问题

### Q1: 为什么我的TextBox不响应键盘输入？

**A**: 确保你正确处理了键盘事件并调用了`handle_key`方法。

```python
# 正确做法
key = cv2.waitKey(1) & 0xFF
if textbox.handle_key(key):
    continue  # TextBox处理了按键
```

### Q2: 如何实现组件的显示/隐藏动画？

**A**: 使用`alpha`属性配合`update`方法实现淡入淡出。

```python
class FadePanel(Panel):
    def fade_in(self, duration=0.3):
        self.fade_target = 1.0
        self.fade_duration = duration
        self.fade_time = 0.0
    
    def update(self, dt):
        super().update(dt)
        if hasattr(self, 'fade_time'):
            self.fade_time += dt
            progress = min(1.0, self.fade_time / self.fade_duration)
            self.alpha = progress * self.fade_target
```

### Q3: 为什么鼠标事件没有传递到子组件？

**A**: 检查以下几点：
1. 父组件是否调用了`super().handle_mouse_event()`
2. 父组件是否返回了`True`阻止了事件传播
3. 子组件是否在父组件的可见区域内

### Q4: 如何实现拖拽功能？

**A**: 监听`LBUTTONDOWN`、`MOUSEMOVE`和`LBUTTONUP`事件。

```python
class DraggablePanel(Panel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dragging = False
        self.drag_offset = (0, 0)
    
    def handle_mouse_event(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.contains_point(x, y):
                self.dragging = True
                ax, ay = self.absolute_position
                self.drag_offset = (x - ax, y - ay)
                return True
        
        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging = False
        
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.dragging:
                self.x = x - self.drag_offset[0]
                self.y = y - self.drag_offset[1]
                return True
        
        return super().handle_mouse_event(event, x, y, flags, param)
```

### Q5: 如何实现滚动容器？

**A**: 使用裁剪区域和偏移量。

```python
class ScrollPanel(Panel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scroll_offset = 0
        self.content_height = 0
    
    def draw(self, canvas):
        # 创建裁剪区域
        ax, ay = self.absolute_position
        roi = canvas[ay:ay+self.height, ax:ax+self.width]
        
        # 在临时画布上绘制内容
        temp_canvas = np.zeros_like(roi)
        
        # 应用滚动偏移
        for child in self.children:
            child.y -= self.scroll_offset
            child.draw(temp_canvas)
            child.y += self.scroll_offset
        
        # 复制到主画布
        canvas[ay:ay+self.height, ax:ax+self.width] = temp_canvas
```

---

## 🔮 未来改进

### 计划功能

- [ ] **布局管理器**: HBox、VBox、GridLayout
- [ ] **更多组件**: Slider、CheckBox、RadioButton、ComboBox
- [ ] **动画系统**: 更完善的动画框架
- [ ] **主题系统**: 预设主题和主题切换
- [ ] **拖拽系统**: 通用的拖拽接口
- [ ] **性能优化**: 脏矩形更新、组件池

### 贡献指南

欢迎提交PR来改进这个框架！

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 📖 相关资源

### OpenCV文档

- [OpenCV Drawing Functions](https://docs.opencv.org/4.x/dc/da5/tutorial_py_drawing_functions.html)
- [OpenCV Mouse Events](https://docs.opencv.org/4.x/db/d5b/tutorial_py_mouse_handling.html)

### 教程

- [NumPy Arrays](https://numpy.org/doc/stable/user/quickstart.html)
- [Python Event Handling](https://realpython.com/python-gui-programming-with-tkinter/)

---

## 📄 许可证

本UI框架作为PIP-Link项目的一部分，采用 [MIT License](LICENSE)

---

## 🙏 致谢

- **OpenCV** - 提供了强大的图像处理能力
- **NumPy** - 高效的数组操作
- **Pygame** - 窗口和事件集成

---

<div align="center">
**📘 更多信息请参考 [PIP-Link项目文档](../README.md)**

Made with ❤️ for Computer Vision Applications
