# 🏨 酒店评价分析与智能问题生成系统

**Hack-AI-thon 2026 Spring 项目**

一个端到端的酒店信息分析系统，通过分析客户评价数据自动识别服务缺口，并为每个酒店生成个性化的客户调研问题。系统结合机器学习、自然语言处理和LLM增强技术，为酒店运营优化提供数据驱动的解决方案。

---

## 🎯 系统概览

### 🔄 工作流程
```
客户评价数据 → Module 1 (缺口分析) → Module 2 (问题生成) → 客户调研问题
```

### 📦 模块架构

**Module 1: 酒店信息档案构建器**
- 🔍 从客户评价中提取20个酒店服务维度
- 📊 构建每个酒店的服务质量档案
- 🚨 识别并评分服务缺口 (4种类型)
- 📈 基于商业重要性进行优先级排序

**Module 2: 智能问题生成器**
- 🤖 基于缺口分析结果生成个性化问题
- 💬 使用OpenAI LLM增强问题自然性
- 📋 模板回退机制确保系统稳定性
- 🎯 生成简单易答的客户调研问题

---

## 🚀 快速开始

### 1️⃣ 环境配置

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2️⃣ 配置API密钥

编辑 `config.py` 文件：
```python
OPENAI_API_KEY = "your_openai_api_key_here"
```

### 3️⃣ 运行系统

**Module 1 - 缺口分析：**
```bash
# 使用示例数据
python -m module1.run --sample

# 分析特定酒店
python -m module1.run --hotel hotel_id_123

# 批量分析
python -m module1.run Reviews_PROC.csv --output results/
```

**Module 2 - 问题生成：**
```bash
# 演示模式（推荐）
python -m module2.run --demo

# 处理 Module 1 输出
python -m module2.run hotel_gaps.json

# 仅使用模板（不调用API）
python -m module2.run --template-only input.json

# 批量处理多个酒店
python -m module2.run --batch hotels_list.json
```

---

## 📊 核心功能详解

### 🔍 Module 1: 缺口识别系统

**20个酒店服务维度：**
- **硬件设施** (7维度): WiFi、空调、电视、停车等
- **服务体验** (8维度): 员工态度、客房清洁、早餐等
- **周边环境** (3维度): 位置、噪音、周边设施
- **酒店政策** (2维度): 入住退房、宠物政策

**4种缺口类型：**
1. 🔴 **官方冲突** (优先级4) - 官方信息与客户评价不符
2. 🟡 **从未提及** (优先级3) - 缺乏客户反馈数据
3. 🟠 **信息过时** (优先级2) - 反馈时间过久需要更新
4. 🟢 **评价冲突** (优先级1) - 客户评价观点不一致

### 🤖 Module 2: 智能问题生成

**问题生成策略：**
- **LLM增强模式**: 使用GPT-3.5-turbo生成自然对话问题
- **模板回退模式**: 基于规则的结构化问题生成
- **个性化设计**: 每个酒店获得专属的5个问题

**问题示例：**
```
城市商务酒店：
- "你觉得酒店的WiFi速度和连接稳定性如何？"
- "你对酒店客房的清洁程度有什么看法？"

海滨度假酒店：
- "你上次使用酒店游泳池是什么时候？"
- "你最近去过酒店的海滩吗？"
```

---

## 📁 项目结构

```
Hack-AI-thon-2026-Spring/
├── 📂 module1/                 # 缺口分析模块
│   ├── dimensions.py          # 20个酒店维度定义
│   ├── extractor.py           # 关键词提取器
│   ├── profiler.py            # 酒店档案构建器
│   ├── gap_finder.py          # 缺口识别与评分
│   ├── business_weights.py    # 商业重要性权重
│   └── run.py                 # 命令行入口
├── 📂 module2/                 # 问题生成模块
│   ├── question_templates.py  # 问题模板系统
│   ├── question_generator.py  # LLM增强生成器
│   └── run.py                 # 命令行入口
├── 📊 Reviews_PROC.csv        # 客户评价数据
├── ⚙️ config.py               # API配置文件
├── 📋 requirements.txt        # 依赖列表
└── 📖 README.md              # 项目文档
```

---

## 🛠️ 详细用法

### Module 1 高级选项

```bash
# 指定输出格式和位置
python -m module1.run --sample --format json --output results/

# 启用LLM增强提取（实验性）
python -m module1.run --sample --use-llm

# 调整评分阈值
python -m module1.run --sample --min-gap-score 30.0

# 详细调试信息
python -m module1.run --sample --verbose
```

### Module 2 高级选项

```bash
# 控制生成问题数量
python -m module2.run --demo --max-questions 3

# 指定输出文件
python -m module2.run input.json --output custom_questions.json

# 不显示终端结果
python -m module2.run --batch hotels.json --no-display
```

---

## 📈 输出结果格式

### Module 1 输出 (JSON):
```json
{
  "property_id": "hotel_001",
  "top_gaps": [
    {
      "dimension": "wifi_speed",
      "label": "WiFi & Internet",
      "category": "hardware",
      "reason": "stale",
      "priority": 2,
      "mention_count": 12,
      "last_mentioned": "2025-08-15",
      "dominant_stance": "negative"
    }
  ]
}
```

### Module 2 输出 (JSON):
```json
{
  "property_id": "hotel_001",
  "questions_generated": 5,
  "generation_method": "llm_enhanced",
  "questions": [
    {
      "question": "你觉得酒店的WiFi速度和连接稳定性如何？",
      "gap_dimension": "wifi_speed",
      "gap_reason": "stale",
      "priority": 2,
      "expected_outcome": "了解客人对WiFi服务质量的感受"
    }
  ]
}
```

---

## ⚙️ 配置选项

### API使用控制
- **成本控制**: 使用GPT-3.5-turbo降低API成本
- **模板回退**: API调用失败时自动使用模板
- **批量优化**: 支持批量处理减少API调用次数

### 评分系统调优
编辑 `module1/business_weights.py` 调整维度权重：
```python
BUSINESS_WEIGHTS = {
    "wifi_speed": 4.5,      # 高优先级
    "room_cleanliness": 4.8, # 最高优先级
    "parking": 2.1,          # 较低优先级
}
```

---

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'Add amazing feature'`
4. 推送分支: `git push origin feature/amazing-feature`
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🏆 Hack-AI-thon 2026 Spring

本项目为 Hack-AI-thon 2026 Spring 竞赛作品，专注于将AI技术应用于酒店行业的数据驱动决策优化。

**核心创新点：**
- 🎯 端到端的酒店信息缺口识别与问题生成流程
- 🤖 LLM增强的自然语言问题生成
- 📊 基于商业重要性的智能优先级排序
- 🔄 模板回退机制确保系统稳定性

---

**项目链接**: https://github.com/dengjiaming/Hack-AI-thon-2026-Spring