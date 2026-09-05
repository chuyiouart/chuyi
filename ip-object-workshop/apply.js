(function () {
  "use strict";

  const form = document.querySelector("[data-application-form]");
  const result = document.querySelector("[data-application-result]");
  const summary = document.querySelector("[data-application-summary]");
  const formStatus = document.querySelector("[data-form-status]");
  const copyStatus = document.querySelector("[data-copy-status]");
  const copyButton = document.querySelector("[data-copy-application]");
  const editButton = document.querySelector("[data-edit-application]");
  const storageKey = "ip-object-workshop-enrollment-draft";

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
      "【IP 实物化实战营 · 长期招生预约资料（尚未提交）】",
      `姓名：${fieldValue("name")}`,
      `城市：${fieldValue("city")}`,
      `电话：${fieldValue("phone")}`,
      `微信：${fieldValue("wechat") || "未填写"}`,
      `起点：${selectedValues("route")[0] || "未选择"}`,
      `项目名称：${fieldValue("projectName")}`,
      `项目介绍：${fieldValue("projectIntro")}`,
      `参考链接：${fieldValue("referenceUrl") || "无"}`,
      `优先目标：${fieldValue("primaryGoal")}`,
      `期望时长：${fieldValue("duration")}`,
      `可到课时间：${fieldValue("availability")}`,
      `建模经验：${fieldValue("modelLevel")}`,
      `绘画 / 涂装经验：${fieldValue("paintLevel")}`,
      `报名方式：${selectedValues("pricePlan")[0] || "未选择"}`,
      `可携带设备：${devices.length ? devices.join("、") : "未选择"}`,
      "",
      "已确认：以上报名信息真实，并已了解课程费用边界；正式展览、批量生产与销售服务不包含在基础课程费用中。",
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
