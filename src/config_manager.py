"""
配置管理器
负责加载配置文件，管理运行时配置，处理环境变量等
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为 config.yaml
        """
        self.config_path = config_path or "config.yaml"
        self.config = self._load_config()
        self._apply_env_overrides()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = self._get_default_config()
        
        if not Path(self.config_path).exists():
            print(f"配置文件 {self.config_path} 不存在，使用默认配置")
            return default_config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
            
            # 合并配置，文件配置覆盖默认配置
            merged_config = self._merge_config(default_config, file_config)
            return merged_config
            
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            print("使用默认配置")
            return default_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'llm': {
                'provider': 'openai',
                'api_key': '',
                'base_url': '',
                'model': 'gpt-3.5-turbo',
                'timeout': 30
            },
            'knowledge_base': {
                'root_path': './knowledge_base',
                'archive_by_year': True,
                'max_folder_depth': 3
            },
            'file_processing': {
                'supported_extensions': ['.docx', '.xlsx', '.pdf', '.txt', '.md'],
                'max_filename_length': 200,
                'version_format': 'simple',
                'date_format': '%Y%m%d'
            },
            'date_extraction': {
                'priority': ['content_date', 'creation_date', 'modification_date', 'current_date']
            },
            'defaults': {
                'auto_create_folders': True,
                'initial_version': 'v1.0',
                'fallback_subject': '未分类文档'
            },
            'output': {
                'verbose': True,
                'colored_output': True,
                'log_file': './file_organizer.log'
            }
        }
    
    def _merge_config(self, default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并配置字典"""
        result = default.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self):
        """应用环境变量覆盖"""
        # API密钥从环境变量获取
        api_key = os.getenv('SMARTFILEORG_LLM_API_KEY')
        if api_key:
            self.config['llm']['api_key'] = api_key
        
        # 知识库路径从环境变量获取
        kb_path = os.getenv('SMARTFILEORG_KNOWLEDGE_BASE')
        if kb_path:
            self.config['knowledge_base']['root_path'] = kb_path
    
    def set_knowledge_base_path(self, path: str):
        """设置知识库路径"""
        self.config['knowledge_base']['root_path'] = path
    
    def set_api_key(self, api_key: str):
        """设置API密钥"""
        self.config['llm']['api_key'] = api_key
    
    def get_knowledge_base_path(self) -> Path:
        """获取知识库路径"""
        return Path(self.config['knowledge_base']['root_path'])
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        return self.config['llm'].copy()
    
    def validate_config(self) -> tuple[bool, list[str]]:
        """
        验证配置的有效性
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # 检查API密钥
        if not self.config['llm']['api_key']:
            errors.append("未配置LLM API密钥，请设置环境变量 SMARTFILEORG_LLM_API_KEY 或在配置文件中指定")
        
        # 检查知识库路径
        kb_path = Path(self.config['knowledge_base']['root_path'])
        if not kb_path.parent.exists():
            errors.append(f"知识库父目录不存在: {kb_path.parent}")
        
        # 检查支持的文件扩展名
        if not self.config['file_processing']['supported_extensions']:
            errors.append("未配置支持的文件扩展名")
        
        return len(errors) == 0, errors 