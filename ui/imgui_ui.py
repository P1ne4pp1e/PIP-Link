"""ImGui UI components"""

import imgui
from typing import Optional, Callable, Dict
from ui.theme import Theme
from config import Config


class ImGuiUI:
    """ImGui UI manager"""

    def __init__(self):
        self.show_menu = False
        self.current_tab = 0  # 0: Connection, 1: Parameters, 2: Settings
        Theme.apply(imgui)

    def draw_menu(self, session_state: str, callbacks: Dict[str, Callable]) -> bool:
        """Draw tabbed menu

        Args:
            session_state: Session state string
            callbacks: Callback dict {"connect": fn, "disconnect": fn, "quit": fn}

        Returns:
            running status
        """
        imgui.set_next_window_position(20, 20, imgui.ALWAYS)
        imgui.set_next_window_size(400, 350, imgui.ALWAYS)

        expanded, opened = imgui.begin("Menu", True)
        running = True

        if expanded:
            # Tab bar
            if imgui.begin_tab_bar("MenuTabs"):
                # Connection tab
                if imgui.begin_tab_item("Connection")[0]:
                    self._draw_connection_tab(session_state, callbacks)
                    imgui.end_tab_item()

                # Parameters tab
                if imgui.begin_tab_item("Parameters")[0]:
                    self._draw_parameters_tab()
                    imgui.end_tab_item()

                # Settings tab
                if imgui.begin_tab_item("Settings")[0]:
                    self._draw_settings_tab()
                    imgui.end_tab_item()

                imgui.end_tab_bar()

        imgui.end()

        # Close button (X) only hides menu, doesn't close program
        if not opened:
            self.show_menu = False

        return running

    def _draw_connection_tab(self, session_state: str, callbacks: Dict[str, Callable]) -> None:
        """Draw connection tab"""
        # State indicator
        self._draw_state_indicator(session_state)
        imgui.same_line()
        imgui.text(f"State: {session_state}")

        imgui.separator()

        # Connect button
        if imgui.button("Connect", width=100):
            if "connect" in callbacks:
                callbacks["connect"]()

        imgui.same_line()

        # Disconnect button
        if imgui.button("Disconnect", width=100):
            if "disconnect" in callbacks:
                callbacks["disconnect"]()

        imgui.separator()

        # Quit button
        if imgui.button("Quit", width=100):
            if "quit" in callbacks:
                callbacks["quit"]()

    def _draw_parameters_tab(self) -> None:
        """Draw parameters tab"""
        from logic.param_manager import ParamManager

        # Get param manager from app context (will be passed via callback)
        # For now, show placeholder
        imgui.text("Mouse Sensitivity")
        imgui.slider_float("##sensitivity", 1.0, 0.1, 5.0)

        imgui.text("FOV")
        imgui.slider_float("##fov", 90.0, 30.0, 120.0)

    def _draw_settings_tab(self) -> None:
        """Draw settings tab"""
        imgui.text("Video Quality")
        imgui.combo("##quality", 0, ["Low", "Medium", "High", "Ultra"])

        imgui.text("Recording")
        imgui.checkbox("Enable Recording##rec", False)

        imgui.text("Debug")
        imgui.checkbox("Show Performance Graph##perf", False)

    def draw_status_bar(self, status: Dict) -> None:
        """Draw status bar

        Args:
            status: Status dict {"fps", "latency_ms", "packet_loss_rate", "frames_received", "session_state"}
        """
        # Bottom-right position
        imgui.set_next_window_position(Config.RENDER_WIDTH - 320, Config.RENDER_HEIGHT - 150, imgui.ALWAYS)
        imgui.set_next_window_size(300, 130, imgui.ALWAYS)

        expanded, opened = imgui.begin("Status", True)
        if expanded:
            fps = status.get("fps", 0.0)
            latency = status.get("latency_ms", 0.0)
            loss = status.get("packet_loss_rate", 0.0)
            frames = status.get("frames_received", 0)

            imgui.text(f"FPS: {fps:.1f}")
            imgui.text(f"Latency: {latency:.1f}ms")
            imgui.text(f"Loss: {loss:.2%}")
            imgui.text(f"Frames: {frames}")

        imgui.end()

    def _draw_state_indicator(self, state: str) -> None:
        """Draw colored state indicator

        Args:
            state: State string
        """
        color = Theme.STATE_COLORS.get(state, Theme.STATE_COLORS["idle"])
        imgui.text_colored("●", *color)
