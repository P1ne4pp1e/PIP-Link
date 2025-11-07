import json
import os
from typing import Any, Dict


class ConfigManager:
    """配置文件管理器"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load()

    def load(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                print(f"[ConfigManager] 配置已加载: {self.config_path}")
            except Exception as e:
                print(f"[ConfigManager] 加载配置失败: {e}")
                self._create_default_config()
        else:
            self._create_default_config()

    def _create_default_config(self):
        """创建默认配置"""
        self.config = {
            "connection": {
                "server_ip": "192.168.1.100",
                "server_port": "8888"
            },
            "stream": {
                "jpeg_quality": 80,
                "frame_scale": 1.0
            },
            "image": {
                "exposure": 1.0,
                "contrast": 1.0,
                "gamma": 1.0
            },
            "control": {
                "mouse_sensitivity": 1.0
            },
            "display": {
                "window_mode": "windowed",
                "resolution_index": 6
            }
        }
        self.save()
        print(f"[ConfigManager] 已创建默认配置: {self.config_path}")

    def save(self):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"[ConfigManager] 配置已保存")
        except Exception as e:
            print(f"[ConfigManager] 保存配置失败: {e}")

    def get(self, section: str, key: str, default=None):
        """获取配置值"""
        return self.config.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value):
        """设置配置值并保存"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save()