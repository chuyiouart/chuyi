# 初艺 OUART 静态站

这个目录是从 `https://chuyiouart.com/` 迁移出来的 GitHub Pages 静态站原型。

## 内容结构

- `index.html`：新版首页
- `courses.html`：课程介绍
- `gallery.html`：作品集入口
- `resources.html`：STL 模型分享索引
- `open-class.html`：公开课文章索引
- `shop.html`：旧 WooCommerce 商品展示页
- `contact.html`：联系与咨询入口
- `data/`：从旧 WordPress REST API 导出的公开 JSON
- `assets/`：已本地化的 logo 和代表图

## 本地预览

可以直接双击 `index.html` 打开。资源库、公开课和商店页已经内置 `data/site-data.js`，不依赖本地 HTTP 服务。

如果需要模拟 GitHub Pages 的 HTTP 环境，也可以运行：


```powershell
cd C:\Users\saint\Desktop\其他\chuyiouart-site
node server.mjs
```

然后打开 `http://127.0.0.1:4177/`。

## 迁移说明

旧站的 WordPress / Elementor / WooCommerce 动态能力不会在 GitHub Pages 原样运行。
新版站点把购物车、支付、会员登录、评论等功能改为展示和咨询入口。
