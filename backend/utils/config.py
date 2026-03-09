import json
from pathlib import Path
from typing import Any, Dict

# 配置文件路径
CONFIG_FILE = Path(__file__).parent.parent / "data" / "app_config.json"


def load_config() -> Dict[str, Any]:
    """加载应用配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config: Dict[str, Any]):
    """保存应用配置"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_config_value(key: str, default: Any = None) -> Any:
    """获取配置值"""
    config = load_config()
    return config.get(key, default)


def set_config_value(key: str, value: Any):
    """设置配置值"""
    config = load_config()
    config[key] = value
    save_config(config)
