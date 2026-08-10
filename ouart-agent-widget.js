(function initOuartWidget() {
  if (document.querySelector("[data-ouart-assistant-widget]")) return;
  if (/\/agent\.html$/.test(location.pathname)) return;

  const siteRoot = new URL("./", location.href);
  const widget = document.createElement("aside");
  widget.className = "ouart-assistant-widget";
  widget.dataset.ouartAssistantWidget = "";
  widget.innerHTML = `
    <button class="ouart-assistant-trigger" type="button" aria-expanded="false" aria-controls="ouartAssistantPanel">
      <img src="${new URL("assets/logo-dark.png", siteRoot).href}" alt="" />
      <span>问问初艺</span>
    </button>
    <section class="ouart-assistant-panel" id="ouartAssistantPanel" aria-label="初艺学习与课程助手" hidden>
      <header>
        <div><span>OUART ASSISTANT</span><strong>学习与课程助手</strong></div>
        <button type="button" data-ouart-assistant-close aria-label="关闭问答助手">×</button>
      </header>
      <div class="ouart-assistant-suggestions" aria-label="推荐问题">
        <button type="button" data-ouart-prompt="零基础应该从哪一阶段开始？">学习路线</button>
        <button type="button" data-ouart-prompt="四阶段主课分别解决什么问题？">四阶段主课</button>
        <button type="button" data-ouart-prompt="DLC 专题课适合什么时候学？">DLC 专题</button>
        <button type="button" data-ouart-prompt="材料与技法课程讲什么？">材料技法</button>
        <button type="button" data-ouart-prompt="初学者第一套油画材料怎么买？">材料采购</button>
        <button type="button" data-ouart-prompt="画面总是脏、灰、干或没有厚重感怎么办？">画面诊断</button>
        <button type="button" data-ouart-prompt="绘画思维和 IP 实物营有什么关系？">IP 实物营</button>
      </div>
      <div class="ouart-assistant-messages" data-ouart-assistant-messages aria-live="polite"></div>
      <form class="ouart-assistant-form" data-ouart-assistant-form>
        <label class="sr-only" for="ouartAssistantQuestion">输入你的问题</label>
        <textarea id="ouartAssistantQuestion" rows="2" placeholder="输入问题，例如：我应该从哪一阶段学起？" data-ouart-assistant-input></textarea>
        <button type="submit">发送</button>
      </form>
      <p class="ouart-assistant-note">具体报价、购买、点评和作品诊断以人工确认为准。<a href="./agent.html">打开完整问答页</a></p>
    </section>
  `;
  document.body.appendChild(widget);

  const panel = widget.querySelector(".ouart-assistant-panel");
  const trigger = widget.querySelector(".ouart-assistant-trigger");
  const input = widget.querySelector("[data-ouart-assistant-input]");
  const messages = widget.querySelector("[data-ouart-assistant-messages]");
  let welcomed = false;

  const loadAgent = () => {
    if (window.OuartAgent) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = new URL("ouart-agent.js?v=20260810-agent-v1", siteRoot).href;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  };
  const open = () => {
    panel.hidden = false;
    trigger.setAttribute("aria-expanded", "true");
    widget.classList.add("is-open");
    loadAgent().then(() => {
      if (!welcomed && window.OuartAgent) {
        ouartRender("agent", window.OuartAgent.answerToHtml(window.OuartAgent.WELCOME));
        welcomed = true;
      }
      input.focus();
    }).catch(() => { window.location.href = new URL("agent.html", siteRoot).href; });
  };
  const close = () => { panel.hidden = true; trigger.setAttribute("aria-expanded", "false"); widget.classList.remove("is-open"); };
  const ouartRender = (role, content) => {
    const item = document.createElement("article");
    item.className = `ouart-message ${role}`;
    item.innerHTML = role === "user" ? `<p>${window.OuartAgent.escapeHtml(content)}</p>` : content;
    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;
  };
  const ask = (value) => {
    const question = value.trim();
    if (!question || !window.OuartAgent) return;
    ouartRender("user", question);
    input.value = "";
    ouartRender("agent", window.OuartAgent.answerToHtml(window.OuartAgent.findAnswer(question)));
  };
  const askPrompt = (value) => { open(); loadAgent().then(() => ask(value)); };

  trigger.addEventListener("click", () => panel.hidden ? open() : close());
  widget.querySelector("[data-ouart-assistant-close]").addEventListener("click", close);
  widget.querySelector("[data-ouart-assistant-form]").addEventListener("submit", (event) => { event.preventDefault(); loadAgent().then(() => ask(input.value)); });
  input.addEventListener("keydown", (event) => { if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) widget.querySelector("[data-ouart-assistant-form]").requestSubmit(); });
  widget.querySelectorAll("[data-ouart-prompt]").forEach((button) => button.addEventListener("click", () => askPrompt(button.dataset.ouartPrompt || "")));
  messages.addEventListener("click", (event) => { const button = event.target.closest("[data-ouart-inline-prompt]"); if (button) askPrompt(button.dataset.ouartInlinePrompt || ""); });
})();
