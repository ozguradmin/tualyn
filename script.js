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

  /* ── Cicikuş ── */
  const bird = document.getElementById("bird");
  if (bird) {
    const stage = document.getElementById("petStage");
    const bubble = document.getElementById("bubble");
    const eyes = document.getElementById("eyes");
    const squishG = bird.querySelector(".bird-squish");
    const danceG = bird.querySelector(".bird-dance");
    const meter = document.getElementById("meter");
    const secret = document.getElementById("secret");

    let happy = 0;
    let celebrated = false;
    let asleep = false;
    let visible = false;
    let lastAct = Date.now();
    let lastPet = 0;
    let petCount = 0;
    let rub = 0;
    let pokes = [];
    let moodTimer, bubbleTimer, talkTimer;

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

    const say = (text, ms = 1800) => {
      bubble.textContent = text;
      bubble.classList.add("is-on");
      bird.classList.add("is-talking");
      clearTimeout(bubbleTimer);
      clearTimeout(talkTimer);
      talkTimer = setTimeout(() => bird.classList.remove("is-talking"), 450);
      bubbleTimer = setTimeout(() => bubble.classList.remove("is-on"), ms);
    };

    const setMood = (name, ms) => {
      bird.classList.remove("is-happy", "is-pout", "is-sleep");
      clearTimeout(moodTimer);
      if (name) bird.classList.add(`is-${name}`);
      if (name && ms) moodTimer = setTimeout(() => setMood(null), ms);
    };

    const wake = () => {
      lastAct = Date.now();
      if (!asleep) return false;
      asleep = false;
      stage.classList.remove("sleeping");
      setMood(null);
      restart(squishG, "squish");
      say("uyandım! cik?", 1500);
      return true;
    };

    const birdPoint = (fx, fy) => {
      const r = bird.getBoundingClientRect();
      return { x: r.left + r.width * fx, y: r.top + r.height * fy };
    };

    const celebrate = () => {
      celebrated = true;
      restart(danceG, "dance");
      setMood("happy", 2600);
      const p = birdPoint(0.5, 0.45);
      burst(p.x, p.y, 18);
      say("cik cik! sana bir şey söyleyeceğim…", 2400);
      setTimeout(() => {
        secret.hidden = false;
        say("Özgür seni çok seviyormuş ♥", 3600);
      }, 2500);
    };

    const addHappy = (n) => {
      happy = Math.min(5, happy + n);
      renderMeter();
      if (happy === 5 && !celebrated) setTimeout(celebrate, 700);
    };

    const pet = (x, y) => {
      const now = Date.now();
      if (now - lastPet < 550) return;
      lastPet = now;
      wake();
      setMood("happy", 1400);
      burst(x, y, 4);
      say(pick(["cik cik ♥", "tam orası", "biraz daha…", "mırr… pardon, ben kuşum", "en güzel sen seviyorsun"]), 1600);
      if (++petCount % 2 === 0) addHappy(1);
    };

    const poke = () => {
      if (wake()) return;
      const now = Date.now();
      restart(squishG, "squish");
      pokes = pokes.filter((t) => now - t < 3000);
      pokes.push(now);
      if (pokes.length >= 4) {
        pokes = [];
        setMood("pout", 2200);
        say(pick(["dürtme beniii", "hıh. küstüm.", "off yaa"]), 2000);
      } else {
        say(pick(["cik!", "hı?", "gıdıklanıyorum", "bir daha yap", "cik cik"]), 1200);
      }
    };

    // Dokun, okşa
    let down = null;
    let hover = null;
    bird.addEventListener("pointerdown", (e) => {
      bird.setPointerCapture(e.pointerId);
      down = { t: Date.now(), moved: 0, x: e.clientX, y: e.clientY };
    });
    bird.addEventListener("pointermove", (e) => {
      const last = down || hover;
      if (last) {
        const d = Math.hypot(e.clientX - last.x, e.clientY - last.y);
        if (down) down.moved += d;
        rub += d;
        if (rub > 240) {
          rub = 0;
          pet(e.clientX, e.clientY);
        }
      }
      if (down) Object.assign(down, { x: e.clientX, y: e.clientY });
      if (e.pointerType === "mouse") hover = { x: e.clientX, y: e.clientY };
    });
    bird.addEventListener("pointerleave", () => { hover = null; rub = 0; });
    bird.addEventListener("pointerup", () => {
      if (down && down.moved < 10 && Date.now() - down.t < 450) poke();
      down = null;
    });
    bird.addEventListener("pointercancel", () => { down = null; });

    // Gözler imleci takip eder
    let eyeFrame = 0;
    window.addEventListener("pointermove", (e) => {
      if (eyeFrame || asleep) return;
      eyeFrame = requestAnimationFrame(() => {
        eyeFrame = 0;
        const c = birdPoint(0.5, 0.47);
        const dx = e.clientX - c.x;
        const dy = e.clientY - c.y;
        const d = Math.hypot(dx, dy) || 1;
        const k = Math.min(1, d / 260);
        eyes.style.transform = `translate(${(dx / d) * 7 * k}px, ${(dy / d) * 6 * k}px)`;
      });
    });

    // Göz kırpma ve uyuma
    const blinkLoop = () => {
      if (!asleep) restart(bird, "blink");
      setTimeout(blinkLoop, rnd(2400, 5200));
    };
    setTimeout(blinkLoop, 2000);
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(([en]) => { visible = en.isIntersecting; if (visible) lastAct = Date.now(); }).observe(stage);
    }
    setInterval(() => {
      if (!asleep && visible && Date.now() - lastAct > 16000) {
        asleep = true;
        setMood("sleep");
        stage.classList.add("sleeping");
        eyes.style.transform = "";
        bubble.classList.remove("is-on");
      }
    }, 1000);

    // Atıştırmalıklar
    const TREATS = [
      { name: "çilek", line: "çilek en sevdiğim!", svg: `<svg viewBox="0 0 60 60"><path fill="#e8475f" d="M30 56C14 46 8 32 10 22c2-8 10-10 20-10s18 2 20 10c2 10-4 24-20 34z"/><path fill="#00a95c" d="M18 14l12 7 12-7-5-6-7 4-7-4z"/><g fill="#ffd23f"><ellipse cx="22" cy="28" rx="1.6" ry="2.4"/><ellipse cx="34" cy="26" rx="1.6" ry="2.4"/><ellipse cx="28" cy="36" rx="1.6" ry="2.4"/><ellipse cx="38" cy="36" rx="1.6" ry="2.4"/><ellipse cx="20" cy="38" rx="1.6" ry="2.4"/><ellipse cx="30" cy="46" rx="1.6" ry="2.4"/></g></svg>` },
      { name: "kurabiye", line: "nom nom nom", svg: `<svg viewBox="0 0 60 60"><path fill="#d9a066" d="M54 22a24 24 0 1 1-16-16 8 8 0 0 0 9 9 8 8 0 0 0 7 7z"/><g fill="#5a3a2a"><circle cx="20" cy="24" r="3"/><circle cx="32" cy="34" r="3.2"/><circle cx="22" cy="42" r="2.6"/><circle cx="40" cy="44" r="2.4"/><circle cx="30" cy="18" r="2.2"/></g></svg>` },
      { name: "tohum", line: "klasik ama güzel", svg: `<svg viewBox="0 0 60 60"><g fill="#c8a26b" stroke="#8a5a3c" stroke-width="1.5"><ellipse cx="22" cy="40" rx="6" ry="9" transform="rotate(-30 22 40)"/><ellipse cx="38" cy="40" rx="6" ry="9" transform="rotate(25 38 40)"/><ellipse cx="30" cy="26" rx="6" ry="9" transform="rotate(5 30 26)"/></g></svg>` },
      { name: "kahve", line: "kahve mi?! uyumam artık", svg: `<svg viewBox="0 0 60 60"><path d="M24 6c-3 4 3 6 0 10M32 6c-3 4 3 6 0 10" stroke="#5d5466" stroke-width="2.5" fill="none" stroke-linecap="round"/><path fill="#fff" stroke="#2a2233" stroke-width="3" d="M10 22h34v16c0 10-8 16-17 16S10 48 10 38z"/><path d="M44 27c9 0 9 12 0 12" stroke="#2a2233" stroke-width="3" fill="none"/><ellipse cx="27" cy="23" rx="15" ry="3" fill="#8a5a3c"/><path fill="#ff48b0" transform="translate(21 32) scale(.12)" d="${HEART}"/></svg>` },
    ];
    const treatRow = document.getElementById("treats");

    const eat = (t) => {
      wake();
      bird.classList.add("is-eating");
      restart(squishG, "squish");
      say(t.line, 1800);
      [250, 450, 700].forEach((ms, i) => setTimeout(() => bird.classList.toggle("is-eating", i === 1), ms));
      if (t.name === "kahve") setTimeout(() => restart(danceG, "dance"), 600);
      else setTimeout(() => setMood("happy", 1200), 750);
      addHappy(1);
    };

    const flyToBird = (ghost, from, t) => {
      const to = birdPoint(0.5, 0.56);
      const anim = ghost.animate([
        { left: `${from.x}px`, top: `${from.y}px`, transform: "translate(-50%, -50%) scale(1) rotate(0deg)" },
        { left: `${(from.x + to.x) / 2}px`, top: `${Math.min(from.y, to.y) - 90}px`, transform: "translate(-50%, -50%) scale(1.1) rotate(180deg)", offset: 0.5 },
        { left: `${to.x}px`, top: `${to.y}px`, transform: "translate(-50%, -50%) scale(.3) rotate(360deg)" },
      ], { duration: reduceMotion ? 1 : 650, easing: "ease-in-out" });
      anim.onfinish = () => { ghost.remove(); eat(t); };
    };

    TREATS.forEach((t) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "treat";
      btn.innerHTML = `${t.svg}<span>${t.name}</span>`;
      btn.setAttribute("aria-label", `Cicikuşa ${t.name} ver`);
      treatRow.appendChild(btn);

      btn.addEventListener("click", (e) => {
        if (e.detail !== 0) return; // klavyeyle basıldığında
        const r = btn.getBoundingClientRect();
        const ghost = makeGhost(t, r.left + r.width / 2, r.top + r.height / 2);
        flyToBird(ghost, { x: r.left + r.width / 2, y: r.top + r.height / 2 }, t);
      });

      btn.addEventListener("pointerdown", (e) => {
        e.preventDefault();
        btn.setPointerCapture(e.pointerId);
        const start = { x: e.clientX, y: e.clientY };
        let moved = false;
        const ghost = makeGhost(t, e.clientX, e.clientY);
        const overBird = (ev) => {
          const r = bird.getBoundingClientRect();
          return ev.clientX > r.left && ev.clientX < r.right && ev.clientY > r.top && ev.clientY < r.bottom;
        };
        const move = (ev) => {
          if (Math.hypot(ev.clientX - start.x, ev.clientY - start.y) > 8) moved = true;
          ghost.style.left = `${ev.clientX}px`;
          ghost.style.top = `${ev.clientY}px`;
          bird.classList.toggle("is-eating", overBird(ev));
        };
        const up = (ev) => {
          btn.removeEventListener("pointermove", move);
          btn.removeEventListener("pointerup", up);
          btn.removeEventListener("pointercancel", up);
          if (!moved) flyToBird(ghost, start, t);
          else if (ev.type === "pointerup" && overBird(ev)) { ghost.remove(); eat(t); }
          else {
            bird.classList.remove("is-eating");
            ghost.animate([{ opacity: 1 }, { opacity: 0, transform: "translate(-50%, -50%) scale(.5)" }], { duration: 250 }).onfinish = () => ghost.remove();
          }
        };
        btn.addEventListener("pointermove", move);
        btn.addEventListener("pointerup", up);
        btn.addEventListener("pointercancel", up);
      });
    });

    function makeGhost(t, x, y) {
      const g = document.createElement("div");
      g.className = "treat-ghost";
      g.innerHTML = t.svg;
      g.style.left = `${x}px`;
      g.style.top = `${y}px`;
      document.body.appendChild(g);
      return g;
    }

    renderMeter();
  }

  /* ── Kazı kazan kuponlar ── */
  const COUPONS = [
    { title: "Bir sarılma", desc: "İstediğin an, istediğin kadar uzun.", c: "#ff48b0" },
    { title: "Film gecesi, film senden", desc: "İtiraz etmeyeceğim. En azından deneyeceğim.", c: "#0078bf" },
    { title: "Bir tartışmayı kazanma hakkı", desc: "Haklı olmasan bile. Bir kereye mahsus.", c: "#00a95c" },
    { title: "Bir kahve benden", desc: "Nerede istersen, ne zaman istersen.", c: "#8a5a3c" },
  ];
  const couponGrid = document.getElementById("couponGrid");
  if (couponGrid) {
    COUPONS.forEach((cp, i) => {
      const card = document.createElement("article");
      card.className = "coupon reveal";
      card.style.setProperty("--c", cp.c);
      card.style.setProperty("--tilt", `${[-1, 0.8, 0.6, -0.8][i]}deg`);
      card.innerHTML = `
        <div class="coupon-stub"><span>kupon no ${String(i + 1).padStart(2, "0")}</span></div>
        <div class="coupon-body">
          <h3>${cp.title}</h3>
          <p>${cp.desc}</p>
          <p class="coupon-fine">son kullanma tarihi yok · devredilemez · sadece Tuana</p>
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
      ctx.fillText("buraya sürt ♥", r.width / 2, r.height / 2 + 24);
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
    if (e.target.closest("button, a, input, label, canvas, .board, .bird, .coupon, .cover-title")) return;
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
