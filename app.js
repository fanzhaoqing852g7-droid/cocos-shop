const state = {
  config: null,
  items: [],
  category: "All",
  slides: [],
  index: 0,
  lastFocus: null,
};

const lookbook = document.querySelector("#lookbook");
const statusNode = document.querySelector("#status");
const filtersNode = document.querySelector("#filters");
const countNode = document.querySelector("#look-count");
const askLink = document.querySelector("#ask-link");
const instagramLink = document.querySelector("#instagram-link");
const viewer = document.querySelector("#viewer");
const viewerImg = document.querySelector("#viewer-img");
const viewerStage = document.querySelector("#viewer-stage");
const viewerCode = document.querySelector("#viewer-code");
const viewerTitle = document.querySelector("#viewer-title");
const viewerLine = document.querySelector("#viewer-line");
const viewerNote = document.querySelector("#viewer-note");
const viewerWa = document.querySelector("#viewer-wa");
const viewerCount = document.querySelector("#viewer-count");
const viewerPrev = document.querySelector("#viewer-prev");
const viewerNext = document.querySelector("#viewer-next");
const viewerClose = document.querySelector("#viewer-close");

function whatsappHref(text) {
  const number = String(state.config.whatsappNumber || "").replace(/[^\d]/g, "");
  return `https://wa.me/${number}?text=${encodeURIComponent(text)}`;
}

function fillTemplate(template, item) {
  return String(template || "")
    .replaceAll("{code}", item?.code || "")
    .replaceAll("{title}", item?.title || "")
    .replaceAll("{category}", item?.category || "")
    .replace(/\(\s*\)/g, "")
    .replace(/\s{2,}/g, " ")
    .trim();
}

function instagramHref(value) {
  const handle = String(value || "").trim();
  if (!handle) return "";
  if (/^https?:\/\//i.test(handle)) return handle;
  return `https://instagram.com/${handle.replace(/^@/, "")}`;
}

function formatDay(iso) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || "");
  if (!match) return { title: iso || "Undated", kicker: "Lookbook" };
  const date = new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])));
  const weekday = new Intl.DateTimeFormat("en-GB", {
    weekday: "long",
    timeZone: "UTC",
  }).format(date);
  const month = new Intl.DateTimeFormat("en-GB", {
    month: "long",
    timeZone: "UTC",
  }).format(date);
  return {
    title: `${Number(match[3])} ${month}`,
    kicker: `${weekday} · ${match[1]}`,
  };
}

function codeNumber(code) {
  const match = /-(\d+)$/.exec(code || "");
  return match ? Number(match[1]) : 0;
}

function visibleItems() {
  if (state.category === "All") return state.items;
  return state.items.filter((item) => item.category === state.category);
}

function groupByDate(items) {
  const groups = [];
  for (const item of items) {
    const last = groups[groups.length - 1];
    if (!last || last.date !== item.date) groups.push({ date: item.date, items: [item] });
    else last.items.push(item);
  }
  return groups;
}

function el(tag, attrs, children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value == null || value === false) continue;
    if (key === "class") node.className = value;
    else node.setAttribute(key, value === true ? "" : value);
  }
  for (const child of children || []) node.append(child);
  return node;
}

function text(tag, className, value) {
  const node = el(tag, { class: className });
  node.textContent = value;
  return node;
}

function itemImages(item) {
  if (Array.isArray(item.images) && item.images.length) return item.images;
  return item.image ? [item.image] : [];
}

function categoriesInUse() {
  const used = new Set(state.items.map((item) => item.category));
  return (state.config.categories || []).filter((category) => used.has(category));
}

function renderFilters() {
  const categories = ["All", ...categoriesInUse()];
  filtersNode.replaceChildren();
  for (const category of categories) {
    const count =
      category === "All"
        ? state.items.length
        : state.items.filter((item) => item.category === category).length;
    const button = el("button", {
      type: "button",
      class: "filter",
      "aria-pressed": category === state.category ? "true" : "false",
    });
    button.append(document.createTextNode(category));
    const countLabel = el("span", { class: "count" });
    countLabel.textContent = String(count);
    button.append(countLabel);
    button.addEventListener("click", () => setCategory(category));
    filtersNode.append(button);
  }
  const active = filtersNode.querySelector('[aria-pressed="true"]');
  if (active) {
    const left = active.offsetLeft - (filtersNode.clientWidth - active.offsetWidth) / 2;
    filtersNode.scrollTo({ left: Math.max(0, left) });
  }
}

function buildSlides(items) {
  const slides = [];
  for (const item of items) {
    const images = itemImages(item);
    images.forEach((src, index) => {
      slides.push({ item, src, frame: index + 1, frames: images.length });
    });
  }
  return slides;
}

function renderGrid() {
  const items = visibleItems();
  state.slides = buildSlides(items);
  const groups = groupByDate(items);
  lookbook.replaceChildren();
  if (!groups.length) {
    statusNode.hidden = false;
    statusNode.textContent = "Nothing in this category yet. Try another filter, or ask Coco what arrived today.";
    lookbook.append(statusNode);
    return;
  }
  statusNode.hidden = true;
  for (const group of groups) {
    const day = formatDay(group.date);
    const pieces = group.items.length === 1 ? "1 piece" : `${group.items.length} pieces`;
    const heading = el("header", { class: "day" }, [
      el("div", {}, [
        text("p", "day-kicker", day.kicker),
        text("h2", "day-title", day.title),
      ]),
      text("p", "day-count", pieces),
    ]);
    const grid = el("div", { class: "grid" });
    for (const item of group.items) {
      const button = el("button", {
        type: "button",
        class: "card",
        "data-code": item.code,
      });
      const image = el("img", {
        src: item.image,
        alt: `${item.title || item.category || "Look"}, ${item.code}`,
        loading: "lazy",
        decoding: "async",
      });
      const frame = el("span", { class: "card-frame" }, [image]);
      if (itemImages(item).length > 1) {
        const count = el("span", { class: "photo-count" });
        count.textContent = String(itemImages(item).length);
        frame.append(count);
      }
      button.append(
        frame,
        el("span", { class: "card-meta" }, [
          text("span", "card-code", item.code),
          text("span", "card-cat", item.category || ""),
          text("span", "card-title", item.title || item.category || "Look"),
        ])
      );
      button.addEventListener("click", () => openViewer(item.code));
      grid.append(button);
    }
    lookbook.append(heading, grid);
  }
}

function categoryFromHash() {
  const raw = decodeURIComponent(location.hash.replace(/^#/, "")).trim().toLowerCase();
  if (!raw) return "All";
  const match = (state.config.categories || []).find((category) => category.toLowerCase() === raw);
  return match || "All";
}

function setCategory(category, { updateHash = true } = {}) {
  const available = new Set(["All", ...categoriesInUse()]);
  if (!available.has(category)) category = "All";
  state.category = category;
  if (updateHash) {
    const hash = category === "All" ? "" : `#${encodeURIComponent(category.toLowerCase())}`;
    const next = `${location.pathname}${location.search}${hash}`;
    if (`${location.pathname}${location.search}${location.hash}` !== next) {
      history.replaceState(null, "", next);
    }
  }
  renderFilters();
  renderGrid();
  if (!viewer.hidden) closeViewer();
}

function showSlide(index) {
  const count = state.slides.length;
  if (!count) return;
  state.index = (index % count + count) % count;
  const slide = state.slides[state.index];
  const item = slide.item;
  const day = formatDay(item.date);
  viewerImg.classList.add("is-fading");
  viewerImg.onload = () => viewerImg.classList.remove("is-fading");
  viewerImg.alt = `${item.title || "Look"}, ${item.code}`;
  viewerImg.src = slide.src;
  if (viewerImg.complete) viewerImg.classList.remove("is-fading");
  viewerCode.textContent = item.code;
  viewerTitle.textContent = item.title || item.category || "Look";
  viewerLine.textContent = [item.category, day.title, day.kicker.split(" · ")[1]]
    .filter(Boolean)
    .join(" · ");
  viewerNote.hidden = !item.note;
  viewerNote.textContent = item.note || "";
  const message = fillTemplate(state.config.whatsappTemplate, item);
  viewerWa.href = whatsappHref(message);
  viewerCount.textContent = `${slide.frame} / ${slide.frames}`;
  const single = count < 2;
  viewerPrev.hidden = single;
  viewerNext.hidden = single;
  const neighbor = state.slides[(state.index + 1) % count];
  if (neighbor) {
    const preload = new Image();
    preload.src = neighbor.src;
  }
}

function openViewer(code) {
  const index = state.slides.findIndex((slide) => slide.item.code === code);
  if (index < 0) return;
  state.lastFocus = document.activeElement;
  viewer.hidden = false;
  document.body.classList.add("viewer-open");
  showSlide(index);
  viewerClose.focus();
}

function closeViewer() {
  viewer.hidden = true;
  document.body.classList.remove("viewer-open");
  if (state.lastFocus && typeof state.lastFocus.focus === "function") state.lastFocus.focus();
}

function focusables() {
  return [...viewer.querySelectorAll("button, a")].filter((node) => !node.hidden);
}

viewerClose.addEventListener("click", closeViewer);
viewerPrev.addEventListener("click", () => showSlide(state.index - 1));
viewerNext.addEventListener("click", () => showSlide(state.index + 1));

document.addEventListener("keydown", (event) => {
  if (viewer.hidden) return;
  if (event.key === "Escape") {
    event.preventDefault();
    closeViewer();
  } else if (event.key === "ArrowRight") {
    event.preventDefault();
    showSlide(state.index + 1);
  } else if (event.key === "ArrowLeft") {
    event.preventDefault();
    showSlide(state.index - 1);
  } else if (event.key === "Tab") {
    const nodes = focusables();
    if (!nodes.length) return;
    const first = nodes[0];
    const last = nodes[nodes.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }
});

let pointerStart = null;
viewerStage.addEventListener("pointerdown", (event) => {
  if (event.button !== 0) return;
  pointerStart = { x: event.clientX, y: event.clientY, id: event.pointerId };
});
viewerStage.addEventListener("pointerup", (event) => {
  if (!pointerStart || pointerStart.id !== event.pointerId) return;
  const dx = event.clientX - pointerStart.x;
  const dy = event.clientY - pointerStart.y;
  pointerStart = null;
  if (Math.abs(dx) < 48 || Math.abs(dx) < Math.abs(dy)) return;
  showSlide(state.index + (dx < 0 ? 1 : -1));
});
viewerStage.addEventListener("pointercancel", () => {
  pointerStart = null;
});

function showError(message) {
  statusNode.hidden = false;
  statusNode.textContent = message;
}

async function init() {
  let config;
  let items;
  try {
    const [configResponse, itemsResponse] = await Promise.all([
      fetch("data/config.json"),
      fetch("data/items.json"),
    ]);
    if (!configResponse.ok || !itemsResponse.ok) {
      throw new Error("Could not read the lookbook files.");
    }
    config = await configResponse.json();
    items = await itemsResponse.json();
  } catch (error) {
    showError("The lookbook could not be loaded. Refresh the page, or ask Coco on WhatsApp.");
    return;
  }
  if (!Array.isArray(items)) {
    showError("The lookbook list is empty or unreadable.");
    return;
  }

  state.config = config;
  document.title = `${config.shopName || "Coco's Shop"} — ${config.tagline || "Guangzhou Fashion Sourcing"}`;
  askLink.href = whatsappHref(config.whatsappGeneral || "Hi Coco, I would like to ask about today's looks.");
  const instagram = instagramHref(config.instagram);
  if (config.showInstagram && instagram) {
    instagramLink.hidden = false;
    instagramLink.href = instagram;
  }

  state.items = items
    .filter((item) => item && item.code && (item.image || (item.images && item.images.length)) && item.date)
    .map((item) => {
      const images = (Array.isArray(item.images) && item.images.length ? item.images : [item.image])
        .filter(Boolean)
        .map(String);
      return {
        code: String(item.code),
        date: String(item.date),
        category: item.category || "Other",
        title: item.title || "",
        note: item.note || "",
        image: images[0],
        images,
      };
    })
    .sort((a, b) => {
      if (a.date !== b.date) return a.date < b.date ? 1 : -1;
      return codeNumber(a.code) - codeNumber(b.code);
    });

  const noun = state.items.length === 1 ? "look" : "looks";
  countNode.textContent = `${state.items.length} ${noun}`;
  setCategory(categoryFromHash(), { updateHash: false });
  window.addEventListener("hashchange", () => {
    const next = categoryFromHash();
    if (next !== state.category) setCategory(next, { updateHash: false });
  });
}

init();
