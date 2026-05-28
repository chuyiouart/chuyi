const htmlToText = (html = "") => {
  const doc = new DOMParser().parseFromString(html, "text/html");
  return doc.body.textContent.replace(/\s+/g, " ").trim();
};

const decodeTitle = (item) => {
  const text = item?.title?.rendered || "";
  const doc = new DOMParser().parseFromString(text, "text/html");
  return doc.body.textContent.trim() || "未命名内容";
};

const formatDate = (value) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value.slice(0, 10);
  return date.toLocaleDateString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" });
};

const loadJson = async (path) => {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`无法读取 ${path}`);
  return response.json();
};

const loadPosts = async () => {
  if (window.CHUYI_DATA?.posts) return window.CHUYI_DATA.posts;
  const pages = await Promise.all([
    loadJson("./data/posts-page-1.json"),
    loadJson("./data/posts-page-2.json"),
  ]);
  return pages.flat();
};

const cardExcerpt = (item) => {
  const text = htmlToText(item?.excerpt?.rendered || item?.content?.rendered || "");
  return text.length > 98 ? `${text.slice(0, 98)}...` : text || "内容摘要整理中。";
};

const renderArticleCards = (container, posts) => {
  if (!posts.length) {
    container.innerHTML = `<div class="empty-state">没有找到匹配内容。</div>`;
    return;
  }

  container.innerHTML = posts
    .map((post) => {
      const title = decodeTitle(post);
      return `
        <article class="article-card">
          <time datetime="${post.date}">${formatDate(post.date)}</time>
          <h2>${title}</h2>
          <p>${cardExcerpt(post)}</p>
          <a class="text-link" href="${post.link}" target="_blank" rel="noopener">查看详情</a>
        </article>
      `;
    })
    .join("");
};

const initResources = async () => {
  const container = document.querySelector('[data-render="resources"]');
  if (!container) return;

  const search = document.querySelector("#resourceSearch");
  const chips = [...document.querySelectorAll("[data-filter-category]")];
  const posts = (await loadPosts()).filter((post) => post.categories.includes(1));
  let category = "all";

  const apply = () => {
    const query = (search?.value || "").trim().toLowerCase();
    const filtered = posts.filter((post) => {
      const title = decodeTitle(post).toLowerCase();
      const text = htmlToText(post.excerpt?.rendered || post.content?.rendered || "").toLowerCase();
      const matchesCategory = category === "all" || post.categories.includes(Number(category));
      const matchesQuery = !query || title.includes(query) || text.includes(query);
      return matchesCategory && matchesQuery;
    });
    renderArticleCards(container, filtered);
  };

  search?.addEventListener("input", apply);
  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      chips.forEach((item) => item.classList.remove("active"));
      chip.classList.add("active");
      category = chip.dataset.filterCategory;
      apply();
    });
  });
  apply();
};

const initOpenClass = async () => {
  const container = document.querySelector('[data-render="open-class"]');
  if (!container) return;
  const posts = (await loadPosts()).filter((post) => post.categories.includes(18));
  renderArticleCards(container, posts);
};

const initProducts = async () => {
  const container = document.querySelector('[data-render="products"]');
  if (!container) return;
  const products = window.CHUYI_DATA?.products || (await loadJson("./data/products.json"));
  if (!products.length) {
    container.innerHTML = `<div class="empty-state">还没有商品展示内容。</div>`;
    return;
  }

  container.innerHTML = products
    .map((product) => {
      const title = decodeTitle(product);
      return `
        <article class="product-card">
          <span>${formatDate(product.date)}</span>
          <h2>${title}</h2>
          <p>${cardExcerpt(product)}</p>
          <a class="text-link" href="./contact.html">咨询详情</a>
        </article>
      `;
    })
    .join("");
};

const initMenu = () => {
  const button = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".nav");
  button?.addEventListener("click", () => {
    const expanded = button.getAttribute("aria-expanded") === "true";
    button.setAttribute("aria-expanded", String(!expanded));
    nav?.classList.toggle("open", !expanded);
  });
};

window.addEventListener("DOMContentLoaded", () => {
  initMenu();
  initResources().catch(console.error);
  initOpenClass().catch(console.error);
  initProducts().catch(console.error);
});
