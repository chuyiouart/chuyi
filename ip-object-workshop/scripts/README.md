# IP 实物化五天实战营：确定性网站发布器

`workshop_publish.py` 只负责把已审核的每日内容包发布为静态页面，不负责调用模型或生成文案。

## 数据文件

- `../course-calendar.json`：72 天公开日历与真实发布状态。
- `../course-updates.js`：由日历确定性生成，供浏览器读取。

## 命令

```bash
python scripts/workshop_publish.py validate --root .
python scripts/workshop_publish.py build-js --root .
python scripts/workshop_publish.py publish --root . --manifest /path/to/manifest.json
```

## 发布清单字段

必填：

- `date`
- `type`
- `title`
- `summary`
- `slug`
- `heroImage`
- `lead`
- `sections`
- `cta.label`
- `cta.url`

可选：

- `galleryImages`
- `disclaimer`

## 安全规则

- 公开内容不得包含 METRION / 元维构旧品牌。
- 公开文件不得包含腾讯问卷统计后台地址。
- 只允许发布日历中已经存在的日期。
- 文章、图片、日历和 JavaScript 更新由同一次命令完成。
- Git 操作必须显式暂存 `ip-object-workshop/` 下允许的文件，禁止使用 `git add .`。
