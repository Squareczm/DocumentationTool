# 📁 智能文件分类系统 - 配置文档

本文档详细说明智能文件分类系统的配置方法、最佳实践和高级功能。

## 📋 目录

- [配置文件概览](#配置文件概览)
- [核心配置](#核心配置)
- [分类规则配置](#分类规则配置)
- [文件夹模板配置](#文件夹模板配置)
- [高级配置](#高级配置)
- [最佳实践](#最佳实践)
- [故障排除](#故障排除)
- [扩展开发](#扩展开发)

## 📁 配置文件概览

### 核心配置文件

```
config/
├── classification_rules.yaml    # 🧠 分类规则（核心）
├── folder_templates.yaml       # 📂 文件夹模板
├── config.yaml                 # ⚙️ 主配置文件
├── README.md                   # 📖 配置文档（本文件）
└── industries/                 # 🏢 行业扩展配置
    ├── medical_rules.yaml      # 医疗行业
    ├── education_rules.yaml    # 教育行业
    ├── legal_rules.yaml        # 法律行业
    └── finance_rules.yaml      # 金融行业
```

### 配置优先级

```
环境变量 > config.yaml > classification_rules.yaml > 默认值
```

## ⚙️ 核心配置

### LLM配置

**基础配置（config.yaml）**：

```yaml
llm:
  provider: "openai"
  api_key: "${SMARTFILEORG_LLM_API_KEY}"
  base_url: "https://api.deepseek.com/v1"
  model: "deepseek-chat"
  timeout: 30
  max_retries: 3
  temperature: 0.1
  max_tokens: 2048
```

**推荐提供商配置**：

<details>
<summary>🔸 DeepSeek（推荐，性价比高）</summary>

```yaml
llm:
  provider: "openai"
  api_key: "sk-xxx"
  base_url: "https://api.deepseek.com/v1"
  model: "deepseek-chat"
  timeout: 30
```

获取API密钥：https://platform.deepseek.com/api_keys
</details>

<details>
<summary>🔸 OpenAI</summary>

```yaml
llm:
  provider: "openai"
  api_key: "sk-xxx"
  base_url: "https://api.openai.com/v1"
  model: "gpt-3.5-turbo"
  timeout: 30
```

获取API密钥：https://platform.openai.com/api-keys
</details>

<details>
<summary>🔸 智谱AI</summary>

```yaml
llm:
  provider: "openai"
  api_key: "xxx.xxx"
  base_url: "https://open.bigmodel.cn/api/paas/v4/"
  model: "glm-4"
  timeout: 30
```

获取API密钥：https://open.bigmodel.cn/usercenter/apikeys
</details>

### 环境变量配置

```bash
# 基础配置
export SMARTFILEORG_LLM_API_KEY="your_api_key"
export SMARTFILEORG_LLM_MODEL="deepseek-chat"
export SMARTFILEORG_LLM_BASE_URL="https://api.deepseek.com/v1"

# 高级配置
export SMARTFILEORG_LOG_LEVEL="INFO"
export SMARTFILEORG_MAX_WORKERS="4"
export SMARTFILEORG_CACHE_SIZE="1000"
```

## 🧠 分类规则配置

### 配置结构

```yaml
# classification_rules.yaml
metadata:
  version: "2.0.0"
  description: "分类规则配置"

classification_rules:
  分类名称:
    description: "分类描述"
    keywords: [关键词列表]
    target_patterns: [目标文件夹模式]
    priority: 优先级数字
    file_types: [支持的文件类型]
```

### 添加新分类

**示例：添加"区块链技术"分类**

```yaml
classification_rules:
  区块链技术:
    description: "区块链、加密货币、DeFi等相关文档"
    keywords:
      # 中文关键词
      - 区块链 - 比特币 - 以太坊 - 智能合约 - DeFi
      - 加密货币 - 数字货币 - NFT - 去中心化 - 共识算法
      # 英文关键词  
      - blockchain - bitcoin - ethereum - smart contract - DeFi
      - cryptocurrency - digital currency - NFT - decentralized
    target_patterns:
      - 区块链技术 - 加密货币 - DeFi研究 - 智能合约
    priority: 12
    file_types: [".pdf", ".md", ".docx", ".pptx"]
```

### 关键词优化技巧

**1. 关键词层次化**：
```yaml
keywords:
  # 核心关键词（权重高）
  - 核心词1 - 核心词2
  # 相关关键词（权重中）
  - 相关词1 - 相关词2
  # 领域关键词（权重低）
  - 领域词1 - 领域词2
```

**2. 多语言支持**：
```yaml
keywords:
  # 优先匹配中文
  - 中文关键词
  # 备用英文匹配
  - english keywords
  # 专业术语
  - technical terms
```

**3. 避免关键词冲突**：
```yaml
# ❌ 不好的例子 - 关键词重叠
技术开发:
  keywords: [技术, 开发, 项目]
项目管理:
  keywords: [项目, 管理, 技术]  # 与技术开发冲突

# ✅ 好的例子 - 关键词明确
技术开发:
  keywords: [编程, 代码, 算法, 架构]
项目管理:
  keywords: [计划, 进度, 里程碑, 需求]
```

### 权重和优先级调优

**优先级设置原则**：
- **1-10**：核心业务分类（如技术开发、项目管理）
- **11-20**：支持业务分类（如数据分析、质量管理）
- **21-30**：个人生活分类
- **31+**：特殊或实验性分类

**权重系统调优**：
```yaml
global_settings:
  scoring_system:
    keyword_match_weight: 0.4      # 关键词匹配权重
    semantic_similarity_weight: 0.3 # 语义相似度权重
    priority_weight: 0.2           # 优先级权重
    file_type_weight: 0.1          # 文件类型权重
```

## 📂 文件夹模板配置

### 基础模板类型

**1. 平铺结构（适合简单场景）**：
```yaml
base_templates:
  flat:
    structure: ["{category}"]
    max_depth: 1
```

**2. 层级结构（推荐）**：
```yaml
base_templates:
  hierarchical:
    structure: 
      - "{category}"
      - "{category}/{subcategory}"
    max_depth: 2
```

**3. 深度结构（专业场景）**：
```yaml
base_templates:
  deep:
    structure:
      - "{category}"
      - "{category}/{subcategory}" 
      - "{category}/{subcategory}/{detailed_category}"
    max_depth: 3
```

### 组织策略配置

**按时间组织**：
```yaml
organization_strategies:
  by_time:
    patterns:
      yearly: "{category}/{year}年"
      monthly: "{category}/{year}年/{month}月"
      daily: "{category}/{year}年/{month}月/{day}日"
```

**按项目组织**：
```yaml
organization_strategies:
  by_project:
    patterns:
      project_based: "{category}/项目_{project_name}"
      phase_based: "{category}/项目_{project_name}/{phase}"
```

**自定义组织策略**：
```yaml
organization_strategies:
  by_department:
    description: "按部门组织"
    patterns:
      dept_based: "{category}/部门_{department}"
      team_based: "{category}/部门_{department}/团队_{team}"
    variables:
      department: "部门名称"
      team: "团队名称"
```

### 动态模板生成

**启用自学习功能**：
```yaml
dynamic_templates:
  auto_generation:
    enabled: true
    learn_from_existing: true
    min_folder_count: 3
    file_type_based: true
```

## 🚀 高级配置

### 性能优化

**缓存配置**：
```yaml
advanced:
  performance:
    enable_keyword_cache: true
    cache_size: 1000
    enable_parallel_processing: true
    max_workers: 4
    batch_size: 50
```

**内存优化**：
```yaml
advanced:
  performance:
    # 大文件处理优化
    large_file_threshold: "10MB"
    chunk_size: "1MB"
    
    # 批量处理优化
    batch_processing: true
    max_batch_size: 100
```

### 多环境配置

**开发环境**：
```yaml
# config/dev.yaml
llm:
  model: "gpt-3.5-turbo"  # 使用更便宜的模型
  temperature: 0.2        # 更高的随机性用于测试

advanced:
  log_matching_details: true
  enable_debug_mode: true
```

**生产环境**：
```yaml
# config/prod.yaml  
llm:
  model: "deepseek-chat"  # 性能优化的模型
  temperature: 0.1        # 更稳定的输出
  timeout: 60            # 更长的超时时间

advanced:
  log_matching_details: false
  enable_performance_monitoring: true
```

**使用方式**：
```bash
# 指定配置文件
python main.py --config config/prod.yaml

# 或通过环境变量
export SMARTFILEORG_CONFIG="config/prod.yaml"
python main.py
```

### 机器学习配置

**自学习功能**（实验性）：
```yaml
advanced:
  machine_learning:
    enable_learning: true
    learning_rate: 0.01
    min_samples: 100
    auto_update_rules: false  # 安全起见，默认关闭自动更新
```

**特征工程**：
```yaml
advanced:
  feature_engineering:
    enable_tfidf: true
    enable_word2vec: false  # 需要额外模型
    enable_bert_embedding: false  # 需要GPU
```

### 监控和告警

**性能监控**：
```yaml
monitoring:
  performance_monitoring:
    enabled: true
    monitor_template_resolution_time: true
    monitor_folder_creation_time: true
    alert_threshold: 1000  # ms
```

**使用统计**：
```yaml
monitoring:
  usage_tracking:
    enabled: true
    track_folder_creation: true
    track_template_usage: true
    track_organization_patterns: true
```

## ✅ 最佳实践

### 1. 配置管理

**版本控制**：
```bash
# 配置文件版本化
git add config/
git commit -m "配置更新：添加区块链技术分类"

# 配置备份
cp config/classification_rules.yaml config/classification_rules.yaml.backup
```

**配置验证**：
```bash
# 验证配置
python main.py --validate-config

# 配置检查
python main.py --check-config --verbose
```

### 2. 分类规则设计

**规则设计原则**：
1. **专一性**：每个分类有明确的边界
2. **完整性**：覆盖所有可能的文档类型
3. **互斥性**：避免分类之间的重叠
4. **可扩展**：便于后续添加新分类

**关键词选择策略**：
```yaml
# 使用分层关键词
技术开发:
  keywords:
    # 第一层：核心概念（必须匹配）
    - 技术 - 开发 - 编程
    # 第二层：相关概念（辅助匹配）
    - 算法 - 架构 - 系统
    # 第三层：技术名词（精确匹配）
    - Python - JavaScript - Docker
```

### 3. 文件夹结构设计

**层级设计原则**：
- **2-3层**：适合大多数场景
- **避免过深**：超过4层会影响可用性
- **语义清晰**：文件夹名称要直观易懂

**命名规范**：
```yaml
naming_conventions:
  folder_naming:
    # 建议的命名模式
    pattern: "^[\\u4e00-\\u9fa5a-zA-Z0-9_\\-\\s]+$"
    max_length: 50
    
    # 推荐命名样式
    preferred_styles:
      - "技术开发"        # 中文简洁
      - "项目_2024_AI"   # 下划线分隔
      - "会议纪要-重要"   # 连字符分隔
```

### 4. 性能优化

**大文件处理优化**：
```yaml
# 针对大量文件的优化配置
advanced:
  performance:
    batch_size: 100           # 批量处理大小
    max_workers: 8           # 并发处理线程
    enable_parallel_processing: true
    
    # 内存优化
    memory_limit: "1GB"
    gc_frequency: 100        # 垃圾回收频率
```

**网络优化**：
```yaml
llm:
  timeout: 60              # 网络超时时间
  max_retries: 5          # 最大重试次数
  retry_delay: 2          # 重试延迟
  
  # 连接池配置
  connection_pool:
    max_connections: 10
    max_keepalive_connections: 5
```

## 🔧 故障排除

### 常见问题

**1. API密钥错误**

```bash
错误信息：Authentication failed
解决方案：
1. 检查API密钥是否正确
2. 确认API密钥有足够余额
3. 检查base_url是否匹配提供商
```

**2. 分类准确率低**

```yaml
# 调优配置
strategy:
  semantic_threshold: 0.02  # 降低阈值提高召回率
  keyword_weight: 0.8      # 提高关键词权重
  min_match_score: 0.05    # 降低最小匹配分数
```

**3. 文件夹创建失败**

```bash
错误信息：Permission denied
解决方案：
1. 检查目标目录写权限
2. 确认文件夹名称合法
3. 检查路径长度限制（Windows: 260字符）
```

**4. 内存占用过高**

```yaml
# 内存优化配置
advanced:
  performance:
    batch_size: 20          # 减小批量大小
    max_workers: 2         # 减少并发线程
    enable_keyword_cache: false  # 禁用缓存
```

### 调试配置

**启用详细日志**：
```yaml
# config.yaml
logging:
  level: "DEBUG"
  format: "detailed"
  file: "logs/debug.log"
  
advanced:
  log_matching_details: true
  enable_debug_mode: true
```

**性能分析**：
```bash
# 性能分析模式
python main.py --profile --output profiling_report.html

# 内存使用分析
python main.py --memory-profile
```

### 配置验证工具

**配置语法检查**：
```bash
# 验证YAML语法
python -c "import yaml; yaml.safe_load(open('config/classification_rules.yaml'))"

# 使用内置验证
python main.py --validate-config --strict
```

**配置完整性检查**：
```bash
# 检查必需字段
python main.py --check-required-fields

# 检查配置冲突
python main.py --check-conflicts
```

## 🔌 扩展开发

### 行业扩展配置

**创建医疗行业扩展**：

```yaml
# config/industries/medical_rules.yaml
metadata:
  industry: "medical"
  version: "1.0.0"
  extends: "classification_rules.yaml"

classification_rules:
  临床医学:
    description: "临床诊断、治疗相关文档"
    keywords:
      - 诊断 - 治疗 - 临床 - 病历 - 处方
      - 症状 - 检查 - 化验 - 影像 - 手术
    target_patterns:
      - 临床医学 - 诊断记录 - 治疗方案
    priority: 1
    
  医院管理:
    description: "医院运营管理相关文档"
    keywords:
      - 医院管理 - 排班 - 科室 - 床位 - 设备
      - 质控 - 感控 - 护理 - 药事 - 后勤
    target_patterns:
      - 医院管理 - 运营管理 - 质量控制
    priority: 2
```

**使用行业扩展**：
```yaml
# config.yaml
extensions:
  industry_extensions:
    medical: "config/industries/medical_rules.yaml"
  
  load_order: ["base", "industry", "custom"]
```

### 自定义插件开发

**插件接口**：
```python
# config/plugins/custom_classifier.py
class CustomClassifier:
    def __init__(self, config):
        self.config = config
    
    def classify(self, file_content, file_path):
        # 自定义分类逻辑
        return {
            'category': '分类名称',
            'confidence': 0.85,
            'reasoning': '分类原因'
        }
    
    def get_folder_suggestions(self, category, file_info):
        # 自定义文件夹建议
        return ['建议文件夹1', '建议文件夹2']
```

**插件配置**：
```yaml
# config.yaml
extensions:
  plugins:
    enabled: true
    custom_classifiers:
      - "config/plugins/custom_classifier.py"
```

### 配置迁移

**从v1.0迁移到v2.0**：
```bash
# 自动迁移
python scripts/migrate_config.py --from v1.0 --to v2.0

# 手动迁移检查
python scripts/check_migration.py --config config/classification_rules.yaml
```

**迁移脚本示例**：
```python
# scripts/migrate_from_v1.py
def migrate_v1_to_v2(old_config_path, new_config_path):
    # 读取旧配置
    with open(old_config_path) as f:
        old_config = yaml.safe_load(f)
    
    # 转换为新格式
    new_config = {
        'metadata': {
            'version': '2.0.0',
            'migrated_from': '1.0.0'
        },
        'classification_rules': {}
    }
    
    # 转换逻辑...
    
    # 保存新配置
    with open(new_config_path, 'w') as f:
        yaml.dump(new_config, f, ensure_ascii=False)
```

## 📚 相关资源

- [主要文档](../README.md) - 系统概览和快速开始
- [扩展指南](../SCALABILITY_GUIDE.md) - 深入的扩展开发指导  
- [配置示例](config.example.yaml) - 完整的配置文件示例
- [API文档](docs/api.md) - 开发者API参考
- [最佳实践](docs/best_practices.md) - 更多实践经验

---

💡 **提示**：建议先从默认配置开始，根据实际使用情况逐步调优。配置更改后记得验证和测试！ 