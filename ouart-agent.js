const OUART_LINKS = {
  home: "./index.html",
  courses: "./courses.html",
  pigments: "./pigments.html",
  daily: "./daily-art.html",
  gallery: "./gallery.html",
  openClass: "./open-class.html",
  contact: "./contact.html?from=ouart-agent",
  ipWorkshop: "./ip-object-workshop/index.html",
};

const OUART_STYLE_LABELS = {
  direct: "课程说明",
  triage: "学习建议",
  material: "材料建议",
  purchase: "购买建议",
};

const OUART_COMMON_COLLECT = [
  "你目前的水平：零基础、已有临摹经验，还是正在创作个人作品。",
  "你想解决的问题：选课、材料购买、技法练习、作品诊断或创作规划。",
  "你的时间和预算：每周可投入多久，是否需要直播、点评或陪跑服务。",
];

const OUART_KNOWLEDGE = [
  {
    id: "course-map",
    title: "初艺课程体系是什么",
    category: "课程总览",
    keywords: ["初艺", "课程", "课程体系", "怎么学", "学什么", "油画课", "从哪开始", "课程地图", "147", "六套"],
    summary: "初艺把油画学习拆成三条可以组合的入口：四阶段油画主课、DLC 专题课、材料与技法。主课负责长期能力，DLC 负责专项补强，材料与技法负责把材料选择和验证变成可执行的方法。",
    bullets: [
      "四阶段主课：第一阶段建立观察、明度、色相、纯度、形体、空间与写生语言；第二阶段进入光色、直接画法与印象派研究；第三阶段理解古典大师、画层与材料关系；第四阶段把方法转化为个人创作和系列作品。",
      "DLC 专题课：素描底层逻辑、色彩范围与色环、风景问题、绘画肌理、坦培拉基础、罩染前底层和局部罩染。",
      "材料与技法：颜料、品牌标签、染色能力、调色板、油壶、画刀、画笔、画架、研磨、色系测试、干燥与古典绘画材料边界。",
      "每一节课都配有课程目录、学习目标、PDF 讲义和视频课程；网站目录用于购买前了解路线，不替代完整课程内容。",
    ],
    templates: { direct: ["你可以先打开课程地图，看三大体系，再按自己的目标进入阶段或专题。"] },
    collect: OUART_COMMON_COLLECT,
    links: [["查看课程地图", OUART_LINKS.courses], ["咨询学习路线", OUART_LINKS.contact]],
    followups: ["零基础应该从哪一阶段开始？", "材料与技法课适合谁？", "DLC 和主课怎么组合？"],
  },
  {
    id: "study-route",
    title: "零基础应该从哪一阶段开始",
    category: "学习路线",
    keywords: ["零基础", "初学者", "从哪一阶段", "从哪开始", "学习路线", "入门", "不会画", "基础差", "成人油画"],
    summary: "零基础通常从第一阶段开始。第一阶段不是只教画一张画，而是建立一套可重复使用的判断语言：明度、色相、纯度、形体、空间和画面完成度。",
    bullets: [
      "如果你还不能稳定判断黑白关系、形体转折和画面整体完成度，优先从第一阶段开始。",
      "如果你已经能完成基本写生，但光色、直接画法和色彩组织不稳定，可以从第二阶段进入。",
      "如果你已经有长期绘画经验，想研究古典画层、罩染或大师临摹，可以把第三阶段与材料/DLC 并行。",
      "如果你已有稳定技法并希望发展个人系列，第四阶段更适合作为创作主线，但仍建议回看前面阶段的判断工具。",
    ],
    templates: { triage: ["最稳妥的做法是先完成基础水平测试，再根据明度、造型、色彩和完成度的短板选起点。"] },
    collect: ["你是否完成过完整油画作品。", "目前最不稳定的是明度、造型、色彩、画层还是创作主题。", "每周可以安排几次练习。"],
    links: [["查看四阶段主课", OUART_LINKS.courses], ["咨询学习路线", OUART_LINKS.contact]],
    followups: ["怎么判断自己能不能从第二阶段开始？", "第一阶段具体练什么？", "主课需要按顺序学吗？"],
  },
  {
    id: "four-stages",
    title: "四阶段主课分别解决什么问题",
    category: "四阶段主课",
    keywords: ["第一阶段", "第二阶段", "第三阶段", "第四阶段", "四阶段", "主课", "基础篇", "印象篇", "古典篇", "创作篇"],
    summary: "四阶段主课是一条从观察、光色、画层到创作的长期路径。每一阶段都有明确的能力重点，前一阶段的判断工具会成为后一阶段的基础。",
    bullets: [
      "第一阶段｜基础篇：观察、明度、色相、纯度、形体、空间与写生，建立画面判断和完成度标准。",
      "第二阶段｜印象篇：研究马奈、莫奈、毕沙罗、修拉等艺术家的光色和组织方式，训练直接画法、色彩预设与写生应用。",
      "第三阶段｜古典篇：理解古典大师的构图、底层、罩染、画层、透明与覆盖关系，把材料行为和画面结构连接起来。",
      "第四阶段｜创作篇：从主题、图像选择、构图、系列规划到局部调整，建立属于自己的创作流程和作品判断。",
    ],
    links: [["进入四阶段课程目录", OUART_LINKS.courses]],
    followups: ["第二阶段适合练什么？", "第三阶段为什么要学画层？", "第四阶段会不会点评个人创作？"],
  },
  {
    id: "dlc",
    title: "DLC 专题课适合什么时候学",
    category: "DLC 专题课",
    keywords: ["DLC", "专题", "素描", "色彩范围", "色环", "风景", "肌理", "坦培拉", "罩染", "补课", "专项"],
    summary: "DLC 不是另一条主线，而是可以插入四阶段的专项模块。它适合补短板、做集中练习，或在进入复杂创作前先把某个方法讲清楚。",
    bullets: [
      "素描底层逻辑：解决观察、结构、比例和黑白关系，为油画造型打底。",
      "色彩范围与色环：帮助你建立可控制的色彩范围，而不是盲目增加颜料数量。",
      "风景问题：从‘画什么’进入构图、光线、空间和现场判断。",
      "绘画肌理、坦培拉与罩染：理解不同材料和画层如何改变表面、透明度、覆盖力与观看距离。",
    ],
    templates: { triage: ["如果你正在主课中遇到一个具体短板，先用 DLC 做专项；如果还没有稳定基础，先不要用 DLC 替代第一阶段。"] },
    links: [["查看 DLC 目录", OUART_LINKS.courses]],
    followups: ["DLC 能不能单独购买？", "罩染应该放在哪个阶段学？", "色彩范围练习怎么做？"],
  },
  {
    id: "materials",
    title: "材料与技法课程讲什么",
    category: "材料与技法",
    keywords: ["材料", "技法", "颜料", "品牌", "标签", "调色板", "油壶", "画刀", "画笔", "画架", "研磨", "干燥", "工具", "买什么", "怎么用"],
    summary: "材料与技法课程把‘我该买什么、怎么用、如何验证’拆成一套工作方法。重点不是罗列品牌，而是观察颜料的覆盖力、染色能力、透明度、干燥、混合和画层行为。",
    bullets: [
      "先讲颜料概览、品牌与标签、颜料等级和染色能力，再进入调色板、油壶、画刀、画笔、画架与画箱。",
      "研磨专题帮助理解颜料从粉体、油性介质到可绘画状态的变化，并建立专业边界意识。",
      "色系专题覆盖黄、红、蓝、绿、黑和土色系，结合色相、覆盖力、干燥速度与古典绘画应用。",
      "课程鼓励建立自己的颜料数据库和测试卡，用记录替代盲目试错；具体购买仍要根据预算、地区和创作目标调整。",
    ],
    templates: { material: ["不要先问‘哪个品牌最好’，先问‘我需要什么颜色行为、透明度、干燥速度和预算’。"] },
    collect: ["你现有的颜料品牌和色号。", "主要画人物、风景、静物、古典临摹还是抽象创作。", "希望解决覆盖力、混色、干燥、开裂、透明度还是工具选择问题。"],
    links: [["查看材料与技法目录", OUART_LINKS.courses], ["打开颜料库", OUART_LINKS.pigments]],
    followups: ["初学者第一套工具怎么买？", "透明颜料和覆盖颜料怎么区分？", "画笔应该怎么选？"],
  },
  {
    id: "materials-buy",
    title: "初学者第一套油画材料怎么买",
    category: "材料购买",
    keywords: ["第一套", "采购", "购买", "买材料", "新手", "工具清单", "颜料清单", "油画工具", "入门材料", "预算"],
    summary: "新手购买建议先建立一套可完成练习的基础配置，不要一次买齐所有颜色和媒介。优先保证画布、有限色颜料、基础画笔、调色板、画刀、清洁和安全用品。",
    bullets: [
      "颜料：先用有限色范围练习明度、色相和纯度，再根据课程和个人题材扩展色系。",
      "工具：调色板、画笔、画刀、油壶/调色媒介容器、画架或稳定支撑面、清洁用品。",
      "练习：先准备小尺寸画布或画板，方便做颜色测试、肌理测试和短周期练习。",
      "安全：保持通风，区分可接触材料和需要谨慎处理的溶剂；不要把网络清单当作唯一标准。",
    ],
    templates: { purchase: ["如果你把预算、题材和现有工具发给我，我可以按‘必须买 / 可后买 / 暂时不用’帮你整理。"] },
    links: [["材料与技法课程", OUART_LINKS.courses], ["颜料库", OUART_LINKS.pigments], ["咨询购买清单", OUART_LINKS.contact]],
    followups: ["有限色应该选哪些颜色？", "油壶和画刀有必要买吗？", "溶剂和媒介怎么选？"],
  },
  {
    id: "paint-problems",
    title: "画面总是脏、灰、干或没有厚重感怎么办",
    category: "技法诊断",
    keywords: ["脏", "灰", "干", "厚重", "覆盖", "混色", "发粉", "开裂", "干燥", "画面问题", "画不好", "怎么改"],
    summary: "画面问题通常不是单一颜料造成的，而是明度、色相、纯度、混色次数、画层顺序和材料行为共同作用的结果。先判断问题发生在哪一层，再决定是改配色、改笔触还是改媒介。",
    bullets: [
      "画面脏：先检查是否混用了过多互补色、是否反复覆盖导致纯度下降，以及明度关系是否已经失控。",
      "画面灰：检查色彩范围是否过宽、白色是否过度加入、局部颜色是否没有围绕整体色调组织。",
      "画面干：检查颜料、媒介、底材吸收和笔触压力，不要只靠增加油剂解决。",
      "没有厚重感：厚度不等于堆颜料，先建立大关系，再用覆盖、刮擦、叠加和局部厚涂形成有节奏的表面。",
    ],
    templates: { triage: ["最有效的诊断资料是：正面作品图、局部近照、使用的颜料/媒介、画布底和你觉得最不满意的区域。"] },
    collect: ["作品正面图和 1-3 张局部近照。", "颜料、媒介、底材和每一层大致的绘制顺序。", "你希望画面达到的效果：透明、厚涂、古典、直接或肌理。"],
    links: [["材料与技法目录", OUART_LINKS.courses], ["提交作品咨询", OUART_LINKS.contact]],
    followups: ["罩染为什么会发脏？", "厚涂和堆颜料有什么区别？", "怎么建立自己的材料测试卡？"],
  },
  {
    id: "ip-workshop",
    title: "绘画思维和 IP 实物营有什么关系",
    category: "跨项目学习",
    keywords: ["IP实物营", "IP", "元维构", "模型", "3D", "实物", "绘画思维", "降维", "结构", "转译", "模型制作"],
    summary: "绘画训练中的观察、形体、明度、边缘、材质和完成度判断，可以迁移到 IP 实物和模型制作中。它帮助你先判断视觉结构，再决定模型、涂装、材料和展示方式。",
    bullets: [
      "观察与形体：帮助从二维图像中提取主形、比例、空间和视觉重心。",
      "明度与边缘：帮助判断模型的分面、转折、光照和涂装层次，而不是只追求外轮廓相似。",
      "材料与表面：绘画中的覆盖、透明、肌理和干燥观察，可以迁移到模型底漆、上色、旧化和保护层。",
      "完成度判断：先设定用途、观看距离和交付标准，再决定哪些细节必须做、哪些细节可以舍弃。",
    ],
    links: [["查看 IP 实物营", OUART_LINKS.ipWorkshop], ["查看课程体系", OUART_LINKS.courses]],
    followups: ["绘画基础如何帮助做模型？", "模型涂装和油画材料有什么相通之处？", "IP 实物营适合什么人？"],
  },
  {
    id: "products",
    title: "初艺课程之外还能提供什么",
    category: "服务与产品",
    keywords: ["产品", "服务", "点评", "训练营", "会员", "作品集", "工作坊", "线下", "出版", "合作", "课程购买", "怎么报名", "怎么买", "价格"],
    summary: "初艺的内容可以形成课程购买、低价专题、训练营、作业点评、会员服务、作品集辅导、材料工具包、画室授权和机构合作等不同层级。网站问答助手会先解释适合的入口，具体价格和服务范围以人工确认。",
    bullets: [
      "课程产品：四阶段主课、DLC、材料与技法，以及 PDF 课程书与视频组合。",
      "练习产品：7 天明度/色彩训练、21 天每日一画、色彩范围练习册和材料测试包。",
      "服务产品：单次作品诊断、作业点评、8-12 周创作陪跑、作品集规划和线下工作坊。",
      "机构产品：画室使用授权、教师版课程、学期教学方案、美术馆/文化馆公共教育和品牌材料教育内容。",
    ],
    templates: { triage: ["如果你告诉我自己的身份、目标和预算，我可以先帮你分到‘自学课程 / 训练营 / 点评 / 机构合作’入口。"] },
    links: [["查看课程目录", OUART_LINKS.courses], ["联系初艺", OUART_LINKS.contact]],
    followups: ["我适合买课程还是训练营？", "可以做作品集辅导吗？", "画室如何合作？"],
  },
];

const OUART_WELCOME = {
  title: "你好，我是初艺学习与课程助手",
  category: "欢迎",
  summary: "我可以回答课程路线、四阶段主课、DLC、材料与技法、颜料购买、画面问题、作品学习和 IP 实物营之间的关系。你也可以直接问：我应该从哪一阶段学起？",
  bullets: [
    "课程目录问题可以直接回答，并给出对应入口。",
    "材料购买和画面诊断会先给方法，再提醒你补充作品图、颜料和目标。",
    "涉及具体报价、购买、点评和人工服务时，我会引导你联系初艺确认。",
  ],
  links: [["查看课程地图", OUART_LINKS.courses], ["颜料库", OUART_LINKS.pigments], ["联系初艺", OUART_LINKS.contact]],
  followups: ["零基础应该从哪一阶段开始？", "材料与技法课程讲什么？", "初学者第一套油画材料怎么买？"],
};

const OUART_FALLBACK = {
  title: "我需要更多信息来判断",
  category: "需要补充信息",
  summary: "这个问题可以继续回答，但我需要知道你的学习阶段、作品类型、材料情况或购买目标。你可以直接补充：你是谁、想解决什么问题、目前做到哪一步。",
  bullets: [
    "课程问题：说明零基础/有经验、每周时间和希望达到的结果。",
    "材料问题：说明颜料品牌、色号、媒介、底材和遇到的现象。",
    "作品问题：提供正面图、局部图、使用材料和你最不满意的区域。",
  ],
  links: [["查看课程地图", OUART_LINKS.courses], ["联系初艺", OUART_LINKS.contact]],
  followups: ["我有作品，应该怎么开始？", "主课和 DLC 怎么组合？", "我想咨询购买和点评服务。"],
};

function ouartNormalize(text) {
  return (text || "").toLowerCase().replace(/[\s，。！？、；：,.!?]/g, "");
}

function ouartStyle(question) {
  const q = ouartNormalize(question);
  if (["买", "购买", "采购", "预算", "多少钱", "品牌", "色号"].some((word) => q.includes(word))) return "purchase";
  if (["怎么开始", "需要什么", "资料", "判断", "提交", "从哪", "如何"].some((word) => q.includes(word))) return "triage";
  if (["材料", "颜料", "画笔", "画刀", "干燥", "罩染", "媒介", "肌理"].some((word) => q.includes(word))) return "material";
  return "direct";
}

function ouartScore(question, entry) {
  const q = ouartNormalize(question);
  return entry.keywords.reduce((score, keyword) => {
    const key = ouartNormalize(keyword);
    if (!key || !q.includes(key)) return score;
    return score + Math.max(3, Math.min(22, key.length + 2));
  }, q.includes(ouartNormalize(entry.title)) ? 8 : 0);
}

function ouartUnique(items) { return [...new Set((items || []).filter(Boolean))]; }
function ouartLinks(items) {
  const seen = new Set();
  return (items || []).filter(([label, href]) => {
    const key = `${label}|${href}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function ouartFindAnswer(question) {
  const style = ouartStyle(question);
  const ranked = OUART_KNOWLEDGE.map((entry) => ({ entry, score: ouartScore(question, entry) })).sort((a, b) => b.score - a.score);
  if (!ranked[0] || ranked[0].score < 3) return { ...OUART_FALLBACK, style };
  const primary = ranked[0].entry;
  const related = ranked.filter((item) => item.score >= 8 && item.entry.id !== primary.id).slice(0, 2).map((item) => item.entry);
  return {
    ...primary,
    style,
    styleLabel: OUART_STYLE_LABELS[style],
    template: primary.templates?.[style] || primary.templates?.direct || [],
    bullets: ouartUnique([...primary.bullets, ...related.flatMap((entry) => entry.bullets.slice(0, 2))]).slice(0, 8),
    collect: ouartUnique([...(primary.collect || []), ...related.flatMap((entry) => entry.collect || []).slice(0, 3)]).slice(0, 7),
    links: ouartLinks([...primary.links, ...related.flatMap((entry) => entry.links || [])]).slice(0, 5),
    related: related.map((entry) => entry.title),
    followups: ouartUnique([...(primary.followups || []), ...related.flatMap((entry) => entry.followups || [])]).slice(0, 5),
  };
}

function ouartEscape(value) {
  return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function ouartAnswerHtml(answer) {
  const meta = `<div class="ouart-answer-meta"><span>${ouartEscape(answer.styleLabel || OUART_STYLE_LABELS[answer.style] || "课程知识")}</span><span>${ouartEscape(answer.category || "知识库")}</span></div>`;
  const list = (items) => items?.length ? `<ul>${items.map((item) => `<li>${ouartEscape(item)}</li>`).join("")}</ul>` : "";
  const template = answer.template?.length ? `<div class="ouart-answer-template">${answer.template.map((item) => `<p>${ouartEscape(item)}</p>`).join("")}</div>` : "";
  const collect = answer.collect?.length ? `<div class="ouart-answer-collect"><strong>为了继续判断，可以补充</strong>${list(answer.collect)}</div>` : "";
  const links = (answer.links || []).map(([label, href]) => `<a href="${href}">${ouartEscape(label)}</a>`).join("");
  const followups = answer.followups?.length ? `<div class="ouart-answer-followups">${answer.followups.map((prompt) => `<button type="button" data-ouart-inline-prompt="${ouartEscape(prompt)}">${ouartEscape(prompt)}</button>`).join("")}</div>` : "";
  return `${meta}<h3>${ouartEscape(answer.title)}</h3><p>${ouartEscape(answer.summary)}</p>${template}${list(answer.bullets)}${collect}${answer.caution ? `<p class="ouart-answer-caution">${ouartEscape(answer.caution)}</p>` : ""}${answer.related?.length ? `<p class="ouart-answer-related">关联主题：${answer.related.map(ouartEscape).join(" / ")}</p>` : ""}<div class="ouart-answer-links">${links}</div>${followups}`;
}

function ouartAddMessage(container, role, content) {
  const message = document.createElement("article");
  message.className = `ouart-message ${role}`;
  message.innerHTML = role === "user" ? `<p>${ouartEscape(content)}</p>` : content;
  container.appendChild(message);
  container.scrollTop = container.scrollHeight;
  return message;
}

function ouartInitConversation(messages, form, input, promptSelector, clearSelector) {
  if (!messages || !form || !input) return;
  ouartAddMessage(messages, "agent", ouartAnswerHtml(OUART_WELCOME));
  const submit = (question) => {
    const clean = question.trim();
    if (!clean) return;
    ouartAddMessage(messages, "user", clean);
    input.value = "";
    ouartAddMessage(messages, "agent", ouartAnswerHtml(ouartFindAnswer(clean)));
  };
  form.addEventListener("submit", (event) => { event.preventDefault(); submit(input.value); });
  input.addEventListener("keydown", (event) => { if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) form.requestSubmit(); });
  document.querySelectorAll(promptSelector).forEach((button) => button.addEventListener("click", () => submit(button.dataset.ouartPrompt || button.dataset.ouartFullPrompt || "")));
  messages.addEventListener("click", (event) => {
    const button = event.target.closest("[data-ouart-inline-prompt]");
    if (button) submit(button.dataset.ouartInlinePrompt || "");
  });
  document.querySelector(clearSelector)?.addEventListener("click", () => { messages.innerHTML = ""; ouartAddMessage(messages, "agent", ouartAnswerHtml(OUART_WELCOME)); });
}

function ouartInitFullPage() {
  ouartInitConversation(document.querySelector("[data-ouart-full-messages]"), document.querySelector("[data-ouart-full-form]"), document.querySelector("[data-ouart-full-input]"), "[data-ouart-full-prompt]", "[data-ouart-full-clear]");
}

window.OuartAgent = { WELCOME: OUART_WELCOME, findAnswer: ouartFindAnswer, answerToHtml: ouartAnswerHtml, escapeHtml: ouartEscape };
document.addEventListener("DOMContentLoaded", ouartInitFullPage);
