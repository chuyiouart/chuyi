(() => {
  const root = document.querySelector("#course-map-app");
  const modal = document.querySelector("#course-modal");
  const modalContent = document.querySelector("#modal-content");
  if (!root || !window.COURSE_GROUPS) return;

  const previewForStage = {
    "stage-01": "./course-book-stage-01/lesson-01-main-oil-value/screenshots/01-course-map-05-55.png",
    "stage-02": "./course-book-stage-02/lesson-01-oil-painting-start/assets/pdf-keyframes/01-course-opening-00-18.jpg",
    "stage-03": "./course-book-stage-03/lesson-01-delacroix-light-local-color/keyframes/01-floral-colour-07-30.png",
    "stage-04": "./course-book-stage-04/lesson-01-s1e01-creative-power/assets/cover-original.png",
    "dlc-all": "./course-book-dlc/lesson-01-sketch-logic/assets/interior-wash-prepared.png",
    "materials-all": "./course-book-material-technique/lesson-01-oil-paint-overview/assets/interior-texture.png",
  };

  const previewForLesson = (lesson, group, stageInfo) => {
    const normalized = lesson.slug.replaceAll("/", "__");
    return `./assets/course-lesson-covers-webp/${normalized}.webp`;
  };

  const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  }[char]));

  const lessonCopy = (lesson, stageInfo, group) => {
    const focus = stageInfo.focus;
    const kind = lesson.kind === "主课" ? "主线课程" : `${lesson.kind}模块`;
    const seriesHint = group.id === "materials"
      ? "先看材料的行为，再把结果带回调色、铺色、罩染与保存。"
      : group.id === "dlc"
        ? "它可以作为主线中的插入练习，也可以单独用来补一个具体短板。"
        : "它在主线中承担一个清晰的能力台阶，并为下一组练习准备观察工具。";
    return {
      summary: `${kind}“${lesson.name}”围绕${focus}展开。课程目录只保留学习者需要的关键线索：问题是什么、画面如何判断、练习如何落地；完整视频与 PDF 在购课后解锁。`,
      bridge: `${seriesHint}完成本课后，你会更容易理解${stageInfo.title}中后续课程的判断方式。`,
      outcome: group.id === "materials"
        ? "能记录材料差异、建立自己的色料卡，并在购买和使用前做出更有依据的选择。"
        : "能把观察、判断和操作拆成可重复的步骤，而不是只凭感觉临摹。",
    };
  };

  const countAll = (group) => group.stages.reduce((total, current) => total + current.lessons.length, 0);

  const renderLesson = (lesson, stageInfo, group) => {
    const copy = lessonCopy(lesson, stageInfo, group);
    return `<article class="lesson-card" data-search="${escapeHtml(`${lesson.no} ${lesson.name} ${lesson.kind}`)}">
      <div class="lesson-card-top"><span class="lesson-no">${escapeHtml(lesson.no)}</span><span class="lesson-kind">${escapeHtml(lesson.kind)}</span></div>
      <h4>${escapeHtml(lesson.name)}</h4>
      <p>${escapeHtml(copy.summary)}</p>
      <button class="lesson-open" type="button" data-group="${escapeHtml(group.id)}" data-stage="${escapeHtml(stageInfo.id)}" data-lesson="${escapeHtml(lesson.no)}">查看本课目录摘要 <span>↗</span></button>
    </article>`;
  };

  const renderStage = (stageInfo, group, index) => {
    const preview = stageInfo.cover || previewForStage[stageInfo.id] || group.cover;
    return `<details class="stage-panel" ${index === 0 ? "open" : ""} data-stage-panel="${escapeHtml(stageInfo.id)}">
      <summary>
        <span class="stage-index">${String(index + 1).padStart(2, "0")}</span>
        <span class="stage-summary-copy"><strong>${escapeHtml(stageInfo.title)}</strong><small>${escapeHtml(stageInfo.subtitle)}</small></span>
        <span class="stage-count">${stageInfo.lessons.length} 课 <b>＋</b></span>
      </summary>
      <div class="stage-panel-body">
        <div class="stage-overview">
          <img src="${preview}" alt="${escapeHtml(stageInfo.title)}课程预览" loading="lazy" onerror="this.src='${group.cover}'" />
          <div><p class="eyebrow">STAGE OVERVIEW</p><h3>${escapeHtml(stageInfo.subtitle)}</h3><p>${escapeHtml(stageInfo.focus)}</p><p class="stage-bridge"><strong>学习关系：</strong>${escapeHtml(stageInfo.id === "stage-01" ? "从观察与基础判断出发，为后续光色与画层建立共同语言。" : stageInfo.id === "stage-02" ? "把基础判断带入艺术家案例和直接画法，逐步获得画面组织能力。" : stageInfo.id === "stage-03" ? "把光色经验推进到画层、底色和材料实验，理解古典绘画的结构。" : "把方法、研究和材料经验汇总为个人创作与作品系列。")}</p></div>
        </div>
        <div class="lesson-grid">${stageInfo.lessons.map((lesson) => renderLesson(lesson, stageInfo, group)).join("")}</div>
      </div>
    </details>`;
  };

  const renderGroup = (group) => `<section class="course-group" id="${escapeHtml(group.id)}" data-group-section="${escapeHtml(group.id)}">
    <div class="course-group-cover">
      <img src="${group.cover}" alt="${escapeHtml(group.title)}封面" />
      <div class="course-group-cover-overlay"><span>${escapeHtml(group.eyebrow)}</span><small>${escapeHtml(group.english)}</small></div>
    </div>
    <div class="course-group-content">
      <div class="course-group-heading"><div><p class="eyebrow">${escapeHtml(group.eyebrow)} / COURSE SYSTEM</p><h2>${escapeHtml(group.title)}</h2></div><span class="course-total"><strong>${countAll(group)}</strong> lessons</span></div>
      <p class="course-group-intro">${escapeHtml(group.intro)}</p><p class="course-group-promise">${escapeHtml(group.promise)}</p>
      <div class="stage-list">${group.stages.map((stageInfo, index) => renderStage(stageInfo, group, index)).join("")}</div>
    </div>
  </section>`;

  root.innerHTML = `<div class="course-map-toolbar section"><div><p class="eyebrow">COURSE INDEX / 可操作目录</p><h2>从体系到单课，逐层打开。</h2></div><label class="course-search"><span>⌕</span><input id="course-search" type="search" placeholder="搜索课程名、课号或关键词" /></label></div>
    <div class="course-group-switcher section" role="tablist" aria-label="课程体系筛选"><button class="is-active" data-filter="all" role="tab">全部课程</button>${window.COURSE_GROUPS.map((group) => `<button data-filter="${group.id}" role="tab">${escapeHtml(group.title)}</button>`).join("")}</div>
    <div class="course-groups section">${window.COURSE_GROUPS.map(renderGroup).join("")}</div>
    <section class="course-map-cta section"><div><p class="eyebrow">NOT SURE WHERE TO START?</p><h2>不知道从哪一阶段开始？</h2><p>告诉我们你的绘画经验、材料条件和想完成的作品，我们会根据这张课程地图给你一个更具体的进入建议。</p></div><a class="button light" href="./contact.html?from=course-map">获取学习路线建议</a></section>`;

  const allLessons = () => [...root.querySelectorAll(".lesson-card")];
  const filterCards = () => {
    const query = (document.querySelector("#course-search")?.value || "").trim().toLowerCase();
    const active = root.querySelector(".course-group-switcher .is-active")?.dataset.filter || "all";
    root.querySelectorAll("[data-group-section]").forEach((section) => {
      const groupVisible = active === "all" || section.dataset.groupSection === active;
      section.hidden = !groupVisible;
      section.querySelectorAll(".lesson-card").forEach((card) => {
        const matches = !query || card.dataset.search.toLowerCase().includes(query);
        card.hidden = !matches;
      });
      section.querySelectorAll(".stage-panel").forEach((panel) => {
        const anyVisible = [...panel.querySelectorAll(".lesson-card")].some((card) => !card.hidden);
        panel.hidden = !anyVisible;
      });
    });
  };

  root.querySelectorAll("[data-filter]").forEach((button) => button.addEventListener("click", () => {
    root.querySelectorAll("[data-filter]").forEach((item) => item.classList.remove("is-active"));
    button.classList.add("is-active");
    filterCards();
  }));
  document.querySelector("#course-search")?.addEventListener("input", filterCards);

  const openModal = (groupId, stageId, lessonNo) => {
    const group = window.COURSE_GROUPS.find((item) => item.id === groupId);
    const stageInfo = group?.stages.find((item) => item.id === stageId);
    const lesson = stageInfo?.lessons.find((item) => item.no === lessonNo);
    if (!group || !stageInfo || !lesson) return;
    const copy = lessonCopy(lesson, stageInfo, group);
    const preview = previewForLesson(lesson, group, stageInfo);
    modalContent.innerHTML = `<div class="modal-kicker">${escapeHtml(group.title)} / ${escapeHtml(stageInfo.title)}</div><h2 id="modal-title">${escapeHtml(lesson.name)}</h2><div class="modal-meta"><span>${escapeHtml(lesson.no)}</span><span>${escapeHtml(lesson.kind)}</span><span>PDF 目录预览</span></div><div class="modal-layout"><img src="${preview}" alt="${escapeHtml(lesson.name)}课程截图" onerror="this.src='${group.cover}'" /><div><h3>这一课会解决什么？</h3><p>${escapeHtml(copy.summary)}</p><h3>它和前后课程怎么连接？</h3><p>${escapeHtml(copy.bridge)}</p><h3>完成后你会带走什么？</h3><p>${escapeHtml(copy.outcome)}</p><div class="modal-note">页面展示的是购买前的课程地图与摘要，完整视频、PDF 书稿和配套资料将在课程开通后提供。</div><a class="button primary" href="./contact.html?course=${encodeURIComponent(lesson.name)}">咨询这节课</a></div></div>`;
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("modal-open");
  };

  root.addEventListener("click", (event) => {
    const button = event.target.closest(".lesson-open");
    if (button) openModal(button.dataset.group, button.dataset.stage, button.dataset.lesson);
  });
  document.querySelectorAll("[data-close-modal]").forEach((item) => item.addEventListener("click", () => {
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("modal-open");
  }));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      modal.setAttribute("aria-hidden", "true");
      document.body.classList.remove("modal-open");
    }
  });
})();
