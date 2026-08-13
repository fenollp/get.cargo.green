(function () {
  'use strict';
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Icons ---------- */
  if (window.lucide) lucide.createIcons();

  /* ---------- Nav: glass on scroll ---------- */
  const nav = document.getElementById('nav');
  const onScroll = () => nav.classList.toggle('nav-scrolled', window.scrollY > 12);
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  /* ---------- Scroll reveal ---------- */
  const items = document.querySelectorAll('.reveal');
  if (reduced || !('IntersectionObserver' in window)) {
    items.forEach(el => el.classList.add('shown'));
  } else {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e, i) => {
        if (!e.isIntersecting) return;
        setTimeout(() => e.target.classList.add('shown'), Math.min(i * 70, 280));
        io.unobserve(e.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    items.forEach(el => io.observe(el));
  }

  /* ---------- Code tabs ---------- */
  const tabs = document.querySelectorAll('.tab');
  const activate = (id) => {
    tabs.forEach(t => {
      const on = t.dataset.tab === id;
      t.classList.toggle('active', on);
      t.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    document.querySelectorAll('.panel').forEach(p => p.classList.toggle('hidden', p.id !== id));
  };
  tabs.forEach(t => t.addEventListener('click', () => activate(t.dataset.tab)));
  const initial = document.querySelector('.tab.active') || tabs[0];
  if (initial) activate(initial.dataset.tab);

  /* ---------- Copy buttons ---------- */
  const flash = (btn, label) => {
    const span = btn.querySelector('span');
    const icon = btn.querySelector('[data-lucide], svg');
    if (span) { const old = span.textContent; span.textContent = label; setTimeout(() => span.textContent = old, 1600); }
    if (icon) { icon.classList.add('flash'); setTimeout(() => icon.classList.remove('flash'), 1600); }
  };
  document.querySelectorAll('.copy').forEach(btn => {
    btn.addEventListener('click', () => {
      const panel = btn.parentElement.querySelector('.panel:not(.hidden)');
      if (!panel) return;
      navigator.clipboard.writeText(panel.innerText.trim()).then(() => flash(btn, 'Copied'));
    });
  });
  document.querySelectorAll('.copy-inline').forEach(btn => {
    btn.addEventListener('click', () => {
      navigator.clipboard.writeText(btn.dataset.copy).then(() => flash(btn, 'Copied'));
    });
  });

  /* ---------- Pricing: billing toggle ---------- */
  const toggle = document.getElementById('billing-toggle');
  const notes = document.querySelectorAll('.annual-note');
  const prices = document.querySelectorAll('[data-price-monthly]');
  const lblM = document.getElementById('lbl-monthly');
  const lblA = document.getElementById('lbl-annual');
  let annual = false;
  if (toggle) toggle.addEventListener('click', () => {
    annual = !annual;
    toggle.setAttribute('aria-checked', annual ? 'true' : 'false');
    toggle.classList.toggle('on', annual);
    prices.forEach(el => { el.textContent = annual ? el.dataset.priceAnnual : el.dataset.priceMonthly; });
    notes.forEach(n => n.classList.toggle('hidden', !annual));
    lblM.classList.toggle('dim', annual);
    lblA.classList.toggle('dim', !annual);
  });

  /* ---------- Hero: build log replay ---------- */
  const term = document.getElementById('term');
  const hits = document.getElementById('stat-hits');
  const rate = document.getElementById('stat-rate');
  const time = document.getElementById('stat-time');

  const CG = window.CG || { lines: [], total: 0, cached: 0, wall: 0 };
  const L = CG.lines;

  const cls = {
    cmd:   'text-slate-200',
    dim:   'text-slate-600',
    hit:   'text-moss-400',
    run:   'text-slate-300',
    ok:    'text-white',
    blank: ''
  };

  const caret = document.createElement('div');
  caret.innerHTML = '<span class="text-slate-600">$ </span><span class="caret"></span>';
  caret.className = 'term-line in';

  function renderAll() {
    term.innerHTML = '';
    L.forEach(([k, t]) => {
      const d = document.createElement('div');
      d.className = 'term-line in whitespace-pre ' + cls[k];
      d.textContent = t || '\u00A0';
      term.appendChild(d);
    });
    hits.textContent = String(CG.cached);
    rate.textContent = (CG.cached / CG.total * 100).toFixed(1);
    time.textContent = CG.wall.toFixed(1);
  }

  function play() {
    term.innerHTML = '';
    let i = 0, shownHits = 0;
    const step = () => {
      if (i >= L.length) {
        term.appendChild(caret);
        return;
      }
      const [k, t] = L[i];
      const d = document.createElement('div');
      d.className = 'term-line whitespace-pre ' + cls[k];
      d.textContent = t || '\u00A0';
      term.appendChild(d);
      requestAnimationFrame(() => d.classList.add('in'));

      if (k === 'hit') { shownHits += 1; }
      if (/more crates restored/.test(L[i][1])) { shownHits = CG.cached; }

      hits.textContent = String(shownHits);
      rate.textContent = (shownHits / CG.total * 100).toFixed(1);
      time.textContent = (i / (L.length - 1) * CG.wall).toFixed(1);

      // Keep the viewport pinned to the newest line
      term.scrollTop = term.scrollHeight;

      i += 1;
      const delay = k === 'blank' ? 90 : (k === 'hit' ? 130 : 240);
      setTimeout(step, delay);
    };
    step();
  }

  if (reduced) {
    renderAll();
  } else {
    // Start the replay once, when the hero is on screen.
    let played = false;
    const heroObs = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting && !played) { played = true; setTimeout(play, 350); }
      });
    }, { threshold: 0.25 });
    heroObs.observe(term);
  }
})();
