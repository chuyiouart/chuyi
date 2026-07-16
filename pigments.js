(() => {
  const dataset = window.OUART_PIGMENTS;
  const enrichmentDataset = window.OUART_PIGMENT_ENRICHMENT || { meta: {}, pigments: {}, images: [] };
  if (!dataset?.records?.length) {
    const summary = document.querySelector("#resultSummary");
    if (summary) summary.textContent = "数据库载入失败，请刷新页面。";
    return;
  }

  const familyOrder = ["all", "yellow", "orange", "red", "violet", "blue", "green", "brown", "black", "white", "misc"];
  const familyLabels = { all: "全部", ...dataset.meta.families };
  const normalizeCi = (value = "") => String(value).toUpperCase().replaceAll(" ", "");
  const imagesByCi = (enrichmentDataset.images || []).reduce((index, item) => {
    (item.ci_codes || []).forEach((code) => {
      const key = normalizeCi(code);
      index[key] = [...(index[key] || []), item];
    });
    return index;
  }, {});
  const records = dataset.records.map((record) => {
    const ciKey = normalizeCi(record.ci_code);
    const enrichment = enrichmentDataset.pigments?.[ciKey] || null;
    return {
    ...record,
    _enrichment: enrichment,
    _images: imagesByCi[ciKey] || [],
    _search: [
      record.ci_code,
      record.ci_name_zh,
      record.name_zh,
      record.name_en,
      record.composition_zh,
      record.composition_en,
      record.constitution_number,
      record.family_zh,
      enrichment?.summary_zh,
      enrichment?.best_uses?.join(" "),
    ].join(" ").toLocaleLowerCase("zh-CN"),
  }});

  const state = {
    query: "",
    family: "all",
    opacity: "all",
    light: "all",
    hazard: "all",
    translation: "all",
    review: "all",
    limit: 80,
  };

  const elements = {
    search: document.querySelector("#pigmentSearch"),
    opacity: document.querySelector("#opacityFilter"),
    light: document.querySelector("#lightFilter"),
    hazard: document.querySelector("#hazardFilter"),
    translation: document.querySelector("#translationFilter"),
    review: document.querySelector("#reviewFilter"),
    reset: document.querySelector("#resetFilters"),
    families: document.querySelector("#familyFilters"),
    rows: document.querySelector("#pigmentRows"),
    empty: document.querySelector("#pigmentEmpty"),
    more: document.querySelector("#loadMore"),
    summary: document.querySelector("#resultSummary"),
    recordCount: document.querySelector("#recordCount"),
    curatedCount: document.querySelector("#curatedCount"),
    deepReviewCount: document.querySelector("#deepReviewCount"),
    dialog: document.querySelector("#pigmentDialog"),
    detail: document.querySelector("#pigmentDetail"),
  };

  const escapeHtml = (value = "") => String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

  const isMissing = (value) => !value || ["-", "N/A", "NA"].includes(String(value).trim().toUpperCase());
  const displayRaw = (value) => isMissing(value) ? "待核验" : escapeHtml(value);
  const sourceUrl = (value) => /^https:\/\//.test(value || "") ? value : dataset.meta.source;

  const familyCounts = records.reduce((counts, record) => {
    counts[record.family] = (counts[record.family] || 0) + 1;
    return counts;
  }, { all: records.length });

  const renderFamilies = () => {
    elements.families.innerHTML = familyOrder.map((family) => `
      <button class="pigment-family ${state.family === family ? "active" : ""}" type="button" data-family="${family}">
        ${family !== "all" ? `<span class="family-dot family-${family}" aria-hidden="true"></span>` : ""}
        <span>${escapeHtml(familyLabels[family])}</span><small>${familyCounts[family] || 0}</small>
      </button>
    `).join("");
  };

  const matches = (record) => {
    if (state.query && !record._search.includes(state.query)) return false;
    if (state.family !== "all" && record.family !== state.family) return false;
    if (state.opacity !== "all") {
      const level = record.opacity.level || "unknown";
      if (level !== state.opacity) return false;
    }
    if (state.light !== "all") {
      const level = record.lightfastness.level || "unknown";
      if (state.light === "unknown") {
        if (level !== "unknown") return false;
      } else if (level !== state.light) return false;
    }
    if (state.hazard !== "all") {
      const level = record.hazard.rating || "unrated";
      if (level !== state.hazard) return false;
    }
    if (state.translation !== "all" && record.translation_status !== state.translation) return false;
    if (state.review === "deep" && !record._enrichment) return false;
    if (state.review === "basic" && record._enrichment) return false;
    return true;
  };

  const statusBadge = (record) => record.translation_status === "curated"
    ? '<span class="translation-badge reviewed">常用名已译审</span>'
    : '<span class="translation-badge">CI 通用名初译</span>';

  const reviewBadge = (record) => record._enrichment
    ? '<span class="review-badge deep">已尽调 v1</span>'
    : '<span class="review-badge">基础操作卡</span>';

  const hazardBadge = (record) => {
    const level = record.hazard.rating || "?";
    return `<span class="hazard-badge hazard-${level === "?" ? "unknown" : level.toLowerCase()}">${escapeHtml(level)} · ${escapeHtml(record.hazard.zh)}</span>`;
  };

  const renderRow = (record) => `
    <tr>
      <td data-label="色系"><span class="pigment-swatch" style="--swatch:${escapeHtml(record.swatch)}" aria-label="${escapeHtml(record.family_zh)}"></span></td>
      <td data-label="CI 编码"><code>${escapeHtml(record.ci_code)}</code><small>${escapeHtml(record.constitution_number || "")}</small></td>
      <td data-label="名称">
        <strong>${escapeHtml(record.name_zh)}</strong>
        <span>${escapeHtml(record.name_en)}</span>
        <span class="record-badges">${statusBadge(record)}${reviewBadge(record)}</span>
      </td>
      <td data-label="透明度"><strong>${escapeHtml(record.opacity.zh)}</strong><small>${displayRaw(record.opacity.raw)}</small></td>
      <td data-label="耐光性"><strong>${escapeHtml(record.lightfastness.zh)}</strong><small>${displayRaw(record.lightfastness.raw)}</small></td>
      <td data-label="风险">${hazardBadge(record)}</td>
      <td><button class="pigment-detail-button" type="button" data-record="${escapeHtml(record.id)}">详情</button></td>
    </tr>
  `;

  const render = () => {
    const filtered = records.filter(matches);
    const visible = filtered.slice(0, state.limit);
    elements.rows.innerHTML = visible.map(renderRow).join("");
    elements.empty.hidden = filtered.length !== 0;
    elements.more.hidden = visible.length >= filtered.length;
    elements.summary.textContent = `找到 ${filtered.length.toLocaleString("zh-CN")} 条，当前显示 ${visible.length.toLocaleString("zh-CN")} 条`;
    renderFamilies();
  };

  const detailBlock = (labelZh, labelEn, zh, en, note = "") => `
    <section class="detail-block">
      <p class="detail-label">${escapeHtml(labelZh)} <span>${escapeHtml(labelEn)}</span></p>
      <p class="detail-primary">${displayRaw(zh)}</p>
      ${!isMissing(en) && en !== zh ? `<p class="detail-secondary" lang="en">${escapeHtml(en)}</p>` : ""}
      ${note ? `<small>${escapeHtml(note)}</small>` : ""}
    </section>
  `;

  const renderImageGallery = (record) => {
    if (!record._images.length) return "";
    return `
      <section class="detail-gallery" aria-label="颜料材料图片">
        ${record._images.map((item) => `
          <figure>
            <img src="./${escapeHtml(item.local_path)}" alt="${escapeHtml(item.caption_zh)}" loading="lazy" />
            <figcaption>
              <strong>${escapeHtml(item.caption_zh)}</strong>
              <span lang="en">${escapeHtml(item.caption_en)}</span>
              <small>${escapeHtml(item.creator)} · ${escapeHtml(item.license)} · <a href="${escapeHtml(item.source_page)}" target="_blank" rel="noopener">原始图片页</a></small>
            </figcaption>
          </figure>
        `).join("")}
        <p>材料外观示意：图片经过等比缩放与 JPEG 优化，未做颜色校正。粉末照片不能代替实际涂膜、品牌或色度测量。</p>
      </section>
    `;
  };

  const renderList = (items = []) => items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");

  const renderPracticalProfile = (record) => {
    const profile = record._enrichment;
    if (!profile) {
      return `
        <section class="detail-review-note">
          <p class="detail-label">当前审校状态 <span>Review status</span></p>
          <h3>基础操作卡：尚未逐条完成专业尽调</h3>
          <p>以下步骤帮助建立可比较的个人材料档案，不表示这条颜料的化学、保存与安全结论已被独立核验。教学或出版前仍需查具体产品的最新版 SDS 和权威材料来源。</p>
        </section>
      `;
    }
    return `
      <section class="detail-review-summary">
        <div>
          <p class="detail-label">首轮尽调结论 <span>Reviewed summary</span></p>
          <h3>${escapeHtml(profile.summary_zh)}</h3>
        </div>
        <aside><strong>身份判断</strong><p>${escapeHtml(profile.identity_notes_zh)}</p></aside>
      </section>
      <section class="detail-practice-grid">
        <article><p class="detail-label">适用场景 <span>Best uses</span></p><ul>${renderList(profile.best_uses)}</ul></article>
        <article><p class="detail-label">混色行为 <span>Mixing</span></p><p>${escapeHtml(profile.mixing_behavior)}</p></article>
        <article><p class="detail-label">操作提示 <span>Handling</span></p><p>${escapeHtml(profile.handling)}</p></article>
        <article><p class="detail-label">限制与误区 <span>Limitations</span></p><p>${escapeHtml(profile.limitations)}</p></article>
        <article class="wide"><p class="detail-label">替代建议 <span>Alternatives</span></p><p>${escapeHtml(profile.alternatives)}</p></article>
      </section>
    `;
  };

  const renderOperations = (record) => {
    const operations = enrichmentDataset.meta?.generic_operations || [];
    const level = record.hazard.rating || "unrated";
    const safety = record._enrichment?.safety_override_zh || enrichmentDataset.meta?.safety_rules?.[level] || enrichmentDataset.meta?.safety_rules?.unrated || "先查产品 SDS。";
    const safetyLabel = record._enrichment?.safety_override_zh ? "专业限制覆盖" : `${level} 级操作边界`;
    return `
      <section class="detail-operations">
        <div>
          <p class="detail-label">标准操作卡 <span>Studio test card</span></p>
          <h3>同一套试片，才能把不同颜料放在一起比较。</h3>
        </div>
        <ol>${renderList(operations)}</ol>
        <p class="operation-safety"><strong>${escapeHtml(safetyLabel)}：</strong>${escapeHtml(safety)}</p>
      </section>
    `;
  };

  const renderReviewedSources = (record) => {
    const sources = record._enrichment?.sources || [];
    if (!sources.length) return "";
    return `
      <section class="detail-reviewed-sources">
        <p class="detail-label">尽调来源 <span>Reviewed references</span></p>
        <div>${sources.map((source) => `<a href="${escapeHtml(source.url)}" target="_blank" rel="noopener">${escapeHtml(source.title)}</a>`).join("")}</div>
        <small>来源用于支持本页简明判断；具体品牌的危险分类、配方和操作仍以最新版 SDS 为准。</small>
      </section>
    `;
  };

  const openDetail = (record) => {
    const tags = (record.course_tags || []).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("");
    const refs = (record.source_links || []).map((link, index) => `
      <a href="${escapeHtml(sourceUrl(link))}" target="_blank" rel="noopener">补充来源 ${index + 1}</a>
    `).join("");
    elements.detail.innerHTML = `
      <header class="detail-header">
        <span class="detail-swatch" style="--swatch:${escapeHtml(record.swatch)}" aria-hidden="true"></span>
        <div>
          <p>${escapeHtml(record.family_zh)} · ${escapeHtml(record.ci_code)}</p>
          <h2 id="dialogTitle">${escapeHtml(record.name_zh)}</h2>
          <p lang="en">${escapeHtml(record.name_en)}</p>
          <span class="record-badges">${statusBadge(record)}${reviewBadge(record)}</span>
        </div>
      </header>
      ${renderImageGallery(record)}
      ${renderPracticalProfile(record)}
      <div class="detail-grid">
        ${detailBlock("CI 通用名", "CI generic name", record.ci_name_zh, record.ci_code)}
        ${detailBlock("化学组成", "Chemical composition", record.composition_zh, record.composition_en, "中文为辅助初译，教学或出版前需复核。")}
        ${detailBlock("色彩描述", "Color description", record.color_description_zh, record.color_description_en)}
        ${detailBlock("透明度", "Opacity", record.opacity.zh, record.opacity.raw, "1 不透明，4 透明；具体结果会受颗粒与胶结料影响。")}
        ${detailBlock("耐光性", "Lightfastness", record.lightfastness.zh, record.lightfastness.raw, "同一颜料在不同品牌和胶结料中可能不同。")}
        ${detailBlock("吸油量", "Oil absorption", record.oil_absorption_raw, "g / 100 g（沿用来源记录）")}
      </div>
      <section class="detail-hazard">
        <p class="detail-label">材料风险 <span>Material hazard</span></p>
        ${hazardBadge(record)}
        ${record.hazard.triggers?.length ? `<p>需复核成分：${record.hazard.triggers.map(escapeHtml).join("、")}</p>` : ""}
        <p>风险等级仅用于筛查。任何干颜料都应避免吸入，不得把本页当作儿童、家庭或工作室安全操作的唯一依据。</p>
      </section>
      ${renderOperations(record)}
      <section class="detail-course-tags">
        <p class="detail-label">课程调用方向 <span>Course use</span></p>
        <div>${tags}</div>
      </section>
      ${renderReviewedSources(record)}
      <footer class="detail-source">
        <a href="${escapeHtml(sourceUrl(record.source.url))}" target="_blank" rel="noopener">查看原始条目</a>
        ${refs}
        <span>数据状态：${record._enrichment ? "核心条目首轮尽调完成" : "结构化初稿，待专业复核"}</span>
      </footer>
    `;
    if (typeof elements.dialog.showModal === "function") elements.dialog.showModal();
    else elements.dialog.setAttribute("open", "");
    history.replaceState(null, "", `#${record.id}`);
  };

  elements.recordCount.textContent = dataset.meta.record_count.toLocaleString("zh-CN");
  elements.curatedCount.textContent = (dataset.meta.translation_status_counts.curated || 0).toLocaleString("zh-CN");
  elements.deepReviewCount.textContent = Object.keys(enrichmentDataset.pigments || {}).length.toLocaleString("zh-CN");

  elements.search.addEventListener("input", () => {
    state.query = elements.search.value.trim().toLocaleLowerCase("zh-CN");
    state.limit = 80;
    render();
  });
  [[elements.opacity, "opacity"], [elements.light, "light"], [elements.hazard, "hazard"], [elements.translation, "translation"], [elements.review, "review"]]
    .forEach(([element, key]) => element.addEventListener("change", () => {
      state[key] = element.value;
      state.limit = 80;
      render();
    }));
  elements.families.addEventListener("click", (event) => {
    const button = event.target.closest("[data-family]");
    if (!button) return;
    state.family = button.dataset.family;
    state.limit = 80;
    render();
  });
  elements.rows.addEventListener("click", (event) => {
    const button = event.target.closest("[data-record]");
    if (!button) return;
    const record = records.find((item) => item.id === button.dataset.record);
    if (record) openDetail(record);
  });
  elements.more.addEventListener("click", () => {
    state.limit += 80;
    render();
  });
  elements.reset.addEventListener("click", () => {
    Object.assign(state, { query: "", family: "all", opacity: "all", light: "all", hazard: "all", translation: "all", review: "all", limit: 80 });
    elements.search.value = "";
    elements.opacity.value = "all";
    elements.light.value = "all";
    elements.hazard.value = "all";
    elements.translation.value = "all";
    elements.review.value = "all";
    render();
  });
  document.querySelector(".pigment-dialog-close").addEventListener("click", () => elements.dialog.close());
  elements.dialog.addEventListener("click", (event) => {
    if (event.target === elements.dialog) elements.dialog.close();
  });
  elements.dialog.addEventListener("close", () => {
    if (location.hash.startsWith("#PIG-")) history.replaceState(null, "", `${location.pathname}${location.search}`);
  });

  render();
  const hashRecord = records.find((record) => `#${record.id}` === location.hash);
  if (hashRecord) openDetail(hashRecord);
})();
