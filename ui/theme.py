"""UI Theme - Modern cyberpunk style"""

import imgui


class Theme:
    """Modern cyberpunk theme"""

    # Color constants (RGBA 0-1)
    BG_DARK = (0.05, 0.05, 0.08, 1.0)
    BG_DARKER = (0.02, 0.02, 0.04, 1.0)
    TEXT_WHITE = (0.95, 0.95, 0.98, 1.0)
    TEXT_SECONDARY = (0.7, 0.7, 0.75, 1.0)

    # Accent colors - cyberpunk neon
    ACCENT_CYAN = (0.0, 0.8, 1.0, 1.0)
    ACCENT_PURPLE = (0.8, 0.2, 1.0, 1.0)
    ACCENT_PINK = (1.0, 0.2, 0.8, 1.0)
    ACCENT_BLUE = (0.2, 0.6, 1.0, 1.0)

    # Connection state colors
    STATE_COLORS = {
        "idle": (0.4, 0.4, 0.45, 1.0),  # Gray
        "discovering": (1.0, 0.7, 0.0, 1.0),  # Orange
        "connecting": (1.0, 0.7, 0.0, 1.0),  # Orange
        "connected": (0.0, 1.0, 0.5, 1.0),  # Bright green
        "disconnected": (1.0, 0.2, 0.2, 1.0),  # Red
        "reconnecting": (1.0, 0.7, 0.0, 1.0),  # Orange
    }

    @staticmethod
    def apply(imgui_ctx):
        """Apply modern cyberpunk theme"""
        style = imgui.get_style()

        # Window
        style.colors[imgui.COLOR_WINDOW_BACKGROUND] = Theme.BG_DARK
        style.colors[imgui.COLOR_TITLE_BACKGROUND] = Theme.BG_DARKER
        style.colors[imgui.COLOR_TITLE_BACKGROUND_ACTIVE] = Theme.ACCENT_CYAN

        # Frame
        style.colors[imgui.COLOR_FRAME_BACKGROUND] = (0.08, 0.08, 0.12, 1.0)
        style.colors[imgui.COLOR_FRAME_BACKGROUND_HOVERED] = (0.12, 0.12, 0.18, 1.0)
        style.colors[imgui.COLOR_FRAME_BACKGROUND_ACTIVE] = Theme.ACCENT_BLUE

        # Button
        style.colors[imgui.COLOR_BUTTON] = (0.1, 0.1, 0.15, 1.0)
        style.colors[imgui.COLOR_BUTTON_HOVERED] = Theme.ACCENT_CYAN
        style.colors[imgui.COLOR_BUTTON_ACTIVE] = Theme.ACCENT_PURPLE

        # Text
        style.colors[imgui.COLOR_TEXT] = Theme.TEXT_WHITE
        style.colors[imgui.COLOR_TEXT_DISABLED] = Theme.TEXT_SECONDARY

        # Border
        style.colors[imgui.COLOR_BORDER] = (0.2, 0.2, 0.3, 1.0)
        style.colors[imgui.COLOR_SEPARATOR] = (0.2, 0.2, 0.3, 1.0)

        # Tab
        style.colors[imgui.COLOR_TAB] = (0.08, 0.08, 0.12, 1.0)
        style.colors[imgui.COLOR_TAB_HOVERED] = (0.15, 0.15, 0.22, 1.0)
        style.colors[imgui.COLOR_TAB_ACTIVE] = Theme.ACCENT_CYAN
        style.colors[imgui.COLOR_TAB_UNFOCUSED] = (0.08, 0.08, 0.12, 1.0)
        style.colors[imgui.COLOR_TAB_UNFOCUSED_ACTIVE] = (0.12, 0.12, 0.18, 1.0)

        # Slider
        style.colors[imgui.COLOR_SLIDER_GRAB] = Theme.ACCENT_CYAN
        style.colors[imgui.COLOR_SLIDER_GRAB_ACTIVE] = Theme.ACCENT_PURPLE

        # Checkbox
        style.colors[imgui.COLOR_CHECK_MARK] = Theme.ACCENT_CYAN

        # Header
        style.colors[imgui.COLOR_HEADER] = (0.1, 0.1, 0.15, 1.0)
        style.colors[imgui.COLOR_HEADER_HOVERED] = (0.15, 0.15, 0.22, 1.0)
        style.colors[imgui.COLOR_HEADER_ACTIVE] = Theme.ACCENT_CYAN

        # Rounding and spacing
        style.frame_rounding = 6.0
        style.window_rounding = 8.0
        style.grab_rounding = 4.0
        style.tab_rounding = 6.0

        # Padding and spacing
        style.frame_padding = (8, 6)
        style.item_spacing = (8, 8)
        style.item_inner_spacing = (6, 6)
        style.window_padding = (12, 12)
