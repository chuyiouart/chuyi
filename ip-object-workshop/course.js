(function () {
  "use strict";

  const config = window.WORKSHOP_CONFIG || {};
  const paymentConfig = config.payment || {};
  const updates = Array.isArray(window.WORKSHOP_UPDATES)
    ? window.WORKSHOP_UPDATES.slice()
    : [];
  const today = startOfDay(new Date());
  const pageSize = 10;
  let activeFilter = "全部";
  let visibleCount = pageSize;
  let selectedChannel = "";

  function startOfDay(date) {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate());
  }

  function parseLocalDate(value) {
    const parts = String(value || "").split("-").map(Number);
    return new Date(parts[0], parts[1] - 1, parts[2]);
  }

  function formatDisplayDate(value) {
    const date = parseLocalDate(value);
    return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, "0")}.${String(date.getDate()).padStart(2, "0")}`;
  }

  function weekday(value) {
    return `周${"日一二三四五六"[parseLocalDate(value).getDay()]}`;
  }

  function escapeHtml(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function applyApplicationLinks() {
    const url = config.applicationFormUrl || "./submit-check.html";
    document.querySelectorAll("[data-application-link]").forEach((link) => {
      link.href = url;
      if (/^https?:\/\//.test(url)) {
        link.target = "_blank";
        link.rel = "noopener";
      }
    });
  }

  function setupNavigation() {
    const toggle = document.querySelector("[data-nav-toggle]");
    const nav = document.querySelector("[data-course-nav]");
    if (!toggle || !nav) return;

    const closeNav = () => {
      nav.classList.remove("is-open");
      document.body.classList.remove("nav-open");
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "打开导航");
    };

    toggle.addEventListener("click", () => {
      const isOpen = nav.classList.toggle("is-open");
      document.body.classList.toggle("nav-open", isOpen);
      toggle.setAttribute("aria-expanded", String(isOpen));
      toggle.setAttribute("aria-label", isOpen ? "关闭导航" : "打开导航");
    });

    nav.querySelectorAll("a").forEach((link) => link.addEventListener("click", closeNav));
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeNav();
    });
    window.addEventListener("resize", () => {
      if (window.innerWidth > 820) closeNav();
    });
  }

  function updateStatus(item) {
    const itemDate = startOfDay(parseLocalDate(item.date));
    if (item.published && item.url) return { text: "查看内容", href: item.url };
    if (item.published) return { text: "已发布" };
    if (itemDate < today) return { text: "待补发布" };
    if (itemDate.getTime() === today.getTime()) return { text: "今日计划" };
    return { text: "即将发布" };
  }

  function renderToday() {
    if (!updates.length) return;
    const exact = updates.find((item) => startOfDay(parseLocalDate(item.date)).getTime() === today.getTime());
    const upcoming = updates.find((item) => startOfDay(parseLocalDate(item.date)) >= today);
    const item = exact || upcoming || updates[updates.length - 1];
    const status = updateStatus(item);
    const cover = document.querySelector("[data-today-cover]");
    const date = document.querySelector("[data-today-date]");
    const title = document.querySelector("[data-today-title]");
    const summary = document.querySelector("[data-today-summary]");
    const link = document.querySelector("[data-today-link]");

    if (cover) {
      cover.src = item.cover;
      cover.alt = item.title;
    }
    if (date) date.textContent = `${formatDisplayDate(item.date)} · ${item.type} · ${item.time}`;
    if (title) title.textContent = item.title;
    if (summary) summary.textContent = item.summary;
    if (link) {
      link.textContent = status.text;
      link.href = status.href || "#updates-list";
      if (status.href && /^https?:\/\//.test(status.href)) {
        link.target = "_blank";
        link.rel = "noopener";
      } else {
        link.removeAttribute("target");
      }
    }
  }

  function filteredUpdates() {
    return updates.filter((item) => activeFilter === "全部" || item.type === activeFilter);
  }

  function renderUpdates() {
    const list = document.querySelector("[data-updates-list]");
    const more = document.querySelector("[data-load-more]");
    if (!list || !more) return;
    const filtered = filteredUpdates();
    const visible = filtered.slice(0, visibleCount);

    list.innerHTML = visible
      .map((item) => {
        const status = updateStatus(item);
        const statusMarkup = status.href
          ? `<a class="update-status" href="${escapeHtml(status.href)}" target="_blank" rel="noopener">${status.text}</a>`
          : `<span class="update-status">${status.text}</span>`;
        return `
          <article class="update-row">
            <div class="update-date"><time datetime="${item.date}">${formatDisplayDate(item.date)}</time><small>${weekday(item.date)} · ${item.time}</small></div>
            <div class="update-copy"><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.summary)}</p></div>
            <span class="update-type">${escapeHtml(item.type)}</span>
            ${statusMarkup}
          </article>`;
      })
      .join("");

    more.hidden = visibleCount >= filtered.length;
    more.textContent = `显示更多更新（剩余 ${Math.max(0, filtered.length - visibleCount)} 条）`;
  }

  function setupUpdateFilters() {
    const buttons = document.querySelectorAll("[data-filter]");
    buttons.forEach((button) => {
      button.addEventListener("click", () => {
        activeFilter = button.dataset.filter || "全部";
        visibleCount = pageSize;
        buttons.forEach((item) => item.classList.toggle("is-active", item === button));
        renderUpdates();
      });
    });
    const more = document.querySelector("[data-load-more]");
    if (more) {
      more.addEventListener("click", () => {
        visibleCount += pageSize;
        renderUpdates();
      });
    }
  }

  function renderLiveSchedule() {
    const list = document.querySelector("[data-live-list]");
    if (!list) return;
    let live = updates.filter((item) => item.type === "直播" && parseLocalDate(item.date) >= today).slice(0, 3);
    if (!live.length) live = updates.filter((item) => item.type === "直播").slice(-3);
    list.innerHTML = live
      .map((item) => {
        const status = updateStatus(item);
        return `
          <article class="live-row">
            <time datetime="${item.date}">${formatDisplayDate(item.date)}<br />${item.time}</time>
            <div><h3>${escapeHtml(item.title)}</h3><p>直播当天仍会同步发布预告图文，结束后补充重点复盘。</p></div>
            <span>${status.text}</span>
          </article>`;
      })
      .join("");
  }

  function setDefaultPrice() {
    const earlyBirdEnd = parseLocalDate("2026-08-20");
    const value = today <= earlyBirdEnd ? "founder" : "standard";
    const option = document.querySelector(`input[name="course-price"][value="${value}"]`);
    if (option) option.checked = true;
  }

  function validChannel(channel) {
    if (!channel || !channel.enabled) return false;
    if (channel.checkoutUrl) return true;
    return Boolean(channel.accountName && channel.bankName && channel.accountNumber);
  }

  function setupPayment() {
    const support = document.querySelector("[data-payment-support]");
    const methods = document.querySelector("[data-payment-methods]");
    const submit = document.querySelector("[data-payment-submit]");
    const message = document.querySelector("[data-payment-message]");
    const approval = document.querySelector("[data-approval-code]");
    const payer = document.querySelector("[data-payer-name]");
    if (!methods || !submit || !message || !approval || !payer) return;

    if (support) support.textContent = paymentConfig.supportText || "初诊通过、名额确认后开放企业付款通道。";
    const definitions = [
      ["wechat", "微信"],
      ["alipay", "支付宝"],
      ["bank", "银行"],
    ];
    const channels = paymentConfig.channels || {};
    methods.innerHTML = definitions
      .map(([key, shortLabel]) => {
        const channel = channels[key] || {};
        const available = paymentConfig.enabled && validChannel(channel);
        const note = available ? "可用" : "初诊通过后开放";
        return `<button type="button" data-channel="${key}" ${available ? "" : "disabled"}><span>${shortLabel}</span>${escapeHtml(channel.label || shortLabel)}<small>${note}</small></button>`;
      })
      .join("");

    methods.querySelectorAll("button:not(:disabled)").forEach((button) => {
      button.addEventListener("click", () => {
        selectedChannel = button.dataset.channel || "";
        methods.querySelectorAll("button").forEach((item) => item.classList.toggle("is-selected", item === button));
        message.textContent = `已选择${button.textContent.replace("可用", "").trim()}，请核对编号后继续。`;
      });
    });

    submit.addEventListener("click", () => {
      if (!approval.value.trim() || !payer.value.trim()) {
        message.textContent = "请先填写初诊确认编号和付款方名称。";
        (!approval.value.trim() ? approval : payer).focus();
        return;
      }
      if (!paymentConfig.enabled) {
        message.textContent = "当前网站付款通道尚未开放。请先完成报名初诊，课程团队确认名额后会发送企业付款入口。";
        return;
      }
      if (!selectedChannel) {
        message.textContent = "请选择一种可用的企业付款方式。";
        return;
      }

      const channel = channels[selectedChannel] || {};
      const selectedPrice = document.querySelector('input[name="course-price"]:checked');
      const query = new URLSearchParams({
        approvalCode: approval.value.trim(),
        payerName: payer.value.trim(),
        priceType: selectedPrice ? selectedPrice.value : "standard",
      });
      if (channel.checkoutUrl) {
        const separator = channel.checkoutUrl.includes("?") ? "&" : "?";
        window.location.href = `${channel.checkoutUrl}${separator}${query.toString()}`;
        return;
      }
      if (selectedChannel === "bank" && validChannel(channel)) {
        message.innerHTML = `请转账至：${escapeHtml(channel.accountName)} · ${escapeHtml(channel.bankName)} · ${escapeHtml(channel.accountNumber)}。附言请写初诊编号。`;
        return;
      }
      message.textContent = "该通道尚未完成安全服务端配置，请联系课程团队处理。";
    });
  }

  applyApplicationLinks();
  setupNavigation();
  renderToday();
  setupUpdateFilters();
  renderUpdates();
  renderLiveSchedule();
  setDefaultPrice();
  setupPayment();
})();
