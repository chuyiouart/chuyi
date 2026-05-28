import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const root = process.cwd();
const outRoot = path.join(root, "content");
const migratedAssetDir = path.join(root, "assets", "migrated");
const execFileAsync = promisify(execFile);

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

const titleOf = (item, fallback) => htmlText(item?.title?.rendered || "") || fallback;

const hashName = (url) => {
  const clean = url.split("?")[0].split("#")[0];
  const extMatch = clean.match(/\.(jpe?g|png|webp|gif)$/i);
  const ext = extMatch ? extMatch[1].toLowerCase().replace("jpeg", "jpg") : "jpg";
  return `${crypto.createHash("sha1").update(clean).digest("hex").slice(0, 16)}.${ext}`;
};

const ensureDir = async (dir) => fs.mkdir(dir, { recursive: true });

const normalizeUrl = (url = "") => {
  if (url.startsWith("//")) return `https:${url}`;
  return url.replace(/&amp;/g, "&");
};

const isUploadUrl = (url) => /^https:\/\/chuyiouart\.com\/wp-content\/uploads\//i.test(normalizeUrl(url));

const posts = [
  ...(await readJson("data/posts-page-1.json")),
  ...(await readJson("data/posts-page-2.json")),
];
const pages = await readJson("data/pages.json");
const products = await readJson("data/products.json");

const pageExclusions = /membership|password|checkout|cart|account|thank-you|registration|join|wshop/i;
const visiblePages = pages.filter((page) => {
  const text = htmlText(page.content?.rendered || "");
  return text.length > 60 && !pageExclusions.test(page.slug || "");
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
    .replace(/\s(?:srcset|sizes)=["'][^"']*["']/gi, "")
    .replace(/\s(?:loading|decoding|fetchpriority|data-[a-z0-9_-]+)=["'][^"']*["']/gi, "")
    .replace(/\sclass=["'][^"']*["']/gi, "")
    .replace(/\sstyle=["'][^"']*["']/gi, "")
    .replace(/\sid=["'][^"']*["']/gi, "");

  output = output.replace(/(<img\b[^>]*\bsrc=["'])([^"']+)(["'][^>]*>)/gi, (all, before, src, after) => {
    const normalized = normalizeUrl(src);
    if (!imageMap.has(normalized)) return all;
    return `${before}${currentPrefix}/${imageMap.get(normalized)}${after}`;
  });

  output = output.replace(/(<a\b[^>]*\bhref=["'])([^"']+)(["'][^>]*>)/gi, (all, before, href, after) => {
    const local = localLink(href, currentPrefix);
    const target = /^https?:\/\//i.test(local) ? ' target="_blank" rel="noopener"' : "";
    return `${before}${local}${after.replace(/\s(target|rel)=["'][^"']*["']/gi, "")}`.replace(/>$/, `${target}>`);
  });

  return output;
};

const shell = ({ title, subtitle, body, section = "内容" }) => `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${title} | 初艺 OUART</title>
    <link rel="stylesheet" href="../../styles.css" />
  </head>
  <body>
    <header class="site-header">
      <a class="brand" href="../../index.html"><img src="../../assets/logo-dark.png" alt="" /><span><strong>初艺 OUART</strong><small>${section}</small></span></a>
      <button class="menu-toggle" type="button" aria-label="打开导航" aria-expanded="false">☰</button>
      <nav class="nav" aria-label="主导航">
        <a href="../../courses.html">课程</a>
        <a href="../../gallery.html">作品集</a>
        <a href="../../resources.html">模型分享</a>
        <a href="../../open-class.html">公开课</a>
        <a href="../../shop.html">商店展示</a>
        <a href="../../contact.html">联系</a>
      </nav>
    </header>
    <main>
      <article class="content-page">
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
    const title = titleOf(page, `初艺内容 ${page.id}`);
    const body = cleanContent(page.content?.rendered || "", "../..");
    await fs.writeFile(
      path.join(outRoot, "pages", `${page.id}.html`),
      shell({ title, body, section: "作品与课程" }),
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
