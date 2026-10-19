(() => {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
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
    approveBtn.textContent = "Onaylandı ✓";
    briefStatus.textContent = "onaylandı, teslimat başladı";
    const r = approveBtn.getBoundingClientRect();
    burst(r.left + r.width / 2, r.top + r.height / 2, 14);
  });

  /* ── Renk kartelası ── */
  const swatches = [
    { name: "Gülüş Pembesi", code: "14-0412", hex: "#ff6fa8", note: "Gülünce ben de istemeden gülümsüyorum." },
    { name: "Ses Mavisi", code: "17-1105", hex: "#4f86e8", note: "Sesini duyduğum anda içim biraz daha rahat ediyor." },
    { name: "Sabah Kahvesi", code: "18-0203", hex: "#8a5a3c", note: "Sabah kahvesi kadar sıcacıksın." },
    { name: "Somurtma Şeftalisi", code: "13-2201", hex: "#ffae85", note: "Somurtman bile bu kadar tatlı, haksızlık bu." },
    { name: "Lale", code: "16-0119", hex: "#e8475f", note: "Her lale gördüğümde aklıma sen geliyorsun." },
    { name: "Cicikuş Sarısı", code: "12-1029", hex: "#ffd23f", note: "Bütün haklar onlarda. Bunu biz konuştuk." },
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

  /* ── Yazı karakteri eksenleri ── */
  const specSheet = document.querySelector(".specimen-sheet");
  const wght = document.getElementById("wght");
  const soft = document.getElementById("soft");
  const wghtVal = document.getElementById("wghtVal");
  const softVal = document.getElementById("softVal");
  const verdict = document.getElementById("verdict");
  const updateAxes = () => {
    const w = +wght.value;
    const s = +soft.value;
    specSheet.style.setProperty("--wght", w);
    specSheet.style.setProperty("--soft", s);
    wghtVal.textContent = w;
    softVal.textContent = s;
    let text;
    if (w < 250) text = "fazla ince. bu kadar az sevemem.";
    else if (w < 500) text = "hâlâ az. sağa çek.";
    else if (w < 750) text = "yaklaşıyoruz…";
    else if (w < 900) text = "biraz daha…";
    else text = "en kalın hâli bu ama yine yetmiyor. font bu kadarını çizemiyor.";
    if (s === 100 && w >= 900) text = "maksimum sevgi, maksimum yumuşaklık. yani sana bakarkenki hâlim.";
    verdict.textContent = text;
  };
  if (wght && soft) {
    wght.addEventListener("input", updateAxes);
    soft.addEventListener("input", updateAxes);
  }
  // Yazılabilir alan: Enter satır eklemesin, boş kalırsa geri gelsin
  const specLive = document.getElementById("specLive");
  specLive?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); specLive.blur(); }
  });
  specLive?.addEventListener("blur", () => {
    if (!specLive.textContent.trim()) specLive.textContent = "Seni seviyorum.";
  });

  /* ── Çıkartmalar ── */
  const STICKERS = [
    { label: "kalp", size: 110, svg: `<svg viewBox="0 0 100 90"><path fill="#ff48b0" d="${HEART}"/><path fill="#fff" opacity=".55" d="M24 16c-8 1-13 8-12 16 3-6 7-10 13-12z"/></svg>` },
    { label: "lale", size: 90, svg: `<svg viewBox="0 0 80 130"><path d="M40 62v60" stroke="#00a95c" stroke-width="7" stroke-linecap="round"/><path fill="#00a95c" d="M40 104c-6-18-20-26-30-24 4 14 16 24 30 24zM40 96c6-14 18-20 28-18-4 12-15 18-28 18z"/><path fill="#ff48b0" d="M14 22c0 26 10 42 26 42s26-16 26-42L54 34 40 12 26 34z"/><path fill="#e8475f" d="M40 12 26 34l14 30 14-30z" opacity=".7"/></svg>` },
    { label: "yıldız", size: 96, svg: `<svg viewBox="0 0 100 100"><path fill="#ffd23f" d="M50 4l13 30 32 3-24 21 7 32-28-17-28 17 7-32L5 37l32-3z" stroke-linejoin="round"/><circle cx="40" cy="52" r="3.5" fill="#2a2233"/><circle cx="60" cy="52" r="3.5" fill="#2a2233"/><path d="M44 62q6 6 12 0" stroke="#2a2233" stroke-width="3" fill="none" stroke-linecap="round"/></svg>` },
    { label: "kedi", size: 118, svg: `<svg viewBox="0 0 120 104"><path fill="#0078bf" d="M14 10l26 20h40l26-20 4 46c0 28-22 44-50 44S10 84 10 56z"/><ellipse cx="34" cy="70" rx="9" ry="6" fill="#ff48b0" opacity=".85"/><ellipse cx="86" cy="70" rx="9" ry="6" fill="#ff48b0" opacity=".85"/><path d="M36 56q6-7 12 0M72 56q6-7 12 0" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round"/><path d="M54 70q6 6 12 0" stroke="#fff" stroke-width="3.5" fill="none" stroke-linecap="round"/></svg>` },
    { label: "cicikuşlar", size: 150, svg: `<svg viewBox="0 0 160 100"><path d="M8 92h144" stroke="#8a5a3c" stroke-width="5" stroke-linecap="round"/><circle cx="52" cy="58" r="30" fill="#ffd23f"/><path fill="#ff9a3c" d="M24 54l-12 6 12 4z"/><circle cx="40" cy="50" r="3.5" fill="#2a2233"/><path fill="#f2b705" d="M58 58c10 0 18 6 18 14-10 2-18-4-18-14z"/><circle cx="108" cy="58" r="30" fill="#ff8cc6"/><path fill="#ff9a3c" d="M136 54l12 6-12 4z"/><circle cx="120" cy="50" r="3.5" fill="#2a2233"/><path fill="#ff48b0" d="M102 58c-10 0-18 6-18 14 10 2 18-4 18-14z"/><path fill="#e8475f" transform="translate(70 12) scale(.2)" d="${HEART}"/></svg>` },
    { label: "Tuana etiketi", size: 150, svg: `<svg viewBox="0 0 170 80"><rect x="3" y="3" width="164" height="74" rx="37" fill="#2a2233"/><text x="85" y="52" text-anchor="middle" font-family="Fraunces, Georgia, serif" font-style="italic" font-weight="700" font-size="38" fill="#ffd23f">Tuana</text></svg>` },
    { label: "yüzde yüz tatlı rozeti", size: 104, svg: `<svg viewBox="0 0 100 100"><path fill="#00a95c" d="M50 2l9 8 12-3 4 12 12 4-3 12 8 9-8 9 3 12-12 4-4 12-12-3-9 8-9-8-12 3-4-12-12-4 3-12-8-9 8-9-3-12 12-4 4-12 12 3z"/><text x="50" y="50" text-anchor="middle" font-family="Space Grotesk, sans-serif" font-weight="700" font-size="22" fill="#fff">%100</text><text x="50" y="68" text-anchor="middle" font-family="Space Mono, monospace" font-size="11" letter-spacing="1.5" fill="#fff">TATLI</text></svg>` },
    { label: "papatya", size: 92, svg: `<svg viewBox="0 0 100 100"><g fill="#fff" stroke="#2a2233" stroke-width="2.5">${Array.from({ length: 8 }, (_, i) => `<ellipse cx="50" cy="22" rx="11" ry="20" transform="rotate(${i * 45} 50 50)"/>`).join("")}</g><circle cx="50" cy="50" r="15" fill="#ffd23f" stroke="#2a2233" stroke-width="2.5"/><circle cx="45" cy="48" r="2" fill="#2a2233"/><circle cx="55" cy="48" r="2" fill="#2a2233"/><path d="M45 55q5 4 10 0" stroke="#2a2233" stroke-width="2" fill="none" stroke-linecap="round"/></svg>` },
    { label: "Ö artı T", size: 96, svg: `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="46" fill="#fff" stroke="#0078bf" stroke-width="5" stroke-dasharray="6 5"/><text x="50" y="62" text-anchor="middle" font-family="Caveat, cursive" font-weight="700" font-size="36" fill="#0078bf">Ö+T</text><path fill="#ff48b0" transform="translate(41 70) scale(.18)" d="${HEART}"/></svg>` },
  ];

  const board = document.getElementById("board");
  let zTop = 10;
  const rand = (a, b) => a + Math.random() * (b - a);

  // Çıkartmalar üst üste binmesin diye kaba bir ızgaraya, biraz oynatarak dağıtılır
  const SLOTS = [[18, 22], [50, 18], [82, 24], [22, 52], [52, 50], [80, 54], [18, 80], [50, 82], [82, 80]];
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
    if (e.target.closest("button, a, input, label, [contenteditable], .board")) return;
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
