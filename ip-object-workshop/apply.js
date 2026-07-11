(function () {
  "use strict";

  const form = document.querySelector("[data-application-form]");
  const result = document.querySelector("[data-application-result]");
  const summary = document.querySelector("[data-application-summary]");
  const formStatus = document.querySelector("[data-form-status]");
  const copyStatus = document.querySelector("[data-copy-status]");
  const copyButton = document.querySelector("[data-copy-application]");
  const editButton = document.querySelector("[data-edit-application]");
  const storageKey = "ip-object-workshop-application-draft";

  if (!form || !result || !summary) return;

  function restoreDraft() {
    let draft;
    try {
      draft = JSON.parse(localStorage.getItem(storageKey) || "{}");
    } catch (error) {
      draft = {};
    }
    Object.entries(draft).forEach(([name, value]) => {
      const fields = form.querySelectorAll(`[name="${name}"]`);
      fields.forEach((field) => {
        if (field.type === "radio" || field.type === "checkbox") {
          field.checked = field.value === value || (Array.isArray(value) && value.includes(field.value));
        } else {
          field.value = value;
        }
      });
    });
  }

  function selectedValues(name) {
    return Array.from(form.querySelectorAll(`[name="${name}"]:checked`)).map((input) => input.value);
  }

  function fieldValue(name) {
    const field = form.elements.namedItem(name);
    return field && "value" in field ? field.value.trim() : "";
  }

  function buildSummary() {
    const devices = selectedValues("device");
    return [
      "【IP 实物化五天实战营 · 报名初诊】",
      `姓名：${fieldValue("name")}`,
      `城市：${fieldValue("city")}`,
      `电话：${fieldValue("phone")}`,
      `微信：${fieldValue("wechat") || "未填写"}`,
      `起点：${selectedValues("route")[0] || "未选择"}`,
      `项目名称：${fieldValue("projectName")}`,
      `项目介绍：${fieldValue("projectIntro")}`,
      `参考链接：${fieldValue("referenceUrl") || "无"}`,
      `优先目标：${fieldValue("primaryGoal")}`,
      `建模经验：${fieldValue("modelLevel")}`,
      `绘画 / 涂装经验：${fieldValue("paintLevel")}`,
      `可携带设备：${devices.length ? devices.join("、") : "未选择"}`,
      "",
      "已了解：提交资料不代表录取；付款在初诊通过并确认边界后进行；展览与销售另行评审。",
    ].join("\n");
  }

  form.addEventListener("input", () => {
    const draft = {};
    new FormData(form).forEach((value, key) => {
      if (typeof value !== "string") return;
      if (draft[key]) draft[key] = Array.isArray(draft[key]) ? [...draft[key], value] : [draft[key], value];
      else draft[key] = value;
    });
    localStorage.setItem(storageKey, JSON.stringify(draft));
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!form.checkValidity()) {
      formStatus.textContent = "请完成所有必填项。";
      form.reportValidity();
      return;
    }
    summary.value = buildSummary();
    form.hidden = true;
    result.hidden = false;
    result.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  copyButton.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(summary.value);
      copyStatus.textContent = "已复制。";
    } catch (error) {
      summary.focus();
      summary.select();
      copyStatus.textContent = "请长按或使用 Ctrl+C 复制。";
    }
  });

  editButton.addEventListener("click", () => {
    result.hidden = true;
    form.hidden = false;
    form.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  restoreDraft();
})();
