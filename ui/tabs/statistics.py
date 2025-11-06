from ui.components.label import Label


class StatisticsTab:
    """统计信息选项卡"""

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.components = []
        self._build_ui()

    def _build_ui(self):
        """构建UI"""
        # 固定标签
        self.frames_label = Label(10, 10, 510, 25, "", "frames_label")
        self.frames_label.text_color = (240, 240, 245)
        self.frames_label.background_color = (45, 45, 52)
        self.frames_label.font_scale = 0.5
        self.frames_label.font_thickness = 2

        self.latency_label = Label(10, 40, 510, 25, "", "latency_label")
        self.latency_label.text_color = (240, 240, 245)
        self.latency_label.background_color = (45, 45, 52)
        self.latency_label.font_scale = 0.5
        self.latency_label.font_thickness = 2

        self.latency_status_label = Label(10, 70, 510, 25, "", "latency_status")
        self.latency_status_label.background_color = (45, 45, 52)
        self.latency_status_label.font_scale = 0.5
        self.latency_status_label.font_thickness = 2

        # 丢包率标签
        self.recent_loss_label = Label(10, 100, 510, 25, "", "recent_loss")
        self.recent_loss_label.background_color = (45, 45, 52)
        self.recent_loss_label.font_scale = 0.5
        self.recent_loss_label.font_thickness = 2

        self.overall_loss_label = Label(10, 130, 510, 25, "", "overall_loss")
        self.overall_loss_label.text_color = (200, 200, 205)
        self.overall_loss_label.background_color = (45, 45, 52)
        self.overall_loss_label.font_scale = 0.45

        # 带宽标签
        self.current_bw_label = Label(10, 160, 510, 25, "", "current_bw")
        self.current_bw_label.background_color = (45, 45, 52)
        self.current_bw_label.font_scale = 0.5
        self.current_bw_label.font_thickness = 2

        self.average_bw_label = Label(10, 190, 510, 25, "", "avg_bw")
        self.average_bw_label.text_color = (200, 200, 205)
        self.average_bw_label.background_color = (45, 45, 52)
        self.average_bw_label.font_scale = 0.45

        self.peak_bw_label = Label(10, 220, 510, 25, "", "peak_bw")
        self.peak_bw_label.text_color = (150, 200, 255)
        self.peak_bw_label.background_color = (45, 45, 52)
        self.peak_bw_label.font_scale = 0.45

        self.total_data_label = Label(10, 250, 510, 25, "", "total_data")
        self.total_data_label.text_color = (200, 200, 205)
        self.total_data_label.background_color = (45, 45, 52)
        self.total_data_label.font_scale = 0.45

        self.packets_label = Label(10, 280, 510, 25, "", "packets_stats")
        self.packets_label.text_color = (150, 150, 155)
        self.packets_label.background_color = (45, 45, 52)
        self.packets_label.font_scale = 0.4

        self.dropped_label = Label(10, 310, 510, 25, "", "dropped_frames")
        self.dropped_label.text_color = (255, 150, 100)
        self.dropped_label.background_color = (45, 45, 52)
        self.dropped_label.font_scale = 0.4

        self.update_label = Label(10, 340, 510, 25, "", "last_update")
        self.update_label.text_color = (150, 150, 155)
        self.update_label.background_color = (45, 45, 52)
        self.update_label.font_scale = 0.4

        self.components = [
            self.frames_label, self.latency_label, self.latency_status_label,
            self.recent_loss_label, self.overall_loss_label,
            self.current_bw_label, self.average_bw_label, self.peak_bw_label,
            self.total_data_label, self.packets_label, self.dropped_label,
            self.update_label
        ]

    def update(self, stats, frames_received, latency_ms, last_param_time):
        """更新统计信息"""
        import time

        # 帧数
        self.frames_label.text = f"Frames Received: {frames_received}"

        # 延迟
        self.latency_label.text = f"Network Latency: {latency_ms:.1f} ms"

        # 延迟状态
        latency_status = "Excellent" if latency_ms < 20 else "Good" if latency_ms < 50 else "Poor"
        latency_color = (100, 255, 100) if latency_ms < 20 else (220, 180, 50) if latency_ms < 50 else (255, 100, 100)
        self.latency_status_label.text = f"Latency Status: {latency_status}"
        self.latency_status_label.text_color = latency_color

        if stats:
            # 最近丢包率
            recent_loss = stats['recent_packet_loss_rate'] * 100
            self.recent_loss_label.text = f"Packet Loss (Recent): {recent_loss:.2f}%"
            if recent_loss < 1.0:
                self.recent_loss_label.text_color = (100, 255, 100)
            elif recent_loss < 5.0:
                self.recent_loss_label.text_color = (220, 180, 50)
            else:
                self.recent_loss_label.text_color = (255, 100, 100)

            # 总体丢包率
            overall_loss = stats['overall_packet_loss_rate'] * 100
            self.overall_loss_label.text = f"Packet Loss (Overall): {overall_loss:.2f}%"

            # 当前带宽
            current_bw = stats['current_bandwidth_mbps']
            self.current_bw_label.text = f"Bandwidth (Current): {current_bw:.2f} Mbps"
            if current_bw >= 10.0:
                self.current_bw_label.text_color = (100, 255, 100)
            elif current_bw >= 5.0:
                self.current_bw_label.text_color = (220, 180, 50)
            else:
                self.current_bw_label.text_color = (255, 150, 100)

            # 平均带宽
            avg_bw = stats['average_bandwidth_mbps']
            self.average_bw_label.text = f"Bandwidth (Average): {avg_bw:.2f} Mbps"

            # 峰值带宽
            peak_bw = stats['peak_bandwidth_mbps']
            self.peak_bw_label.text = f"Bandwidth (Peak): {peak_bw:.2f} Mbps"

            # 总数据量
            total_mb = stats['total_bytes_received'] / (1024 * 1024)
            self.total_data_label.text = f"Total Data: {total_mb:.2f} MB"

            # 数据包统计
            self.packets_label.text = f"Packets: {stats['total_packets_received']}/{stats['total_packets_expected']}"

            # 丢弃帧数
            self.dropped_label.text = f"Frames Dropped: {stats['total_frames_dropped']}"

        # 参数更新时间
        time_since_update = time.time() - last_param_time if last_param_time > 0 else 999
        update_text = f"Last Update: {time_since_update:.1f}s ago" if time_since_update < 10 else "No recent updates"
        self.update_label.text = update_text

    def get_components(self):
        """返回UI组件列表"""
        return self.components