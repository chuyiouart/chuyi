import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const root = process.cwd();
const outRoot = path.join(root, "content");
const migratedAssetDir = path.join(root, "assets", "migrated");
const execFileAsync = promisify(execFile);
const assetVersion = "20260612a";

const readJson = async (file) => JSON.parse(await fs.readFile(path.join(root, file), "utf8"));
const slugify = (value) =>
  String(value || "")
    .replace(/<[^>]+>/g, "")
    .replace(/[\\/:*?"<>|]+/g, "-")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .slice(0, 80) || "untitled";

const htmlText = (html = "") =>
  html
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();

const titleOf = (item, fallback) => {
  const title = htmlText(item?.title?.rendered || "");
  if (title) return title;
  try {
    const slugTitle = decodeURIComponent(item?.slug || "").replace(/-/g, " ").trim();
    if (slugTitle) return slugTitle;
  } catch {}
  return fallback;
};

const hashName = (url) => {
  const clean = url.split("?")[0].split("#")[0];
  const extMatch = clean.match(/\.(jpe?g|png|webp|gif)$/i);
  const originalExt = extMatch ? extMatch[1].toLowerCase().replace("jpeg", "jpg") : "jpg";
  const ext = originalExt === "png" ? "jpg" : originalExt;
  return `${crypto.createHash("sha1").update(clean).digest("hex").slice(0, 16)}.${ext}`;
};

const ensureDir = async (dir) => fs.mkdir(dir, { recursive: true });

const normalizeUrl = (url = "") => {
  if (url.startsWith("//")) return `https:${url}`;
  return url.replace(/&amp;/g, "&");
};

const isUploadUrl = (url) => /^https:\/\/chuyiouart\.com\/wp-content\/uploads\//i.test(normalizeUrl(url));
const isOldSiteUrl = (url) => /^https:\/\/chuyiouart\.com/i.test(normalizeUrl(url));

const posts = [
  ...(await readJson("data/posts-page-1.json")),
  ...(await readJson("data/posts-page-2.json")),
];
const pages = await readJson("data/pages.json");
const products = await readJson("data/products.json");

const requiredPageIds = new Set([1641, 1646, 1982, 2109, 2110, 2113, 2114, 2115]);
const coursePageIds = new Set([1982, 2109, 2110]);
const galleryPageIds = new Set([2113, 2114, 2115]);
const pageDescriptions = new Map([
  [1982, "面向成人绘画学习者的系统油画课程，从材料、色彩、构图、临摹到个人创作，帮助学习者逐步建立观察与表达的方法。"],
  [2109, "面向 5-16 岁学生的综合美术课程，结合绘画、手工、设计与当代工具，重视想象力、造型能力和长期表达。"],
  [2110, "围绕景观模型、微缩场景与空间制作展开，把绘画、材料、结构和模型工艺结合在一起。"],
  [2113, "成人绘画作品记录不同阶段的练习、临摹与个人创作成果。"],
  [2114, "少儿美术作品呈现儿童在色彩、材料、造型和主题表达中的创造力。"],
  [2115, "模型场景作品展示人偶、景观、微缩空间和综合材料制作成果。"],
]);
const pageTitles = new Map([[1982, "成人油画课程"]]);
const courseHeroImages = new Map([
  [1982, "../../assets/course-oil-ai.jpg"],
  [2109, "../../assets/course-kids-ai.jpg"],
  [2110, "../../assets/course-model-ai.jpg"],
]);
const courseHighlights = new Map([
  [
    1982,
    [
      ["课程目标", "建立观察、构图、色彩和画面推进的方法，让学习者能绘画、会创作、懂欣赏、善思考。"],
      ["课程结构", "包含基础入门、印象大师、古典大师、创作训练和延展内容，适合长期系统学习。"],
      ["学习方式", "围绕材料示范、临摹分析、阶段练习和个人作品反馈展开，帮助每位学员找到自己的节奏。"],
    ],
  ],
  [
    2109,
    [
      ["年龄阶段", "面向 5-16 岁学生，根据年龄、基础和兴趣方向调整课程难度。"],
      ["课程内容", "覆盖绘画、色彩、手工、设计、材料实验与主题创作。"],
      ["学习目标", "培养观察力、想象力、造型能力和长期表达习惯。"],
    ],
  ],
  [
    2110,
    [
      ["课程方向", "围绕景观模型、微缩场景、空间结构和综合材料制作展开。"],
      ["核心训练", "学习构图、比例、材料处理、地形塑造和模型呈现。"],
      ["适合人群", "适合对模型制作、场景设计、空间表达感兴趣的学习者。"],
    ],
  ],
]);
const courseNotes = new Map([
  [
    1982,
    [
      ["基础入门", "认识油画材料、媒介、笔触和画布准备，建立稳定的观察与起稿方法。"],
      ["大师研究", "通过印象派与古典绘画案例理解色彩关系、光影结构、边缘处理和画面节奏。"],
      ["个人创作", "从临摹过渡到主题创作，结合阶段反馈完成更完整的个人作品。"],
      ["学习安排", "原课程内容按系统课时组织，可根据基础、目标和作品方向沟通具体学习路径。"],
    ],
  ],
]);
const pageExclusions = /membership|password|checkout|cart|account|thank-you|registration|join|wshop/i;
const visiblePages = pages.filter((page) => {
  const text = htmlText(page.content?.rendered || "");
  return requiredPageIds.has(page.id) || (text.length > 60 && !pageExclusions.test(page.slug || ""));
});

const pagePath = (type, item) => `./content/${type}/${item.id}.html`;
const pagePathFromContent = (type, item) => `../${type}/${item.id}.html`;

const byPostId = new Map(posts.map((item) => [String(item.id), `./content/posts/${item.id}.html`]));
const byPageId = new Map(visiblePages.map((item) => [String(item.id), `./content/pages/${item.id}.html`]));
const byProductLink = new Map(products.map((item) => [item.link, `./content/products/${item.id}.html`]));

const imageUrls = new Set();
for (const item of [...posts, ...visiblePages, ...products]) {
  const html = item.content?.rendered || "";
  for (const match of html.matchAll(/<img\b[^>]*\bsrc=["']([^"']+)["']/gi)) {
    const src = normalizeUrl(match[1]);
    if (isUploadUrl(src)) imageUrls.add(src);
  }
}

const imageMap = new Map(
  [...imageUrls].map((url) => [url, `assets/migrated/${hashName(url)}`])
);

const localLink = (href = "", currentPrefix = "../..") => {
  const url = normalizeUrl(href);
  if (isUploadUrl(url) && imageMap.has(url)) return `${currentPrefix}/${imageMap.get(url)}`;
  if (url === "https://chuyiouart.com/" || url === "https://chuyiouart.com") return `${currentPrefix}/index.html`;

  const postId = url.match(/[?&]p=(\d+)/)?.[1];
  if (postId && byPostId.has(postId)) return `${currentPrefix}/content/posts/${postId}.html`;

  const pageId = url.match(/[?&]page_id=(\d+)/)?.[1];
  if (pageId && byPageId.has(pageId)) return `${currentPrefix}/content/pages/${pageId}.html`;

  if (byProductLink.has(url)) return `${currentPrefix}/${byProductLink.get(url).replace("./", "")}`;

  if (url.includes("?cat=1")) return `${currentPrefix}/resources.html`;
  if (url.includes("?cat=18")) return `${currentPrefix}/open-class.html`;
  if (url.includes("?post_type=product") || url.includes("?product_cat=")) return `${currentPrefix}/shop.html`;
  if (/^https:\/\/chuyiouart\.com/i.test(url)) return `${currentPrefix}/index.html`;
  return href;
};

const cleanContent = (html = "", currentPrefix = "../..") => {
  let output = html
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/<form[\s\S]*?<\/form>/gi, '<p class="contact-inline">如需咨询课程、作品或艺术项目，请通过页面底部的联系方式与我们联系。</p>')
    .replace(/\s(?:srcset|sizes)=["'][^"']*["']/gi, "")
    .replace(/\s(?:loading|decoding|fetchpriority|data-[a-z0-9_-]+)=["'][^"']*["']/gi, "")
    .replace(/\sclass=["'][^"']*["']/gi, "")
    .replace(/\sstyle=["'][^"']*["']/gi, "")
    .replace(/\sid=["'][^"']*["']/gi, "");

  output = output.replace(/(<img\b[^>]*\bsrc=["'])([^"']+)(["'][^>]*>)/gi, (all, before, src, after) => {
    const normalized = normalizeUrl(src);
    if (!imageMap.has(normalized)) {
      return isOldSiteUrl(normalized) ? '<span class="missing-image-note">图片整理中</span>' : all;
    }
    return `${before}${currentPrefix}/${imageMap.get(normalized)}${after}`;
  });

  output = output.replace(/(<a\b[^>]*\bhref=["'])([^"']+)(["'][^>]*>)/gi, (all, before, href, after) => {
    const local = localLink(href, currentPrefix);
    const target = /^https?:\/\//i.test(local) ? ' target="_blank" rel="noopener"' : "";
    return `${before}${local}${after.replace(/\s(target|rel)=["'][^"']*["']/gi, "")}`.replace(/>$/, `${target}>`);
  });

  return output;
};

const imageSrc = (img = "") => img.match(/\bsrc=["']([^"']+)["']/i)?.[1] || "";

const extractImages = (html = "") => {
  const seen = new Set();
  const images = [];
  for (const match of html.matchAll(/<img\b[^>]*>/gi)) {
    const src = imageSrc(match[0]);
    if (!src || seen.has(src)) continue;
    seen.add(src);
    images.push(match[0]);
  }
  return images;
};

const textBlocks = (html = "", title = "") => {
  const blocks = [];
  const seen = new Set([title]);
  const withoutImages = html
    .replace(/<figure[\s\S]*?<\/figure>/gi, " ")
    .replace(/<img\b[^>]*>/gi, " ");
  for (const match of withoutImages.matchAll(/<(h[1-6]|p|li)\b[^>]*>([\s\S]*?)<\/\1>/gi)) {
    const text = htmlText(match[2]);
    if (text.length < 8 || text === "更多" || seen.has(text)) continue;
    seen.add(text);
    blocks.push({ tag: match[1].startsWith("h") ? "h3" : "p", text });
  }
  return blocks.slice(0, 18);
};

const renderTextBlocks = (blocks) =>
  blocks.length
    ? `<div class="detail-copy">${blocks.map((block) => `<${block.tag}>${block.text}</${block.tag}>`).join("")}</div>`
    : "";

const renderImageGrid = (images, className = "detail-image-grid") =>
  images.length
    ? `<div class="${className}">${images.map((img) => `<figure>${img}</figure>`).join("")}</div>`
    : "";

const courseBody = ({ id, title, cleaned, description }) => {
  const images = extractImages(cleaned);
  const blocks = textBlocks(cleaned, title);
  const heroImage = courseHeroImages.get(id);
  const notes = courseNotes.get(id);
  const highlights = courseHighlights.get(id) || [
    ["课程结构", "围绕基础训练、材料实践和阶段作品推进。"],
    ["学习方式", "结合示范、练习、反馈和作品整理。"],
    ["创作目标", "帮助学习者建立稳定的观察与表达方法。"],
  ];
  if (heroImage) {
    return `
      <section class="course-landing">
        <div class="course-landing-copy">
          <p class="eyebrow">OUART COURSE</p>
          <h2>课程如何展开</h2>
          <p>${description}</p>
          <div class="course-actions">
            <a class="button primary" href="../../contact.html">咨询课程</a>
            <a class="button secondary" href="../../gallery.html">查看作品</a>
          </div>
        </div>
        <figure class="course-landing-media">
          <img src="${heroImage}" alt="${title}课程视觉图" />
        </figure>
      </section>
      <section class="course-highlight-grid">
        ${highlights.map(([label, text]) => `<article><span>${label}</span><p>${text}</p></article>`).join("")}
      </section>
      ${
        notes
          ? `<section class="course-note-grid">${notes.map(([label, text]) => `<article><h3>${label}</h3><p>${text}</p></article>`).join("")}</section>`
          : renderTextBlocks(blocks)
      }
    `;
  }
  return `
    <section class="detail-intro">
      <p>${description}</p>
    </section>
    ${renderImageGrid(images, "course-image-grid")}
    ${renderTextBlocks(blocks)}
  `;
};

const galleryBody = ({ cleaned, description }) => {
  const images = extractImages(cleaned);
  return `
    <section class="detail-intro">
      <p>${description}</p>
    </section>
    ${renderImageGrid(images, "artwork-grid")}
  `;
};

const shell = ({ title, subtitle, body, section = "内容", layoutClass = "" }) => `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${title} | 初艺 OUART</title>
    <link rel="stylesheet" href="../../styles.css?v=${assetVersion}" />
    <meta name="application-name" content="OUART" />
    <meta name="apple-mobile-web-app-title" content="OUART" />
    <meta name="theme-color" content="#000000" />
    <link rel="icon" type="image/png" href="../../assets/favicon-32.png" />
    <link rel="apple-touch-icon" sizes="180x180" href="../../assets/apple-touch-icon.png" />
    <link rel="manifest" href="../../site.webmanifest" />
  </head>
  <body>
    <header class="site-header">
      <a class="brand" href="../../index.html"><img src="../../assets/logo-dark.png?v=20260612b" alt="" /><span><strong>初艺 OUART</strong><small>${section}</small></span></a>
      <button class="menu-toggle" type="button" aria-label="打开导航" aria-expanded="false">☰</button>
      <nav class="nav" aria-label="主导航">
        <a href="../../courses.html">课程</a>
        <a href="../../daily-art.html">每日一画</a>
        <a href="../../gallery.html">作品集</a>
        <a href="../../open-class.html">公开课</a>
        <a href="../../contact.html">联系</a>
      </nav>
    </header>
    <main>
      <article class="content-page${layoutClass ? ` ${layoutClass}` : ""}">
        <p class="eyebrow">${section}</p>
        <h1>${title}</h1>
        ${subtitle ? `<p class="content-meta">${subtitle}</p>` : ""}
        <div class="wp-content">${body}</div>
      </article>
    </main>
    <footer class="site-footer"><p>© 初艺 OUART</p><a href="../../index.html">返回首页</a></footer>
    <script src="../../site.js"></script>
  </body>
</html>
`;

const writeGeneratedPages = async () => {
  await ensureDir(path.join(outRoot, "posts"));
  await ensureDir(path.join(outRoot, "pages"));
  await ensureDir(path.join(outRoot, "products"));

  for (const post of posts) {
    const title = titleOf(post, `文章 ${post.id}`);
    const body = cleanContent(post.content?.rendered || post.excerpt?.rendered || "", "../..");
    await fs.writeFile(
      path.join(outRoot, "posts", `${post.id}.html`),
      shell({ title, subtitle: new Date(post.date).toLocaleDateString("zh-CN"), body, section: post.categories?.includes(18) ? "公开课" : "模型分享" }),
      "utf8"
    );
    post.local_url = `./content/posts/${post.id}.html`;
  }

  for (const page of visiblePages) {
    const title = pageTitles.get(page.id) || titleOf(page, `初艺内容 ${page.id}`);
    const cleaned = cleanContent(page.content?.rendered || "", "../..");
    let body = cleaned;
    let layoutClass = "";
    if (coursePageIds.has(page.id)) {
      layoutClass = "course-detail";
      body = courseBody({
        id: page.id,
        title,
        cleaned,
        description: pageDescriptions.get(page.id) || "课程内容围绕创作方法、材料实践与作品推进展开。",
      });
    }
    if (galleryPageIds.has(page.id)) {
      layoutClass = "gallery-detail";
      body = galleryBody({
        cleaned,
        description: pageDescriptions.get(page.id) || "作品按系列整理展示，方便集中浏览。",
      });
    }
    await fs.writeFile(
      path.join(outRoot, "pages", `${page.id}.html`),
      shell({ title, body, section: coursePageIds.has(page.id) ? "课程" : "作品集", layoutClass }),
      "utf8"
    );
    page.local_url = `./content/pages/${page.id}.html`;
  }

  for (const product of products) {
    const title = titleOf(product, `项目 ${product.id}`);
    const body = cleanContent(product.content?.rendered || product.excerpt?.rendered || "", "../..");
    await fs.writeFile(
      path.join(outRoot, "products", `${product.id}.html`),
      shell({ title, subtitle: "课程与作品展示", body, section: "商店展示" }),
      "utf8"
    );
    product.local_url = `./content/products/${product.id}.html`;
  }
};

const downloadOne = async (url) => {
  const relative = imageMap.get(url);
  const file = path.join(root, relative);
  try {
    await fs.access(file);
    return { url, skipped: true };
  } catch {}

  await execFileAsync("curl.exe", ["-k", "-L", "--fail", "--silent", "--show-error", encodeURI(url), "-o", file], {
    windowsHide: true,
    maxBuffer: 1024 * 1024,
  });
  const stat = await fs.stat(file);
  return { url, bytes: stat.size };
};

const downloadImages = async () => {
  await ensureDir(migratedAssetDir);
  const urls = [...imageUrls];
  let index = 0;
  let ok = 0;
  let failed = 0;
  const workers = Array.from({ length: 10 }, async () => {
    while (index < urls.length) {
      const url = urls[index++];
      try {
        const result = await downloadOne(url);
        if (!result.skipped) ok++;
        else ok++;
      } catch (error) {
        failed++;
        if (failed <= 20) console.warn(`image failed: ${error.message}`);
      }
      if ((ok + failed) % 100 === 0) console.log(`images ${ok + failed}/${urls.length}`);
    }
  });
  await Promise.all(workers);
  return { total: urls.length, ok, failed };
};

await ensureDir(outRoot);
await writeGeneratedPages();
const imageResult = await downloadImages();

const siteData = {
  posts: posts.map((post) => ({ ...post, content: undefined })),
  products: products.map((product) => ({ ...product, content: undefined })),
};
await fs.writeFile(path.join(root, "data", "site-data.js"), `window.CHUYI_DATA = ${JSON.stringify(siteData)};\n`, "utf8");

console.log(JSON.stringify({
  posts: posts.length,
  pages: visiblePages.length,
  products: products.length,
  images: imageResult,
}, null, 2));
