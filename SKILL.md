---
name: home-buyer-helper
description: 买房助手 - 帮助用户记录房源信息、计算购房预算与月供、生成房源对比表格、提供买房避坑指南、智能推荐房源、批量导入、网页解析、图片识别、网站抓取。使用场景：(1) 记录和筛选房源信息 - 说"记录一个新房源"或"查看我的房源列表"；(2) 计算购房预算 - 说"帮我算一下购房预算"或"这个房子每月要花多少钱"；(3) 生成房源对比表格 - 说"对比一下这几个房源"或"生成房源对比表"；(4) 买房避坑指南 - 说"买房要注意什么"或"有什么避坑建议"；(5) 智能推荐房源 - 说"给我推荐几套房源"、"我工作在xxx，给我推荐附近3KM的房源，总价在xx以内"；(6) 看房记录 - 说"我在看房，想记录每个房子的优缺点"；(7) 批量导入 - 说"批量导入房源"；(8) 网页解析 - 说"帮我解析这个链接"；(9) 图片识别 - 说"从这张图片提取房源信息"；(10) 网站抓取 - 说"从贝壳/链家/58同城抓取房源"。
---

# 买房助手

帮助用户高效管理买房全流程，从房源发现、记录、对比到最终决策。

## 功能模块

### 1. 房源记录与筛选

**记录新房源：**
```
用户说："记录一个新房源"
需要收集的信息：
- 房源地址/小区名称（`--community`，必填；`--name` 改为备注别名，非小区名）
- 售价（总价，万元，`--price`）
- 户型（几室几厅，`--room-type`）
- 面积（建筑面积 `--area` / 套内面积 `--inner-area`）
- 楼层/总楼层/电梯（`--floor` / `--total-floors` / `--has-elevator`）
- 朝向（`--orientation`）
- 建筑年代/房龄（`--year-built` / `--building-age`）
- 装修情况（`--decoration`）
- 产权性质（`--property-type`，商品房/经济适用房等）
- 房屋类型（`--house-type`，普通住宅/公寓/别墅等）
- 是否满五唯一（`--is-full5-unique`）
- 是否有抵押/查封
- 学区/学位（`--school-district` / `--school-tier` / `--school-notes`，推荐中低权重参考）
- 车位情况（`--has-parking` / `--parking-price`）
- 交通情况（`--transport`，文字描述；`--nearest-metro` 最近地铁站；`--metro-distance` 最近地铁站步行距离，单位米）
- 参考月租（`--monthly-rent`，元/月）/ 租金来源（`--rent-source`）
- 周边配套（`--facilities`，学校/医院/商场/公园等）
- 税费估算（`--tax-estimate`，万元）
- 中介费率（`--agent-fee-rate`）/ 中介费（`--agent-fee`，万元）
- 个人评分（`--my-score`，1-10分）
- 中介/房东联系方式（`--contact`）
- 优缺点备注（`--pros` / `--cons`）
- 房源链接（`--url`）/ 图片（`--images`）
```

**查看房源列表：**
- 列出所有记录的房源
- 支持按总价、面积、户型、位置、房龄、是否满五等筛选

**查看单个房源详情：**
- 显示该房源的所有信息，包括税费估算

**更新房源状态：**
- 标记为"待看房"/"已看房"/"有意向"/"已放弃"/"已签约"/"已过户"

### 2. 智能推荐房源

**出租投资/近地铁优先推荐：**
```
用户说：
- "给我推荐几套房源"
- "帮我筛选适合上班族租的近地铁房源"
- "总价500万以内，优先看月租5000以上、租售比高的房源"
- "近地铁权重大一点，学区只做参考"
- "租售比2%以上重点推荐，800米以内地铁优先"

处理流程：
1. 询问用户的购房需求（如果未提供）
   - 总价预算范围（硬过滤，不参与评分）
   - 参考月租 / 租售比阈值
   - 地铁距离阈值
   - 适租户型和面积段
   - 权重是否需要覆盖默认值

2. 从已记录的房源中筛选匹配项

3. 按匹配度排序推荐
   - 租金收益
   - 地铁/通勤友好
   - 户型面积适租性
   - 流动性/交易属性
   - 房龄 / 装修状况
   - 学区参考（低权重）
```

**推荐算法：**
- 预算/价格：只作为硬过滤，资金固定时不参与评分
- 默认 rental 权重：租金收益35、地铁通勤30、适租户型15、流动性10、房龄装修5、学区参考5
- 所有权重和阈值都必须作为执行参数支持覆盖，不能写死在使用流程里
- 默认重点标签：近地铁强推荐、地铁友好、上班族适租、高租金、高租售比、强租售比、学区参考
- 租售比计算：`monthly_rent * 12 / (price_wan * 10000) * 100`
- 缺少租金时，可用 `scripts/enrich_rent_estimates.py` 按小区查询贝壳租房第一页整租样本，以每㎡月租中位数 * 二手房面积估算 `monthly_rent`；写回时记录 `rent_per_sqm`、`rent_sample_count` 和 `rent_reference_url`
- 如果房源来自贝壳/链家 `--near-subway` 抓取但缺少精确 `metro_distance`，推荐时按“地铁友好”计分；精确距离硬过滤仍要求 `metro_distance`
- 需要方便点击详情时，推荐输出使用 `--format markdown`；人在回路抓取结束后的推荐默认就是带链接的 Markdown 表格

**默认命令：**
```
python3 scripts/recommend_listings.py \
  --profile rental \
  --budget-max <预算万> \
  --target-monthly-rent 5000 \
  --target-rent-yield 2.0 \
  --strong-rent-yield 2.5 \
  --max-metro-distance 800 \
  --format markdown
```

**调整权重示例：**
```
python3 scripts/recommend_listings.py \
  --budget-max 500 \
  --weight-rent 35 \
  --weight-metro 35 \
  --weight-rental-fit 12 \
  --weight-liquidity 8 \
  --weight-condition 5 \
  --weight-school 5 \
  --target-monthly-rent 5500 \
  --target-rent-yield 2.2 \
  --metro-good-distance 800
```

### 3. 看房记录与评分

**看房时记录：**
```
用户说："我在看房，想记录每个房子的优缺点"

记录内容：
- 房源ID
- 看房时间
- 实际与描述是否一致
- 采光情况（1-5分）
- 通风情况（1-5分）
- 噪音情况（1-5分）
- 房屋保养状况（1-5分）
- 户型合理性（1-5分）
- 车位便利性（1-5分）
- 学区/周边配套评分（1-5分）
- 中介/房东态度
- 税费/中介费明细
- 优缺点详细记录
- 整体评分（1-10分）
- 是否考虑签约
```

### 4. 购房预算计算

**计算总成本：**
```
输入：总价、首付比例、贷款年限、LPR利率、税费、中介费
输出：
- 首付金额
- 贷款金额
- 等额本息/等额本金月供
- 契税（首套/二套不同税率）
- 增值税及附加（满二唯一免增值税）
- 个人所得税
- 中介费
- 其他杂费（评估费、登记费等）
- 过户当日需支付总额
- 首月+过户总支出（首付+税费+中介费等）
- 每月月供 + 物业费 + 取暖费 总支出
```

**贷款计算器：**
- 支持公积金贷款 + 商业贷款组合
- 显示不同首付比例下的月供对比
- 支持LPR加点/减点自定义

**预算建议：**
- 首付资金来源建议（自有/父母资助/其他）
- 月供不超过家庭月收入的40-50%（含公积金覆盖部分）
- 预留6-12个月月供的应急资金

### 5. 房源对比表格

**生成对比表：**
- 选择2-5个房源进行对比
- 对比维度：总价、单价、面积、户型、楼层、朝向、房龄、税费、首付、月供、通勤、学区、优缺点、看房评分等
- 输出格式：Markdown 表格或飞书多维表格

### 6. 买房避坑指南

**查看指南：**
- 看房前准备
- 现场看房检查清单
- 产权核验要点
- 签约注意事项
- 常见陷阱识别

详见 [references/pitfall-guide.md](references/pitfall-guide.md)

### 7. 批量导入房源

**从CSV/Excel导入：**
```
用户说："批量导入房源"
支持格式：
- CSV文件（逗号分隔）
- Excel文件（.xlsx/.xls）

必需字段：name（小区名称）、price（总价万）
可选字段：address、room_type、area、floor、orientation、year_built、decoration、
property_type、is_full5_unique、has_parking、school_district、transport、
facilities、contact、pros、cons、source、url、tax_estimate、agent_fee
```

### 8. 网页链接解析

**粘贴链接自动解析：**
```
用户说："帮我解析这个链接" + 粘贴URL
支持平台：
- 贝壳找房 (ke.com)
- 链家 (lianjia.com)
- 安居客 (anjuke.com)
- 58同城 (58.com)
- 其他通用网页

自动提取：小区名称、总价、单价、户型、面积、楼层、朝向、建筑年代、描述等
```

### 9. 图片识别（OCR）

**上传房源截图：**
```
用户说："从这张图片提取房源信息" + 上传截图
自动识别：
- 小区名称
- 总价/单价
- 户型/面积
- 楼层/朝向
- 联系方式
- 房源描述

需要安装OCR工具：
- 方案1: pip install pytesseract pillow + brew install tesseract tesseract-lang
- 方案2: pip install easyocr
```

### 10. 网站抓取房源

**自动抓取买房网站：**
```
用户说："从贝壳抓取北京朝阳区500-800万的房源"
支持平台：
- 贝壳找房 (ke.com)
- 链家 (lianjia.com)
- 58同城 (58.com)
- 安居客 (anjuke.com)

抓取参数：
- 城市（北京、上海、广州、深圳等）
- 区域/商圈/学区
- 总价区间
- 房型要求
- 抓取数量
```

**贝壳/链家验证码处理优先级：**
- 严格反爬场景优先让用户在系统 Chrome 中手动筛选、翻页、登录和过验证，然后调用 `scripts/crawl_interactive.py --current-chrome --save` 读取当前标签页。
- URL 中包含 `su1` / `sf1` 时，`--current-chrome` 会自动标记近地铁 / 普通住宅；可额外传 `--budget-min` / `--budget-max` 作为本地价格保护。
- 用户要排除商住两用/办公类时，在抓取和推荐命令加 `--exclude-keywords 大厦,商务,商住,商业,办公,写字楼,酒店式,公寓`；如果“大厦”误伤纯住宅，可去掉“大厦”或只传明确黑名单词。
- 不要把无人在场的自动翻页作为默认方案；贝壳页码 URL 容易触发极验。需要多页时，用 `--auto-next` 从当前 Chrome 页开始连续读取，默认最多10页；到最后一页或触发验证时停止，触发验证则让用户在 Chrome 中过验证，页面稳定后继续执行。
- `--current-chrome` 会等待列表 DOM 出现，避免 Chrome 标题/URL 已更新但列表内容尚未保存出来时误判为无列表。
- 抓取结束后默认按评分展示前15名；如果本次 URL/参数命中 `su1` / `sf1`，榜单也只看近地铁 / 普通住宅；默认输出 Markdown 表格，房源名带详情链接；需要调整数量时用 `--recommend-limit <N>`，不想展示时用 `--no-recommend`。
- 不带 `--auto-next` 时只读取当前页并提示可以翻页；`--open-next` 是旧参数，等同 `--auto-next`。
- 如果用户已经保存了列表页 HTML，再用 `--html` 解析。
- 不建议绕过验证码或高频请求；抓取失败时应提示用户使用人在回路流程。

房源数据默认存储在 `data/listings.json`
看房记录存储在 `data/viewings.json`

## 使用脚本

- `scripts/add_listing.py` - 添加新房源（支持 --community 小区名 --metro-distance 地铁距离 --my-score 个人评分）
- `scripts/update_status.py` - 更新房源状态
- `scripts/list_listings.py` - 列出房源（支持筛选，展示：小区 / 名称 / 总价 / 面积 / 地铁距离 / 个人评分 / 状态 / 链接）
- `scripts/recommend_listings.py` - 智能推荐房源；支持 `--only-near-subway` / `--only-ordinary-residence` / `--exclude-keywords` 做硬过滤
- `scripts/enrich_rent_estimates.py` - 按小区租房第一页整租样本估算参考月租；贝壳租房需登录时用 `--chrome --pause-on-block`
- `scripts/add_viewing.py` - 记录看房信息与评分
- `scripts/calculate_budget.py` - 计算购房预算与月供
- `scripts/compare_listings.py` - 生成对比表（含小区 / 距地铁 / 我的评分列）
- `scripts/import_listings.py` - 批量导入房源（CSV/Excel）
- `scripts/parse_url.py` - 从网页链接解析房源；遇到验证码时建议改用交互式抓取
- `scripts/parse_image.py` - 从图片识别房源信息（OCR）
- `scripts/crawl_listings.py` - 从买房网站抓取房源；支持 `--html` 解析已保存列表页，贝壳/链家支持 `--near-subway`、`--ordinary-residence`、`--exclude-keywords` 与 `--pages`
- `scripts/crawl_interactive.py` - 人在回路网页抓取；贝壳/链家严格反爬时优先用 `--current-chrome --auto-next` 从用户已手动筛选/过验证的当前页开始读取，默认最多10页，触发验证即停止；抓取结束后默认展示评分前15名；也支持 `--near-subway`、`--ordinary-residence`、`--exclude-keywords` 与 `--pages`

## 工作流

### 记录新房源
1. 询问用户房源基本信息（总价、户型、面积、房龄、产权等）
2. 调用 `scripts/add_listing.py` 保存数据
3. 确认记录成功

### 智能推荐房源
1. 询问用户的购房需求（位置、总价、首付、户型、学区等）
2. 调用 `scripts/recommend_listings.py` 进行匹配
3. 展示推荐结果，说明推荐理由

### 看房记录
1. 询问用户看房的是哪个房源
2. 引导用户逐项评分和记录
3. 调用 `scripts/add_viewing.py` 保存记录
4. 生成看房总结

### 计算购房预算
1. 询问总价、首付比例、贷款年限等信息
2. 调用 `scripts/calculate_budget.py`
3. 展示预算分析结果（首付、月供、税费明细）

### 生成对比表格
1. 询问要对比的房源ID或名称
2. 调用 `scripts/compare_listings.py`
3. 输出对比表格

### 查看避坑指南
1. 读取 `references/pitfall-guide.md`
2. 根据用户需求展示相关内容

### 批量导入房源
1. 询问用户文件路径
2. 调用 `scripts/import_listings.py` 导入数据
3. 显示导入结果

### 网页链接解析
1. 获取用户提供的链接
2. 调用 `scripts/parse_url.py` 解析页面
3. 显示提取的信息并确认保存

### 图片识别
1. 获取用户上传的图片路径
2. 调用 `scripts/parse_image.py` 进行OCR识别
3. 显示提取的信息并确认保存

### 更新房源状态
1. 询问用户要更新哪个房源、新状态
2. 调用 `scripts/update_status.py`
3. 确认更新成功

### 查看房源详情
1. 询问用户要查看哪个房源ID
2. 调用 `scripts/list_listings.py --id <ID>`
3. 展示完整信息（含税费估算、个人评分、地铁距离、房源链接）

### 网站抓取
1. 询问目标平台、城市、区域、预算
2. 如果是贝壳/链家，优先让用户在系统 Chrome 中手动选好区域、价格、近地铁、普通住宅并停在目标起始页，然后调用 `scripts/crawl_interactive.py --platform 贝壳 --city <城市> --budget-min <最低总价> --budget-max <最高总价> --current-chrome --auto-next --save`，默认最多读10页；触发验证后让用户过验证再继续；抓取结束后默认展示评分前15名
3. 如果用户已经保存了页面 HTML，调用 `scripts/crawl_listings.py --platform 贝壳 --city <城市> --html <文件路径> --save`
4. 只有在不需要登录/验证码时才直接调用 `scripts/crawl_listings.py`
5. 若推荐评分缺少租金，调用 `scripts/enrich_rent_estimates.py --city <城市> --budget-max <预算> --only-near-subway --only-ordinary-residence --chrome --pause-on-block --save`，按小区租房第一页整租样本估算月租
6. 显示抓取结果并确认保存
