# 初艺颜料详情尽调 · 第二阶段报告

日期：2026-07-16

版本：1.0.0

状态：首批课程核心颜料已接入网站；全库仍按批次持续尽调

## 本阶段结果

- 872 条颜料记录全部获得统一的五步试片操作卡和按风险等级生成的操作边界。
- 19 个课程核心 CI 完成 `deep-reviewed-v1`：增加身份判断、适用场景、混色行为、操作、限制、替代与现代来源。
- 13 张开放许可图片已下载到 `assets/pigments/`，覆盖 14 个 CI；每张都保留作者、许可、原始页面与处理说明。
- 网站详情页新增图片、审校徽标、专业实践卡、来源区和“已尽调/基础操作卡”筛选。
- 新建 `PIGMENT-DETAIL-CALLING-PROTOCOL.md`，供课程、PDF、五天培训、教师手册与 B2B 流程复用。

## 证据策略

Art is Creation 继续只承担条目发现。核心性质优先用 MFA Boston CAMEO；油画锌白保存问题使用 Smithsonian Museum Conservation Institute 研究；镉材料的操作边界参考 OSHA；一般艺术材料安全参考 CPSC。具体品牌的最终操作仍必须查最新版 SDS。

## 图片策略

图片来自 Wikimedia Commons。当前许可包括 Public domain、CC0 1.0 和 CC BY-SA 3.0。网站本地副本只做等比缩放与 JPEG 优化，没有颜色校正；页面明确说明粉末图不是涂膜或色度标准。

## 安全策略

- PW1 铅白、PY35/PY37 镉黄、PR108 镉红不进入儿童、家庭或普通培训的实际操作。
- 钴、铬、炭黑等条目不允许把干粉、喷涂和打磨写成普通课程步骤。
- 本库不生成颜料合成、加热、研磨或历史危险配方。
- A/B/C/D 只做数据库筛查，实际产品以 SDS 和场地条件为准。

## 技术文件

- `knowledge-core/data/pigment-enrichment.json`：专业详情源数据。
- `knowledge-core/data/pigment-image-manifest.json`：图片授权清单。
- `data/pigment-enrichment-data.js`：静态网页数据包。
- `knowledge-core/scripts/build_pigment_enrichment.py`：生成网页数据包。
- `knowledge-core/scripts/download_pigment_images.py`：按核验清单下载并标准化图片。

## 验收

- 872 条基础记录可解析。
- 19 个尽调 CI 全部命中现有记录。
- 13 张本地图片均存在、可读取且授权字段完整。
- JSON 与两个网页 JS 文件通过语法检查。
- 页面仍可通过 `file://` 直接读取，不依赖 Art is Creation 或 Wikimedia 实时可用性。

## 下一步建议

下一批不要平均分配给剩余 853 个 CI，而应先读取课程和 PDF 实际出现的颜料清单，再补齐约 30 个高频条目。这样每一次尽调都会立即回流课程，而不是形成与教学脱离的百科目录。
