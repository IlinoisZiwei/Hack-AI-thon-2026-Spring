# 🏨 酒店评价分析与缺口识别系统

**Hack-AI-thon 2026 Spring 项目**

一个基于机器学习和自然语言处理的酒店信息档案构建与缺口评分系统。通过分析客户评价数据，自动识别酒店服务的信息缺口，为酒店运营优化提供数据驱动的决策支持。

---

## 🎯 项目概述

### 核心功能
- 🔍 **自动提取酒店维度信息** - 从客户评价中识别20个预定义的酒店服务维度
- 📊 **构建酒店服务档案** - 为每个酒店生成全面的服务质量档案
- 🚨 **智能缺口评分** - 自动计算并排序最需要关注的服务缺口
- 📈 **优先级排序** - 基于商业重要性和数据质量进行智能排序

### 应用场景
- 🏨 **酒店运营管理** - 识别服务改进优先级
- 🔍 **竞争分析** - 分析竞争对手的服务优劣势
- 📋 **质量监控** - 持续监控服务质量变化
- 💡 **决策支持** - 为投资和改进提供数据依据

---

## 🏗️ 系统架构

### Module 1: 酒店信息档案构建器
**功能**: 从客户评价中提取和聚合酒店服务信息

**核心组件**:
- 📋 **维度定义** (`dimensions.py`) - 20个预定义酒店服务维度
- 🔍 **信息提取** (`extractor.py`) - 支持规则匹配和LLM两种提取方式
- 📊 **档案构建** (`profiler.py`) - 聚合生成酒店服务档案

**20个分析维度**:
```
硬件设施 (6项):  WiFi速度、隔音效果、空调供暖、电梯、电源插座、水压淋浴
服务体验 (6项):  前台效率、房间清洁、餐厅质量、早餐质量、行李存储、员工友善度
周边环境 (4项):  交通便利、噪音水平、附近餐饮、地理位置便利性
酒店政策 (4项):  退房时间、早餐时间、停车政策、宠物政策
```

### Module 2: 智能缺口评分系统
**功能**: 为每个酒店×维度组合计算缺口评分，识别最需要关注的服务缺口

**评分算法**:
```
gap_score = missing_weight + stale_weight + conflict_weight + business_priority
```

**权重组成**:
- 🔍 **missing_weight** (0-30分) - 数据缺失严重程度
- ⏰ **stale_weight** (0-25分) - 信息过时程度
- ⚡ **conflict_weight** (0-25分) - 评价冲突程度
- 🎯 **business_priority** (5-20分) - 商业重要性权重

---

## ⚙️ 安装配置

### 1. 克隆项目
```bash
git clone <repository-url>
cd Hack-AI-thon-2026-Spring
```

### 2. 创建虚拟环境
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows
```

### 3. 安装依赖
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 准备数据
确保项目根目录下有 `Reviews_PROC.csv` 评价数据文件。

### 5. 配置环境变量 (可选)
如果要使用LLM提取功能，创建 `.env` 文件：
```bash
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

---

## 🚀 使用方法

### 运行 Module 1: 构建酒店档案

#### 基础用法
```bash
# 激活虚拟环境
source venv/bin/activate

# 运行 Module 1 - 处理评价数据并构建酒店档案
python -c "
import pandas as pd
import json
from datetime import datetime

# 1. 加载和预处理评价数据
print('🏨 加载评价数据...')
reviews = pd.read_csv('Reviews_PROC.csv').head(1000)  # 处理前1000条
reviews = reviews[['eg_property_id', 'acquisition_date', 'rating', 'review_title', 'review_text']].copy()

# 解析JSON评分
def safe_parse_rating(x):
    try:
        return json.loads(x) if pd.notna(x) else {}
    except:
        return {}

reviews['rating_dict'] = reviews['rating'].apply(safe_parse_rating)
reviews['review_title'] = reviews['review_title'].fillna('').astype(str)
reviews['review_text'] = reviews['review_text'].fillna('').astype(str)
reviews['review_text_clean'] = (reviews['review_title'] + ' ' + reviews['review_text']).str.lower().str.strip()
reviews = reviews[reviews['review_text_clean'].str.len() > 0].copy()
reviews['acquisition_date'] = pd.to_datetime(reviews['acquisition_date'], errors='coerce')

print(f'✅ 预处理完成: {len(reviews)} 条有效评价')

# 2. 提取维度信息
from module1.extractor import extract_rule_based
from module1.profiler import build_hotel_profiles

print('🔍 提取维度信息...')
all_mentions = []
for idx, row in reviews.iterrows():
    mentions = extract_rule_based(row.to_dict())
    for mention in mentions:
        mention.update({
            'eg_property_id': row['eg_property_id'],
            'review_date': row['acquisition_date']
        })
    all_mentions.extend(mentions)

print(f'✅ 提取到 {len(all_mentions)} 个维度提及')

# 3. 构建酒店档案
if all_mentions:
    mentions_df = pd.DataFrame(all_mentions)
    property_ids = reviews['eg_property_id'].unique().tolist()
    hotel_profiles = build_hotel_profiles(mentions_df, property_ids)

    print(f'✅ 为 {len(hotel_profiles)} 个酒店构建了档案')

    # 保存结果
    from module1.profiler import profile_to_flat_rows
    all_rows = []
    for pid, profile in hotel_profiles.items():
        all_rows.extend(profile_to_flat_rows(pid, profile))

    profiles_df = pd.DataFrame(all_rows)
    profiles_df.to_csv('hotel_profiles_output.csv', index=False, encoding='utf-8')
    print('💾 酒店档案已保存至: hotel_profiles_output.csv')
else:
    print('⚠️ 未提取到维度信息')
"
```

#### 查看结果
```bash
# 查看生成的酒店档案
head -10 hotel_profiles_output.csv
```

### 运行 Module 2: 计算缺口评分

#### 基础用法
```bash
# 在 Module 1 基础上继续运行 Module 2
python -c "
# (前面 Module 1 的代码...)
# 假设已经有了 hotel_profiles

# 4. 计算缺口评分
from module2.gap_scorer import compute_gap_scores, get_top_gaps, analyze_gap_patterns

print('📊 计算缺口评分...')
gap_scores_df = compute_gap_scores(hotel_profiles)

print(f'✅ 计算完成: {len(gap_scores_df)} 个缺口评分')
print(f'📈 评分范围: {gap_scores_df[\"gap_score\"].min():.1f} - {gap_scores_df[\"gap_score\"].max():.1f}')

# 5. 获取高优先级缺口
print('\\n🚨 前10个最需要关注的缺口:')
top_gaps = get_top_gaps(gap_scores_df, top_n=10, min_score=30.0)

for i, (_, row) in enumerate(top_gaps.head(10).iterrows(), 1):
    reasons = ', '.join(row['reason_breakdown']) if row['reason_breakdown'] else '无原因'
    print(f'  {i:2d}. 🏨 {row[\"eg_property_id\"][:12]}... | {row[\"label\"]:<20} | 评分: {row[\"gap_score\"]:5.1f} | {reasons}')

# 6. 统计分析
analysis = analyze_gap_patterns(gap_scores_df)
print(f'\\n📈 缺口统计:')
print(f'  总缺口: {analysis[\"total_gaps\"]} 个')
print(f'  平均评分: {analysis[\"score_distribution\"][\"mean\"]:.1f}')
print(f'  高优先级 (≥50分): {analysis[\"high_priority_gaps\"][\"count\"]} 个 ({analysis[\"high_priority_gaps\"][\"percentage\"]}%)')

# 7. 保存结果
gap_scores_df.to_csv('gap_scores_output.csv', index=False, encoding='utf-8')
print('\\n💾 缺口评分已保存至: gap_scores_output.csv')
"
```

#### 使用演示脚本
```bash
# 运行 Module 2 内置演示
python -m module2.run
```

### 完整流程一键运行
```bash
# 激活虚拟环境
source venv/bin/activate

# 完整流程：Module 1 + Module 2
python -c "
import pandas as pd
import json
from datetime import datetime

print('🔄 开始完整分析流程...')

# 数据加载和预处理
reviews = pd.read_csv('Reviews_PROC.csv').head(500)
reviews = reviews[['eg_property_id', 'acquisition_date', 'rating', 'review_title', 'review_text']].copy()

def safe_parse_rating(x):
    try: return json.loads(x) if pd.notna(x) else {}
    except: return {}

reviews['rating_dict'] = reviews['rating'].apply(safe_parse_rating)
reviews['review_title'] = reviews['review_title'].fillna('').astype(str)
reviews['review_text'] = reviews['review_text'].fillna('').astype(str)
reviews['review_text_clean'] = (reviews['review_title'] + ' ' + reviews['review_text']).str.lower().str.strip()
reviews = reviews[reviews['review_text_clean'].str.len() > 0].copy()
reviews['acquisition_date'] = pd.to_datetime(reviews['acquisition_date'], errors='coerce')

print(f'✅ 数据预处理: {len(reviews)} 条评价')

# Module 1: 构建档案
from module1.extractor import extract_rule_based
from module1.profiler import build_hotel_profiles

all_mentions = []
for idx, row in reviews.iterrows():
    mentions = extract_rule_based(row.to_dict())
    for mention in mentions:
        mention.update({'eg_property_id': row['eg_property_id'], 'review_date': row['acquisition_date']})
    all_mentions.extend(mentions)

if all_mentions:
    mentions_df = pd.DataFrame(all_mentions)
    property_ids = reviews['eg_property_id'].unique().tolist()
    hotel_profiles = build_hotel_profiles(mentions_df, property_ids)
    print(f'✅ Module 1: 为 {len(hotel_profiles)} 个酒店构建档案')

    # Module 2: 缺口评分
    from module2.gap_scorer import compute_gap_scores, get_top_gaps, analyze_gap_patterns

    gap_scores_df = compute_gap_scores(hotel_profiles)
    print(f'✅ Module 2: 计算了 {len(gap_scores_df)} 个缺口评分')

    # 分析结果
    top_gaps = get_top_gaps(gap_scores_df, top_n=5, min_score=25.0)
    print('\\n🏆 Top 5 最需要关注的缺口:')
    for i, (_, row) in enumerate(top_gaps.head(5).iterrows(), 1):
        reasons = ', '.join(row['reason_breakdown'][:2]) if row['reason_breakdown'] else '无原因'
        print(f'  {i}. 🏨 {row[\"eg_property_id\"][:12]}... | {row[\"label\"]:<18} | {row[\"gap_score\"]:5.1f}分 | {reasons}')

    # 保存结果
    gap_scores_df.to_csv('complete_gap_analysis.csv', index=False, encoding='utf-8')
    print('\\n💾 完整分析结果保存至: complete_gap_analysis.csv')

    # 统计摘要
    analysis = analyze_gap_patterns(gap_scores_df)
    print(f'\\n📊 分析摘要: 平均评分 {analysis[\"score_distribution\"][\"mean\"]:.1f}，高优先级缺口 {analysis[\"high_priority_gaps\"][\"count\"]} 个')

else:
    print('❌ 未提取到维度信息，请检查数据')

print('🎉 分析完成！')
"
```

---

## 📁 项目结构

```
Hack-AI-thon-2026-Spring/
├── README.md                          # 项目文档
├── requirements.txt                   # Python依赖包
├── Reviews_PROC.csv                   # 评价数据文件
├── Hack_AI_thon_2026_Spring.ipynb    # Jupyter演示notebook
│
├── module1/                           # Module 1: 酒店档案构建
│   ├── __init__.py                    # 模块初始化
│   ├── dimensions.py                  # 维度定义 (20个酒店服务维度)
│   ├── extractor.py                   # 信息提取器 (规则匹配 + LLM)
│   ├── profiler.py                    # 档案构建器
│   ├── description_enricher.py        # 官方描述处理
│   ├── gap_finder.py                  # 缺口识别 (legacy)
│   ├── run.py                         # 运行脚本
│   └── test_module1.ipynb            # 测试notebook
│
├── module2/                           # Module 2: 智能缺口评分
│   ├── __init__.py                    # 模块初始化
│   ├── business_weights.py            # 商业优先级权重定义
│   ├── gap_scorer.py                  # 缺口评分核心算法
│   └── run.py                         # 演示脚本
│
├── venv/                              # Python虚拟环境
└── WAIAI Hack-AI-thon Resources/      # 比赛资源文件
    └── data/
        ├── Description_PROC.csv       # 酒店描述数据
        ├── Reviews_PROC.csv           # 评价数据备份
        └── DICTIONARY.md              # 数据字典
```

---

## 📊 输出文件说明

### Module 1 输出
- **`hotel_profiles_output.csv`** - 酒店服务档案
  - 每行代表一个酒店×维度的信息汇总
  - 包含提及次数、主导情感、证据文本等

### Module 2 输出
- **`gap_scores_output.csv`** - 缺口评分结果
  - **gap_score**: 总缺口评分 (0-100分，越高越需要关注)
  - **missing_weight**: 数据缺失权重
  - **stale_weight**: 信息过时权重
  - **conflict_weight**: 冲突权重
  - **business_priority**: 商业优先级权重
  - **reason_breakdown**: 缺口原因列表

### 评分解读
- **50+ 分**: 🚨 紧急处理 - 严重缺口，立即关注
- **40-49 分**: ⚠️ 高优先级 - 近期需要解决
- **30-39 分**: 📋 中优先级 - 中期规划处理
- **30 分以下**: ✅ 低优先级 - 暂时无需关注

---

## 🛠️ 高级功能

### 使用 LLM 提取 (需要 OpenAI API)
```python
# 在 extractor.py 中使用 LLM 模式
from module1.extractor import extract_llm_batch

# 批量LLM提取 (需要设置 OPENAI_API_KEY)
llm_results = extract_llm_batch(
    rows=review_data_list,
    model="gpt-4o-mini",
    batch_size=5
)
```

### 自定义评分参数
```python
from module2.gap_scorer import GapScorer, ScoringConfig

# 自定义评分配置
config = ScoringConfig()
config.MISSING_NO_DATA = 35.0      # 提高数据缺失权重
config.STALE_DAYS_THRESHOLD = 90   # 缩短过时阈值到3个月

scorer = GapScorer(config)
gap_scores = scorer.compute_gap_score(property_id, dimension, dimension_info)
```

### 按类别筛选分析
```python
from module2.gap_scorer import get_top_gaps

# 只分析服务类别的缺口
service_gaps = get_top_gaps(
    gap_scores_df,
    category_filter="service",
    min_score=40.0
)
```

---

## 🔧 故障排除

### 常见问题

**Q: ImportError: No module named 'module1'**
```bash
# 确保在项目根目录运行
cd Hack-AI-thon-2026-Spring
source venv/bin/activate
```

**Q: pandas/numpy 导入错误**
```bash
# 重新安装依赖
pip uninstall pandas numpy
pip install pandas numpy
```

**Q: 评价数据文件未找到**
```bash
# 确保数据文件在正确位置
ls -la Reviews_PROC.csv
# 或使用备份数据
cp "WAIAI Hack-AI-thon Resources/data/Reviews_PROC.csv" .
```

**Q: LLM 提取失败**
```bash
# 检查API密钥设置
echo $OPENAI_API_KEY
# 或使用规则匹配模式 (默认)
```

**Q: 内存不足**
```bash
# 减少处理的数据量
reviews = pd.read_csv('Reviews_PROC.csv').head(500)  # 只处理前500条
```

### 性能优化

**处理大量数据时**:
```python
# 分批处理，避免内存溢出
chunk_size = 1000
for i in range(0, len(reviews), chunk_size):
    chunk = reviews[i:i+chunk_size]
    # 处理chunk...
```

**加速评分计算**:
```python
# 使用多进程 (在 gap_scorer.py 中可扩展)
from multiprocessing import Pool
```

---

## 📈 扩展开发

### 添加新维度
在 `module1/dimensions.py` 中添加：
```python
DIMENSIONS["new_dimension"] = {
    "category": "service",
    "label": "新服务维度",
    "keywords": ["关键词1", "关键词2", "关键词3"],
}
```

### 自定义商业权重
在 `module2/business_weights.py` 中修改：
```python
BUSINESS_WEIGHTS["new_dimension"] = 15  # 5-20分范围
```

### 集成到现有系统
```python
# API 封装示例
def analyze_hotel_gaps(hotel_id, reviews_data):
    """分析特定酒店的服务缺口"""
    # Module 1: 构建档案
    hotel_profile = build_single_hotel_profile(hotel_id, reviews_data)

    # Module 2: 计算评分
    gaps = compute_hotel_gaps(hotel_profile)

    return {
        'hotel_id': hotel_id,
        'top_gaps': gaps.head(10).to_dict('records'),
        'summary': generate_gap_summary(gaps)
    }
```

---

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'Add amazing feature'`
4. 推送分支: `git push origin feature/amazing-feature`
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 📧 Email: [your-email]
- 🐛 Issues: [GitHub Issues](repository-url/issues)

---

**🎉 祝您使用愉快！如果这个项目对您有帮助，请给我们一个 ⭐ Star！**