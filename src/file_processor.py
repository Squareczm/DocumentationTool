"""
文件处理器
整合文件读取、内容分析、重命名、归档等功能的核心组件
"""

import os
import re
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from .file_reader import FileReader
from .date_extractor import DateExtractor
from .llm_client import LLMClient


class FileProcessor:
    """文件处理器"""
    
    def __init__(self, config: Dict[str, Any], llm_client: LLMClient):
        """
        初始化文件处理器
        
        Args:
            config: 配置字典
            llm_client: LLM客户端实例
        """
        self.config = config
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)
        
        # 初始化子组件
        self.file_reader = FileReader()
        self.date_extractor = DateExtractor(config)
        
        # 知识库路径
        self.knowledge_base_path = Path(config['knowledge_base']['root_path'])
        
        # 文件处理配置
        self.max_filename_length = config['file_processing']['max_filename_length']
        self.version_format = config['file_processing']['version_format']
        
        # 默认配置
        self.initial_version = config['defaults']['initial_version']
        self.fallback_subject = config['defaults']['fallback_subject']
        
        # 特殊字符替换映射
        self.invalid_chars = {
            '<': '《',
            '>': '》',
            ':': '：',
            '"': '"',
            '|': '｜',
            '?': '？',
            '*': '＊',
            '\\': '_',
            '/': '_'
        }
    
    def process_file(self, file_path: Path, dry_run: bool = False) -> Dict[str, Any]:
        """
        处理单个文件
        
        Args:
            file_path: 文件路径
            dry_run: 是否为预览模式
            
        Returns:
            处理结果字典
        """
        try:
            # 1. 读取文件内容
            self.logger.info(f"读取文件: {file_path}")
            file_info = self.file_reader.read_file(file_path)
            
            # 2. 提取主体信息
            self.logger.info("提取文档主体")
            subject_result = self.llm_client.extract_subject_and_folder(file_info)
            subject = subject_result.get('subject', self.fallback_subject)
            
            # 3. 提取日期信息
            self.logger.info("提取日期信息")
            date_result = self.date_extractor.extract_date(file_info)
            date = date_result.get('date')
            
            # 4. 确定版本号
            self.logger.info("确定版本号")
            version = self._determine_version(subject, file_info, file_path.parent)
            
            # 5. 生成新文件名
            new_filename = self._generate_filename(subject, date, version, file_info['suffix'])
            
            # 6. 确定目标文件夹
            target_folder_info = self._determine_target_folder(subject, subject_result)
            target_folder = target_folder_info['path']
            folder_will_be_created = target_folder_info['create_new']
            
            # 7. 构建完整的目标路径
            target_path = target_folder / new_filename
            
            result = {
                'status': 'pending',
                'file_path': str(file_path),
                'original_name': file_info['name'],
                'subject': subject,
                'date': date,
                'version': version,
                'new_name': new_filename,
                'target_folder': str(target_folder),
                'target_path': str(target_path),
                'folder_will_be_created': folder_will_be_created,
                'subject_confidence': subject_result.get('confidence', 0.0),
                'date_source': date_result.get('source', ''),
                'date_confidence': date_result.get('confidence', 0.0),
                'llm_reasoning': subject_result.get('reasoning', ''),
            }
            
            # 检查目标文件是否已存在
            if target_path.exists():
                result['warning'] = f"目标文件已存在: {target_path}"
            
            return result
            
        except Exception as e:
            self.logger.error(f"处理文件失败: {e}")
            return {
                'status': 'error',
                'file_path': str(file_path),
                'original_name': file_path.name,
                'error': str(e)
            }
    
    def execute_operation(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行实际的文件操作
        
        Args:
            result: process_file返回的结果字典
            
        Returns:
            执行结果
        """
        try:
            source_path = Path(result['file_path'])
            target_path = Path(result['target_path'])
            target_folder = target_path.parent
            
            # 创建目标文件夹（如果需要）
            if result['folder_will_be_created']:
                self.logger.info(f"创建文件夹: {target_folder}")
                target_folder.mkdir(parents=True, exist_ok=True)
            
            # 如果目标文件已存在，先备份
            if target_path.exists():
                backup_path = self._get_backup_path(target_path)
                self.logger.warning(f"目标文件已存在，备份到: {backup_path}")
                shutil.move(str(target_path), str(backup_path))
            
            # 移动并重命名文件
            self.logger.info(f"移动文件: {source_path} -> {target_path}")
            shutil.move(str(source_path), str(target_path))
            
            return {
                'status': 'success',
                'source_path': str(source_path),
                'target_path': str(target_path),
                'message': '文件处理成功'
            }
            
        except Exception as e:
            self.logger.error(f"执行文件操作失败: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'message': '文件操作失败'
            }
    
    def _determine_version(self, subject: str, file_info: Dict[str, Any], search_dir: Path) -> str:
        """确定版本号"""
        try:
            # 在知识库中查找相似主题的文件
            similar_files = self._find_similar_files(subject, file_info)
            
            if similar_files:
                # 获取最高版本号
                highest_version = self._get_highest_version(similar_files)
                # 递增版本号
                return self._increment_version(highest_version)
            else:
                return self.initial_version
                
        except Exception as e:
            self.logger.warning(f"确定版本号失败，使用默认版本: {e}")
            return self.initial_version
    
    def _find_similar_files(self, subject: str, file_info: Dict[str, Any]) -> List[Path]:
        """在知识库中查找相似主题的文件"""
        similar_files = []
        
        if not self.knowledge_base_path.exists():
            return similar_files
        
        # 搜索包含主体关键词的文件
        subject_keywords = self._extract_keywords(subject)
        
        for file_path in self.knowledge_base_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            filename = file_path.stem.lower()
            
            # 检查文件名是否包含主体关键词
            if any(keyword.lower() in filename for keyword in subject_keywords):
                # 使用LLM进行更精确的相似性检查
                if self.llm_client.enabled:
                    try:
                        existing_file_info = self.file_reader.read_file(file_path)
                        similarity_result = self.llm_client.check_content_similarity(
                            file_info.get('content', ''),
                            existing_file_info.get('content', '')
                        )
                        
                        if similarity_result.get('is_similar', False):
                            similar_files.append(file_path)
                    except Exception as e:
                        self.logger.debug(f"相似性检查失败 {file_path}: {e}")
                else:
                    # 回退到简单的文件名匹配
                    similar_files.append(file_path)
        
        return similar_files
    
    def _extract_keywords(self, subject: str) -> List[str]:
        """从主体中提取关键词"""
        # 移除常见的停用词
        stop_words = {'的', '是', '在', '和', '与', '及', '或', '等', '了', '中', '对', '于'}
        
        # 简单的分词（可以使用更复杂的分词库）
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', subject)
        keywords = [word for word in words if len(word) > 1 and word not in stop_words]
        
        return keywords
    
    def _get_highest_version(self, files: List[Path]) -> str:
        """获取文件列表中的最高版本号"""
        versions = []
        
        version_pattern = r'v(\d+)\.(\d+)(?:\.(\d+))?'
        
        for file_path in files:
            filename = file_path.stem
            match = re.search(version_pattern, filename, re.IGNORECASE)
            
            if match:
                major = int(match.group(1))
                minor = int(match.group(2))
                patch = int(match.group(3)) if match.group(3) else 0
                versions.append((major, minor, patch))
        
        if versions:
            # 找到最高版本
            highest = max(versions)
            if self.version_format == 'semantic':
                return f"v{highest[0]}.{highest[1]}.{highest[2]}"
            else:
                return f"v{highest[0]}.{highest[1]}"
        
        return self.initial_version
    
    def _increment_version(self, version: str) -> str:
        """递增版本号"""
        version_pattern = r'v(\d+)\.(\d+)(?:\.(\d+))?'
        match = re.match(version_pattern, version, re.IGNORECASE)
        
        if match:
            major = int(match.group(1))
            minor = int(match.group(2))
            patch = int(match.group(3)) if match.group(3) else 0
            
            if self.version_format == 'semantic':
                # 递增补丁版本
                return f"v{major}.{minor}.{patch + 1}"
            else:
                # 递增次版本
                return f"v{major}.{minor + 1}"
        
        return self.initial_version
    
    def _determine_target_folder(self, subject: str, subject_result: Dict[str, Any]) -> Dict[str, Any]:
        """确定目标文件夹"""
        if self.llm_client.enabled:
            # 获取现有文件夹列表
            existing_folders = self.get_existing_folders()
            
            # 使用新的严格文件夹建议逻辑
            folder_suggestion = self.llm_client.suggest_folder_structure(subject, existing_folders)
            suggested_path = folder_suggestion.get('suggested_path', '')
            create_new = folder_suggestion.get('create_new', True)
            
            if suggested_path:
                # 使用建议的路径
                folder_path = self.knowledge_base_path / suggested_path
                
                return {
                    'path': folder_path,
                    'create_new': create_new
                }
        
        # 回退到原有逻辑
        suggested_folder = subject_result.get('suggested_folder', '')
        
        if suggested_folder:
            # 使用LLM建议的路径
            folder_path = self.knowledge_base_path / suggested_folder
        else:
            # 使用主体作为文件夹名
            safe_subject = self._sanitize_filename(subject)
            
            if self.config['knowledge_base']['archive_by_year']:
                # 按年份归档
                from datetime import datetime
                year = datetime.now().year
                folder_path = self.knowledge_base_path / str(year) / safe_subject
            else:
                folder_path = self.knowledge_base_path / safe_subject
        
        # 检查文件夹是否已存在
        create_new = not folder_path.exists()
        
        return {
            'path': folder_path,
            'create_new': create_new
        }
    
    def _generate_filename(self, subject: str, date: str, version: str, extension: str) -> str:
        """生成新文件名"""
        # 清理主体名称
        safe_subject = self._sanitize_filename(subject)
        
        # 检查主体中是否已经包含日期
        date_pattern = r'\d{8}'  # YYYYMMDD格式
        has_date_in_subject = re.search(date_pattern, safe_subject)
        
        if has_date_in_subject:
            # 如果主体中已包含日期，只添加版本号
            filename = f"{safe_subject}_{version}{extension}"
        else:
            # 如果主体中没有日期，按标准格式添加日期
            filename = f"{safe_subject}_{date}_{version}{extension}"
        
        # 检查文件名长度
        if len(filename) > self.max_filename_length:
            # 截断主体部分
            if has_date_in_subject:
                max_subject_length = self.max_filename_length - len(f"_{version}{extension}")
            else:
                max_subject_length = self.max_filename_length - len(f"_{date}_{version}{extension}")
            safe_subject = safe_subject[:max_subject_length]
            
            if has_date_in_subject:
                filename = f"{safe_subject}_{version}{extension}"
            else:
                filename = f"{safe_subject}_{date}_{version}{extension}"
        
        return filename
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除或替换非法字符"""
        # 替换特殊字符
        for invalid_char, replacement in self.invalid_chars.items():
            filename = filename.replace(invalid_char, replacement)
        
        # 移除首尾空格
        filename = filename.strip()
        
        # 如果文件名为空，使用默认名称
        if not filename:
            filename = "untitled"
        
        return filename
    
    def _get_backup_path(self, target_path: Path) -> Path:
        """生成备份文件路径"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_name = f"{target_path.stem}_backup_{timestamp}{target_path.suffix}"
        return target_path.parent / backup_name
    
    def get_existing_folders(self) -> List[str]:
        """获取知识库中现有的文件夹列表"""
        folders = []
        
        if self.knowledge_base_path.exists():
            for item in self.knowledge_base_path.rglob("*"):
                if item.is_dir():
                    relative_path = item.relative_to(self.knowledge_base_path)
                    folders.append(str(relative_path))
        
        return folders 