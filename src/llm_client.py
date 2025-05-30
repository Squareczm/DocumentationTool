"""
LLM客户端
负责与大语言模型API进行交互，提取文档主体、建议文件夹等
"""

import json
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import re
import os
from pathlib import Path
import yaml


class LLMClient:
    """大语言模型客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化LLM客户端
        
        Args:
            config: 包含LLM配置的字典
        """
        self.config = config.get('llm', {})
        self.enabled = self.config.get('enabled', True)  # 默认启用
        self.logger = logging.getLogger(__name__)
        
        # 加载分类规则配置
        self.classification_rules = self._load_classification_rules()
        
        # API密钥获取优先级：config.yaml > 环境变量
        api_key = self.config.get('api_key')
        if not api_key:
            api_key = os.getenv('SMARTFILEORG_LLM_API_KEY')
        
        if not api_key:
            self.logger.warning("未找到API密钥，请在config.yaml中配置api_key或设置环境变量SMARTFILEORG_LLM_API_KEY")
            self.enabled = False
        else:
            self.config['api_key'] = api_key
            self.logger.info(f"LLM客户端已启用，使用提供商: {self.config.get('provider', 'openai')}")
    
    def _load_classification_rules(self) -> Dict[str, Any]:
        """加载分类规则配置"""
        try:
            rules_file = Path("config/classification_rules.yaml")
            if rules_file.exists():
                with open(rules_file, 'r', encoding='utf-8') as f:
                    rules = yaml.safe_load(f)
                self.logger.info("成功加载分类规则配置")
                return rules
            else:
                self.logger.warning("分类规则配置文件不存在，使用默认规则")
                return self._get_default_classification_rules()
        except Exception as e:
            self.logger.error(f"加载分类规则失败: {e}")
            return self._get_default_classification_rules()
    
    def _get_default_classification_rules(self) -> Dict[str, Any]:
        """获取默认分类规则"""
        return {
            'classification_rules': {
                '技术开发': {
                    'keywords': ['技术', '开发', '系统', '软件', 'tech', 'dev'],
                    'target_patterns': ['技术', '开发'],
                    'priority': 1
                },
                '项目管理': {
                    'keywords': ['项目', '管理', 'project'],
                    'target_patterns': ['项目', '管理'],
                    'priority': 2
                },
                '会议沟通': {
                    'keywords': ['会议', '纪要', 'meeting'],
                    'target_patterns': ['会议', '沟通'],
                    'priority': 3
                }
            },
            'fallback_folders': ['文档', '其他', 'documents'],
            'strategy': {
                'semantic_threshold': 0.3,
                'allow_new_folders': False,
                'force_existing': True
            }
        }
    
    def extract_subject_and_folder(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取文档主体并建议文件夹路径
        
        Args:
            file_info: 文件信息字典
            
        Returns:
            包含主体和建议文件夹路径的字典
        """
        if not self.enabled:
            return {
                'subject': self._extract_fallback_subject(file_info),
                'suggested_folder': '',
                'confidence': 0.0,
                'reasoning': '未配置LLM API，使用回退方案'
            }
        
        try:
            # 构建提示词
            prompt = self._build_subject_extraction_prompt(file_info)
            
            # 调用LLM API
            response = self._call_llm_api(prompt)
            
            # 解析响应
            result = self._parse_subject_response(response)
            
            self.logger.info(f"LLM提取主体成功: {result['subject']}")
            return result
            
        except Exception as e:
            self.logger.error(f"LLM提取主体失败: {e}")
            return {
                'subject': self._extract_fallback_subject(file_info),
                'suggested_folder': '',
                'confidence': 0.0,
                'reasoning': f'LLM调用失败: {str(e)}'
            }
    
    def check_content_similarity(self, content1: str, content2: str) -> Dict[str, Any]:
        """
        检查两个文档内容的相似性
        
        Args:
            content1: 第一个文档内容
            content2: 第二个文档内容
            
        Returns:
            相似性分析结果
        """
        if not self.enabled:
            return {
                'is_similar': False,
                'similarity_score': 0.0,
                'reasoning': '未配置LLM API'
            }
        
        try:
            prompt = self._build_similarity_prompt(content1, content2)
            response = self._call_llm_api(prompt)
            result = self._parse_similarity_response(response)
            
            self.logger.info(f"内容相似性检查完成: {result['similarity_score']}")
            return result
            
        except Exception as e:
            self.logger.error(f"相似性检查失败: {e}")
            return {
                'is_similar': False,
                'similarity_score': 0.0,
                'reasoning': f'LLM调用失败: {str(e)}'
            }
    
    def suggest_folder_structure(self, subject: str, existing_folders: List[str]) -> Dict[str, Any]:
        """
        基于主体和现有文件夹建议合适的文件夹结构
        
        Args:
            subject: 文档主体
            existing_folders: 现有文件夹列表
            
        Returns:
            文件夹建议结果
        """
        if not self.enabled:
            return {
                'suggested_path': subject,
                'create_new': True,
                'reasoning': '未配置LLM API，使用主体作为文件夹名'
            }
        
        try:
            self.logger.info(f"开始文件夹建议 - 主体: {subject}")
            
            # 重新扫描文件夹结构，确保获取最新的手动修改
            refreshed_folders = self._scan_current_folders()
            combined_folders = list(set(existing_folders + refreshed_folders))
            self.logger.info(f"合并后的文件夹列表: {combined_folders}")
            
            # 第一步：尝试精确文本匹配
            exact_match = self._find_exact_folder_match(subject, combined_folders)
            if exact_match:
                self.logger.info(f"找到精确匹配，返回: {exact_match}")
                return {
                    'suggested_path': exact_match,
                    'create_new': False,
                    'reasoning': f'找到精确匹配的文件夹: {exact_match}'
                }
            
            # 第二步：使用配置化语义分析匹配
            semantic_match = self._find_semantic_folder_match(subject, combined_folders)
            if semantic_match:
                self.logger.info(f"找到语义匹配，返回: {semantic_match}")
                return {
                    'suggested_path': semantic_match,
                    'create_new': False,
                    'reasoning': f'通过语义分析找到匹配的文件夹: {semantic_match}'
                }
            
            # 第二步补充：如果语义匹配找到了类别但没有对应现有文件夹，创建新文件夹
            semantic_category = self._find_semantic_category_match(subject)
            if semantic_category:
                self.logger.info(f"语义分析找到类别但无现有文件夹，创建新文件夹: {semantic_category}")
                return {
                    'suggested_path': semantic_category,
                    'create_new': True,
                    'reasoning': f'通过语义分析创建新类别文件夹: {semantic_category}'
                }
            
            # 第三步：尝试相似性匹配
            similar_match = self._find_similar_folder_match(subject, combined_folders)
            if similar_match:
                self.logger.info(f"找到相似匹配，返回: {similar_match}")
                return {
                    'suggested_path': similar_match,
                    'create_new': False,
                    'reasoning': f'找到相似匹配的文件夹: {similar_match}'
                }
            
            self.logger.info("未找到精确、语义或相似匹配，调用LLM")
            
            # 第四步：如果没有找到匹配，调用LLM进行智能建议
            prompt = self._build_strict_folder_suggestion_prompt(subject, combined_folders)
            response = self._call_llm_api(prompt)
            result = self._parse_folder_response(response)
            
            self.logger.info(f"LLM原始响应结果: {result}")
            
            # 验证LLM建议的路径是否确实存在
            if not result.get('create_new', True):
                suggested_path = result.get('suggested_path', '')
                # 统一路径分隔符进行比较
                normalized_suggested = suggested_path.replace('\\', '/')
                normalized_folders = [f.replace('\\', '/') for f in combined_folders]
                
                if normalized_suggested not in normalized_folders:
                    self.logger.warning(f"LLM建议的路径不存在: {suggested_path}，改为创建新文件夹")
                    result['create_new'] = True
                    result['reasoning'] = f"LLM建议的路径不存在，改为创建: {suggested_path}"
                else:
                    self.logger.info(f"LLM建议的路径验证通过: {suggested_path}")
            
            # 第五步：如果LLM试图创建新文件夹，进行最终处理
            if result.get('create_new', True):
                # 如果没有任何现有文件夹，允许创建语义匹配的分类文件夹
                if not combined_folders:
                    semantic_category = self._find_semantic_category_match(subject)
                    if semantic_category:
                        self.logger.info(f"无现有文件夹时，允许创建语义分类文件夹: {semantic_category}")
                        result = {
                            'suggested_path': semantic_category,
                            'create_new': True,
                            'reasoning': f'无现有文件夹，创建语义分类文件夹: {semantic_category}'
                        }
                    else:
                        self.logger.info(f"无语义匹配，使用主体作为文件夹名: {subject}")
                        result = {
                            'suggested_path': subject,
                            'create_new': True,
                            'reasoning': f'无现有文件夹和语义匹配，使用主体名称: {subject}'
                        }
                else:
                    # 有现有文件夹但LLM试图创建新文件夹，强制选择现有分类
                    self.logger.warning("LLM试图创建新文件夹，启动强制匹配")
                    forced_match = self._force_existing_folder_match(subject, combined_folders)
                    if forced_match:
                        result = {
                            'suggested_path': forced_match,
                            'create_new': False,
                            'reasoning': f'强制使用现有文件夹: {forced_match}（LLM试图创建新文件夹）'
                        }
                        self.logger.warning(f"LLM试图创建新文件夹，强制使用现有分类: {forced_match}")
                    else:
                        # 如果强制匹配也失败，允许创建语义分类文件夹
                        semantic_category = self._find_semantic_category_match(subject)
                        if semantic_category:
                            self.logger.info(f"强制匹配失败，创建语义分类文件夹: {semantic_category}")
                            result = {
                                'suggested_path': semantic_category,
                                'create_new': True,
                                'reasoning': f'强制匹配失败，创建语义分类文件夹: {semantic_category}'
                            }
            
            self.logger.info(f"文件夹建议完成: {result['suggested_path']}")
            return result
            
        except Exception as e:
            self.logger.error(f"文件夹建议失败: {e}")
            return {
                'suggested_path': subject,
                'create_new': True,
                'reasoning': f'LLM调用失败: {str(e)}'
            }
    
    def _scan_current_folders(self) -> List[str]:
        """实时扫描当前知识库文件夹结构"""
        folders = []
        try:
            kb_path = Path("knowledge_base")
            if kb_path.exists():
                for root, dirs, files in os.walk(kb_path):
                    for dir_name in dirs:
                        full_path = Path(root) / dir_name
                        relative_path = full_path.relative_to(kb_path)
                        folders.append(str(relative_path))
        except Exception as e:
            self.logger.warning(f"扫描文件夹失败: {e}")
        return folders
    
    def _serialize_metadata_safely(self, metadata: Dict[str, Any]) -> str:
        """安全地序列化metadata，处理datetime对象"""
        if not metadata:
            return '无'
        
        safe_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, datetime):
                safe_metadata[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            elif hasattr(value, '__str__'):
                safe_metadata[key] = str(value)
            else:
                safe_metadata[key] = value
                
        try:
            return json.dumps(safe_metadata, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.warning(f"序列化metadata失败: {e}")
            return str(safe_metadata)
    
    def _build_subject_extraction_prompt(self, file_info: Dict[str, Any]) -> str:
        """构建主体提取提示词"""
        content = file_info.get('content', '')[:3000]  # 限制内容长度
        metadata = file_info.get('metadata', {})
        
        prompt = f"""
请分析以下文档内容，提取核心主体并建议合适的文件夹路径。

文件名: {file_info['name']}
文件类型: {file_info['suffix']}

元数据信息:
{self._serialize_metadata_safely(metadata)}

文档内容:
{content}

**重要说明：请严格按照JSON格式返回结果，不要添加任何额外的文字说明**

{{
    "subject": "文档的核心主体，用作重命名的基础（简洁明了，适合作为文件名）",
    "suggested_folder": "建议的文件夹路径（如果需要多层级，用/分隔）",
    "confidence": 0.85,
    "reasoning": "提取主体和建议文件夹的理由"
}}

文件夹建议原则：
1. 优先按主题分类：会议纪要、项目文档、技术方案、财务报告、人力资源等
2. 避免为每个文档创建单独文件夹，应归类到合适的主题文件夹
3. 文件夹名称简洁清晰，避免过长
4. 考虑文档的业务类型和用途
"""
        return prompt
    
    def _build_similarity_prompt(self, content1: str, content2: str) -> str:
        """构建相似性检查提示词"""
        # 限制内容长度避免超出token限制
        content1 = content1[:2000]
        content2 = content2[:2000]
        
        prompt = f"""
请比较以下两个文档内容的相似性，判断它们是否可能是同一主题的不同版本。

文档1内容:
{content1}

文档2内容:
{content2}

请以JSON格式返回结果：
{{
    "is_similar": true/false,
    "similarity_score": 相似度分数(0-1),
    "reasoning": "相似性判断的理由"
}}

判断标准：
- 如果两个文档讨论的是同一个主题、项目或事件，即使内容有差异也应该被认为是相似的
- 相似度分数应该反映主题相关性而不是文字重复度
- 0.7以上可以认为是同一主题的不同版本
"""
        return prompt
    
    def _build_strict_folder_suggestion_prompt(self, subject: str, existing_folders: List[str]) -> str:
        """构建严格的文件夹建议提示词"""
        existing_str = "\n".join(f"- {folder}" for folder in existing_folders) if existing_folders else "暂无现有文件夹"
        
        # 读取知识库结构文件
        structure_content = self._read_knowledge_base_structure()
        
        prompt = f"""
请为文档主体"{subject}"建议合适的文件夹归档路径。

**当前知识库文件夹结构参考：**
{structure_content}

**现有文件夹完整列表：**
{existing_str}

**绝对严格要求（违反将导致处理失败）：**
1. **suggested_path必须完全等于现有文件夹列表中的某一项**
2. **绝对禁止创建任何新文件夹，create_new必须为false**
3. **必须从上述现有文件夹列表中选择最匹配的一个**
4. **如果主体包含"运维"、"监控"、"部署"关键词，必须选择"技术方案/DevOps运维"**
5. **如果主体包含"容器"、"Docker"关键词，必须选择"技术方案/容器化部署"**

**强制选择逻辑（按此优先级执行）：**
- 运维/监控/部署相关 → 强制选择 "技术方案/DevOps运维"
- 容器/Docker相关 → 强制选择 "技术方案/容器化部署"  
- 项目管理相关 → 强制选择 "项目文档/项目管理"
- 会议记录相关 → 强制选择 "会议纪要"
- 培训相关 → 强制选择 "人力资源/培训计划"
- 面试相关 → 强制选择 "人力资源/面试记录"
- 其他技术文档 → 强制选择 "技术方案"

**请严格按照JSON格式返回：**

{{
    "suggested_path": "必须是现有文件夹列表中的完整路径",
    "create_new": false,
    "reasoning": "详细说明为什么选择这个现有文件夹"
}}

**最后检查：返回前确认suggested_path确实在现有文件夹列表中！**
"""
        return prompt
    
    def _read_knowledge_base_structure(self) -> str:
        """读取知识库结构文件"""
        try:
            structure_file = Path("knowledge_base/structure.md")
            if structure_file.exists():
                with open(structure_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 提取文件夹结构部分（从"当前文件夹结构"到"分类规则"）
                start_marker = "## 🗂️ 当前文件夹结构"
                end_marker = "## 📋 分类规则"
                
                start_idx = content.find(start_marker)
                end_idx = content.find(end_marker)
                
                if start_idx != -1 and end_idx != -1:
                    structure_section = content[start_idx:end_idx].strip()
                    return structure_section
                else:
                    return content[:1000]  # 返回前1000字符作为备选
            else:
                return "知识库结构文件不存在，请按标准分类创建文件夹"
        except Exception as e:
            self.logger.warning(f"读取知识库结构失败: {e}")
            return "无法读取知识库结构，请按标准分类创建文件夹"
    
    def _call_llm_api(self, prompt: str) -> str:
        """调用LLM API"""
        provider = self.config.get('provider', 'openai').lower()
        
        if provider == 'openai':
            return self._call_openai_api(prompt)
        elif provider == 'anthropic':
            return self._call_anthropic_api(prompt)
        elif provider == 'zhipu':
            return self._call_zhipu_api(prompt)
        else:
            raise ValueError(f"不支持的LLM提供商: {provider}")
    
    def _call_openai_api(self, prompt: str) -> str:
        """调用OpenAI API"""
        url = self.config.get('base_url', 'https://api.openai.com/v1') + '/chat/completions'
        
        headers = {
            'Authorization': f"Bearer {self.config['api_key']}",
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.config.get('model', 'gpt-3.5-turbo'),
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3,
            'max_tokens': 1000
        }
        
        response = requests.post(
            url, 
            headers=headers, 
            json=data, 
            timeout=self.config.get('timeout', 30)
        )
        
        if response.status_code != 200:
            raise Exception(f"API调用失败: {response.status_code} - {response.text}")
        
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def _call_anthropic_api(self, prompt: str) -> str:
        """调用Anthropic API（Claude）"""
        url = self.config.get('base_url', 'https://api.anthropic.com/v1') + '/messages'
        
        headers = {
            'x-api-key': self.config['api_key'],
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        data = {
            'model': self.config.get('model', 'claude-3-haiku-20240307'),
            'max_tokens': 1000,
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        }
        
        response = requests.post(
            url, 
            headers=headers, 
            json=data, 
            timeout=self.config.get('timeout', 30)
        )
        
        if response.status_code != 200:
            raise Exception(f"API调用失败: {response.status_code} - {response.text}")
        
        result = response.json()
        return result['content'][0]['text']
    
    def _call_zhipu_api(self, prompt: str) -> str:
        """调用智谱AI API"""
        # 这里可以根据智谱AI的实际API实现
        raise NotImplementedError("智谱AI接口尚未实现")
    
    def _parse_subject_response(self, response: str) -> Dict[str, Any]:
        """解析主体提取响应"""
        try:
            # 首先尝试直接解析JSON
            result = json.loads(response.strip())
            
            # 验证必需字段
            if 'subject' not in result:
                raise ValueError("响应中缺少subject字段")
            
            # 清理主体名称，去除不符合文件系统规范的字符
            subject = result.get('subject', '').strip()
            subject = self._clean_filename(subject)
            
            return {
                'subject': subject,
                'suggested_folder': result.get('suggested_folder', '').strip(),
                'confidence': float(result.get('confidence', 0.5)),
                'reasoning': result.get('reasoning', '')
            }
            
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"尝试JSON解析失败: {e}，尝试其他解析方法")
            
            # 尝试提取被```包围的JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(1))
                    subject = self._clean_filename(result.get('subject', ''))
                    if subject:
                        return {
                            'subject': subject,
                            'suggested_folder': result.get('suggested_folder', '').strip(),
                            'confidence': float(result.get('confidence', 0.5)),
                            'reasoning': result.get('reasoning', '')
                        }
                except (json.JSONDecodeError, ValueError):
                    pass
            
            # 尝试查找单独JSON对象
            json_match = re.search(r'\{[^{}]*"subject"[^{}]*\}', response, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(0))
                    subject = self._clean_filename(result.get('subject', ''))
                    if subject:
                        return {
                            'subject': subject,
                            'suggested_folder': result.get('suggested_folder', '').strip(),
                            'confidence': float(result.get('confidence', 0.5)),
                            'reasoning': result.get('reasoning', '')
                        }
                except (json.JSONDecodeError, ValueError):
                    pass
            
            self.logger.warning(f"所有解析方法失败，使用文本提取")
            
            # 简单的文本提取作为最后回退
            lines = response.strip().split('\n')
            subject = ''
            suggested_folder = ''
            
            for line in lines:
                line = line.strip()
                if ('subject' in line.lower() or '主体' in line) and ':' in line:
                    subject = line.split(':')[-1].strip().strip('"\'""''')
                elif ('folder' in line.lower() or '文件夹' in line) and ':' in line:
                    suggested_folder = line.split(':')[-1].strip().strip('"\'""''')
            
            # 如果还是没找到，尝试直接提取文档内容中的标题
            if not subject:
                # 尝试从原始响应中提取可能的主体信息
                potential_subjects = re.findall(r'["\']([^"\']{3,50})["\']', response)
                for ps in potential_subjects:
                    if ps and not any(skip in ps.lower() for skip in ['json', 'format', '格式', '示例']):
                        subject = ps
                        break
            
            # 清理提取的主体名称
            subject = self._clean_filename(subject) if subject else '未知主体'
            
            return {
                'subject': subject,
                'suggested_folder': self._clean_filename(suggested_folder),
                'confidence': 0.3,
                'reasoning': '响应解析失败，使用文本提取'
            }
    
    def _clean_filename(self, name: str) -> str:
        """清理文件名，去除不符合文件系统规范的字符"""
        if not name:
            return name
        
        # 去除首尾的引号和空格
        name = name.strip().strip('"\'""''')
        
        # 替换不符合Windows文件系统规范的字符
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '/', '\\']
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # 去除尾部的点、空格、逗号、下划线等
        name = name.rstrip('.,_ ')
        
        # 限制长度（Windows路径限制）
        if len(name) > 100:
            name = name[:100].rstrip('.,_ ')
        
        return name or '未分类文档'
    
    def _parse_similarity_response(self, response: str) -> Dict[str, Any]:
        """解析相似性检查响应"""
        try:
            result = json.loads(response)
            return {
                'is_similar': bool(result.get('is_similar', False)),
                'similarity_score': float(result.get('similarity_score', 0.0)),
                'reasoning': result.get('reasoning', '')
            }
        except (json.JSONDecodeError, ValueError):
            return {
                'is_similar': False,
                'similarity_score': 0.0,
                'reasoning': '响应解析失败'
            }
    
    def _parse_folder_response(self, response: str) -> Dict[str, Any]:
        """解析文件夹建议响应"""
        try:
            # 首先尝试直接解析JSON
            result = json.loads(response.strip())
            return {
                'suggested_path': result.get('suggested_path', '').strip(),
                'create_new': bool(result.get('create_new', True)),
                'reasoning': result.get('reasoning', '')
            }
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"尝试JSON解析失败: {e}，尝试其他解析方法")
            
            # 尝试提取被```包围的JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(1))
                    return {
                        'suggested_path': result.get('suggested_path', '').strip(),
                        'create_new': bool(result.get('create_new', True)),
                        'reasoning': result.get('reasoning', '')
                    }
                except (json.JSONDecodeError, ValueError):
                    pass
            
            # 尝试查找单独JSON对象
            json_match = re.search(r'\{[^{}]*"suggested_path"[^{}]*\}', response, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(0))
                    return {
                        'suggested_path': result.get('suggested_path', '').strip(),
                        'create_new': bool(result.get('create_new', True)),
                        'reasoning': result.get('reasoning', '')
                    }
                except (json.JSONDecodeError, ValueError):
                    pass
            
            # 文本提取作为回退
            lines = response.strip().split('\n')
            suggested_path = ''
            reasoning = ''
            
            for line in lines:
                line = line.strip()
                if ('path' in line.lower() or '路径' in line or '文件夹' in line) and ':' in line:
                    suggested_path = line.split(':')[-1].strip().strip('"\'""''')
                elif ('reason' in line.lower() or '理由' in line) and ':' in line:
                    reasoning = line.split(':')[-1].strip().strip('"\'""''')
            
            # 如果还是没找到，尝试从响应中提取可能的路径
            if not suggested_path:
                # 查找可能的文件夹路径
                folder_patterns = [
                    r'会议纪要', r'项目文档', r'技术文档', r'财务报告', r'人力资源',
                    r'管理制度', r'客户资料', r'培训材料', r'技术方案', r'项目管理'
                ]
                for pattern in folder_patterns:
                    if re.search(pattern, response, re.IGNORECASE):
                        suggested_path = pattern
                        break
            
            return {
                'suggested_path': self._clean_filename(suggested_path),
                'create_new': True,
                'reasoning': reasoning or '响应解析失败，使用文本提取'
            }
    
    def _extract_fallback_subject(self, file_info: Dict[str, Any]) -> str:
        """提取主体的回退方案（不依赖LLM）"""
        # 优先使用文档元数据中的标题
        metadata = file_info.get('metadata', {})
        if metadata.get('title'):
            return metadata['title']
        
        # 使用文件名（去掉扩展名）
        stem = file_info.get('stem', '')
        if stem:
            return stem
        
        # 最后的回退
        return '未分类文档'
    
    def _find_exact_folder_match(self, subject: str, folders: List[str]) -> Optional[str]:
        """查找精确匹配的文件夹 - 基于文本直接匹配"""
        subject_lower = subject.lower()
        self.logger.info(f"精确匹配检查 - 主体: {subject_lower}")
        self.logger.info(f"可用文件夹: {folders}")
        
        # 直接文本包含匹配
        for folder_path in folders:
            folder_name = folder_path.split('/')[-1].lower()
            
            # 检查文件夹名是否包含在主体中，或主体包含文件夹名
            if folder_name in subject_lower or any(word in folder_name for word in subject_lower.split()):
                self.logger.info(f"直接文本匹配: {folder_path}")
                return folder_path
        
        self.logger.info("未找到精确匹配")
        return None
    
    def _find_semantic_folder_match(self, subject: str, folders: List[str]) -> Optional[str]:
        """基于语义相似性的文件夹匹配 - 使用配置化规则"""
        # 获取分类规则和策略配置
        rules = self.classification_rules.get('classification_rules', {})
        strategy = self.classification_rules.get('strategy', {})
        threshold = strategy.get('semantic_threshold', 0.3)
        
        # 计算每个语义类别的匹配分数
        category_scores = {}
        
        for category, info in rules.items():
            keywords = info.get('keywords', [])
            priority = info.get('priority', 10)
            
            # 关键词匹配计分
            matched_keywords = 0
            for keyword in keywords:
                if keyword.lower() in subject.lower():
                    matched_keywords += 1
            
            # 计算归一化分数（不考虑优先级，优先级仅用于最终选择）
            if matched_keywords > 0:
                normalized_score = matched_keywords / len(keywords)
                category_scores[category] = {
                    'score': normalized_score,
                    'priority': priority,
                    'matched_keywords': matched_keywords
                }
        
        # 过滤低于阈值的分数
        valid_categories = {k: v for k, v in category_scores.items() if v['score'] >= threshold}
        
        if not valid_categories:
            self.logger.info(f"没有类别达到阈值 {threshold}")
            return None
        
        # 在有效类别中，优先选择分数最高的，分数相同时选择优先级最高的（数字最小）
        best_category = max(valid_categories.items(), 
                          key=lambda x: (x[1]['score'], -x[1]['priority']))
        
        best_category_name = best_category[0]
        best_info = best_category[1]
        best_patterns = rules[best_category_name].get('target_patterns', [])
        
        self.logger.info(f"最佳语义类别: {best_category_name}, 分数: {best_info['score']:.3f}, 优先级: {best_info['priority']}")
        
        # 在现有文件夹中寻找匹配该语义类别的文件夹
        for pattern in best_patterns:
            for folder_path in folders:
                if pattern in folder_path:
                    self.logger.info(f"语义匹配成功 - 类别: {best_category_name}, 模式: {pattern}, 文件夹: {folder_path}")
                    return folder_path
        
        return None
    
    def _find_similar_folder_match(self, subject: str, folders: List[str]) -> Optional[str]:
        """查找相似的文件夹（基于编辑距离或包含关系）"""
        subject_lower = subject.lower()
        
        # 检查是否有文件夹名包含在主体中，或主体包含文件夹名
        best_match = None
        best_score = 0
        
        for folder_path in folders:
            folder_name = folder_path.split('/')[-1].lower()  # 获取文件夹名称
            
            # 计算相似度分数
            score = 0
            
            # 包含关系检查
            if folder_name in subject_lower or subject_lower in folder_name:
                score += 0.8
            
            # 关键词重叠检查
            subject_words = set(subject_lower.split())
            folder_words = set(folder_name.split())
            if subject_words & folder_words:  # 有交集
                score += 0.6
            
            # 如果分数足够高，记录为最佳匹配
            if score > best_score and score >= 0.6:
                best_score = score
                best_match = folder_path
        
        return best_match 
    
    def _force_existing_folder_match(self, subject: str, folders: List[str]) -> Optional[str]:
        """强制从现有文件夹中选择一个匹配的 - 通用分类策略"""
        subject_lower = subject.lower()
        
        # 第一步：尝试语义匹配
        semantic_match = self._find_semantic_folder_match(subject_lower, folders)
        if semantic_match:
            return semantic_match
        
        # 第二步：基于通用分类策略的强制分配
        # 优先级从高到低的通用分类
        generic_classification_rules = [
            # 技术相关
            {
                'keywords': ['技术', '开发', '系统', '软件', '代码', '程序', '工程', 'tech', 'dev'],
                'target_patterns': ['技术', '开发', '工程', 'tech']
            },
            # 管理相关
            {
                'keywords': ['管理', '项目', '计划', '规划', '策略', 'management', 'project'],
                'target_patterns': ['项目', '管理', 'project']
            },
            # 业务相关
            {
                'keywords': ['业务', '流程', '规范', '标准', '需求', 'business'],
                'target_patterns': ['业务', '流程', 'business']
            },
            # 人事相关
            {
                'keywords': ['人事', '人力', '员工', '招聘', '培训', '面试', 'hr'],
                'target_patterns': ['人力资源', '人事', 'hr', '培训']
            },
            # 财务相关
            {
                'keywords': ['财务', '预算', '成本', '费用', '报告', 'finance'],
                'target_patterns': ['财务', 'finance', '报告']
            },
            # 会议交流相关
            {
                'keywords': ['会议', '纪要', '讨论', '沟通', 'meeting'],
                'target_patterns': ['会议', 'meeting', '沟通']
            },
            # 学习成长相关
            {
                'keywords': ['学习', '成长', '知识', '教育', '哲学', '思考'],
                'target_patterns': ['学习', '成长', '知识', '教育']
            }
        ]
        
        # 按规则检查并分配
        for rule in generic_classification_rules:
            # 检查主体是否包含该分类的关键词
            if any(keyword in subject_lower for keyword in rule['keywords']):
                # 在现有文件夹中寻找匹配的模式
                for pattern in rule['target_patterns']:
                    for folder_path in folders:
                        if pattern in folder_path:
                            self.logger.info(f"通用分类匹配 - 关键词: {rule['keywords']}, 模式: {pattern}, 文件夹: {folder_path}")
                            return folder_path
        
        # 第三步：如果还是没有匹配，使用最通用的策略
        return self._get_most_generic_folder(folders)
    
    def _get_most_generic_folder(self, folders: List[str]) -> Optional[str]:
        """获取最通用的文件夹作为回退方案 - 使用配置化回退列表"""
        # 从配置中获取回退文件夹列表
        fallback_list = self.classification_rules.get('fallback_folders', [
            '文档', '资料', '其他', '未分类', '通用', 'documents', 'files', 'misc'
        ])
        
        # 寻找最通用的文件夹
        for priority_name in fallback_list:
            for folder_path in folders:
                if priority_name.lower() in folder_path.lower():
                    self.logger.info(f"使用配置化回退文件夹: {folder_path}")
                    return folder_path
        
        # 如果还是没有，使用第一个顶级文件夹
        top_level_folders = [f for f in folders if '/' not in f and '\\' not in f]
        if top_level_folders:
            result = top_level_folders[0]
            self.logger.info(f"使用第一个顶级文件夹: {result}")
            return result
        
        # 最后的回退：使用第一个可用文件夹
        if folders:
            result = folders[0]
            self.logger.info(f"使用第一个可用文件夹: {result}")
            return result
        
        return None
    
    def _find_semantic_category_match(self, subject: str) -> Optional[str]:
        """基于语义相似性找到分类类别（不依赖现有文件夹）"""
        if not self.classification_rules:
            return None
        
        try:
            # 读取配置文件获取最新规则
            import yaml
            from pathlib import Path
            
            rules_file = Path("config/classification_rules.yaml")
            if rules_file.exists():
                with open(rules_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                rules = config.get('classification_rules', {})
            else:
                rules = self.classification_rules
                
        except Exception as e:
            self.logger.warning(f"读取分类规则失败，使用内存中的规则: {e}")
            rules = self.classification_rules
        
        subject_lower = subject.lower()
        threshold = 0.02  # 降低阈值
        
        # 计算每个类别的匹配分数
        category_scores = {}
        
        for category_name, category_info in rules.items():
            keywords = category_info.get('keywords', [])
            priority = category_info.get('priority', 99)
            
            # 计算关键词匹配分数 - 进一步改进算法
            matched_keywords = 0
            total_keyword_score = 0
            high_confidence_matches = 0
            partial_matches = 0
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                match_score = 0
                
                # 1. 完全匹配检查
                if keyword_lower == subject_lower:
                    match_score = 1.0
                    high_confidence_matches += 1
                # 2. 完整包含匹配
                elif keyword_lower in subject_lower:
                    match_score = 0.9 if len(keyword_lower) >= 4 else 0.7
                    high_confidence_matches += 1
                # 3. 反向包含匹配（主体包含在关键词中）
                elif subject_lower in keyword_lower:
                    match_score = 0.8
                    high_confidence_matches += 1
                # 4. 部分单词匹配
                else:
                    # 检查关键词的单词是否在主体中
                    keyword_words = set(keyword_lower.split())
                    subject_words = set(subject_lower.split())
                    
                    if keyword_words & subject_words:  # 有交集
                        overlap_ratio = len(keyword_words & subject_words) / len(keyword_words)
                        if overlap_ratio >= 0.6:  # 60%以上单词匹配
                            match_score = 0.6 * overlap_ratio
                            partial_matches += 1
                        elif overlap_ratio >= 0.3:  # 30%以上单词匹配
                            match_score = 0.4 * overlap_ratio
                            partial_matches += 1
                
                if match_score > 0:
                    matched_keywords += 1
                    total_keyword_score += match_score
            
            # 归一化分数：基于匹配的关键词数量和质量
            if matched_keywords > 0:
                # 基础分数：平均匹配分数
                base_score = total_keyword_score / len(keywords)
                
                # 奖励机制
                coverage_bonus = min(matched_keywords / len(keywords), 0.4)  # 关键词覆盖奖励
                confidence_bonus = min(high_confidence_matches * 0.15, 0.3)  # 高置信度奖励
                partial_bonus = min(partial_matches * 0.05, 0.1)  # 部分匹配奖励
                
                # 特殊类别优先级奖励
                priority_bonus = 0
                if category_name in ['技术开发', '个人财务', '学习成长']:
                    priority_bonus = 0.1
                elif category_name in ['项目管理', '运维管理']:
                    priority_bonus = 0.05
                
                # 长关键词奖励（更具体的关键词给予奖励）
                long_keyword_bonus = 0
                for keyword in keywords:
                    if len(keyword) >= 6 and keyword.lower() in subject_lower:
                        long_keyword_bonus += 0.05
                long_keyword_bonus = min(long_keyword_bonus, 0.2)
                
                final_score = base_score + coverage_bonus + confidence_bonus + partial_bonus + priority_bonus + long_keyword_bonus
                
                if final_score >= threshold:
                    category_scores[category_name] = {
                        'score': final_score,
                        'priority': priority,
                        'matched_keywords': matched_keywords,
                        'high_confidence': high_confidence_matches,
                        'partial_matches': partial_matches
                    }
        
        if not category_scores:
            return None
        
        # 选择最佳匹配：优先按分数，然后按优先级
        best_category_name, best_info = max(
            category_scores.items(),
            key=lambda x: (x[1]['score'], -x[1]['priority'])
        )
        
        # 获取该类别的第一个目标模式作为文件夹名
        target_patterns = rules[best_category_name].get('target_patterns', [])
        if target_patterns:
            folder_name = target_patterns[0]  # 使用第一个模式
            
            self.logger.info(f"语义类别匹配 - 类别: {best_category_name}, 分数: {best_info['score']:.3f}, 优先级: {best_info['priority']}, 建议文件夹: {folder_name}")
            return folder_name
        
        return None 