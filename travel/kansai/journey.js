"use strict";

const get = (id) => document.getElementById(id);
const html = (text = "") => String(text).replace(/[&<>"']/g, (ch) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
})[ch]);
const tabs = {plan:"行程", food:"餐食", map:"真实地图", shop:"购物清单", art:"画展与活动", friends:"旅伴图鉴", pictures:"参考图"};
const allowed = new Set(Object.keys(tabs));
const params = new URLSearchParams(location.search);
const fragment = new URLSearchParams(location.hash.slice(1));
let secret = fragment.get("key") || "";
if(!secret){try{secret=localStorage.getItem("kansai-travel:device-access:v1")||"";}catch{}}
let selectedView = allowed.has(params.get("view")) ? params.get("view") : "plan";
let selectedDay = /^[0-7]$/.test(params.get("day")) ? params.get("day") : "all";
let openMeal = params.get("meal") || "";
let selectedMapArea=params.get("area") || "umeda";
let selectedMapId=params.get("place") || "";
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
  const cover = data.gallery.find((photo) => photo.role === "ayao-cover") || data.gallery.find((photo) => photo.role === "cover");
  get("cover-art").innerHTML = cover ? `<img src="${html(cover.embedded || `./assets/${cover.file}`)}" alt="${html(cover.title)}" width="${cover.width}" height="${cover.height}" fetchpriority="high"><figcaption>${html(cover.credit)}</figcaption>` : "";
  get("cover-art").hidden = !cover;
}

function uiIcon(view){
 const atlas=data.gallery.find(p=>p.role==="ayao-icons");
 if(!atlas)return "";
 const i=({plan:0,food:1,map:2,shop:3,art:4,friends:5,pictures:6})[view]||0;
 return `<span class="ui-icon" aria-hidden="true" style="background-image:url('${html(atlas.embedded||`./assets/${atlas.file}`)}');background-position:${(i%4)*100/3}% ${Math.floor(i/4)*100}%"></span>`;
}

function tripHighlights() {
  const highlights = [
    {day:0, file:"kyoto-night.webp", text:"京都 · 清水寺夜游"},
    {day:1, file:"otagi-rakan.webp", text:"岚山 · 爱宕念佛寺"},
    {day:2, file:"nara-deer.webp", text:"奈良 · 小鹿〔暂定〕"},
    {day:3, file:"nintendo-entrance.webp", text:"任天堂博物馆 · 已购票"},
    {day:5, file:"sky-tree.webp", text:"梅田 · 圣诞市集"},
    {day:6, file:"wyeth-preview.webp", text:"怀斯画展 · 已排／待购票"}
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
  return `<a class="action" href="${html(url)}" target="_blank" rel="noopener noreferrer">${html(label)}</a>`;
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
  return `<div class="overview"><div class="overview-row head"><span>日期 / 住宿</span><span>上午 — 午饭</span><span>下午 · 13:30—18:00</span><span>晚上</span></div>${data.days.map((day,i) => `<article class="overview-row"><div><button class="daynum" data-day="${i}" aria-label="查看${html(day.short)}详情">${html(day.short)} ${html(day.week)}</button><p class="small">${html(day.city)}</p><p class="soft small">${html(day.hotel)}</p><button class="meal-jump" data-food-day="${i}">午晚餐 · 各3选</button></div>${period(day,"am","上午 — 午饭")}${period(day,"pm","下午")}${period(day,"night","晚上")}</article>`).join("")}</div>`;
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
  const transit = data.transport.find((item) => item.day === day.short);
  return header + dayPicker() + title(`${day.short} ${day.week} · ${day.theme}`, `住宿  ${day.hotel}`) + (transit ? transitPanel(transit, true) : "") + `<div class="split day-split"><ol class="timeline">${day.events.map(eventRow).join("")}</ol><aside class="day-aside">${(day.photos || []).map((file) => picture(file,"day-photo")).join("")}<div class="notes"><h3>当天备注</h3><ul>${day.notes.map(([name, note]) => `<li><strong>${html(name)}</strong><p class="small">${html(note)}</p></li>`).join("")}</ul></div></aside></div><div class="day-dining"><h3>当天午餐与晚餐</h3><p class="soft">每餐三个选择，点开查看照片、楼层、营业时间与菜单。</p>${data.dining.meals.filter(m=>m.day===Number(selectedDay)).map(m=>mealBlock(m,false)).join("")}</div>`;
}

function restaurantCard(id, meal, index) {
  const place = data.dining.restaurants.find(r=>r.id===id);
  const nav = `https://www.google.com/maps/dir/?${new URLSearchParams({api:"1",destination:place.query})}`;
  const label = meal.birthday ? "生日晚餐候选" : meal.planned===id ? "原定午餐 · 未订座" : index===0 ? "顺路建议" : "备选";
  return `<article class="restaurant-card" data-restaurant="${html(id)}">${picture(place.photo,"food-photo")}<div class="restaurant-body">${statusTag(label)}<h4>${html(place.name)}</h4><p class="restaurant-jp" lang="ja">${html(place.jp)}</p><p class="food-budget">${html(place.budget)}</p>${place.familyBudget ? `<p class="small">${html(place.familyBudget)}</p>` : ""}<p class="food-order">${html(place.dishes)}</p><dl class="food-facts"><div><dt>楼层</dt><dd>${html(place.floor)}</dd></div><div><dt>营业</dt><dd>${html(place.hours)}</dd></div><div><dt>找店</dt><dd>${html(place.find)}</dd></div></dl>${place.note ? `<p class="restaurant-note">${html(place.note)}</p>` : ""}${addLinks(action(nav,"导航去这里"),action(place.menu,place.menuLabel || "查看菜单"),action(place.campaign,"联名菜单"),action(place.booking,"查看预约"))}${place.menuNote ? `<p class="small soft menu-note">${html(place.menuNote)}</p>`:""}<details class="food-source"><summary>营业信息来源</summary>${action(place.source,"门店官方资料")}<p class="small soft">整理于${html(data.dining.checked)}，未公开的最后点餐或楼层细节以店内公告为准。</p></details></div></article>`;
}

function mealBlock(meal, expanded) {
  const places=meal.options.map(id=>data.dining.restaurants.find(r=>r.id===id));
  const cover=data.gallery.find(p=>p.file===places[0].photo);
  const day=data.days[meal.day];
  const image=cover ? `<img class="meal-cover" src="${html(cover.embedded || `./assets/${cover.file}`)}" alt="${html(cover.title)}" width="${cover.width}" height="${cover.height}" loading="lazy">` : "";
  return `<details class="meal-section ${meal.birthday ? "birthday-meal" : ""}" id="meal-${html(meal.id)}" ${expanded || openMeal===meal.id ? "open" : ""}><summary>${image}<span class="meal-summary"><span class="meal-kicker">${html(day.short)} ${html(day.week)} · ${meal.slot==="lunch"?"午餐":"晚餐"} · ${html(meal.time)}</span><strong>${html(meal.title)}</strong><span class="meal-area">${html(meal.area)} · ${html(meal.status)}</span><span class="meal-options">${places.map(p=>html(p.name.split(" · ")[0])).join(" / ")}</span><span class="meal-hint">查看三个选择与找店信息</span></span><span class="meal-toggle" aria-hidden="true">＋</span></summary><div class="meal-expanded"><p class="meal-route">${html(meal.note)}</p><div class="restaurant-grid">${meal.options.map((id,index)=>restaurantCard(id,meal,index)).join("")}</div></div></details>`;
}

function food() {
  const meals=data.dining.meals.filter(m=>selectedDay==="all" || m.day===Number(selectedDay));
  return title("沿途好好吃饭", "午餐、晚餐各三个选择。点开一餐，照片、楼层与导航都在一起。") + `<div class="food-intro"><div><span class="eyebrow">THE TABLE · KANSAI</span><h3>一天两顿，顺路坐下来</h3><p>逛店、看展、赏枫之间，把吃饭和休息留出来。生日那一晚，三个选择都保留。</p><button data-food-day="2">看生日晚餐</button></div><div class="food-stats"><strong>8天 · 16餐</strong><span>48个候选位置</span><span>实景与菜品参考图</span></div></div>` + dayPicker() + `<p class="food-guide-note">${html(data.dining.intro)} <span>更新 ${html(data.dining.checked)}</span></p><div class="meal-list">${meals.map(m=>mealBlock(m,selectedDay!=="all")).join("")}</div>`;
}

function hotelPanel() {
  const hotel = data.hotel;
  return `<section class="hotel-callout"><div class="hotel-content"><h3>京都住处 · ${html(hotel.name)}</h3><p class="small soft">${html(hotel.japanese)} · ${html(hotel.english)}</p><p class="small">${html(hotel.address)}</p><p>${html(hotel.exit)}</p>${addLinks(action(google(hotel.query),"酒店定位"),action(hotel.official,"酒店官方路线"))}</div>${hotel.image ? `<details class="hotel-screenshot"><summary>查看你发的酒店定位截图</summary><figure><img src="${html(hotel.image)}" alt="Google 地图显示酒店在京都站八条通南侧、teamLab 在东侧" loading="lazy"><figcaption>Google 地图 · 你提供的定位截图。旁边房价与日期来自截图界面。</figcaption></figure></details>` : ""}</section>`;
}

function transitPanel(route, short = false) {
  return `<details class="transit-panel"><summary>${short ? "当天交通 · 车次、票价与入口" : `${html(route.day)} · ${html(route.label)}`}</summary><p class="route-start">${html(route.start)}</p><ol class="transport-steps">${route.rows.map((row) => `<li><h4>${html(row.title)}</h4><p>${html(row.ride)}</p><div class="route-facts"><span>${html(row.fare)}</span><span>${html(row.distance)}</span></div><p class="small soft">${html(row.note)}</p>${addLinks(action(directions(row.from,row.to,row.mode),row.mode === "walking" ? "步行导航" : "查当前路线"),action(row.source,"原始时刻表／入口"))}</li>`).join("")}</ol>${route.photos.length ? `<div class="route-photos">${route.photos.map((file) => picture(file)).join("")}</div>` : ""}</details>`;
}

function savedPanel() {
  return `<h3 class="subhead">你的收藏 · 顺路安排</h3><p class="small soft">从已保存的关西地点中选出与行程同区的店和景点，备选按体力选逛。</p><div class="entries saved-entries">${data.savedStops.map((place) => `<article class="entry"><p class="small soft">${html(place.area)} · ${html(place.day)}</p><h4>${html(place.name)}</h4><p class="small">${html(place.note)}</p>${addLinks(action(google(place.query),"地图定位"))}</article>`).join("")}</div>`;
}

function embeddedGoogle(query){return `https://www.google.com/maps?${new URLSearchParams({q:query,output:"embed",hl:"zh-CN"})}`;}
function mapContent(){
 const guide=data.placeGuide;
 const area=guide.areas.find(a=>a.id===selectedMapArea)||guide.areas[0];
 selectedMapArea=area.id;
 const points=guide.places.filter(p=>area.id==="all"||p.area===area.id);
 const current=points.find(p=>p.id===selectedMapId);
 const query=current?.query||area.query;
 const frame=current?embeddedGoogle(query):(area.embed||embeddedGoogle(query));
 return `<div class="map-controls"><label>选择区域<select data-map-area aria-label="地图区域">${guide.areas.map(a=>`<option value="${html(a.id)}" ${a.id===area.id?"selected":""}>${html(a.name)}</option>`).join("")}</select></label><p>${html(area.note)}</p><span class="map-count">${points.length} 个地点</span></div><div class="real-map-layout"><div class="real-map-main"><div class="real-map-caption"><div><span class="eyebrow">GOOGLE MAPS · LIVE</span><h3>${html(current?.name||area.name)}</h3></div>${action(google(query),"打开Google地图")}</div><iframe class="real-map-frame" title="Google地图 · ${html(current?.name||area.name)}" src="${html(frame)}" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe><div class="real-map-detail" aria-live="polite"><p>${html(current?.floor||"可在地图中缩放、移动、查看街道与车站。")}</p>${current?`<p lang="ja" class="small soft">${html(current.jp)}</p><p class="small">${html(current.note)}</p>${current.hours?`<p class="small">营业 ${html(current.hours)}</p>`:""}${current.budget?`<p class="small">预算 ${html(current.budget)}／人</p>`:""}${addLinks(action(`https://www.google.com/maps/dir/?${new URLSearchParams({api:"1",destination:current.query})}`,"从当前位置导航"),action(current.source,"地点官方资料"))}`:""}<p class="map-network-note">真实地图需要联网。离线时仍可查看右侧地点名、楼层和保存的行程；恢复网络后打开Google地图导航。</p></div></div><div class="map-place-list" aria-label="${html(area.name)}地点索引">${points.map(p=>`<article class="map-place ${current?.id===p.id?"is-selected":""}"><div class="map-place-heading"><span class="small soft">${html(p.kind)}</span><button data-map-preview="${html(p.id)}" aria-label="在地图预览${html(p.name)}" aria-pressed="${current?.id===p.id}">地图预览</button></div><a class="map-place-name" href="${html(google(p.query))}" target="_blank" rel="noopener noreferrer">${html(p.name)}</a><p class="small soft" lang="ja">${html(p.jp)}</p>${p.floor?`<p class="map-floor">${html(p.floor)}</p>`:""}</article>`).join("")}</div></div>`;
}
function mapLocationState(){
 const url=new URL(location.href);
 url.searchParams.set("area",selectedMapArea);
 if(selectedMapId)url.searchParams.set("place",selectedMapId);else url.searchParams.delete("place");
 history.replaceState(null,"",url);
}
function refreshMap(){get("map-explorer").innerHTML=mapContent();mapLocationState();}
function maps() {
 return title("真实地图，照着走", "地点名直接跳转Google地图；“地图预览”在本页查看。楼层和入口单独标明。")+`<p class="map-intro">${html(data.placeGuide.note)}</p><section id="map-explorer">${mapContent()}</section>`+`<details class="map-hotel-details"><summary>京都住处与定位截图</summary>${hotelPanel()}</details><h3 class="subhead">每天怎么走</h3><p class="small soft transit-caveat">以下为分段交通、单程票价与步行估算。所列车次按11月18日资料整理，当天核对站内屏与运营方时刻表。</p>${data.transport.map(route=>transitPanel(route)).join("")}`;
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

function friendPortrait(person){
 const photo=data.gallery.find(p=>p.file===person.photo);
 return photo?`<img src="${html(photo.embedded||`./assets/${photo.file}`)}" alt="${html(person.name)} · ${html(person.shape)}" width="${photo.width}" height="${photo.height}" loading="lazy">`:"";
}
function friends(){
 const world=data.ayaoWorld;
 return title("星际朋友，这次一起出发", "十二位伙伴、守卷人，还有这次新加入的四位旅伴。")+`<div class="world-intro"><div><span class="eyebrow">AYAO · ORIGINAL WORLD</span><h3>阿耀来了</h3><p>${html(world.intro)}</p><p>${html(world.welcome)}</p><p class="small soft">${html(world.source)}</p></div>${picture("ayao-original-title.webp","world-title")}</div><div class="cast-grid">${world.characters.map(c=>`<article class="cast-card" data-character="${html(c.id)}"><div class="cast-portrait">${friendPortrait(c)}</div><div class="cast-info"><p class="cast-number">星际朋友 ${html(c.id)}</p><h3>${html(c.name)}</h3><p class="small soft">${html(c.shape)}</p><p>${html(c.about)}</p></div></article>`).join("")}</div><article class="keeper-card" data-character="keeper"><div class="keeper-portrait">${friendPortrait(world.keeper)}</div><div><span class="eyebrow">星图与线索</span><h3>守卷人</h3><p>${html(world.keeper.about)}</p><p class="small soft">${html(world.keeper.shape)}</p><button data-view="map">打开这次旅行的真实地图</button></div></article><section class="world-intro new-companions"><div><span class="eyebrow">NEW TRAVEL COMPANIONS</span><h3>原画里的四位新旅伴</h3><p>${html(world.newCompanions.note)}</p><div class="new-companion-list">${world.newCompanions.characters.map(c=>`<article><h4>${html(c.label)}</h4><p>${html(c.shape)}</p></article>`).join("")}</div></div>${picture(world.newCompanions.photo,"world-title")}</section><details class="original-chapters"><summary>回声图鉴 · 原作九章旅程</summary><div class="original-chapter-grid">${world.chapters.map(c=>`<article><span class="small soft">第${c.cycle}轮旅程</span><h4>${html(c.name)}</h4><p>${html(c.text)}</p></article>`).join("")}</div></details><details class="original-chapters"><summary>一路带来的力量</summary><div class="original-chapter-grid">${world.abilities.map(a=>`<article><h4>${html(a.name)}</h4><p>${html(a.text)}</p></article>`).join("")}</div></details><p class="world-quote">${html(world.quote)}</p>`;
}

const renderers = {plan, food, map:maps, shop:shops, art, friends, pictures};
function render() {
  const url=new URL(location.href);
  if(!new URLSearchParams(url.hash.slice(1)).get("key")&&secret)url.hash=new URLSearchParams({key:secret}).toString();
  url.searchParams.set("view",selectedView);
  if(selectedDay!=="all")url.searchParams.set("day",selectedDay);else url.searchParams.delete("day");
  if(openMeal)url.searchParams.set("meal",openMeal);else url.searchParams.delete("meal");
  history.replaceState(null,"",url);
  get("views").innerHTML = Object.entries(tabs).map(([id,label]) => `<button data-view="${id}" aria-pressed="${id === selectedView}">${uiIcon(id)}<span>${label}</span></button>`).join("");
  get("view").innerHTML = renderers[selectedView]();
  if(selectedView==="map")mapLocationState();
}

function bind() {
  get("trip").addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    if (button.dataset.foodDay !== undefined) {
      selectedView="food";
      selectedDay=button.dataset.foodDay;
      openMeal=selectedDay==="2" ? "2-dinner" : "";
      render();
      (get("view").querySelector(selectedDay==="2" ? "#meal-2-dinner" : ".day-pick") || get("views")).scrollIntoView({block:"start",behavior:"smooth"});
    } else if (button.dataset.view) {
      selectedView = button.dataset.view;
      render();
      get("views").querySelector(`[data-view=${selectedView}]`).focus({preventScroll:true});
    } else if (button.dataset.day) {
      selectedDay = button.dataset.day;
      openMeal="";
      render();
      get("view").querySelector(`.day-pick [data-day="${selectedDay}"]`).focus();
    } else if (button.dataset.mapPreview) {
      selectedMapId=button.dataset.mapPreview;
      refreshMap();
      get("map-explorer").querySelector(".real-map-caption").scrollIntoView({block:"start",behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
    }
  });
  get("trip").addEventListener("change", (event) => {
    const input = event.target;
    if(input.hasAttribute("data-map-area")){selectedMapArea=input.value;selectedMapId="";refreshMap();return;}
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
    get("message").textContent = "请用完整的行程链接打开，或在下方粘贴链接。";
    return;
  }
  try {
    const response = await fetch("./trip-transport.enc.json");
    if (!response.ok) throw new Error("content unavailable");
    const payload = await response.json();
    const key = await crypto.subtle.importKey("raw",decode(secret),"AES-GCM",false,["decrypt"]);
    const clear = await crypto.subtle.decrypt({name:"AES-GCM",iv:decode(payload.iv)},key,decode(payload.content));
    data = JSON.parse(new TextDecoder().decode(clear));
    try{localStorage.setItem("kansai-travel:device-access:v1",secret);}catch{}
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
      const reportReady=()=>{ get("offline").textContent="行程与配图已存离线"; };
      if (registration.installing) {
        registration.installing.addEventListener("statechange", event=>{if(event.target.state==="activated")reportReady();});
      } else if (registration.active) reportReady();
    } catch { get("offline").textContent = "当前浏览器未保存离线资料"; }
  }
}

get("restore-access").addEventListener("submit",async(event)=>{
 event.preventDefault();
 const button=event.currentTarget.querySelector("button");
 try{
  const link=new URL(get("access-link").value.trim());
  const supplied=new URLSearchParams(link.hash.slice(1)).get("key")||"";
  if(!/^[A-Za-z0-9_-]{43}$/.test(supplied))throw new Error("invalid access link");
  secret=supplied;button.disabled=true;get("message").textContent="正在打开你的关西行程…";
  await unlock();
 }catch{get("message").textContent="请粘贴完整的本次行程链接，再点打开行程。";}
 finally{button.disabled=false;}
});
unlock();
