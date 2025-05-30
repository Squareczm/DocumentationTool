# 🏢 行业扩展配置

本目录包含针对特定行业的分类规则扩展。

## 📁 可用扩展

### 医疗行业 (medical_rules.yaml)
- 临床医学、医院管理、医疗器械等
- 适用于医院、诊所、医疗机构

### 教育行业 (education_rules.yaml)
- 教学管理、学生档案、课程资料等
- 适用于学校、培训机构、教育企业

### 法律行业 (legal_rules.yaml)
- 法律文档、案件资料、合同管理等
- 适用于律师事务所、法务部门

### 金融行业 (finance_rules.yaml)
- 投资分析、风险管理、合规文档等
- 适用于银行、证券、保险公司

## 🚀 使用方法

在主配置文件中启用行业扩展：

```yaml
# config.yaml
extensions:
  industry_extensions:
    medical: "config/industries/medical_rules.yaml"
    education: "config/industries/education_rules.yaml"
  
  load_order: ["base", "industry", "custom"]
```

## ✨ 自定义行业扩展

参考现有扩展创建您的行业配置：

```yaml
# your_industry_rules.yaml
metadata:
  industry: "your_industry"
  version: "1.0.0"
  extends: "classification_rules.yaml"

classification_rules:
  您的行业分类:
    description: "行业特定描述"
    keywords: [行业关键词]
    target_patterns: [目标文件夹]
    priority: 1
``` 