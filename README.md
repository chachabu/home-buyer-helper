# 🏠 买房助手

> 用 AI 帮你找房、比价、算月供、避坑 —— 买房最耗时的这些事，一句话交给 OpenClaw 自主完成。

[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-blue?logo=openclaw)](https://github.com/chachabu/openclaw)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-green)](https://python.org)
[![MIT License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🤖 一句话让 AI 成为你的买房顾问

还在手动刷贝壳/链家？还在 Excel 里算月供？还在对着几十套房源记笔记？

**买房助手**把这些全自动化了——

- 全网扒房源，一句话抓取贝壳、链家、安居客、58同城
- 自动录入、标签化、给每套房算税费和月供
- 多套横向对比，优缺点一目了然
- 看房现场打分，回家自动生成评分报告
- 智能推荐匹配你的预算、户型、学区、通勤需求

**你只需要说一句话，剩下的交给 AI。**

---

## ✨ 核心能力

### 🔍 全网房源抓取

```
你：帮我找 [目标城市][目标区域] 总价 [XX万] 以内的 [户型偏好]
AI：自动打开贝壳/链家，抓取所有匹配房源，录入本地数据库
```

支持平台：**贝壳找房 · 链家 · 安居客 · 58同城**

需要登录的平台，AI 会提醒你扫码登录，完成后自动批量爬取。

贝壳/链家如果触发验证码，推荐使用人在回路模式：脚本打开真实浏览器，你在页面里完成登录、扫码或验证码，回到终端按回车后脚本读取当前页面并解析房源。这个流程不绕过验证码，也不需要逐条手抄数据。

---

### 📝 智能房源管理

AI 帮你把所有看中的房源整理得井井有条：

| 字段 | 说明 |
|------|------|
| 基础信息 | 总价、单价、户型、面积、楼层、朝向 |
| 房产信息 | 房龄、装修、产权性质、是否满五唯一 |
| 居住属性 | 学区、车位、电梯、物业 |
| 财务数据 | 预估税费、中介费、首付、月供 |
| 周边配套 | 地铁距离、商圈、医院、学校 |
| 状态跟踪 | 待看房 → 已看房 → 有意向 → 已签约 → 已过户 |

---

### 🎯 智能推荐

根据你的需求自动匹配和排序：

```
你：我在 [公司/商圈] 附近，预算 [XX万]，想要 [X室X厅]，学区优先
AI：从已有房源中筛选，按匹配度打分排序，给出推荐理由
```

评分维度：**价格合理性 · 通勤便利性 · 学区匹配度 · 房龄 · 升值空间**

---

### 💰 预算 & 月供一键计算

输入总价，自动输出完整财务账单：

```
总价 [XXX万] → 首付 [XX万]，贷款 [XXX万]
月供（等额本息）→ [XXXX] 元/月
契税 [X.X万] + 增值税（满二免） + 个税（满五唯一免） + 中介费 [X.X万]
过户当日需支付 → ~[XX] 万元
```

支持：**等额本息 / 等额本金 / 公积金 + 商贷组合**

---

### 📊 房源横向对比

选择 2-5 套房源，一键生成对比表格：

- 总价 / 单价 / 面积 / 户型 / 房龄
- 首付 / 月供 / 税费
- 学区 / 地铁 / 配套
- 优缺点逐项对比 + 智能分析

---

### ⭐ 看房评分系统

看房过程中实时打分，回家自动汇总：

```
采光 ⭐⭐⭐⭐☆  通风 ⭐⭐⭐⭐☆  噪音 ⭐⭐⭐☆☆
保养 ⭐⭐⭐☆☆  户型 ⭐⭐⭐⭐☆  车位 ⭐⭐☆☆☆
学区 ⭐⭐⭐⭐⭐  整体 7.5/10 → 考虑签约
```

---

### 🛡️ 买房避坑指南

内置完整避坑手册，覆盖：

- ✅ 购房资格 & 征信检查清单
- ✅ 现场看房 30+ 项逐项核对
- ✅ 产权核验（抵押 / 查封 / 居住权 / 学位占用）
- ✅ 合同签约陷阱识别（阴阳合同 / 补充条款 / 违约责任）
- ✅ 税费速查表 & 资金安全指南

---

### 📥 批量导入

CSV / Excel 一键导入，瞬间建好候选池。适合从各平台导出的房源列表批量录入。

---

## 🚀 快速开始

### 安装

```bash
# 通过 ClawHub 安装（推荐）
clawhub install home-buyer-helper

# 或手动 clone
git clone git@github.com:chachabu/home-buyer-helper.git ~/.openclaw/skills/home-buyer-helper
```

### 数据存储

数据与脚本同仓库，自动纳入 git 版本管理：

```
home-buyer-helper/
├── data/
│   ├── listings.json   # 房源数据
│   └── viewings.json   # 看房记录
└── scripts/
```

### 一行命令搞定常见操作

```bash
# 录入新房源
python3 scripts/add_listing.py \
  --community "目标小区" \
  --name "备注别名（如：满五唯一/精装修）" \
  --price <总价万元> \
  --room-type "<户型 如 2室1厅>" \
  --area <面积㎡> \
  --year-built <建成年份> \
  --building-age <房龄> \
  --decoration <装修情况> \
  --has-elevator <有/否> \
  --school-district "<学区>" \
  --transport "<交通描述>" \
  --metro-distance <距地铁米数> \
  --tax-estimate <税费估算万元> \
  --agent-fee-rate <中介费率 如 0.02> \
  --my-score <个人评分1-10> \
  --url "<房源链接>" \
  --pros "<优点>" --cons "<缺点>"

# 列出全部房源（含小区/总价/面积/地铁/评分/链接）
python3 scripts/list_listings.py

# 按条件筛选
python3 scripts/list_listings.py \
  --min-price <最低价> \
  --max-price <最高价> \
  --room-type "<户型关键字>"

# 看单个房源详情
python3 scripts/list_listings.py --id <ID>

# 算月供
python3 scripts/calculate_budget.py \
  --price <总价> \
  --down-payment <首付> \
  --loan-rate <利率> \
  --loan-years <年限>

# 对比房源
python3 scripts/compare_listings.py --ids <房源ID1> <房源ID2> <房源ID3>

# 智能推荐
python3 scripts/recommend_listings.py \
  --max-price <预算> \
  --room-type "<户型>" \
  --min-area <最低面积>

# 贝壳/链家：人在回路抓取（推荐）
python3 scripts/crawl_interactive.py \
  --platform 贝壳 \
  --city 北京 \
  --area 朝阳区 \
  --budget-min 300 \
  --budget-max 800 \
  --limit 20 \
  --save

# 如果已经在浏览器中保存了列表页 HTML
python3 scripts/crawl_listings.py \
  --platform 贝壳 \
  --city 北京 \
  --html page.local.html \
  --save
```

---

## 📂 项目结构

```
home-buyer-helper/
├── SKILL.md              # OpenClaw 技能定义
├── _meta.json            # 元数据
├── README.md             # 本文件
├── references/
│   └── pitfall-guide.md  # 买房避坑指南
├── data/                 # 房源 & 看房数据（git 版本管理）
│   ├── listings.json     # 房源数据
│   └── viewings.json     # 看房记录
└── scripts/              # 功能脚本（Python 3.9+，纯标准库）
    ├── add_listing.py        # 添加新房源（自动 git push）
    ├── update_status.py      # 更新房源状态（自动 git push）
    ├── add_viewing.py        # 记录看房（自动 git push）
    ├── list_listings.py      # 列出/筛选/详情
    ├── recommend_listings.py # 智能推荐
    ├── calculate_budget.py   # 预算 & 月供计算
    ├── compare_listings.py   # 房源对比表
    ├── import_listings.py    # 批量导入 CSV/Excel
    ├── parse_url.py          # 网页链接解析
    ├── parse_image.py        # 图片 OCR 识别
    ├── crawl_listings.py     # 网站自动抓取
    ├── crawl_interactive.py  # 交互式抓取（支持登录场景）
    └── _git_push.py          # 内部工具：自动 git add+commit+push
```

---

## 🧠 典型工作流

```
① 告诉 AI 你的需求
   "帮我找 [目标城市][目标区域][目标预算] 以内的 [户型偏好]"

② AI 全网扒取 + 自动录入
   贝壳/链家/安居客 → 抓取 → 标准化录入 → 本地数据库

③ 筛选 + 对比
   AI 按预算/户型/学区/通勤排序 → 生成对比表 → 推荐 TOP 5

④ 看房 + 打分
   现场用 AI 记笔记 → 采光/噪音/户型打分 → 自动汇总

⑤ 算账 + 决策
   首付/月供/税费全算 → 看房评分 + 财务压力 → 最终决策
```

---

## 🔧 环境要求

- **Python** ≥ 3.9（macOS 自带 3.9+ 即可）
- **OpenClaw** ≥ 2025.0（可选，用于技能自动加载）
- 核心脚本纯标准库实现
- 人在回路浏览器模式可选安装 Playwright：`python3 -m pip install playwright && python3 -m playwright install chromium`
- 图片 OCR 需额外安装：`pip install easyocr` 或 `pip install pytesseract`

---

## 💡 适用场景

| 场景 | 能力 |
|------|------|
| 🔎 **找房初期** | 全网抓取 + 智能推荐 + 候选池管理 |
| 📋 **筛选对比** | 批量对比表格 + 综合评分 + 优缺点分析 |
| 🏠 **实地看房** | 看房记录 + 7维评分 + 自动汇总 |
| 💰 **财务规划** | 月供计算 + 税费明细 + 首付建议 |
| 📝 **签约准备** | 避坑指南 + 合同检查清单 + 资金安全 |

---

## 🤝 贡献

欢迎提 Issue 和 PR！

```bash
# 本地开发
cd ~/.openclaw/skills/home-buyer-helper
git checkout -b feat/your-feature
# 改完提交
git push origin feat/your-feature
```

---

## 📄 License

MIT

---

<div align="center">

**用 AI 把买房从"体力活"变成"决策活"** 🦾

[⭐ Star on GitHub](https://github.com/chachabu/home-buyer-helper) · [🐛 报告问题](https://github.com/chachabu/home-buyer-helper/issues)

</div>
