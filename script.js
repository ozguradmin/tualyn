(() => {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const rnd = (a, b) => a + Math.random() * (b - a);
  const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];
  const HEART = "M50 86C20 64 2 46 2 26 2 12 13 2 27 2c10 0 18 6 23 14C55 8 63 2 73 2c14 0 25 10 25 24 0 20-18 38-48 60z";

  /* ── Barkod: "TUANA" harflerinden türetilir, her seferinde aynı ── */
  const barcode = document.getElementById("barcode");
  if (barcode) {
    const seed = "TUANA♥OZGUR";
    let html = "";
    for (const ch of seed) {
      const n = ch.codePointAt(0);
      for (let k = 0; k < 4; k++) {
        const bit = (n >> k) & 3;
        html += `<i style="width:${bit + 1}px"></i><i class="gap" style="width:${((n >> (k + 1)) & 1) + 1}px"></i>`;
      }
    }
    barcode.innerHTML = html;
  }

  /* ── Kapak: mavi katman imleçle hafifçe kayar (riso kayması) ── */
  const cover = document.querySelector(".cover");
  const blueInk = document.querySelector(".cover-title .ink-blue");
  if (cover && blueInk && !reduceMotion) {
    cover.addEventListener("pointermove", (e) => {
      const r = cover.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5;
      const y = (e.clientY - r.top) / r.height - 0.5;
      blueInk.style.setProperty("--mx", `${5 + x * 18}px`);
      blueInk.style.setProperty("--my", `${4 + y * 12}px`);
    });
    cover.addEventListener("pointerleave", () => {
      blueInk.style.removeProperty("--mx");
      blueInk.style.removeProperty("--my");
    });
  }

  /* ── Brief onayı ── */
  const approveBtn = document.getElementById("approveBtn");
  const stamp = document.getElementById("stamp");
  const briefStatus = document.getElementById("briefStatus");
  const sheet = document.querySelector(".brief-sheet");
  approveBtn?.addEventListener("click", () => {
    stamp.classList.add("is-on");
    sheet.classList.add("shake");
    approveBtn.disabled = true;
    approveBtn.textContent = "onaylandı ✓";
    briefStatus.textContent = "onaylandı, başlıyoz";
    const r = approveBtn.getBoundingClientRect();
    burst(r.left + r.width / 2, r.top + r.height / 2, 14);
  });

  /* ── Renk kartelası ── */
  const swatches = [
    { name: "Gülüş Pembesi", code: "14-0412", hex: "#ff6fa8", note: "güldüğünde ben de istemeden gülüyorum" },
    { name: "Ses Mavisi", code: "17-1105", hex: "#4f86e8", note: "sesini duyunca içim rahatlıyo" },
    { name: "Sabah Kahvesi", code: "18-0203", hex: "#8a5a3c", note: "seni her şeyden çok seviyorum" },
    { name: "Somurtma Şeftalisi", code: "13-2201", hex: "#ffae85", note: "aşırı güzelsin, aşığım sana" },
    { name: "Lale", code: "16-0119", hex: "#e8475f", note: "her an aklımdasın fıstık" },
    { name: "Cicikuş Yeşili", code: "15-0343", hex: "#7cc243", note: "keşke sabah akşam sana baksam" },
  ];
  const grid = document.getElementById("swatchGrid");
  if (grid) {
    swatches.forEach((s, i) => {
      const tilt = [-2.5, 1.5, -1, 2.5, -1.8, 1][i % 6];
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "swatch reveal";
      btn.style.setProperty("--c", s.hex);
      btn.style.setProperty("--tilt", `${tilt}deg`);
      btn.style.transitionDelay = `${i * 70}ms`;
      btn.setAttribute("aria-label", `${s.name} rengi. Arkasını çevirmek için dokun.`);
      btn.innerHTML = `
        <span class="swatch-inner">
          <span class="swatch-face swatch-front">
            <span class="swatch-color"></span>
            <span class="swatch-label">
              <span class="swatch-brand">TUANA<sup>®</sup></span>
              <span class="swatch-code">${s.code} TCX</span>
              <span class="swatch-name">${s.name}</span>
            </span>
          </span>
          <span class="swatch-face swatch-back">
            <p>${s.note}</p>
            <span>${s.hex}</span>
          </span>
        </span>`;
      btn.addEventListener("click", () => {
        btn.classList.toggle("is-flipped");
        btn.setAttribute("aria-pressed", btn.classList.contains("is-flipped"));
      });
      grid.appendChild(btn);
    });
  }

  /* ── Çıkartmalar ── */
  const STICKERS = [
    { label: "kalp", size: 110, svg: `<svg viewBox="0 0 100 90"><path fill="#ff48b0" d="${HEART}"/><path fill="#fff" opacity=".55" d="M24 16c-8 1-13 8-12 16 3-6 7-10 13-12z"/></svg>` },
    { label: "lale", size: 90, svg: `<svg viewBox="0 0 80 130"><path d="M40 62v60" stroke="#00a95c" stroke-width="7" stroke-linecap="round"/><path fill="#00a95c" d="M40 104c-6-18-20-26-30-24 4 14 16 24 30 24zM40 96c6-14 18-20 28-18-4 12-15 18-28 18z"/><path fill="#ff48b0" d="M14 22c0 26 10 42 26 42s26-16 26-42L54 34 40 12 26 34z"/><path fill="#e8475f" d="M40 12 26 34l14 30 14-30z" opacity=".7"/></svg>` },
    { label: "yıldız", size: 96, svg: `<svg viewBox="0 0 100 100"><path fill="#ffd23f" d="M50 4l13 30 32 3-24 21 7 32-28-17-28 17 7-32L5 37l32-3z" stroke-linejoin="round"/><circle cx="40" cy="52" r="3.5" fill="#2a2233"/><circle cx="60" cy="52" r="3.5" fill="#2a2233"/><path d="M44 62q6 6 12 0" stroke="#2a2233" stroke-width="3" fill="none" stroke-linecap="round"/></svg>` },
    { label: "kedi", size: 118, svg: `<svg viewBox="0 0 120 104"><path fill="#0078bf" d="M14 10l26 20h40l26-20 4 46c0 28-22 44-50 44S10 84 10 56z"/><ellipse cx="34" cy="70" rx="9" ry="6" fill="#ff48b0" opacity=".85"/><ellipse cx="86" cy="70" rx="9" ry="6" fill="#ff48b0" opacity=".85"/><path d="M36 56q6-7 12 0M72 56q6-7 12 0" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round"/><path d="M54 70q6 6 12 0" stroke="#fff" stroke-width="3.5" fill="none" stroke-linecap="round"/></svg>` },
    { label: "cicikuşlar", size: 150, svg: `<svg viewBox="0 0 160 100"><path d="M8 92h144" stroke="#8a5a3c" stroke-width="5" stroke-linecap="round"/><circle cx="52" cy="58" r="30" fill="#7cc243"/><circle cx="46" cy="50" r="16" fill="#ffe45c"/><path fill="#ff9a3c" d="M24 54l-12 6 12 4z"/><circle cx="40" cy="50" r="3.5" fill="#2a2233"/><path fill="#4f9a2c" d="M58 58c10 0 18 6 18 14-10 2-18-4-18-14z"/><circle cx="108" cy="58" r="30" fill="#c3e05a"/><circle cx="114" cy="50" r="16" fill="#fff07a"/><path fill="#ff9a3c" d="M136 54l12 6-12 4z"/><circle cx="120" cy="50" r="3.5" fill="#2a2233"/><path fill="#93b83a" d="M102 58c-10 0-18 6-18 14 10 2 18-4 18-14z"/><path fill="#e8475f" transform="translate(70 12) scale(.2)" d="${HEART}"/></svg>` },
    { label: "Tuana etiketi", size: 150, svg: `<svg viewBox="0 0 170 80"><rect x="3" y="3" width="164" height="74" rx="37" fill="#2a2233"/><text x="85" y="52" text-anchor="middle" font-family="Fraunces, Georgia, serif" font-style="italic" font-weight="700" font-size="38" fill="#ffd23f">Tuana</text></svg>` },
    { label: "yüzde yüz tatlı rozeti", size: 104, svg: `<svg viewBox="0 0 100 100"><path fill="#00a95c" d="M50 2l9 8 12-3 4 12 12 4-3 12 8 9-8 9 3 12-12 4-4 12-12-3-9 8-9-8-12 3-4-12-12-4 3-12-8-9 8-9-3-12 12-4 4-12 12 3z"/><text x="50" y="50" text-anchor="middle" font-family="Space Grotesk, sans-serif" font-weight="700" font-size="22" fill="#fff">%100</text><text x="50" y="68" text-anchor="middle" font-family="Space Mono, monospace" font-size="11" letter-spacing="1.5" fill="#fff">TATLI</text></svg>` },
    { label: "papatya", size: 92, svg: `<svg viewBox="0 0 100 100"><g fill="#fff" stroke="#2a2233" stroke-width="2.5">${Array.from({ length: 8 }, (_, i) => `<ellipse cx="50" cy="22" rx="11" ry="20" transform="rotate(${i * 45} 50 50)"/>`).join("")}</g><circle cx="50" cy="50" r="15" fill="#ffd23f" stroke="#2a2233" stroke-width="2.5"/><circle cx="45" cy="48" r="2" fill="#2a2233"/><circle cx="55" cy="48" r="2" fill="#2a2233"/><path d="M45 55q5 4 10 0" stroke="#2a2233" stroke-width="2" fill="none" stroke-linecap="round"/></svg>` },
    { label: "Ö artı T", size: 96, svg: `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="46" fill="#fff" stroke="#0078bf" stroke-width="5" stroke-dasharray="6 5"/><text x="50" y="62" text-anchor="middle" font-family="Caveat, cursive" font-weight="700" font-size="36" fill="#0078bf">Ö+T</text><path fill="#ff48b0" transform="translate(41 70) scale(.18)" d="${HEART}"/></svg>` },
    { label: "parol kutusu", size: 112, svg: `<svg viewBox="0 0 120 84"><rect x="4" y="4" width="112" height="76" rx="8" fill="#fff" stroke="#2a2233" stroke-width="3"/><path fill="#0078bf" d="M4 58h112v14a8 8 0 0 1-8 8H12a8 8 0 0 1-8-8z"/><path fill="#e8475f" d="M4 50h112v8H4z"/><text x="60" y="34" text-anchor="middle" font-family="Space Grotesk, sans-serif" font-weight="700" font-size="22" fill="#0078bf">parol</text><circle cx="48" cy="42" r="2.4" fill="#2a2233"/><circle cx="72" cy="42" r="2.4" fill="#2a2233"/><path d="M56 45q4 4 8 0" stroke="#2a2233" stroke-width="2" fill="none" stroke-linecap="round"/><ellipse cx="42" cy="46" rx="4" ry="2.4" fill="#ff8cc6"/><ellipse cx="78" cy="46" rx="4" ry="2.4" fill="#ff8cc6"/><text x="60" y="73" text-anchor="middle" font-family="Space Mono, monospace" font-size="8" fill="#fff">BAŞ AĞRISINA BİREBİR</text></svg>` },
  ];

  const board = document.getElementById("board");
  let zTop = 10;
  const rand = (a, b) => a + Math.random() * (b - a);

  // Çıkartmalar üst üste binmesin diye kaba bir ızgaraya, biraz oynatarak dağıtılır
  const SLOTS = [[16, 20], [44, 16], [76, 20], [90, 50], [18, 50], [48, 48], [70, 56], [16, 82], [44, 82], [80, 84]];
  const place = (el, i) => {
    const [x, y] = SLOTS[i % SLOTS.length];
    el.style.left = `${x + rand(-5, 5)}%`;
    el.style.top = `${y + rand(-5, 5)}%`;
    el.style.setProperty("--r", `${Math.round(rand(-22, 22))}deg`);
  };
  const shuffledSlots = () => {
    const order = SLOTS.map((_, i) => i);
    for (let i = order.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [order[i], order[j]] = [order[j], order[i]];
    }
    return order;
  };

  if (board) {
    const scale = window.innerWidth < 640 ? 0.72 : 1;
    const order = shuffledSlots();
    STICKERS.forEach((s, i) => {
      const el = document.createElement("div");
      el.className = "sticker";
      el.tabIndex = 0;
      el.setAttribute("role", "img");
      el.setAttribute("aria-label", `${s.label} çıkartması`);
      el.style.setProperty("--size", `${Math.round(s.size * scale)}px`);
      el.innerHTML = s.svg;
      place(el, order[i]);
      makeDraggable(el);
      board.appendChild(el);
    });

    document.getElementById("shuffleBtn")?.addEventListener("click", () => {
      const order = shuffledSlots();
      board.querySelectorAll(".sticker").forEach((el, i) => place(el, order[i]));
    });
  }

  function makeDraggable(el) {
    let start = null;
    let lastTap = 0;

    el.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      el.setPointerCapture(e.pointerId);
      el.style.zIndex = ++zTop;
      const b = board.getBoundingClientRect();
      start = {
        x: e.clientX, y: e.clientY,
        left: (parseFloat(el.style.left) / 100) * b.width,
        top: (parseFloat(el.style.top) / 100) * b.height,
        moved: false,
      };
      el.classList.add("is-dragging");
    });

    el.addEventListener("pointermove", (e) => {
      if (!start) return;
      const dx = e.clientX - start.x;
      const dy = e.clientY - start.y;
      if (Math.abs(dx) + Math.abs(dy) > 4) start.moved = true;
      const b = board.getBoundingClientRect();
      const x = Math.min(Math.max(start.left + dx, 0), b.width);
      const y = Math.min(Math.max(start.top + dy, 0), b.height);
      el.style.left = `${(x / b.width) * 100}%`;
      el.style.top = `${(y / b.height) * 100}%`;
    });

    const end = () => {
      if (!start) return;
      el.classList.remove("is-dragging");
      if (!start.moved) {
        const now = Date.now();
        if (now - lastTap < 320) {
          rotate(el, 30);
          lastTap = 0;
        } else {
          lastTap = now;
        }
      }
      start = null;
    };
    el.addEventListener("pointerup", end);
    el.addEventListener("pointercancel", end);

    // Klavye: ok tuşlarıyla taşı, R ile döndür
    el.addEventListener("keydown", (e) => {
      const step = e.shiftKey ? 5 : 1.5;
      const moves = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
      if (moves[e.key]) {
        e.preventDefault();
        const [mx, my] = moves[e.key];
        el.style.left = `${Math.min(Math.max(parseFloat(el.style.left) + mx, 0), 100)}%`;
        el.style.top = `${Math.min(Math.max(parseFloat(el.style.top) + my, 0), 100)}%`;
      } else if (e.key === "r" || e.key === "R") {
        rotate(el, 30);
      }
    });
  }

  function rotate(el, deg) {
    const cur = parseFloat(el.style.getPropertyValue("--r")) || 0;
    el.style.setProperty("--r", `${cur + deg}deg`);
  }

  /* ── Kapak harfleri: dokununca ya da üstünden geçince zıplar ── */
  document.querySelectorAll(".cover-title .ink").forEach((layer) => {
    layer.innerHTML = [...layer.textContent].map((c) => `<span class="ch">${c}</span>`).join("");
  });
  const pinkChars = document.querySelectorAll(".cover-title .ink-pink .ch");
  const blueChars = document.querySelectorAll(".cover-title .ink-blue .ch");
  const boing = (i) => {
    [pinkChars[i], blueChars[i]].forEach((el) => {
      el.classList.remove("boing");
      void el.offsetWidth;
      el.classList.add("boing");
    });
  };
  pinkChars.forEach((el, i) => {
    el.addEventListener("pointerenter", () => boing(i));
    el.addEventListener("click", () => boing(i));
  });
  if (!reduceMotion) pinkChars.forEach((_, i) => setTimeout(() => boing(i), 700 + i * 110));

  /* ── Cicikuşlar ── */
  const birdsWrap = document.getElementById("birds");
  if (birdsWrap) {
    const stage = document.getElementById("petStage");
    const bubble = document.getElementById("bubble");
    const meter = document.getElementById("meter");
    const secret = document.getElementById("secret");
    const tcCard = document.getElementById("tcCard");

    const PALETTES = [
      { body: "#7cc243", light: "#b5e27a", dark: "#4f9a2c", mask: "#ffe45c", wing: "#efe06a", tail: "#2f6db5", tail2: "#3f86cf", cheek: "#6f63d8", cere: "#4a7bd6", bow: false },
      { body: "#c3e05a", light: "#eaf6a0", dark: "#93b83a", mask: "#fff07a", wing: "#f6ec8a", tail: "#3b8ac9", tail2: "#5aa0db", cheek: "#8a7fe0", cere: "#d8a383", bow: true },
    ];
    const wing = `<path class="o" d="M34 112c-12 30-4 70 26 92 10-26 8-62-8-90z"/><path class="ln" d="M38 132q7 7 14 0M40 152q7 7 14 0M46 172q7 7 14 0M53 190q6 6 11 0"/>`;
    const budgie = (p, id) => `
      <svg class="bird" viewBox="0 0 200 250" role="img" aria-label="Muhabbet kuşu. Okşamak için üstünde parmağını gezdir, dürtmek için dokun.">
        <defs>
          <radialGradient id="gb${id}" cx="40%" cy="32%" r="78%"><stop offset="0" stop-color="${p.light}"/><stop offset=".55" stop-color="${p.body}"/><stop offset="1" stop-color="${p.dark}"/></radialGradient>
          <radialGradient id="gm${id}" cx="45%" cy="28%" r="72%"><stop offset="0" stop-color="#fffbe6"/><stop offset="1" stop-color="${p.mask}"/></radialGradient>
        </defs>
        <g class="bird-dance"><g class="bird-squish"><g class="bird-breathe">
          <path class="o" fill="${p.tail}" d="M90 192l-7 50q11 8 21 0l-2-50z"/>
          <path class="o" fill="${p.tail2}" d="M100 192l9 42q11 2 15-7l-11-37z"/>
          <path class="foot" d="M74 206q-2 12 2 18M86 206q2 12 6 17M114 206q-2 12-6 17M126 206q2 12-2 18"/>
          <path class="o" fill="url(#gb${id})" d="M100 26c50 0 76 46 76 98 0 54-32 88-76 88s-76-34-76-88c0-52 26-98 76-98z"/>
          <ellipse cx="100" cy="168" rx="46" ry="34" fill="${p.light}" opacity=".5"/>
          <g class="wing wing-l" fill="${p.wing}">${wing}</g>
          <g class="wing wing-r" fill="${p.wing}"><g transform="translate(200 0) scale(-1 1)">${wing}</g></g>
          <g class="head-tilt">
            <path class="ln" opacity=".5" d="M76 36q24-9 48 0M68 44q32-10 64 0"/>
            <path fill="url(#gm${id})" d="M100 46c32 0 52 24 52 52 0 32-22 52-52 52s-52-20-52-52c0-28 20-52 52-52z"/>
            <path class="ln" opacity=".5" d="M36 86q8-2 12-12M31 102q9-2 15-11M32 118q8 0 14-9M164 86q-8-2-12-12M169 102q-9-2-15-11M168 118q-8 0-14-9"/>
            <ellipse cx="57" cy="128" rx="9" ry="6.5" fill="${p.cheek}"/>
            <ellipse cx="143" cy="128" rx="9" ry="6.5" fill="${p.cheek}"/>
            <g fill="#3b2a35"><circle cx="83" cy="146" r="3.2"/><circle cx="94.5" cy="150" r="3.2"/><circle cx="105.5" cy="150" r="3.2"/><circle cx="117" cy="146" r="3.2"/></g>
            <ellipse class="blush" cx="62" cy="115" rx="12" ry="7" fill="#ff8cc6"/>
            <ellipse class="blush" cx="138" cy="115" rx="12" ry="7" fill="#ff8cc6"/>
            <g class="eyes">
              <g class="eyes-open">
                <circle cx="72" cy="94" r="13.5" fill="#fff"/><ellipse cx="72" cy="94" rx="10" ry="11.5" fill="#2a2233"/><circle cx="75.5" cy="89.5" r="4" fill="#fff"/><circle cx="68.5" cy="98" r="1.8" fill="#fff"/>
                <circle cx="128" cy="94" r="13.5" fill="#fff"/><ellipse cx="128" cy="94" rx="10" ry="11.5" fill="#2a2233"/><circle cx="131.5" cy="89.5" r="4" fill="#fff"/><circle cx="124.5" cy="98" r="1.8" fill="#fff"/>
              </g>
              <g class="eyes-happy"><path d="M60 97q12-14 24 0M116 97q12-14 24 0"/></g>
              <g class="eyes-closed"><path d="M60 94q12 10 24 0M116 94q12 10 24 0"/></g>
              <g class="eyes-pout"><path d="M64 87l15 8-15 8M136 87l-15 8 15 8"/></g>
            </g>
            <path class="o" stroke-width="2.5" fill="${p.cere}" d="M88 106q12-9 24 0-3 7-12 7t-12-7z"/>
            <g class="beak-closed"><path class="o" stroke-width="2.6" fill="#f6c453" d="M90 112q10-3 20 0-1 16-10 22-9-6-10-22z"/><path d="M95 116q2 6 4 10" stroke="#fff" stroke-width="2" opacity=".7" fill="none" stroke-linecap="round"/></g>
            <g class="beak-open"><path class="o" stroke-width="2.6" fill="#f6c453" d="M90 111q10-3 20 0-2 10-10 14-8-4-10-14z"/><ellipse cx="100" cy="131" rx="6" ry="4" fill="#3b2a35"/><path class="o" stroke-width="2.6" fill="#f6c453" d="M94 134q6 4 12 0-2 6-6 8-4-2-6-8z"/></g>
            ${p.bow ? `<g transform="translate(138 44) rotate(18)"><path class="o" stroke-width="3" fill="#ff48b0" d="M0 0C-16-14-26 2-16 9-9 13-3 6 0 0zM0 0C16-14 26 2 16 9 9 13 3 6 0 0z"/><circle class="o" stroke-width="3" r="5" fill="#ff8cc6"/></g>` : ""}
          </g>
        </g></g></g>
      </svg>`;
    birdsWrap.innerHTML = PALETTES.map(budgie).join("");
    const birds = [...birdsWrap.querySelectorAll(".bird")].map((el) => ({
      el,
      eyes: el.querySelector(".eyes"),
      squishG: el.querySelector(".bird-squish"),
      danceG: el.querySelector(".bird-dance"),
      moodTimer: 0,
      talkTimer: 0,
    }));

    let happy = 0;
    let celebrated = false;
    let asleep = false;
    let visible = false;
    let lastAct = Date.now();
    let lastPet = 0;
    let petCount = 0;
    let feedTurn = 0;
    let bubbleTimer;

    meter.innerHTML = Array.from({ length: 5 }, () => `<svg viewBox="-4 -4 108 98"><path d="${HEART}"/></svg>`).join("");
    const renderMeter = () => {
      [...meter.children].forEach((h, i) => h.classList.toggle("on", i < happy));
      meter.setAttribute("aria-label", `Mutluluk: ${happy} / 5`);
    };

    const restart = (el, cls) => {
      el.classList.remove(cls);
      void el.getBoundingClientRect();
      el.classList.add(cls);
    };
    const other = (b) => birds[birds[0] === b ? 1 : 0];
    const center = (b, fy = 0.4) => {
      const r = b.el.getBoundingClientRect();
      return { x: r.left + r.width / 2, y: r.top + r.height * fy };
    };

    const say = (b, text, ms = 1800) => {
      bubble.textContent = text;
      // balon konuşan kuşun üstünde dursun ama sahneden taşmasın
      const s = stage.getBoundingClientRect();
      const half = bubble.offsetWidth / 2 + 10;
      const x = center(b).x - s.left;
      bubble.style.setProperty("--bx", `${Math.min(s.width - half, Math.max(half, x))}px`);
      bubble.classList.add("is-on");
      b.el.classList.add("is-talking");
      clearTimeout(bubbleTimer);
      clearTimeout(b.talkTimer);
      b.talkTimer = setTimeout(() => b.el.classList.remove("is-talking"), 450);
      bubbleTimer = setTimeout(() => bubble.classList.remove("is-on"), ms);
    };

    const setMood = (b, name, ms) => {
      b.el.classList.remove("is-happy", "is-pout", "is-sleep");
      clearTimeout(b.moodTimer);
      if (name) b.el.classList.add(`is-${name}`);
      if (name && ms) b.moodTimer = setTimeout(() => setMood(b, null), ms);
    };

    const wake = () => {
      lastAct = Date.now();
      if (!asleep) return false;
      asleep = false;
      stage.classList.remove("sleeping");
      birds.forEach((b) => { setMood(b, null); restart(b.squishG, "squish"); });
      say(birds[1], "uyandık cik", 1500);
      return true;
    };

    const celebrate = () => {
      celebrated = true;
      birds.forEach((b, i) => setTimeout(() => { restart(b.danceG, "dance"); setMood(b, "happy", 2600); }, i * 200));
      const s = stage.getBoundingClientRect();
      burst(s.left + s.width / 2, s.top + s.height * 0.45, 18);
      say(birds[0], "cik cik! sana bi şey göstericez", 2400);
      setTimeout(() => {
        tcCard.classList.add("is-up");
        secret.hidden = false;
        say(birds[1], "resmi yani, kimlikte yazıyo", 3600);
      }, 2500);
    };

    const addHappy = (n) => {
      happy = Math.min(5, happy + n);
      renderMeter();
      if (happy === 5 && !celebrated) setTimeout(celebrate, 700);
    };

    const pet = (b, x, y) => {
      const now = Date.now();
      if (now - lastPet < 550) return;
      lastPet = now;
      wake();
      setMood(b, "happy", 1400);
      burst(x, y, 4);
      say(b, pick(["cik cik ♥", "orası tam yeri", "bi daha bi daha", "mmmh", "en güzel sen seviyosun"]), 1600);
      if (++petCount % 2 === 0) addHappy(1);
      if (Math.random() < 0.35) {
        const o = other(b);
        setTimeout(() => {
          o.el.classList.add("curious");
          say(o, pick(["ya ben?", "bi de beni sev", "kıskandım şu an", "bana sıra ne zaman"]), 1500);
          setTimeout(() => o.el.classList.remove("curious"), 1400);
        }, 1700);
      }
    };

    let pokes = [];
    const poke = (b) => {
      if (wake()) return;
      const now = Date.now();
      restart(b.squishG, "squish");
      pokes = pokes.filter((t) => now - t < 3000);
      pokes.push(now);
      if (pokes.length >= 4) {
        pokes = [];
        setMood(b, "pout", 2200);
        say(b, pick(["dürtme beni ya", "küstüm", "yeter ama"]), 2000);
      } else {
        say(b, pick(["cik!", "efendim?", "gıdıklanıyom", "noluyo"]), 1200);
      }
    };

    birds.forEach((b) => {
      let down = null;
      let hover = null;
      let rub = 0;
      b.el.addEventListener("pointerdown", (e) => {
        b.el.setPointerCapture(e.pointerId);
        down = { t: Date.now(), moved: 0, x: e.clientX, y: e.clientY };
      });
      b.el.addEventListener("pointermove", (e) => {
        const last = down || hover;
        if (last) {
          const d = Math.hypot(e.clientX - last.x, e.clientY - last.y);
          if (down) down.moved += d;
          rub += d;
          if (rub > 220) {
            rub = 0;
            pet(b, e.clientX, e.clientY);
          }
        }
        if (down) Object.assign(down, { x: e.clientX, y: e.clientY });
        if (e.pointerType === "mouse") hover = { x: e.clientX, y: e.clientY };
      });
      b.el.addEventListener("pointerleave", () => { hover = null; rub = 0; });
      b.el.addEventListener("pointerup", () => {
        if (down && down.moved < 10 && Date.now() - down.t < 450) poke(b);
        down = null;
      });
      b.el.addEventListener("pointercancel", () => { down = null; });
    });

    // Gözler imleci takip eder
    let eyeFrame = 0;
    window.addEventListener("pointermove", (e) => {
      if (eyeFrame || asleep) return;
      eyeFrame = requestAnimationFrame(() => {
        eyeFrame = 0;
        birds.forEach((b) => {
          const c = center(b, 0.38);
          const dx = e.clientX - c.x;
          const dy = e.clientY - c.y;
          const d = Math.hypot(dx, dy) || 1;
          const k = Math.min(1, d / 260);
          b.eyes.style.transform = `translate(${(dx / d) * 5 * k}px, ${(dy / d) * 4.5 * k}px)`;
        });
      });
    });

    // Göz kırpma ve uyuma
    birds.forEach((b) => {
      const loop = () => {
        if (!asleep) restart(b.el, "blink");
        setTimeout(loop, rnd(2200, 5600));
      };
      setTimeout(loop, rnd(1200, 3000));
    });
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(([en]) => { visible = en.isIntersecting; if (visible) lastAct = Date.now(); }).observe(stage);
    }
    setInterval(() => {
      if (!asleep && visible && Date.now() - lastAct > 16000) {
        asleep = true;
        birds.forEach((b) => { setMood(b, "sleep"); b.eyes.style.transform = ""; });
        stage.classList.add("sleeping");
        bubble.classList.remove("is-on");
      }
    }, 1000);

    // Atıştırmalıklar
    const TREATS = [
      { name: "çilek", line: "çileeek", svg: `<svg viewBox="0 0 60 60"><path fill="#e8475f" d="M30 56C14 46 8 32 10 22c2-8 10-10 20-10s18 2 20 10c2 10-4 24-20 34z"/><path fill="#00a95c" d="M18 14l12 7 12-7-5-6-7 4-7-4z"/><g fill="#ffd23f"><ellipse cx="22" cy="28" rx="1.6" ry="2.4"/><ellipse cx="34" cy="26" rx="1.6" ry="2.4"/><ellipse cx="28" cy="36" rx="1.6" ry="2.4"/><ellipse cx="38" cy="36" rx="1.6" ry="2.4"/><ellipse cx="20" cy="38" rx="1.6" ry="2.4"/><ellipse cx="30" cy="46" rx="1.6" ry="2.4"/></g></svg>` },
      { name: "kurabiye", line: "nom nom", svg: `<svg viewBox="0 0 60 60"><path fill="#d9a066" d="M54 22a24 24 0 1 1-16-16 8 8 0 0 0 9 9 8 8 0 0 0 7 7z"/><g fill="#5a3a2a"><circle cx="20" cy="24" r="3"/><circle cx="32" cy="34" r="3.2"/><circle cx="22" cy="42" r="2.6"/><circle cx="40" cy="44" r="2.4"/><circle cx="30" cy="18" r="2.2"/></g></svg>` },
      { name: "darı", line: "klasik ama severim", svg: `<svg viewBox="0 0 60 60"><path d="M30 56V10" stroke="#a07a3c" stroke-width="3" stroke-linecap="round"/><g fill="#f2c94c" stroke="#a07a3c" stroke-width="1.2">${[14, 20, 26, 32, 38, 44].map((y, i) => `<ellipse cx="${i % 2 ? 35 : 25}" cy="${y}" rx="5" ry="4"/>`).join("")}</g></svg>` },
      { name: "kahve", line: "kahve mi? artık uyumam", svg: `<svg viewBox="0 0 60 60"><path d="M24 6c-3 4 3 6 0 10M32 6c-3 4 3 6 0 10" stroke="#5d5466" stroke-width="2.5" fill="none" stroke-linecap="round"/><path fill="#fff" stroke="#2a2233" stroke-width="3" d="M10 22h34v16c0 10-8 16-17 16S10 48 10 38z"/><path d="M44 27c9 0 9 12 0 12" stroke="#2a2233" stroke-width="3" fill="none"/><ellipse cx="27" cy="23" rx="15" ry="3" fill="#8a5a3c"/><path fill="#ff48b0" transform="translate(21 32) scale(.12)" d="${HEART}"/></svg>` },
    ];
    const treatRow = document.getElementById("treats");

    const eat = (b, t) => {
      wake();
      b.el.classList.add("is-eating");
      restart(b.squishG, "squish");
      say(b, t.line, 1800);
      [250, 450, 700].forEach((ms, i) => setTimeout(() => b.el.classList.toggle("is-eating", i === 1), ms));
      if (t.name === "kahve") setTimeout(() => restart(b.danceG, "dance"), 600);
      else setTimeout(() => setMood(b, "happy", 1200), 750);
      addHappy(1);
    };

    const birdUnder = (x, y) => birds.find((b) => {
      const r = b.el.getBoundingClientRect();
      return x > r.left && x < r.right && y > r.top && y < r.bottom;
    });

    const flyTo = (ghost, from, b, t) => {
      const to = center(b, 0.5);
      const anim = ghost.animate([
        { left: `${from.x}px`, top: `${from.y}px`, transform: "translate(-50%, -50%) scale(1) rotate(0deg)" },
        { left: `${(from.x + to.x) / 2}px`, top: `${Math.min(from.y, to.y) - 90}px`, transform: "translate(-50%, -50%) scale(1.1) rotate(180deg)", offset: 0.5 },
        { left: `${to.x}px`, top: `${to.y}px`, transform: "translate(-50%, -50%) scale(.3) rotate(360deg)" },
      ], { duration: reduceMotion ? 1 : 650, easing: "ease-in-out" });
      anim.onfinish = () => { ghost.remove(); eat(b, t); };
    };

    const makeGhost = (t, x, y) => {
      const g = document.createElement("div");
      g.className = "treat-ghost";
      g.innerHTML = t.svg;
      g.style.left = `${x}px`;
      g.style.top = `${y}px`;
      document.body.appendChild(g);
      return g;
    };

    TREATS.forEach((t) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "treat";
      btn.innerHTML = `${t.svg}<span>${t.name}</span>`;
      btn.setAttribute("aria-label", `Cicikuşlara ${t.name} ver`);
      treatRow.appendChild(btn);

      btn.addEventListener("click", (e) => {
        if (e.detail !== 0) return; // klavyeyle basıldığında
        const r = btn.getBoundingClientRect();
        const from = { x: r.left + r.width / 2, y: r.top + r.height / 2 };
        flyTo(makeGhost(t, from.x, from.y), from, birds[feedTurn++ % 2], t);
      });

      btn.addEventListener("pointerdown", (e) => {
        e.preventDefault();
        btn.setPointerCapture(e.pointerId);
        const start = { x: e.clientX, y: e.clientY };
        let moved = false;
        const ghost = makeGhost(t, e.clientX, e.clientY);
        const move = (ev) => {
          if (Math.hypot(ev.clientX - start.x, ev.clientY - start.y) > 8) moved = true;
          ghost.style.left = `${ev.clientX}px`;
          ghost.style.top = `${ev.clientY}px`;
          const hit = birdUnder(ev.clientX, ev.clientY);
          birds.forEach((b) => b.el.classList.toggle("is-eating", b === hit));
        };
        const up = (ev) => {
          btn.removeEventListener("pointermove", move);
          btn.removeEventListener("pointerup", up);
          btn.removeEventListener("pointercancel", up);
          const hit = ev.type === "pointerup" && birdUnder(ev.clientX, ev.clientY);
          if (!moved) flyTo(ghost, start, birds[feedTurn++ % 2], t);
          else if (hit) { ghost.remove(); eat(hit, t); }
          else {
            birds.forEach((b) => b.el.classList.remove("is-eating"));
            ghost.animate([{ opacity: 1 }, { opacity: 0, transform: "translate(-50%, -50%) scale(.5)" }], { duration: 250 }).onfinish = () => ghost.remove();
          }
        };
        btn.addEventListener("pointermove", move);
        btn.addEventListener("pointerup", up);
        btn.addEventListener("pointercancel", up);
      });
    });

    renderMeter();
  }

  /* ── Parolla ── */
  const PZ = [
    ["A", "bu sitenin her yerinde var, üç harf", ["aşk"]],
    ["B", "tasarımcıya iş verirken yazılan şey, bu dergide de var", ["brief", "brif"]],
    ["C", "bu sitenin tüm hakları onlarda", ["cicikuşlar", "cicikuş"]],
    ["D", "bu aralar başının belası olan ödev", ["doku"]],
    ["F", "hello kitty'nin kafasındaki şey", ["fiyonk"]],
    ["G", "okuduğun bölüm, ___ tasarım", ["grafik"]],
    ["H", "ağzı olmayan en ünlü kedi", ["hello kitty", "hellokitty"]],
    ["K", "sabah ___ kadar sıcacıksın", ["kahve"]],
    ["L", "bu dergide açan çiçek", ["lale"]],
    ["M", "cicikuşlar aslında ne kuşu", ["muhabbet", "muhabbet kuşu"]],
    ["Ö", "bu dergiyi yapan çocuk", ["özgür"]],
    ["P", "başın ağrıyınca ilk sarıldığın şey (benden sonra tabii)", ["parol"]],
    ["R", "bu derginin baskı tekniği, pembe mavi sarı mürekkepli", ["risograf", "riso", "risografi"]],
    ["S", "kupon defterindeki ilk kupon", ["sarılma"]],
    ["T", "bu derginin tek okuru", ["tuana"]],
    ["Y", "cicikuşların rengi", ["yeşil"]],
    ["31", "dünyanın en komik esprisi", ["31", "otuzbir"], "rakamla yazılır"],
  ];
  const pzWheel = document.getElementById("pzWheel");
  if (pzWheel) {
    const fold = (s) => s.toLocaleLowerCase("tr")
      .replace(/[çğıöşüâî]/g, (c) => ({ ç: "c", ğ: "g", ı: "i", ö: "o", ş: "s", ü: "u", â: "a", î: "i" })[c])
      .replace(/[^a-z0-9]/g, "");
    const els = {
      now: document.getElementById("pzNow"),
      hint: document.getElementById("pzHint"),
      clue: document.getElementById("pzClue"),
      form: document.getElementById("pzForm"),
      input: document.getElementById("pzInput"),
      pass: document.getElementById("pzPass"),
      fb: document.getElementById("pzFeedback"),
      play: document.getElementById("pzPlay"),
      end: document.getElementById("pzEnd"),
      final: document.getElementById("pzFinal"),
      endMsg: document.getElementById("pzEndMsg"),
      again: document.getElementById("pzAgain"),
      right: document.getElementById("pzRight"),
      wrong: document.getElementById("pzWrong"),
      left: document.getElementById("pzLeft"),
    };
    const letters = PZ.map(([l], i) => {
      const a = -Math.PI / 2 + (i * 2 * Math.PI) / PZ.length;
      const el = document.createElement("span");
      el.className = "pz-l";
      el.textContent = l;
      el.style.setProperty("--x", Math.cos(a).toFixed(4));
      el.style.setProperty("--y", Math.sin(a).toFixed(4));
      pzWheel.appendChild(el);
      return el;
    });

    let status, pending, cur, busy;
    const counts = () => {
      const r = status.filter((s) => s === "right").length;
      const w = status.filter((s) => s === "wrong").length;
      els.right.textContent = r;
      els.wrong.textContent = w;
      els.left.textContent = PZ.length - r - w;
      return r;
    };
    const paint = () => {
      letters.forEach((el, i) => {
        el.className = `pz-l${status[i] ? ` ${status[i]}` : ""}${i === cur ? " now" : ""}`;
      });
      counts();
    };
    const show = () => {
      const [l, clue, , hint] = PZ[cur];
      els.now.textContent = l;
      restart2(els.now, "pz-pop");
      els.hint.textContent = hint || `${l} ile başlar`;
      els.clue.textContent = clue;
      els.input.value = "";
      els.fb.innerHTML = "&nbsp;";
      els.fb.className = "pz-feedback hand";
      paint();
    };
    const finish = () => {
      cur = -1;
      paint();
      const r = counts();
      els.play.hidden = true;
      els.end.hidden = false;
      els.final.textContent = r;
      document.getElementById("pzTotal").textContent = `/${PZ.length}`;
      els.endMsg.textContent =
        r === PZ.length ? "hepsini bildin. tabii bilcektin zaten" :
        r >= PZ.length - 4 ? "baya iyi ya, beni en iyi sen tanıyosun" :
        r >= PZ.length / 2 ? "fena değil ama bi daha oyna bence" :
        "ciddi misin tuana :( bi daha oyna";
      if (r >= PZ.length - 4) {
        const b = pzWheel.getBoundingClientRect();
        burst(b.left + b.width / 2, b.top + b.height / 2, 16);
      }
    };
    const next = () => {
      busy = false;
      if (!pending.length) return finish();
      cur = pending.shift();
      show();
    };
    const start = () => {
      status = PZ.map(() => null);
      pending = PZ.map((_, i) => i);
      els.play.hidden = false;
      els.end.hidden = true;
      next();
    };
    function restart2(el, cls) {
      el.classList.remove(cls);
      void el.offsetWidth;
      el.classList.add(cls);
    }

    els.form.addEventListener("submit", (e) => {
      e.preventDefault();
      if (busy || cur < 0) return;
      const v = fold(els.input.value);
      if (!v) return;
      busy = true;
      const answers = PZ[cur][2];
      if (answers.some((a) => fold(a) === v)) {
        status[cur] = "right";
        els.fb.textContent = pick(["evet!", "bildin tabii", "işte bu", "doğru"]);
        els.fb.className = "pz-feedback hand good";
        paint();
        setTimeout(next, 900);
      } else {
        status[cur] = "wrong";
        els.fb.textContent = `yok, cevap ${answers[0].toLocaleUpperCase("tr")}`;
        els.fb.className = "pz-feedback hand bad";
        paint();
        setTimeout(next, 1800);
      }
      els.input.focus({ preventScroll: true });
    });
    els.pass.addEventListener("click", () => {
      if (busy || cur < 0) return;
      status[cur] = "passed";
      pending.push(cur);
      next();
      els.input.focus({ preventScroll: true });
    });
    els.again.addEventListener("click", start);
    start();
  }

  /* ── Kazı kazan kuponlar ── */
  const COUPONS = [
    { title: "Bi sarılma", desc: "ne zaman istersen, ne kadar istersen", c: "#ff48b0" },
    { title: "Bi öpücük", desc: "yeri ve zamanı sen seç", c: "#e8475f" },
    { title: "Tam şu an bi fotoğrafını çekip bana yolla", desc: "evet şu an. bekliyorum", c: "#0078bf" },
    { title: "Bi yemek benden", desc: "nereyi istersen, ne istersen", c: "#00a95c" },
    { title: "Bi gün her dediğin olur", desc: "bütün gün hayır yok, sadece evet", c: "#8a5a3c" },
  ];
  const couponGrid = document.getElementById("couponGrid");
  if (couponGrid) {
    COUPONS.forEach((cp, i) => {
      const card = document.createElement("article");
      card.className = "coupon reveal";
      card.style.setProperty("--c", cp.c);
      card.style.setProperty("--tilt", `${[-1, 0.8, 0.6, -0.8, 0.4][i % 5]}deg`);
      card.innerHTML = `
        <div class="coupon-stub"><span>kupon no ${String(i + 1).padStart(2, "0")}</span></div>
        <div class="coupon-body">
          <h3>${cp.title}</h3>
          <p>${cp.desc}</p>
          <p class="coupon-fine">süresi yok · sadece tuana kullanabilir</p>
          <canvas aria-label="Kazınacak alan. Parmağınla ya da fareyle sürterek kazı."></canvas>
        </div>`;
      couponGrid.appendChild(card);
      setupScratch(card, cp.c);
    });
  }

  function setupScratch(card, color) {
    const cv = card.querySelector("canvas");
    const ctx = cv.getContext("2d");
    let touched = false;
    let done = false;
    let last = null;
    let strokes = 0;

    const paint = () => {
      const r = cv.getBoundingClientRect();
      if (!r.width) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      cv.width = Math.round(r.width * dpr);
      cv.height = Math.round(r.height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.globalCompositeOperation = "source-over";
      ctx.fillStyle = color;
      ctx.fillRect(0, 0, r.width, r.height);
      ctx.fillStyle = "rgba(255, 255, 255, .2)";
      for (let y = 4, row = 0; y < r.height; y += 9, row++) {
        for (let x = row % 2 ? 8.5 : 4; x < r.width; x += 9) {
          ctx.beginPath();
          ctx.arc(x, y, 1.7, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      ctx.fillStyle = "#fff";
      ctx.textAlign = "center";
      ctx.font = "700 12px 'Space Mono', monospace";
      ctx.fillText("K A Z I   K A Z A N", r.width / 2, r.height / 2 - 6);
      ctx.font = "700 26px Caveat, cursive";
      ctx.fillText("kazı bakalım ♥", r.width / 2, r.height / 2 + 24);
      ctx.globalCompositeOperation = "destination-out";
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.lineWidth = 38;
    };
    (document.fonts ? document.fonts.ready : Promise.resolve()).then(paint);
    window.addEventListener("resize", () => { if (!touched) paint(); });

    const progress = () => {
      const { data } = ctx.getImageData(0, 0, cv.width, cv.height);
      let clear = 0, total = 0;
      for (let i = 3; i < data.length; i += 4 * 23) { total++; if (data[i] === 0) clear++; }
      return clear / total;
    };

    const point = (e) => {
      const r = cv.getBoundingClientRect();
      return { x: e.clientX - r.left, y: e.clientY - r.top };
    };
    cv.addEventListener("pointerdown", (e) => {
      if (done) return;
      cv.setPointerCapture(e.pointerId);
      touched = true;
      last = point(e);
      ctx.beginPath();
      ctx.arc(last.x, last.y, 19, 0, Math.PI * 2);
      ctx.fill();
    });
    cv.addEventListener("pointermove", (e) => {
      if (!last || done) return;
      const p = point(e);
      ctx.beginPath();
      ctx.moveTo(last.x, last.y);
      ctx.lineTo(p.x, p.y);
      ctx.stroke();
      last = p;
      if (++strokes % 8 === 0 && progress() > 0.5) {
        done = true;
        card.classList.add("revealed");
        const r = card.getBoundingClientRect();
        burst(r.left + r.width / 2, r.top + r.height / 2, 12);
      }
    });
    const stop = () => { last = null; };
    cv.addEventListener("pointerup", stop);
    cv.addEventListener("pointercancel", stop);
  }

  /* ── Kalp kavanozu (küçük bir fizik motoru) ── */
  const jar = document.getElementById("jar");
  if (jar) {
    const ctx = jar.getContext("2d");
    const heartPath = new Path2D(HEART);
    const HEART_COLORS = ["#ff48b0", "#ff48b0", "#ff8cc6", "#e8475f", "#0078bf", "#ffd23f"];
    const countEl = document.getElementById("jarCount");
    const msg = document.getElementById("jarMsg");
    const bodies = [];
    const J = {};
    let W = 0, H = 0;
    let full = false;
    let lid = null;
    let shake = 0;
    let running = false;
    let visible = false;

    const layout = () => {
      const r = jar.getBoundingClientRect();
      if (!r.width) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      if (W) bodies.forEach((b) => { b.x *= r.width / W; b.y *= r.height / H; b.r *= r.width / W; });
      W = r.width;
      H = r.height;
      jar.width = Math.round(W * dpr);
      jar.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      Object.assign(J, {
        u: W / 420,
        L: W * 0.1, R: W * 0.9, B: H * 0.94,
        top: H * 0.12, neckL: W * 0.27, neckR: W * 0.73,
        shoulder: H * 0.26, rad: W * 0.13,
      });
      J.max = Math.floor(((J.R - J.L) * (J.B - J.shoulder) * 0.85) / (Math.PI * (16 * J.u) ** 2));
      draw();
    };

    const updateCount = () => {
      countEl.textContent = `kavanozda ${bodies.length} kalp var`;
    };

    const spawn = () => {
      if (full) return;
      const r = rnd(12, 20) * J.u;
      bodies.push({
        x: rnd(J.neckL + r, J.neckR - r), y: J.top - r * 1.5,
        vx: rnd(-60, 60) * J.u, vy: rnd(0, 80) * J.u,
        r, a: rnd(-0.5, 0.5), color: pick(HEART_COLORS),
      });
      updateCount();
      if (bodies.length >= J.max) {
        full = true;
        lid = { y: -60 * J.u, vy: 0 };
        setTimeout(() => { msg.hidden = false; }, 900);
      }
      wakeLoop();
    };

    const constrain = (b) => {
      const { L, R, B, rad, neckL, neckR, shoulder } = J;
      if (b.y < shoulder) {
        if (b.x - b.r < neckL) { b.x = neckL + b.r; b.vx = Math.abs(b.vx) * 0.3; }
        if (b.x + b.r > neckR) { b.x = neckR - b.r; b.vx = -Math.abs(b.vx) * 0.3; }
      } else {
        if (b.y - b.r < shoulder && (b.x < neckL || b.x > neckR)) { b.y = shoulder + b.r; b.vy = Math.abs(b.vy) * 0.2; }
        if (b.x - b.r < L) { b.x = L + b.r; b.vx = Math.abs(b.vx) * 0.3; }
        if (b.x + b.r > R) { b.x = R - b.r; b.vx = -Math.abs(b.vx) * 0.3; }
      }
      if (b.y + b.r > B) { b.y = B - b.r; b.vy = -Math.abs(b.vy) * 0.25; b.vx *= 0.96; }
      // yuvarlak alt köşeler
      for (const cx of [L + rad, R - rad]) {
        const cy = B - rad;
        const inCorner = cx < W / 2 ? b.x < cx : b.x > cx;
        if (inCorner && b.y > cy) {
          const dx = b.x - cx, dy = b.y - cy, d = Math.hypot(dx, dy);
          if (d > rad - b.r) {
            const nx = dx / d, ny = dy / d;
            b.x = cx + nx * (rad - b.r);
            b.y = cy + ny * (rad - b.r);
            const vn = b.vx * nx + b.vy * ny;
            if (vn > 0) { b.vx -= 1.3 * vn * nx; b.vy -= 1.3 * vn * ny; }
          }
        }
      }
    };

    const step = (dt) => {
      const g = 1500 * J.u;
      for (const b of bodies) {
        b.vy += g * dt;
        b.vx *= 0.995;
        b.x += b.vx * dt;
        b.y += b.vy * dt;
        b.a += (b.vx * dt) / b.r * 0.5;
      }
      for (let it = 0; it < 2; it++) {
        for (let i = 0; i < bodies.length; i++) {
          const a = bodies[i];
          for (let j = i + 1; j < bodies.length; j++) {
            const b = bodies[j];
            const dx = b.x - a.x, dy = b.y - a.y, m = a.r + b.r, d2 = dx * dx + dy * dy;
            if (d2 >= m * m || d2 < 1e-6) continue;
            const d = Math.sqrt(d2), nx = dx / d, ny = dy / d, o = (m - d) / 2;
            a.x -= nx * o; a.y -= ny * o; b.x += nx * o; b.y += ny * o;
            const rv = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny;
            if (rv < 0) {
              const k = -0.6 * rv;
              a.vx -= k * nx; a.vy -= k * ny; b.vx += k * nx; b.vy += k * ny;
            }
          }
        }
        bodies.forEach(constrain);
      }
      if (lid) {
        const target = J.top - 22 * J.u;
        lid.vy += g * dt;
        lid.y += lid.vy * dt;
        if (lid.y > target) { lid.y = target; lid.vy = Math.abs(lid.vy) > 60 ? -lid.vy * 0.35 : 0; }
      }
      shake *= 0.85;
    };

    const jarPath = () => {
      const { L, R, B, top, neckL, neckR, shoulder, rad } = J;
      const p = new Path2D();
      p.moveTo(neckL, top);
      p.lineTo(neckL, shoulder - H * 0.07);
      p.quadraticCurveTo(L, shoulder - H * 0.06, L, shoulder + H * 0.03);
      p.lineTo(L, B - rad);
      p.arcTo(L, B, L + rad, B, rad);
      p.lineTo(R - rad, B);
      p.arcTo(R, B, R, B - rad, rad);
      p.lineTo(R, shoulder + H * 0.03);
      p.quadraticCurveTo(R, shoulder - H * 0.06, neckR, shoulder - H * 0.07);
      p.lineTo(neckR, top);
      return p;
    };

    const roundRect = (x, y, w, h, r) => {
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.arcTo(x + w, y, x + w, y + h, r);
      ctx.arcTo(x + w, y + h, x, y + h, r);
      ctx.arcTo(x, y + h, x, y, r);
      ctx.arcTo(x, y, x + w, y, r);
      ctx.closePath();
    };

    function draw() {
      const { u, L, R, top, neckL, neckR, shoulder } = J;
      ctx.clearRect(0, 0, W, H);
      ctx.save();
      ctx.translate(Math.sin(shake * 3) * shake, 0);
      const glass = jarPath();

      // cam (arka)
      ctx.fillStyle = "rgba(255, 253, 248, .75)";
      ctx.fill(glass);

      // kalpler
      for (const b of bodies) {
        ctx.save();
        ctx.translate(b.x, b.y);
        ctx.rotate(b.a);
        const s = (b.r * 2.2) / 100;
        ctx.scale(s, s);
        ctx.translate(-50, -46);
        ctx.fillStyle = b.color;
        ctx.fill(heartPath);
        ctx.fillStyle = "rgba(255, 255, 255, .45)";
        ctx.beginPath();
        ctx.ellipse(27, 22, 10, 6, -0.6, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }

      // cam (ön) + parlama
      ctx.lineWidth = 3 * u;
      ctx.strokeStyle = "#2a2233";
      ctx.stroke(glass);
      ctx.strokeStyle = "rgba(255, 255, 255, .8)";
      ctx.lineWidth = 7 * u;
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(L + 22 * u, shoulder + 30 * u);
      ctx.lineTo(L + 22 * u, shoulder + 120 * u);
      ctx.stroke();

      // ağız halkası
      ctx.fillStyle = "#fffdf8";
      roundRect(neckL - 8 * u, top - 6 * u, neckR - neckL + 16 * u, 14 * u, 5 * u);
      ctx.fill();
      ctx.lineWidth = 3 * u;
      ctx.strokeStyle = "#2a2233";
      ctx.stroke();

      // etiket
      ctx.save();
      ctx.translate(W / 2, shoulder + 40 * u);
      ctx.rotate(-0.04);
      ctx.fillStyle = "#fffdf8";
      roundRect(-62 * u, -20 * u, 124 * u, 40 * u, 4 * u);
      ctx.fill();
      ctx.lineWidth = 1.5 * u;
      ctx.stroke();
      ctx.fillStyle = "#2a2233";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.font = `700 ${24 * u}px Caveat, cursive`;
      ctx.fillText("Tuana'nın kalpleri", 0, 1 * u, 116 * u);
      ctx.restore();

      // kapak
      if (lid) {
        const w = neckR - neckL + 28 * u;
        ctx.fillStyle = "#0078bf";
        roundRect(neckL - 14 * u, lid.y, w, 26 * u, 7 * u);
        ctx.fill();
        ctx.stroke();
        ctx.save();
        ctx.translate(W / 2, lid.y - 2 * u);
        ctx.scale(0.18 * u, 0.18 * u);
        ctx.translate(-50, -60);
        ctx.fillStyle = "#ff48b0";
        ctx.fill(heartPath);
        ctx.restore();
      }
      ctx.restore();
    }

    let prev = 0;
    const loop = (t) => {
      if (!visible) { running = false; return; }
      const dt = Math.min(0.032, (t - (prev || t)) / 1000) || 0.016;
      prev = t;
      const sub = 3;
      for (let i = 0; i < sub; i++) step(dt / sub);
      draw();
      requestAnimationFrame(loop);
    };
    function wakeLoop() {
      if (running || !visible) return;
      running = true;
      prev = 0;
      requestAnimationFrame(loop);
    }

    // Dokun: bir kalp. Basılı tut: dök. Sürükle: salla.
    let pour = null;
    let lastX = null;
    jar.addEventListener("pointerdown", (e) => {
      jar.setPointerCapture(e.pointerId);
      lastX = e.clientX;
      spawn();
      pour = setTimeout(function again() { spawn(); pour = setTimeout(again, 70); }, 300);
    });
    jar.addEventListener("pointermove", (e) => {
      if (lastX === null) return;
      const dx = e.clientX - lastX;
      lastX = e.clientX;
      if (Math.abs(dx) > 2) {
        clearTimeout(pour);
        shake = Math.min(14, shake + Math.abs(dx) * 0.3);
        bodies.forEach((b) => { b.vx += dx * 14 * J.u; b.vy -= Math.abs(dx) * 4 * J.u; });
        wakeLoop();
      }
    });
    const release = () => { clearTimeout(pour); lastX = null; };
    jar.addEventListener("pointerup", release);
    jar.addEventListener("pointercancel", release);

    document.getElementById("jarReset").addEventListener("click", () => {
      bodies.length = 0;
      full = false;
      lid = null;
      msg.hidden = true;
      updateCount();
      draw();
    });

    if ("IntersectionObserver" in window) {
      new IntersectionObserver(([en]) => { visible = en.isIntersecting; if (visible) wakeLoop(); }).observe(jar);
    } else {
      visible = true;
    }
    (document.fonts ? document.fonts.ready : Promise.resolve()).then(layout);
    window.addEventListener("resize", layout);
    layout();
  }

  /* ── Tıklayınca riso kalpleri ── */
  const COLORS = ["#ff48b0", "#0078bf", "#ffd23f"];
  function burst(x, y, count = 5) {
    if (reduceMotion) return;
    for (let i = 0; i < count; i++) {
      const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      s.setAttribute("viewBox", "0 0 100 90");
      s.setAttribute("class", "pop");
      s.innerHTML = `<path fill="${COLORS[i % 3]}" d="${HEART}"/>`;
      const a = rand(0, Math.PI * 2);
      const d = rand(30, count > 6 ? 140 : 70);
      s.style.left = `${x}px`;
      s.style.top = `${y}px`;
      s.style.width = `${Math.round(rand(14, 30))}px`;
      s.style.setProperty("--dx", `${Math.cos(a) * d}px`);
      s.style.setProperty("--dy", `${Math.sin(a) * d - 30}px`);
      s.style.setProperty("--r", `${Math.round(rand(-30, 30))}deg`);
      s.style.animationDelay = `${i * 25}ms`;
      document.body.appendChild(s);
      s.addEventListener("animationend", () => s.remove());
    }
  }
  document.addEventListener("click", (e) => {
    if (e.target.closest("button, a, input, label, form, canvas, .board, .bird, .coupon, .cover-title, .pz-wheel")) return;
    burst(e.clientX, e.clientY);
  });

  /* ── Kaydırınca belirme ── */
  const reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !reduceMotion) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (en.isIntersecting) {
          en.target.classList.add("is-in");
          io.unobserve(en.target);
        }
      });
    }, { threshold: 0.12 });
    reveals.forEach((el) => io.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add("is-in"));
  }
})();
