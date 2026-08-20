(function () {
  'use strict';
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

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

  /* ---------- Code tabs (each tab is an anchor target: #use-remote & co) ---------- */
  const tabs = Array.from(document.querySelectorAll('.tab'));
  const panels = Array.from(document.querySelectorAll('.panel'));
  const section = document.getElementById('use');

  const activate = (id, updateHash) => {
    const tab = tabs.find(t => t.id === id);
    if (!tab) return false;
    tabs.forEach(t => {
      const on = t === tab;
      t.classList.toggle('active', on);
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      t.setAttribute('tabindex', on ? '0' : '-1');
    });
    panels.forEach(p => p.classList.toggle('hidden', p.id !== tab.dataset.panel));
    if (updateHash && history.replaceState) {
      // replaceState, not location.hash: no scroll jump and no history spam per tab click.
      history.replaceState(null, '', '#' + id);
    }
    return true;
  };

  tabs.forEach(t => t.addEventListener('click', () => activate(t.id, true)));

  // Arrow keys move between tabs, per the ARIA tabs pattern.
  tabs.forEach((t, i) => t.addEventListener('keydown', (e) => {
    const step = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
    if (!step) return;
    e.preventDefault();
    const next = tabs[(i + step + tabs.length) % tabs.length];
    activate(next.id, true);
    next.focus();
  }));

  const openFromHash = (smooth) => {
    let id = '';
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (e) { return false; }
    if (!activate(id)) return false;
    if (section) {
      section.scrollIntoView({ block: 'start', behavior: (smooth && !reduced) ? 'smooth' : 'auto' });
    }
    return true;
  };

  // On load the browser has already jumped to the tab button, so scroll instantly to avoid
  // animating out of that jump. Later hash changes get the smooth treatment.
  if (!openFromHash(false)) {
    const initial = tabs.find(t => t.classList.contains('active')) || tabs[0];
    if (initial) activate(initial.id);
  }
  window.addEventListener('hashchange', () => openFromHash(true));

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

  // Every entry is [seconds after launch, kind, text], straight out of a recorded
  // `cargo green install` (see record.py). The replay is scheduled against a wall
  // clock rather than a per-line delay, so what you watch is the speed it really ran:
  // the long pause while cargo resolves, then 332 crates landing in bursts.
  const CG = window.CG || { lines: [], crates: 0, wall: 0 };
  const L = CG.lines;

  const caret = document.createElement('div');
  caret.innerHTML = '<span class="ansi-dim">$ </span><span class="caret"></span>';
  caret.className = 'term-line in';

  const span = (cls, text) => {
    const s = document.createElement('span');
    if (cls) s.className = cls;
    s.textContent = text;
    return s;
  };

  // Cargo prints its status verb in bold green and the rest of the line in the
  // terminal's default foreground; the replay reproduces exactly that, so the
  // panel reads like the output people already know.
  const STATUS = /^(\s*)([A-Z][A-Za-z-]*)([\s\S]*)$/;

  const lineNode = (kind, text, shown) => {
    const d = document.createElement('div');
    d.className = 'term-line whitespace-pre' + (kind === 'dim' ? ' ansi-dim' : '') + (shown ? ' in' : '');
    if (!text) { d.textContent = '\u00A0'; return d; }
    if (kind === 'cmd') {
      d.appendChild(span('ansi-dim', '$ '));
      d.appendChild(span('', text.replace(/^\$ /, '')));
      return d;
    }
    const m = (kind === 'hit' || kind === 'ok' || kind === 'run') && STATUS.exec(text);
    if (!m) { d.textContent = text; return d; }
    d.appendChild(span('', m[1]));
    d.appendChild(span('ansi-green', m[2]));
    d.appendChild(span('', m[3]));
    return d;
  };

  const setStats = (crates, elapsed) => {
    hits.textContent = String(crates);
    rate.textContent = CG.crates > 0 ? (crates / CG.crates * 100).toFixed(1) : '0.0';
    time.textContent = elapsed.toFixed(1);
  };

  function renderAll() {
    term.innerHTML = '';
    L.forEach(([, k, t]) => term.appendChild(lineNode(k, t, true)));
    term.scrollTop = term.scrollHeight;
    setStats(CG.crates, CG.wall);
  }

  function play() {
    term.innerHTML = '';
    const started = performance.now();
    let i = 0, crates = 0;

    const frame = () => {
      const elapsed = (performance.now() - started) / 1000;

      // Several crates can share a timestamp; emit every line that is now due.
      while (i < L.length && L[i][0] <= elapsed) {
        const [, k, t] = L[i];
        const d = lineNode(k, t, false);
        term.appendChild(d);
        requestAnimationFrame(() => d.classList.add('in'));
        if (k === 'hit') crates += 1;
        i += 1;
      }

      setStats(crates, Math.min(elapsed, CG.wall));
      term.scrollTop = term.scrollHeight;   // stay pinned to the newest line

      if (i < L.length || elapsed < CG.wall) {
        requestAnimationFrame(frame);
      } else {
        term.appendChild(caret);
        term.scrollTop = term.scrollHeight;
      }
    };
    requestAnimationFrame(frame);
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
