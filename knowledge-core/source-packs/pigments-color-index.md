# SP-01 颜料、Colour Index 与颜色属性

## 用途

服务色相、纯度、限色、白色颜料、透明度、遮盖力、耐光性和材料记录。对应 `KM-004`、`KM-005`、`KM-011`、`KM-013` 至 `KM-018`。

## 核心来源

1. Art is Creation：[Pigment Database Quick Reference Index](https://www.artiscreation.com/color_index_index.html)
2. Art is Creation：[Color Index Names](https://artiscreation.com/Color_index_names.html)
3. CIE：`SRC-EXIST-0093` *Colorimetry, 4th Edition*
4. CIE：`SRC-EXIST-0094` *International Lighting Vocabulary*
5. George Field：*Field's Chromatography*，Art is Creation 书目 `AIC-BOOK-0240`
6. `Students' Text-Book of Color`，Art is Creation 书目 `AIC-BOOK-0176`
7. Getty Conservation Institute：*Historical Painting Techniques, Materials, and Studio Practice*，Art is Creation 书目 `AIC-BOOK-0241`

## 可进入知识模块的结论

- Colour Index Generic Name 用于识别颜料类别，如 PW6、PB29、PR101；商品颜色名不能替代颜料身份。
- 颜料代码仍不足以预测一支成品颜料的全部表现。连接料、颜料浓度、粒径、分散和研磨会改变透明度、着色力、流动和表面。
- 色相、明度和课程所说的纯度要同时观察；屏幕色值不能直接等同于实体颜料表现。
- 历史色彩书可用于追踪术语和方法演变，但不能单独支撑现代耐光、安全或产品选择。
- Art is Creation 的颜料页适合作为快速定位入口；重要参数必须回到现行标准、保护科学和具体制造商资料。

## 教学输出

- 颜料管身识读卡：商品名、Colour Index、连接料、耐光等级、透明度、SDS。
- 色相-明度-纯度三维定位图。
- 遮盖力、着色力、混白和薄刮四项试片。
- 历史颜料名与现代产品名对照，但不提供危险制备步骤。

## 已建立的本地索引

- 结构化数据：`data/pigments.json`，共 872 条；覆盖黄、橙、红、紫、蓝、绿、棕、黑、白和杂项材料 10 类。
- 浏览器数据：`data/pigments-data.js`，供静态页面直接读取，国内访问不依赖原站实时可用性。
- 网站入口：`pigments.html`，支持 CI 编码、中英文名称、化学组成、透明度、耐光性与风险等级检索。
- 生成脚本：`knowledge-core/scripts/build_pigment_database.py`，用于重新抓取、去重、标准化和生成双语初稿。
- 内容边界：公开数据不包含原站的长篇旁注、营销名称清单和历史配方，只保留标识与简明事实字段。
- 审校状态：162 条常用颜料名已进入人工译名表；其余记录以 CI 通用中文名作为可检索初译，不能直接视为出版定稿。
- 详情扩展：`knowledge-core/data/pigment-enrichment.json`，首批 19 个课程核心 CI 已完成 `deep-reviewed-v1`，包含身份判断、适用场景、混色、操作、限制、替代与现代来源。
- 开放图片：`knowledge-core/data/pigment-image-manifest.json`，首批 13 张已本地化图片均记录作者、许可、来源页和处理方式；不得脱离署名清单复制。
- 网页兼容包：`data/pigment-enrichment-data.js`，由 `knowledge-core/scripts/build_pigment_enrichment.py` 从以上两份数据生成。

## 限制

- Art is Creation 页面为 `yellow`：可研究、摘要和引用事实，不能整站复制翻译。
- Field 等历史资料只作为 C 级历史证据。
- 颜料安全至少需要一项现代 A 级来源；学校版本采用更严格材料清单。
- “基础操作卡”只用于建立试片和提出问题，不得被描述成该颜料已经逐条尽调。
- 危险等级 C、D 只输出身份、风险、替代与专业边界，不输出制备、研磨、喷涂或打磨步骤。
