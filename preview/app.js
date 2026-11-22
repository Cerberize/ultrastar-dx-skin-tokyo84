/**
 * Tokyo84 — Interactive Material Design 3 Web Previewer
 * Plays the real synthesized 1984 FM/DX7 WAV SFX and animates the
 * Song Selection EQ + Singing Screen Hi-Fi Neon Pitch Bars.
 */

const SFX_FILES = {
  change: "../sounds/Change.wav",
  click: "../sounds/Click.wav",
  start: "../sounds/Start.wav",
  option: "../sounds/Option.wav",
  back: "../sounds/Back.wav",
  swoosh: "../sounds/Swoosh.wav",
};

const SONGS = [
  {
    title: "Plastic Love",
    artist: "Mariya Takeuchi · 1984 · City Pop",
    badges: ["1984 CLASSIC", "DUET READY", "HD VIDEO"],
    cover: "../themes/Tokyo84/ui/song_cover_default.png",
  },
  {
    title: "Mayonaka no Door (Stay With Me)",
    artist: "Miki Matsubara · 1979 · Tokyo Midnight",
    badges: ["GOLDEN NOTES", "HD VIDEO"],
    cover: "../themes/Tokyo84/bg/bg_main.jpg",
  },
  {
    title: "Midnight Pretenders",
    artist: "Tomoko Aran · 1983 · Shinjuku Synth",
    badges: ["SYNTHWAVE", "MEDLEY"],
    cover: "../themes/Tokyo84/bg/bg_score.jpg",
  },
  {
    title: "Ride on Time",
    artist: "Tatsuro Yamashita · 1980 · Hi-Fi Groove",
    badges: ["1980s GROOVE", "DUET READY"],
    cover: "../themes/Tokyo84/bg/bg_sing.jpg",
  },
];

let sfxEnabled = true;
let activeScreen = "main";
let songIdx = 0;

function playSfx(name) {
  if (!sfxEnabled || !SFX_FILES[name]) return;
  try {
    const audio = new Audio(SFX_FILES[name]);
    audio.volume = 0.55;
    audio.play().catch(() => {});
  } catch {
    // Ignore autoplay restrictions before first gesture
  }
}

// ---------------------------------------------------------------------------
// Screen Switching
// ---------------------------------------------------------------------------
const tabs = document.querySelectorAll(".m3-tab");
const screens = document.querySelectorAll(".usdx-screen");

function switchScreen(target, sfx = "swoosh") {
  if (!target || target === activeScreen) return;
  activeScreen = target;
  playSfx(sfx);

  tabs.forEach((t) => {
    const on = t.dataset.screen === target;
    t.classList.toggle("is-active", on);
    t.setAttribute("aria-selected", String(on));
  });

  screens.forEach((s) => {
    s.classList.toggle("is-active", s.id === `screen-${target}`);
  });
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => switchScreen(tab.dataset.screen, "click"));
});

document.querySelectorAll("[data-goto]").forEach((btn) => {
  btn.addEventListener("click", () => {
    switchScreen(btn.dataset.goto, btn.dataset.sfx || "click");
  });
});

// Main Menu hover focus + description update + Tools flyout (matches USDX MainButtonCollection1)
const mainBtns = document.querySelectorAll("#screen-main .usdx-pill");
const mainDesc = document.getElementById("mainDesc");
const toolsToggle = document.getElementById("toolsToggle");
const toolsFlyout = document.getElementById("toolsFlyout");

mainBtns.forEach((btn) => {
  btn.addEventListener("mouseenter", () => {
    mainBtns.forEach((b) => b.classList.remove("is-focused"));
    btn.classList.add("is-focused");
    if (btn.dataset.desc) mainDesc.textContent = btn.dataset.desc;
    playSfx("change");
  });
});

if (toolsToggle && toolsFlyout) {
  toolsToggle.addEventListener("click", () => {
    toolsFlyout.classList.toggle("is-open");
    playSfx("option");
  });
}

// SFX Toggle
const sfxToggle = document.getElementById("sfxToggle");
sfxToggle.addEventListener("click", () => {
  sfxEnabled = !sfxEnabled;
  sfxToggle.classList.toggle("is-on", sfxEnabled);
  sfxToggle.setAttribute("aria-pressed", String(sfxEnabled));
  sfxToggle.innerHTML = `<span class="dot"></span> 80s FM SFX: ${sfxEnabled ? "ON" : "OFF"}`;
  if (sfxEnabled) playSfx("option");
});

// ---------------------------------------------------------------------------
// Song Carousel + Animated Hi-Fi VU Equalizer
// ---------------------------------------------------------------------------
const carousel = document.getElementById("coverCarousel");
const songTitle = document.getElementById("songTitle");
const songArtist = document.getElementById("songArtist");
const songBadges = document.getElementById("songBadges");
const songIndexEl = document.getElementById("songIndex");
const singTrackLabel = document.getElementById("singTrackLabel");

function renderCarousel() {
  const prev = (songIdx - 1 + SONGS.length) % SONGS.length;
  const next = (songIdx + 1) % SONGS.length;
  const visible = [prev, songIdx, next];

  carousel.innerHTML = visible
    .map((idx, pos) => {
      const s = SONGS[idx];
      return `
        <div class="cover-card ${pos === 1 ? "is-center" : ""}" data-pick="${idx}">
          <img src="${s.cover}" alt="${s.title}" />
          <div class="cover-label">${s.title}</div>
        </div>
      `;
    })
    .join("");

  carousel.querySelectorAll(".cover-card").forEach((card) => {
    card.addEventListener("click", () => {
      songIdx = Number(card.dataset.pick);
      playSfx("change");
      renderCarousel();
    });
  });

  const cur = SONGS[songIdx];
  songTitle.textContent = cur.title;
  songArtist.textContent = cur.artist;
  songIndexEl.textContent = String(songIdx + 1).padStart(2, "0");
  singTrackLabel.textContent = `${cur.artist.split("·")[0].trim()} — ${cur.title}`;
  songBadges.innerHTML = cur.badges
    .map((b, i) => `<span class="mini-badge ${i % 2 ? "cyan" : ""}">${b}</span>`)
    .join("");
}

document.getElementById("prevSong").addEventListener("click", () => {
  songIdx = (songIdx - 1 + SONGS.length) % SONGS.length;
  playSfx("change");
  renderCarousel();
});

document.getElementById("nextSong").addEventListener("click", () => {
  songIdx = (songIdx + 1) % SONGS.length;
  playSfx("change");
  renderCarousel();
});

renderCarousel();

// VU Equalizer bars
const eqContainer = document.getElementById("songEq");
const eqBars = [];
for (let i = 0; i < 18; i++) {
  const bar = document.createElement("div");
  bar.className = "vu-bar";
  bar.style.height = "14px";
  eqContainer.appendChild(bar);
  eqBars.push(bar);
}

// ---------------------------------------------------------------------------
// Singing Screen — Animated Hi-Fi Neon Pitch Bars & Score Tick
// ---------------------------------------------------------------------------
const notesTrackP1 = document.getElementById("notesTrackP1");
const notesTrackP2 = document.getElementById("notesTrackP2");
const singProgress = document.getElementById("singProgress");
const p1ScoreEl = document.getElementById("p1Score");
const p2ScoreEl = document.getElementById("p2Score");

const P1_PATTERN = [
  { x: 6, w: 12, y: 58 },
  { x: 20, w: 16, y: 36, golden: true },
  { x: 40, w: 14, y: 46 },
  { x: 58, w: 20, y: 24 },
  { x: 82, w: 14, y: 52 },
];

const P2_PATTERN = [
  { x: 8, w: 14, y: 48 },
  { x: 25, w: 14, y: 62 },
  { x: 43, w: 18, y: 30, golden: true },
  { x: 65, w: 15, y: 42 },
  { x: 84, w: 13, y: 26 },
];

function renderPitchLane(container, pattern, playerClass, phase) {
  container.innerHTML = pattern
    .map((n) => {
      let left = ((n.x - phase) % 105 + 105) % 105 - 5;
      const isSung = left < 26;
      const cls = [
        "neon-note",
        playerClass,
        isSung ? "sung" : "",
        n.golden ? "golden" : "",
      ].join(" ");
      return `<div class="${cls}" style="left:${left.toFixed(1)}%; top:${n.y}%; width:${n.w}%;"></div>`;
    })
    .join("");
}

// Options interactive value cyclers
document.querySelectorAll(".opt-value").forEach((btn) => {
  const choices = btn.dataset.cycle.split(",");
  let idx = 0;
  btn.addEventListener("click", () => {
    idx = (idx + 1) % choices.length;
    btn.textContent = choices[idx];
    playSfx("option");
  });
});

// Animation Loop
let phase = 0;
let p1Pts = 7840;
let p2Pts = 7420;
let lastTick = performance.now();

function animate(now) {
  const dt = (now - lastTick) / 1000;
  lastTick = now;

  if (activeScreen === "song") {
    eqBars.forEach((bar, i) => {
      const h = 10 + Math.abs(Math.sin(now * 0.005 + i * 0.65)) * 34;
      bar.style.height = `${h.toFixed(0)}px`;
    });
  }

  if (activeScreen === "sing") {
    phase = (phase + dt * 16) % 105;
    renderPitchLane(notesTrackP1, P1_PATTERN, "p1", phase);
    renderPitchLane(notesTrackP2, P2_PATTERN, "p2", phase);

    const pct = 28 + ((now * 0.002) % 62);
    singProgress.style.width = `${pct.toFixed(1)}%`;

    if (Math.random() < 0.14) {
      p1Pts = Math.min(9990, p1Pts + 10);
      p2Pts = Math.min(9850, p2Pts + 10);
      p1ScoreEl.textContent = p1Pts.toLocaleString("en-US").padStart(6, "0");
      p2ScoreEl.textContent = p2Pts.toLocaleString("en-US").padStart(6, "0");
    }
  }

  requestAnimationFrame(animate);
}

requestAnimationFrame(animate);
