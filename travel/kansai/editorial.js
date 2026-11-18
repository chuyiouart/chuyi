"use strict";

const get = (id) => document.getElementById(id);
const html = (text = "") => String(text).replace(/[&<>"']/g, (ch) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
})[ch]);
const tabs = {plan:"行程", map:"地图与路线", shop:"购物清单", art:"画展与活动", pictures:"参考图"};
const allowed = new Set(Object.keys(tabs));
const params = new URLSearchParams(location.search);
const fragment = new URLSearchParams(location.hash.slice(1));
const secret = fragment.get("key") || "";
let selectedView = allowed.has(params.get("view")) ? params.get("view") : "plan";
let selectedDay = "all";
let data;

function picture(file, cssClass = "", eager = false) {
  const photo = data.gallery.find((item) => item.file === file);
  if (!photo) return "";
  const src = photo.embedded || `./assets/${photo.file}`;
  const link = photo.embedded ? (photo.source || src) : src;
  const caption = photo.source ? `<a href="${html(photo.source)}" target="_blank" rel="noopener noreferrer">${html(photo.credit)}</a>` : html(photo.credit);
  const license = photo.license ? ` · <a href="${html(photo.license)}" target="_blank" rel="noopener noreferrer">${html(photo.licenseName)}</a> · 网页缩放` : "";
  return `<figure class="photo ${cssClass}"><a href="${html(link)}" target="_blank" rel="noopener noreferrer"><img src="${html(src)}" alt="${html(photo.title)}" ${eager ? 'fetchpriority="high"' : 'loading="lazy"'} width="${photo.width}" height="${photo.height}"></a><figcaption>${html(photo.title)}${caption ? ` · ${caption}` : ""}${license}</figcaption></figure>`;
}

function coverImage() {
  const cover = data.gallery.find((photo) => photo.role === "cover");
  get("cover-art").innerHTML = cover ? `<img src="${html(cover.embedded || `./assets/${cover.file}`)}" alt="${html(cover.title)}" width="${cover.width}" height="${cover.height}" fetchpriority="high"><figcaption>${html(cover.credit)}</figcaption>` : "";
  get("cover-art").hidden = !cover;
}

function tripHighlights() {
  const highlights = [
    {day:0, file:"kyoto-night.webp", text:"京都 · 清水寺夜游"},
    {day:3, file:"uji-koshoji.webp", text:"宇治 · 红叶与任天堂"},
    {day:5, file:"sky-tree.webp", text:"大阪 · 梅田圣诞市集"}
  ];
  return `<div class="trip-highlights" aria-label="旅行亮点">${highlights.map(({day,file,text}) => {
    const photo = data.gallery.find((item) => item.file === file);
    if (!photo) return "";
    const source = photo.embedded || `./assets/${photo.file}`;
    return `<button class="highlight" data-day="${day}"><img src="${html(source)}" alt="" width="${photo.width}" height="${photo.height}"><span class="highlight-date">${html(data.days[day].short)}</span><span class="highlight-title">${html(text)}</span></button>`;
  }).join("")}</div>`;
}

function action(url, label) {
  if (!url || !/^https:\/\/|^\.\/assets\//.test(url)) return "";
  return `<a class="action" href="${html(url)}" target="_blank" rel="noopener noreferrer">${html(label)} ↗</a>`;
}

function google(query) {
  return query ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}` : "";
}

function directions(from, to, mode) {
  return `https://www.google.com/maps/dir/?${new URLSearchParams({api:"1",origin:from,destination:to,travelmode:mode})}`;
}

function statusTag(text) {
  if (!text) return "";
  const cls = text.includes("待购") ? "wait" : text.includes("未定") ? "empty" : "";
  return `<span class="tag ${cls}">${html(text)}</span>`;
}

function title(name, description = "") {
  return `<div class="section-top"><h2>${html(name)}</h2>${description ? `<p class="soft">${html(description)}</p>` : ""}</div>`;
}

function addLinks(...items) {
  return items.some(Boolean) ? `<div class="inline-links">${items.join("")}</div>` : "";
}

function dayPicker() {
  return `<div class="day-pick" aria-label="选择日期"><button data-day="all" aria-pressed="${selectedDay === "all"}">八天总览</button>${data.days.map((day,i) => `<button data-day="${i}" aria-pressed="${String(i) === selectedDay}">${html(day.short)} ${html(day.week)}${i === 2 ? " · 生日" : ""}</button>`).join("")}</div>`;
}

function period(day, key, label) {
  const [main, detail] = day[key];
  const status = day[key + "Status"];
  return `<div class="overview-slot"><span class="slot-label">${label}</span><p>${html(main)}</p>${status ? statusTag(status === "booked" ? "待购票" : main.includes("任天堂") ? "已购票" : "已确认") : ""}<p class="soft small">${html(detail)}</p>${key === "pm" ? `<p class="rest">${html(day.rest)}</p>` : ""}</div>`;
}

function overview() {
  return `<div class="overview"><div class="overview-row head"><span>日期 / 住宿</span><span>上午 — 午饭</span><span>下午 · 13:30—18:00</span><span>晚上</span></div>${data.days.map((day,i) => `<article class="overview-row"><div><button class="daynum" data-day="${i}" aria-label="查看${html(day.short)}详情">${html(day.short)} ${html(day.week)}</button><p class="small">${html(day.city)}</p><p class="soft small">${html(day.hotel)}</p></div>${period(day,"am","上午 — 午饭")}${period(day,"pm","下午")}${period(day,"night","晚上")}</article>`).join("")}</div>`;
}

function eventRow(event) {
  const isBreak = event.status === "休息安排";
  const end = event.end && !event.status.includes("航班") ? `<div class="small soft">至 ${html(event.end)}</div>` : "";
  return `<li class="${isBreak ? "break" : ""}"><div><time>${html(event.start)}</time>${end}</div><div><h3>${html(event.title)}</h3>${statusTag(event.status)}<p class="small">${html(event.detail)}</p>${addLinks(action(google(event.query),"地图定位"),action(event.url,"官网"))}</div></li>`;
}

function plan() {
  const header = title("每日行程", "午饭后留出下午茶或午休。未定时段按当天体力调整。");
  if (selectedDay === "all") return header + tripHighlights() + dayPicker() + overview();
  const day = data.days[Number(selectedDay)];
  return header + dayPicker() + title(`${day.short} ${day.week} · ${day.theme}`, `住宿  ${day.hotel}`) + `<div class="split day-split"><ol class="timeline">${day.events.map(eventRow).join("")}</ol><aside class="day-aside">${(day.photos || []).map((file) => picture(file,"day-photo")).join("")}<div class="notes"><h3>当天备注</h3><ul>${day.notes.map(([name, note]) => `<li><strong>${html(name)}</strong><p class="small">${html(note)}</p></li>`).join("")}</ul></div></aside></div>`;
}

function paintMap(stage, section) {
  const canvas = stage.querySelector("canvas");
  const context = canvas.getContext("2d");
  const w = canvas.width = 660;
  const h = canvas.height = 470;
  context.strokeStyle = "#d3ddce";
  context.lineWidth = 1;
  for (let x = 30; x < w; x += 40) {
    context.beginPath(); context.moveTo(x,0); context.lineTo(x,h); context.stroke();
  }
  for (let y = 30; y < h; y += 40) {
    context.beginPath(); context.moveTo(0,y); context.lineTo(w,y); context.stroke();
  }
  for (const line of section.lines) {
    context.strokeStyle = line === section.lines[0] ? "#527e69" : "#b16a50";
    context.lineWidth = 3;
    context.setLineDash([7,6]);
    context.beginPath();
    line.forEach((i,j) => {
      const point = section.points[i];
      context[j ? "lineTo" : "moveTo"](w*point.x/100,h*point.y/100);
    });
    context.stroke();
  }
}

function showPlace(panel, group, index) {
  const place = data.maps[group].points[index];
  panel.querySelectorAll("[data-pin]").forEach((button) => button.setAttribute("aria-pressed", String(Number(button.dataset.pin) === index)));
  panel.querySelector(".place-readout").innerHTML = `<h3>${html(place.cn)}</h3><p class="soft">${html(place.jp || place.query)}</p>${place.floor ? `<p>${html(place.floor)}</p>` : ""}${place.detail ? `<p class="small">${html(place.detail)}</p>` : ""}${place.lat ? `<p class="coordinates small">${place.lat.toFixed(5)}, ${place.lon.toFixed(5)} · 约略点位</p>` : ""}${addLinks(action(google(place.query),"Google Maps"),action(place.url,"官网"))}`;
}

function mapPanel(section, group) {
  return `<div class="map-panel" data-map="${group}"><h3>${html(section.name)}</h3><p class="small soft">${html(section.description)}</p><div class="map-stage"><canvas aria-hidden="true"></canvas>${section.points.map((p,i) => `<button aria-label="${html(p.cn)}" data-pin="${i}" style="left:${p.x}%;top:${p.y}%">${i+1}</button>`).join("")}</div><div class="map-key">${section.points.map((p,i) => `<button data-pin="${i}">${i+1} · ${html(p.short || p.cn)}</button>`).join("")}</div><div class="place-readout" aria-live="polite"></div></div>`;
}

function maps() {
  const routes = data.routes.map((r) => `<details><summary>${html(r.day)} · ${html(r.label)}</summary><p class="small soft">${html(r.note)}</p><div class="route-list">${r.legs.map(([from,to,mode,caption]) => `<div><p>${html(caption)}</p>${action(directions(from,to,mode),mode === "walking" ? "步行导航" : "公共交通")}</div>`).join("")}</div></details>`).join("");
  return title("地图与路线", "离线可看地点和相对方位。点击编号查楼层、地址，再用 Google Maps 看实际路线。") + `<div class="map-grid">${data.maps.map(mapPanel).join("")}</div><h3 class="subhead">分段导航</h3>${routes}`;
}

function checked(key) {
  try { return localStorage.getItem(`kansai-travel:v1:check:${key}`) === "1"; }
  catch { return false; }
}

function shops() {
  const checklist = data.shopping.map((item) => `<label><input type="checkbox" data-check="${html(item.id)}" ${checked(item.id) ? "checked" : ""}><span><strong>${html(item.title)}</strong><br><span class="small soft">${html(item.detail)}</span></span></label>`).join("");
  const stores = data.stores.map((store) => `<article class="entry">${picture(store.photo,"entry-photo")}<h3>${html(store.cn)}</h3><p class="small soft">${html(store.jp)} · ${html(store.en)}</p><p><strong>${html(store.floor)}</strong></p><p class="small">${html(store.find)}</p>${store.ask ? `<details><summary>给店员看的日文</summary><p>${html(store.ask)}</p></details>` : ""}${addLinks(action(google(store.query),"地图定位"),action(store.source,"官网"))}</article>`).join("");
  return title("购物清单", "勾选记录保存在当前浏览器。Apple TV 和望远镜以当天库存为准。") + `<div class="split"><div><h3>要买 / 要看</h3><div class="checklist">${checklist}</div>${action("https://www.yodobashi.com/product/100000001010266130/","Apple TV 商品页")}</div><aside class="notes"><h3>跟店员说</h3><p lang="ja">デッサン用のペン型消しゴムと消しゴム鉛筆を探しています。</p><p class="small">我在找素描用的笔式橡皮和橡皮铅笔。</p></aside></div><h3 class="subhead">梅田目标商店</h3><div class="entries">${stores}</div>`;
}

function art() {
  const cards = (entries) => `<div class="entries">${entries.map((event) => `<article class="entry">${picture(event.photo,"entry-photo")} ${statusTag(event.status)}<h3>${html(event.title)}</h3><p class="small soft">${html(event.when)} · ${html(event.where)}</p><p>${html(event.about)}</p>${event.note ? `<p class="small soft">${html(event.note)}</p>` : ""}${addLinks(action(event.url,"活动官网"),action(event.ticket,"购票或入场规则"),action(google(event.query),"地图定位"))}</article>`).join("")}</div>`;
  return title("画展与活动", "已加入的项目和备选分别列出，票务信息以官方页面为准。") + cards(data.art.main) + `<h3 class="subhead">备选与日期提醒</h3>${cards(data.art.backups)}`;
}

function pictures() {
  const groups = [["景点与展览","scene"],["楼层图与找店参考","guide"]];
  return title("参考图", "点图可查看原图或来源。楼层和入口以现场标识及官方最新版本为准。") + groups.map(([label,role]) => `<h3 class="subhead">${label}</h3><div class="gallery">${data.gallery.filter((photo) => (photo.role || "guide") === role).map((photo) => picture(photo.file)).join("")}</div>`).join("");
}

const renderers = {plan, map:maps, shop:shops, art, pictures};
function render() {
  get("views").innerHTML = Object.entries(tabs).map(([id,label]) => `<button data-view="${id}" aria-pressed="${id === selectedView}">${label}</button>`).join("");
  get("view").innerHTML = renderers[selectedView]();
  get("view").querySelectorAll("[data-map]").forEach((panel) => {
    const group = Number(panel.dataset.map);
    paintMap(panel.querySelector(".map-stage"), data.maps[group]);
    showPlace(panel, group, 0);
  });
}

function bind() {
  get("trip").addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    if (button.dataset.view) {
      selectedView = button.dataset.view;
      render();
      get("views").querySelector(`[data-view=${selectedView}]`).focus({preventScroll:true});
    } else if (button.dataset.day) {
      selectedDay = button.dataset.day;
      render();
      get("view").querySelector(`.day-pick [data-day="${selectedDay}"]`).focus();
    } else if (button.dataset.pin) {
      const panel = button.closest("[data-map]");
      showPlace(panel, Number(panel.dataset.map), Number(button.dataset.pin));
    }
  });
  get("trip").addEventListener("change", (event) => {
    const input = event.target;
    if (input.dataset.check) {
      try { localStorage.setItem(`kansai-travel:v1:check:${input.dataset.check}`, input.checked ? "1" : "0"); }
      catch { /* Storage may be unavailable in private browsing. */ }
    }
  });
  document.querySelector(".brand").addEventListener("click", (event) => {
    event.preventDefault();
    selectedDay = "all";
    selectedView = "plan";
    render();
    window.scrollTo(0,0);
  });
}

function decode(value) {
  return Uint8Array.from(atob(value.replace(/-/g,"+").replace(/_/g,"/")), (ch) => ch.charCodeAt(0));
}

async function unlock() {
  if (!/^[A-Za-z0-9_-]{43}$/.test(secret)) {
    get("message").textContent = "请用带专用密钥的完整链接打开。";
    return;
  }
  try {
    const response = await fetch("./trip-editorial.enc.json");
    if (!response.ok) throw new Error("content unavailable");
    const payload = await response.json();
    const key = await crypto.subtle.importKey("raw",decode(secret),"AES-GCM",false,["decrypt"]);
    const clear = await crypto.subtle.decrypt({name:"AES-GCM",iv:decode(payload.iv)},key,decode(payload.content));
    data = JSON.parse(new TextDecoder().decode(clear));
    get("trip-dates").textContent = data.dates;
    coverImage();
    get("locked").hidden = true;
    get("trip").hidden = false;
    bind();
    render();
  } catch (error) {
    get("message").textContent = "打不开行程资料。请检查专用链接是否完整，并联网重新打开一次。";
    console.error(error);
    return;
  }
  if ("serviceWorker" in navigator) {
    get("offline").hidden = false;
    try {
      await navigator.serviceWorker.register("./sw.js", {scope:"./"});
      const registration = await navigator.serviceWorker.ready;
      if (registration.active) get("offline").textContent = "离线资料已保存";
    } catch { get("offline").textContent = "当前浏览器未保存离线资料"; }
  }
}

unlock();
