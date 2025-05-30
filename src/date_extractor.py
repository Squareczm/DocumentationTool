"""
日期提取器
从文档内容、元数据和文件属性中提取日期信息
"""

import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path


class DateExtractor:
    """日期提取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化日期提取器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 日期提取优先级
        self.priority = config['date_extraction']['priority']
        self.date_format = config['file_processing']['date_format']
        
        # 日期正则表达式模式
        self.date_patterns = [
            # YYYY-MM-DD 格式
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
            # YYYY年MM月DD日 格式
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            # MM/DD/YYYY 格式
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            # DD.MM.YYYY 格式
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
            # YYYYMMDD 格式
            r'(\d{8})',
        ]
        
        # 中文日期关键词
        self.chinese_date_keywords = [
            '日期', '时间', '创建时间', '修改时间', '撰写时间',
            '会议时间', '报告时间', '记录时间', '发布时间'
        ]
    
    def extract_date(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据优先级提取日期
        
        Args:
            file_info: 文件信息字典
            
        Returns:
            日期提取结果
        """
        result = {
            'date': None,
            'source': '',
            'confidence': 0.0,
            'raw_date': None
        }
        
        for source in self.priority:
            try:
                if source == 'content_date':
                    date_result = self._extract_from_content(file_info.get('content', ''))
                elif source == 'creation_date':
                    date_result = self._extract_from_file_creation(file_info)
                elif source == 'modification_date':
                    date_result = self._extract_from_file_modification(file_info)
                elif source == 'current_date':
                    date_result = self._extract_current_date()
                else:
                    continue
                
                if date_result['date']:
                    result.update(date_result)
                    result['source'] = source
                    self.logger.info(f"从 {source} 提取到日期: {result['date']}")
                    break
                    
            except Exception as e:
                self.logger.warning(f"从 {source} 提取日期失败: {e}")
                continue
        
        # 如果没有提取到任何日期，使用当前日期作为最后回退
        if not result['date']:
            result.update(self._extract_current_date())
            result['source'] = 'fallback_current_date'
            result['confidence'] = 0.1
        
        return result
    
    def _extract_from_content(self, content: str) -> Dict[str, Any]:
        """从文档内容中提取日期"""
        if not content:
            return {'date': None, 'confidence': 0.0, 'raw_date': None}
        
        # 查找关键词附近的日期
        content_lines = content.split('\n')
        best_date = None
        best_confidence = 0.0
        raw_date = None
        
        for line in content_lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否包含日期关键词
            has_keyword = any(keyword in line for keyword in self.chinese_date_keywords)
            
            # 在该行中查找日期
            dates = self._find_dates_in_text(line)
            
            for date_obj, pattern_confidence, match_text in dates:
                confidence = pattern_confidence
                if has_keyword:
                    confidence += 0.3  # 如果有关键词，增加置信度
                
                if confidence > best_confidence:
                    best_date = date_obj
                    best_confidence = confidence
                    raw_date = match_text
        
        # 如果没有找到关键词附近的日期，在整个内容中查找
        if not best_date:
            all_dates = self._find_dates_in_text(content[:1000])  # 限制搜索范围
            if all_dates:
                best_date, best_confidence, raw_date = all_dates[0]  # 取第一个找到的日期
        
        if best_date:
            formatted_date = best_date.strftime(self.date_format)
            return {
                'date': formatted_date,
                'confidence': min(best_confidence, 1.0),
                'raw_date': raw_date
            }
        
        return {'date': None, 'confidence': 0.0, 'raw_date': None}
    
    def _extract_from_file_creation(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """从文件创建时间提取日期"""
        creation_time = file_info.get('creation_time')
        if creation_time:
            formatted_date = creation_time.strftime(self.date_format)
            return {
                'date': formatted_date,
                'confidence': 0.7,
                'raw_date': creation_time.isoformat()
            }
        return {'date': None, 'confidence': 0.0, 'raw_date': None}
    
    def _extract_from_file_modification(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """从文件修改时间提取日期"""
        modification_time = file_info.get('modification_time')
        if modification_time:
            formatted_date = modification_time.strftime(self.date_format)
            return {
                'date': formatted_date,
                'confidence': 0.6,
                'raw_date': modification_time.isoformat()
            }
        return {'date': None, 'confidence': 0.0, 'raw_date': None}
    
    def _extract_current_date(self) -> Dict[str, Any]:
        """使用当前日期"""
        current_time = datetime.now()
        formatted_date = current_time.strftime(self.date_format)
        return {
            'date': formatted_date,
            'confidence': 0.5,
            'raw_date': current_time.isoformat()
        }
    
    def _find_dates_in_text(self, text: str) -> List[tuple]:
        """在文本中查找所有日期"""
        dates = []
        
        for i, pattern in enumerate(self.date_patterns):
            matches = re.finditer(pattern, text)
            
            for match in matches:
                try:
                    date_obj = self._parse_date_match(match, i)
                    if date_obj:
                        # 根据模式类型设置置信度
                        confidence = self._get_pattern_confidence(i)
                        dates.append((date_obj, confidence, match.group(0)))
                except Exception as e:
                    self.logger.debug(f"解析日期匹配失败: {e}")
                    continue
        
        # 按置信度排序
        dates.sort(key=lambda x: x[1], reverse=True)
        return dates
    
    def _parse_date_match(self, match: re.Match, pattern_index: int) -> Optional[datetime]:
        """解析日期匹配结果"""
        groups = match.groups()
        
        try:
            if pattern_index == 0:  # YYYY-MM-DD
                year, month, day = map(int, groups)
                return datetime(year, month, day)
            
            elif pattern_index == 1:  # YYYY年MM月DD日
                year, month, day = map(int, groups)
                return datetime(year, month, day)
            
            elif pattern_index == 2:  # MM/DD/YYYY
                month, day, year = map(int, groups)
                return datetime(year, month, day)
            
            elif pattern_index == 3:  # DD.MM.YYYY
                day, month, year = map(int, groups)
                return datetime(year, month, day)
            
            elif pattern_index == 4:  # YYYYMMDD
                date_str = groups[0]
                if len(date_str) == 8:
                    year = int(date_str[:4])
                    month = int(date_str[4:6])
                    day = int(date_str[6:8])
                    return datetime(year, month, day)
            
        except (ValueError, IndexError) as e:
            self.logger.debug(f"日期解析错误: {e}")
            return None
        
        return None
    
    def _get_pattern_confidence(self, pattern_index: int) -> float:
        """根据模式类型获取置信度"""
        confidence_map = {
            0: 0.9,  # YYYY-MM-DD (最标准)
            1: 0.9,  # YYYY年MM月DD日 (中文标准)
            2: 0.7,  # MM/DD/YYYY (美式)
            3: 0.7,  # DD.MM.YYYY (欧式)
            4: 0.8,  # YYYYMMDD (紧凑)
        }
        return confidence_map.get(pattern_index, 0.5)
    
    def validate_date(self, date_str: str) -> bool:
        """验证日期字符串是否有效"""
        try:
            datetime.strptime(date_str, self.date_format)
            return True
        except ValueError:
            return False
    
    def format_date(self, date_obj: datetime) -> str:
        """格式化日期对象"""
        return date_obj.strftime(self.date_format) 