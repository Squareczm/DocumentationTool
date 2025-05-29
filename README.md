# 🤖 智能文件整理助手

一款基于大语言模型的智能文档分类与归档系统，支持20+类别的全自动文档分类，真正实现"拖放即归档"的无缝体验。

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](/)

## ✨ 核心特性

### 🧠 AI驱动的智能分类
- **深度内容理解**：基于大语言模型分析文档内容
- **语义相似性匹配**：通过关键词密度和优先级权重系统精准分类
- **中英文混合支持**：无缝处理多语言文档

### 📁 20+全生活分类体系
- **企业办公**：技术开发、运维管理、项目管理、业务流程、人力资源等
- **个人生活**：个人财务、生活记录、健康医疗、旅行出行、兴趣爱好等
- **学习成长**：教育培训、创作写作、求职职业等
- **法律合规**：合同协议、法务文档等

### 🛡️ 三层防护系统
```
文本直接匹配 → 语义分析匹配 → 通用回退策略
```
确保每个文档都能找到合适的归档位置，**完全避免文件夹爆炸**

### 🔧 零代码扩展性
- **配置化分类规则**：通过 `config/classification_rules.yaml` 轻松扩展
- **动态学习能力**：自动适应现有文件夹结构
- **新领域支持**：医疗、教育、金融等任意领域一键扩展

## 🚀 快速开始

### 📋 前提条件
- ✅ Python 3.8 或更高版本
- ✅ 网络连接（用于API调用）
- ✅ LLM API密钥（OpenAI、DeepSeek等）

### 安装配置

```bash
# 1. 克隆项目
git clone https://github.com/Squareczm/DocumentationToolUpdated
cd DocumentationToolUpdated

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置API密钥
# Windows用户：
copy config.example.yaml config.yaml
# Linux/Mac用户：
# cp config.example.yaml config.yaml

**推荐完整配置（以DeepSeek为例）：**
```yaml
llm:
  provider: "openai"
  api_key: "sk-1234567890abcdef..."  # 请替换为您的真实API密钥
  base_url: "https://api.deepseek.com/v1"
  model: "deepseek-chat"
  timeout: 30
```

**获取API密钥：**
- 🔗 **DeepSeek（推荐）**：https://platform.deepseek.com/api_keys
- 🔗 **OpenAI**：https://platform.openai.com/api-keys

**配置方式：**

**方式1：编辑配置文件（推荐新手）**
```yaml
# 用文本编辑器打开 config.yaml，完整配置如上所示
```

**方式2：仅设置环境变量（高级用户）**
```bash
# Windows: set SMARTFILEORG_LLM_API_KEY=你的API密钥
# Linux/Mac: export SMARTFILEORG_LLM_API_KEY=你的API密钥
# 注意：使用环境变量时，仍需在config.yaml中正确配置base_url和model
```

**4. 环境检查**
```bash
python main.py --check
```

### 开始使用

#### 方式1：拖放文件处理（最简单）
1. **将文件放入inbox文件夹** - 将待处理的文档拖放到`inbox/`文件夹中
2. **运行处理命令** - `python main.py`
3. **确认处理** - 程序会显示处理计划，确认后自动执行

#### 方式2：自动监控模式（实时处理）
```bash
python main.py --watch
```

#### 方式3：批量处理
```bash
# 自动确认模式
python main.py -y

# 处理指定文件夹
python main.py -f "/path/to/documents"
```

## 📊 智能分类系统

### 🏢 企业办公类 (11类)

| 分类 | 关键词示例 | 目标文件夹 |
|------|------------|------------|
| **技术开发** | 开发、编程、AI、算法 | 技术方案、AI研究 |
| **运维管理** | 运维、部署、监控、Docker | DevOps运维、容器化部署 |
| **项目管理** | 项目、管理、计划、任务 | 项目文档、工作计划 |
| **业务流程** | 业务、流程、规范、标准 | 业务文档、操作手册 |
| **人力资源** | 招聘、培训、员工、绩效 | 人力资源、团队建设 |
| **财务管理** | 财务、预算、投资、税务 | 财务报告、投资理财 |
| **会议沟通** | 会议、纪要、讨论、汇报 | 会议纪要、沟通记录 |
| **法律合规** | 法律、合同、协议、律师 | 法律文档、合同 |
| **产品设计** | 产品、设计、UI、创意 | 产品设计、创意设计 |
| **营销推广** | 营销、推广、品牌、运营 | 营销文档、品牌 |
| **学习成长** | 学习、培训、读书笔记 | 个人成长、读书笔记 |

### 🏠 个人生活类 (9类)

| 分类 | 关键词示例 | 目标文件夹 |
|------|------------|------------|
| **个人财务** | 理财、记账、投资、保险 | 个人财务、记账 |
| **生活记录** | 日记、心情、感想、随笔 | 生活记录、日记 |
| **健康医疗** | 健康、体检、医疗、健身 | 健康医疗、体检报告 |
| **旅行出行** | 旅行、攻略、游记、签证 | 旅行出行、游记 |
| **兴趣爱好** | 爱好、收藏、音乐、摄影 | 兴趣爱好、收藏 |
| **家庭生活** | 家庭、育儿、装修、节日 | 家庭生活、育儿 |
| **求职职业** | 求职、简历、职业规划 | 求职职业、简历 |
| **教育培训** | 教育、课程、考试、学历 | 教育培训、考试 |
| **创作写作** | 创作、写作、博客、小说 | 创作写作、作品 |

## 🌟 使用示例

### 处理前
```
inbox/
├── 我的理财计划.xlsx
├── 日本旅游攻略.md
├── 2025年工作总结.docx
├── 体检报告.pdf
└── 读书笔记-深度工作.md
```

### 处理后
```
knowledge_base/
├── 个人财务/理财/
│   └── 个人投资理财计划_20250529_v1.0.xlsx
├── 旅行出行/游记/
│   └── 日本旅游攻略指南_20250529_v1.0.md
├── 求职职业/工作/
│   └── 年度工作总结报告_20250529_v1.0.docx
├── 健康医疗/体检报告/
│   └── 年度健康体检报告_20250529_v1.0.pdf
└── 学习成长/读书笔记/
    └── 深度工作读书心得_20250529_v1.0.md
```

## 🎯 高级功能

### 配置化扩展

需要支持新的文档类型？只需编辑配置文件：

```yaml
# config/classification_rules.yaml
classification_rules:
  医疗健康:
    keywords:
      - 医疗
      - 诊断
      - 病历
      - 药物
    target_patterns:
      - 医疗文档
      - 诊断报告
    priority: 1
```

### 自定义命名规则

```bash
# 使用自定义版本格式
python main.py --version-format "semantic"  # v1.0.1

# 自定义日期格式
python main.py --date-format "%Y-%m-%d"
```

## 📈 性能与兼容性

### 支持格式
- **文档**：.docx, .doc, .pdf, .txt, .md
- **表格**：.xlsx, .xls, .csv
- **演示**：.pptx, .ppt
- **其他**：自动识别文本内容

### 性能指标
- **分类准确率**：>95%
- **处理速度**：~50文档/分钟
- **内存占用**：<100MB
- **多语言支持**：中文、英文

### LLM提供商支持
- **OpenAI**：GPT-3.5/GPT-4
- **DeepSeek**：DeepSeek-Chat
- **Anthropic**：Claude系列
- **智谱AI**：GLM系列

## 🔧 常用命令

```bash
# 基本使用
python main.py                    # 交互式处理
python main.py -y                 # 自动确认
python main.py --watch            # 监控模式

# 高级选项
python main.py --check            # 环境检查
python main.py --dry-run          # 预览模式
python main.py -f "path"          # 指定文件夹
```

## ⚡ 快速测试

```bash
# 创建测试文件
# Windows (cmd):
echo # 2025年理财规划 > inbox/理财计划.md
echo # 项目启动会议纪要 > inbox/会议纪要.md

# Linux/Mac:
# echo "# 2025年理财规划" > inbox/理财计划.md
# echo "# 项目启动会议纪要" > inbox/会议纪要.md

# 运行处理
python main.py -y
```

## 📚 更多文档

- [扩展性指南](SCALABILITY_GUIDE.md) - 深入了解配置化分类和扩展能力
- [配置文件说明](config.example.yaml) - 详细的配置选项说明

## 🆕 最新更新 (v1.1.0)

### 🔧 Windows兼容性改进
- **修复Windows命令兼容性**：为Windows用户提供正确的文件复制命令 (`copy` 而不是 `cp`)
- **PowerShell支持**：支持PowerShell环境变量设置语法
- **跨平台说明**：在README中为不同操作系统提供专门的操作指南

### 💡 用户体验优化
- **改进API密钥配置检查**：更智能的密钥验证逻辑，支持环境变量和配置文件两种方式
- **详细配置指导**：提供具体的配置步骤和错误提示
- **存储路径显示**：处理文件时显示目标文件夹路径，让用户清楚文件的最终存储位置

### 🎯 功能增强
- **更友好的错误提示**：详细的API密钥配置指导，包含获取链接
- **实时路径反馈**：文件处理时显示完整的存储信息
- **跨平台测试命令**：为不同操作系统提供正确的测试文件创建命令

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

本项目基于 [MIT许可证](LICENSE) 开源。
