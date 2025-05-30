"""
工具函数模块
包含日志设置、横幅显示、文件系统操作等辅助功能
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any
from colorama import Fore, Style


def setup_logging(config: Dict[str, Any], verbose: bool = False):
    """
    设置日志系统
    
    Args:
        config: 配置字典
        verbose: 是否显示详细日志
    """
    # 确定日志级别
    if verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    
    # 日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 配置根日志器
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[]
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # 文件处理器
    log_file = config['output']['log_file']
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # 文件中记录更详细的日志
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        
        # 添加处理器到根日志器
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
    
    # 只在非详细模式下添加控制台处理器，避免重复输出
    if not verbose:
        root_logger = logging.getLogger()
        root_logger.addHandler(console_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def print_banner():
    """打印程序横幅"""
    banner = f"""
{Fore.CYAN}╭─────────────────────────────────────────────────────────────╮
│                                                             │
│     🤖 智能文件整理助手 (CLI版本)                           │
│                                                             │
│     📄 自动分析文档内容                                     │
│     🎯 智能提取主体信息                                     │
│     📅 灵活识别日期信息                                     │
│     📁 自动创建归档文件夹                                   │
│     🔖 智能版本号管理                                       │
│                                                             │
╰─────────────────────────────────────────────────────────────╯{Style.RESET_ALL}
"""
    print(banner)


def create_directory_if_not_exists(directory: Path) -> bool:
    """
    创建目录（如果不存在）
    
    Args:
        directory: 目录路径
        
    Returns:
        是否成功创建或目录已存在
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"创建目录失败 {directory}: {e}")
        return False


def is_file_accessible(file_path: Path) -> bool:
    """
    检查文件是否可访问
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件是否可访问
    """
    try:
        return file_path.exists() and file_path.is_file() and os.access(file_path, os.R_OK)
    except Exception:
        return False


def get_file_size_mb(file_path: Path) -> float:
    """
    获取文件大小（MB）
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件大小（MB）
    """
    try:
        size_bytes = file_path.stat().st_size
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小显示
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        格式化的文件大小字符串
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    截断文本并添加省略号
    
    Args:
        text: 原始文本
        max_length: 最大长度
        
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def sanitize_path_component(component: str) -> str:
    """
    清理路径组件，移除非法字符
    
    Args:
        component: 路径组件
        
    Returns:
        清理后的路径组件
    """
    # Windows和Unix共同的非法字符
    invalid_chars = '<>:"|?*'
    
    for char in invalid_chars:
        component = component.replace(char, '_')
    
    # 移除首尾空格和点
    component = component.strip(' .')
    
    # 检查是否为保留名称（Windows）
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    if component.upper() in reserved_names:
        component = f"_{component}"
    
    return component


def validate_api_key(api_key: str) -> bool:
    """
    验证API密钥格式
    
    Args:
        api_key: API密钥
        
    Returns:
        是否为有效格式
    """
    if not api_key:
        return False
    
    # 基本长度检查
    if len(api_key) < 10:
        return False
    
    # 检查是否包含明显的占位符
    placeholders = ['your_api_key', 'your-api-key', 'api_key_here', 'replace_me']
    if api_key.lower() in placeholders:
        return False
    
    return True


def count_words(text: str) -> int:
    """
    统计文本中的词数
    
    Args:
        text: 文本内容
        
    Returns:
        词数
    """
    import re
    
    # 中文字符计数
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    
    # 英文单词计数
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
    
    return chinese_chars + english_words


def progress_bar(current: int, total: int, width: int = 50) -> str:
    """
    生成进度条字符串
    
    Args:
        current: 当前进度
        total: 总数
        width: 进度条宽度
        
    Returns:
        进度条字符串
    """
    if total <= 0:
        return f"[{'=' * width}] 100%"
    
    percentage = min(100, (current / total) * 100)
    filled_width = int((current / total) * width)
    bar = '=' * filled_width + '-' * (width - filled_width)
    
    return f"[{bar}] {percentage:.1f}%"


def get_system_info() -> Dict[str, str]:
    """
    获取系统信息
    
    Returns:
        系统信息字典
    """
    import platform
    import sys
    
    return {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'python_version': sys.version,
        'architecture': platform.architecture()[0],
        'processor': platform.processor() or 'Unknown'
    } 