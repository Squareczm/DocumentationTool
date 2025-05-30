#!/usr/bin/env python3
"""
知识库结构管理器
负责维护和更新knowledge_base/structure.md文件
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set


class StructureManager:
    """知识库结构管理器"""
    
    def __init__(self, knowledge_base_path: Path):
        """
        初始化结构管理器
        
        Args:
            knowledge_base_path: 知识库根目录路径
        """
        self.kb_path = Path(knowledge_base_path)
        self.structure_file = self.kb_path / "structure.md"
        self.logger = logging.getLogger(__name__)
    
    def update_structure(self):
        """更新知识库结构文件"""
        try:
            # 确保知识库目录存在
            self.kb_path.mkdir(exist_ok=True)
            
            # 扫描当前文件夹结构
            folder_structure = self._scan_folder_structure()
            
            # 统计信息
            stats = self._calculate_stats()
            
            # 生成新的结构文件内容
            content = self._generate_structure_content(folder_structure, stats)
            
            # 写入文件
            self.structure_file.write_text(content, encoding='utf-8')
            
            self.logger.info(f"知识库结构文件已更新: {self.structure_file}")
            
        except Exception as e:
            self.logger.error(f"更新知识库结构失败: {e}")
    
    def ensure_structure_file_exists(self):
        """确保结构文件存在，如果不存在则创建"""
        if not self.structure_file.exists():
            self.logger.info("结构文件不存在，创建初始结构文件...")
            self.update_structure()
    
    def _scan_folder_structure(self) -> Dict[str, Dict]:
        """扫描知识库文件夹结构"""
        structure = {}
        
        if not self.kb_path.exists():
            return structure
        
        # 遍历一级文件夹
        for item in self.kb_path.iterdir():
            if item.is_dir() and item.name != '.git':
                category_name = item.name
                structure[category_name] = {
                    'path': str(item.relative_to(self.kb_path)),
                    'subfolders': self._scan_subfolders(item),
                    'description': self._get_category_description(category_name)
                }
        
        return structure
    
    def _scan_subfolders(self, parent_path: Path, level: int = 1, max_level: int = 3) -> Dict:
        """递归扫描子文件夹"""
        subfolders = {}
        
        if level > max_level:
            return subfolders
        
        for item in parent_path.iterdir():
            if item.is_dir():
                folder_name = item.name
                rel_path = str(item.relative_to(self.kb_path))
                
                # 计算文件夹中的文档数量
                file_count = self._count_files_in_folder(item)
                
                subfolders[folder_name] = {
                    'path': rel_path,
                    'file_count': file_count,
                    'subfolders': self._scan_subfolders(item, level + 1, max_level) if level < max_level else {},
                    'description': self._get_folder_description(folder_name, rel_path)
                }
        
        return subfolders
    
    def _count_files_in_folder(self, folder_path: Path) -> int:
        """计算文件夹中的文件数量"""
        count = 0
        try:
            for item in folder_path.rglob('*'):
                if item.is_file() and not item.name.startswith('.') and item.name != 'structure.md':
                    count += 1
        except Exception:
            pass
        return count
    
    def _get_category_description(self, category_name: str) -> str:
        """获取分类描述 - 基于配置化规则"""
        try:
            import yaml
            from pathlib import Path
            
            rules_file = Path("config/classification_rules.yaml")
            if rules_file.exists():
                with open(rules_file, 'r', encoding='utf-8') as f:
                    rules = yaml.safe_load(f)
                
                classification_rules = rules.get('classification_rules', {})
                
                # 查找匹配的分类规则
                for category, info in classification_rules.items():
                    target_patterns = info.get('target_patterns', [])
                    if category_name in target_patterns or any(pattern in category_name for pattern in target_patterns):
                        keywords = info.get('keywords', [])
                        priority = info.get('priority', 99)
                        return f"{category} - 关键词: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''} (优先级: {priority})"
                        
        except Exception as e:
            self.logger.warning(f"读取配置规则失败: {e}")
        
        # 回退到默认描述
        default_descriptions = {
            '个人成长': '个人发展、人生感悟类内容',
            '人力资源': 'HR相关：培训、面试、员工管理等',
            '会议纪要': '各类会议记录和纪要',
            '技术方案': '技术文档、方案设计、技术研究等',
            '财务报告': '财务相关的报告和分析',
            '项目文档': '具体项目的相关文档',
            '技术开发': '开发、编程、系统架构相关',
            '运维管理': '运维、部署、监控相关',
            '项目管理': '项目计划、管理、策略相关',
            '业务流程': '业务需求、流程、规范相关',
            '财务管理': '财务、预算、成本相关',
            '会议沟通': '会议纪要、讨论、沟通相关',
            '法律合规': '法律、合同、合规相关',
            '产品设计': '产品、设计、用户体验相关',
            '营销推广': '营销、推广、市场相关',
            '学习成长': '学习、成长、知识相关',
            '个人财务': '个人理财、记账、投资相关',
            '生活记录': '日记、生活感悟、个人记录',
            '健康医疗': '健康、医疗、体检相关',
            '旅行出行': '旅行、旅游、出行攻略',
            '兴趣爱好': '个人兴趣、收藏、娱乐',
            '家庭生活': '家庭、亲情、育儿相关',
            '求职职业': '求职、简历、职业规划',
            '教育培训': '教育、课程、培训相关',
            '创作写作': '创作、写作、文章相关'
        }
        return default_descriptions.get(category_name, '相关文档和资料')
    
    def _get_folder_description(self, folder_name: str, full_path: str) -> str:
        """获取文件夹描述"""
        # 基于文件夹名称和路径推断描述
        descriptions = {
            '人生哲学': '人生感悟、哲学思考类文档',
            '入职培训': '员工入职培训相关文档',
            '咨询顾问': '面试记录和反馈',
            'AI培训': 'AI相关培训会议记录或培训材料',
            '产品开发': '产品开发相关会议纪要',
            'AI前沿研究': '前沿AI技术研究和分析',
            'AI工具应用': 'AI工具使用和应用案例',
            'AI应用': 'AI应用场景和案例',
            'AI技术': 'AI技术分析和评论',
            'AI研究': 'AI技术研究报告',
            '推荐系统': '推荐系统相关技术方案',
            '服务器搭建': '服务器搭建和部署指南',
            'WordPress': 'WordPress服务器配置文档',
            '季度报告': '季度财务分析报告',
            '人机协作': 'AI开发和人机协作项目',
            'LLM Native': 'LLM原生技术方案',
            '零代码项目': '零代码游戏开发项目'
        }
        
        return descriptions.get(folder_name, f'{folder_name}相关文档')
    
    def _calculate_stats(self) -> Dict:
        """计算统计信息"""
        folder_count = 0
        file_count = 0
        max_depth = 0
        
        for root, dirs, files in os.walk(self.kb_path):
            # 计算深度
            depth = len(Path(root).relative_to(self.kb_path).parts)
            max_depth = max(max_depth, depth)
            
            # 计算文件夹数量
            folder_count += len(dirs)
            
            # 计算文件数量（排除隐藏文件和结构文件）
            for file in files:
                if not file.startswith('.') and file != 'structure.md':
                    file_count += 1
        
        return {
            'folder_count': folder_count,
            'file_count': file_count,
            'max_depth': max_depth
        }
    
    def _generate_structure_content(self, structure: Dict, stats: Dict) -> str:
        """生成结构文件内容"""
        current_time = datetime.now().strftime("%Y-%m-%d")
        
        content = f"""# 📁 知识库文件夹结构

> 本文件自动维护知识库的文件夹结构，用于指导新文件的归类。
> 最后更新时间：{current_time}

## 🗂️ 当前文件夹结构

"""
        
        # 生成文件夹结构部分
        for category, info in sorted(structure.items()):
            emoji = self._get_category_emoji(category)
            content += f"### {emoji} {category}\n"
            content += f"- **{category}** - {info['description']}\n"
            
            # 添加子文件夹
            for subfolder, subfolder_info in sorted(info['subfolders'].items()):
                content += f"- **{subfolder}** - {subfolder_info['description']}\n"
                
                # 添加三级文件夹
                for subsubfolder, subsubfolder_info in sorted(subfolder_info['subfolders'].items()):
                    content += f"  - **{subsubfolder}** - {subsubfolder_info['description']}\n"
            
            content += "\n"
        
        # 添加分类规则
        content += """## 📋 分类规则

### 智能分类系统
本系统采用配置化的智能分类规则，支持20+类别的文档自动分类。

"""
        
        # 添加动态分类规则信息
        try:
            import yaml
            from pathlib import Path
            
            rules_file = Path("config/classification_rules.yaml")
            if rules_file.exists():
                with open(rules_file, 'r', encoding='utf-8') as f:
                    rules = yaml.safe_load(f)
                
                classification_rules = rules.get('classification_rules', {})
                strategy = rules.get('strategy', {})
                
                content += "### 当前分类规则配置\n"
                content += f"- **语义匹配阈值**: {strategy.get('semantic_threshold', 0.05)}\n"
                content += f"- **允许创建新文件夹**: {'是' if strategy.get('allow_new_folders', False) else '否'}\n"
                content += f"- **强制使用现有文件夹**: {'是' if strategy.get('force_existing', True) else '否'}\n"
                content += f"- **配置分类总数**: {len(classification_rules)}个\n\n"
                
                content += "### 主要分类类别\n"
                # 按优先级排序显示分类规则
                sorted_rules = sorted(classification_rules.items(), key=lambda x: x[1].get('priority', 99))
                
                for i, (category, info) in enumerate(sorted_rules[:10], 1):  # 只显示前10个
                    keywords = info.get('keywords', [])[:3]  # 只显示前3个关键词
                    priority = info.get('priority', 99)
                    content += f"{i}. **{category}** (优先级: {priority}) - 关键词: {', '.join(keywords)}{'...' if len(info.get('keywords', [])) > 3 else ''}\n"
                
                if len(classification_rules) > 10:
                    content += f"... 以及其他 {len(classification_rules) - 10} 个分类\n"
                    
        except Exception as e:
            # 如果配置读取失败，使用默认说明
            content += """### 主要分类维度
1. **技术开发** - 开发、编程、系统架构相关
2. **项目管理** - 项目计划、管理、策略相关
3. **业务流程** - 业务需求、流程、规范相关
4. **人力资源** - HR相关：培训、面试、员工管理等
5. **财务管理** - 财务、预算、成本相关
6. **会议沟通** - 会议纪要、讨论、沟通相关
7. **个人财务** - 个人理财、记账、投资相关
8. **生活记录** - 日记、生活感悟、个人记录
9. **旅行出行** - 旅行、旅游、出行攻略
10. **学习成长** - 学习、成长、知识相关

"""
        
        content += """
### 智能分类流程
1. **精确匹配** - 检查文档标题是否包含现有文件夹名称
2. **语义分析** - 基于配置化关键词规则进行语义匹配
3. **相似性匹配** - 检查文档与现有文件夹的相似度
4. **LLM智能决策** - 如前面步骤无法确定，调用LLM进行智能分析
5. **强制分类** - 确保文档最终被分类到合适的现有文件夹

### 扩展配置
要添加新的分类类别或修改现有规则，请编辑 `config/classification_rules.yaml` 文件。
系统将自动应用新的配置规则，无需修改代码。

"""
        
        # 添加统计信息
        content += f"""## 📊 统计信息
- 当前文件夹数量：{stats['folder_count']}个
- 文档总数：{stats['file_count']}个
- 最大层级深度：{stats['max_depth']}级
"""
        
        return content
    
    def _get_category_emoji(self, category: str) -> str:
        """获取分类对应的emoji"""
        emojis = {
            # 企业类别
            '技术开发': '💻',
            '运维管理': '⚙️',
            '项目管理': '📋',
            '业务流程': '🔄',
            '人力资源': '👥',
            '财务管理': '💰',
            '会议沟通': '📝',
            '法律合规': '⚖️',
            '产品设计': '🎨',
            '营销推广': '📢',
            '学习成长': '📚',
            # 个人类别
            '个人财务': '💳',
            '生活记录': '📖',
            '健康医疗': '🏥',
            '旅行出行': '✈️',
            '兴趣爱好': '🎯',
            '家庭生活': '🏠',
            '求职职业': '💼',
            '教育培训': '🎓',
            '创作写作': '✍️',
            # 兼容旧分类
            '个人成长': '📈',
            '会议纪要': '📝',
            '技术方案': '🔧',
            '财务报告': '💰',
            '项目文档': '📁'
        }
        return emojis.get(category, '📄') 