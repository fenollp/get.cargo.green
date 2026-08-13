#!/usr/bin/env python3
"""Build FILE from content.md.

Usage:
    python3 build.py              build once
    python3 build.py --watch      build, serve on :4347, open a browser, rebuild on change
    python3 build.py --out FILE   write somewhere else
"""

from __future__ import annotations

import functools
import html
import http.server
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content.md"
ASSETS = ROOT / "assets"
DEFAULT_OUT = ROOT / "index.html"
PORT = 4347
URL = f"http://localhost:{PORT}"
SOURCES = [CONTENT, ASSETS / "theme.css", ASSETS / "app.js", ASSETS / "tailwind.config.js", Path(__file__)]


# ─────────────────────────────  parsing  ─────────────────────────────

class Block:
    """A section or an item: named fields, list fields, prose, and maybe code."""

    def __init__(self, name: str = ""):
        self.name = name
        self.fields: dict[str, object] = {}
        self.lines: list[str] = []
        self.items: list[Block] = []
        self.code = ""
        self.lang = ""

    def get(self, key: str, default: str = "") -> str:
        value = self.fields.get(key, default)
        return value if isinstance(value, str) else default

    def list(self, key: str) -> list[str]:
        value = self.fields.get(key, [])
        return value if isinstance(value, list) else []

    def flag(self, key: str) -> bool:
        return self.get(key).strip().lower() in ("true", "yes", "1")

    def paragraphs(self) -> list[str]:
        out, buf = [], []
        for line in self.lines:
            if line.strip():
                buf.append(line.strip())
            elif buf:
                out.append(" ".join(buf))
                buf = []
        if buf:
            out.append(" ".join(buf))
        return out


FIELD_RE = re.compile(r"^([a-z_]+):[ \t]*(.*)$")
BULLET_RE = re.compile(r"^\s*-\s+(.*)$")


def parse(text: str) -> dict[str, Block]:
    sections: dict[str, Block] = {}
    section = item = None
    target = None          # block currently receiving lines
    list_key = None        # list field currently being filled
    in_code = False

    for raw in text.splitlines():
        line = raw.rstrip()

        if in_code:
            if line.startswith("```"):
                in_code = False
            elif target is not None:
                target.code += line + "\n"
            continue

        if line.startswith("```"):
            if target is not None:
                in_code = True
                target.lang = line[3:].strip() or "text"
            continue

        if line.startswith("## "):
            section = Block(line[3:].strip())
            sections[section.name] = section
            target, item, list_key = section, None, None
            continue

        if line.startswith("### ") and section is not None:
            item = Block(line[4:].strip())
            section.items.append(item)
            target, list_key = item, None
            continue

        if target is None:
            continue  # preamble before the first section

        bullet = BULLET_RE.match(line)
        if bullet and list_key:
            target.fields[list_key].append(bullet.group(1).strip())  # type: ignore[union-attr]
            continue

        field = FIELD_RE.match(line)
        if field:
            key, value = field.group(1), field.group(2).strip()
            if value:
                target.fields[key], list_key = value, None
            else:
                target.fields[key] = []
                list_key = key
            continue

        list_key = None
        target.lines.append(line)

    return sections


def split_pipe(value: str, count: int = 2) -> list[str]:
    parts = [p.strip() for p in value.split("|")]
    parts += [""] * (count - len(parts))
    return parts[:count] if count else parts


# ─────────────────────────────  inline markdown  ─────────────────────────────

def esc(text: str) -> str:
    """Escape text nodes without turning quotes and apostrophes into entities."""
    return html.escape(text, quote=False)


LINK_CLS = "text-moss-400 underline decoration-moss-400/30 underline-offset-4 hover:decoration-moss-400"


def inline(text: str, brace: str = "em") -> str:
    """Render the inline subset: code, bold, emphasis, links, {highlight}."""
    out = html.escape(text, quote=False)
    out = re.sub(r"`([^`]+)`", r'<code class="code">\1</code>', out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", out)
    out = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", rf'<a href="\2" class="{LINK_CLS}">\1</a>', out)
    if brace == "grad":
        out = re.sub(r"\{([^}]+)\}", r'<span class="hl">\1</span>', out)
    elif brace == "em":
        out = re.sub(r"\{([^}]+)\}", r'<span class="val">\1</span>', out)
    else:
        out = out.replace("{", "").replace("}", "")
    return out


def prose(block: Block, cls: str, limit: int | None = None) -> str:
    paras = block.paragraphs()
    if limit:
        paras = paras[:limit]
    return "\n".join(f'<p class="{cls}">{inline(p)}</p>' for p in paras)


# ─────────────────────────────  code highlighting  ─────────────────────────────

CMD_WORDS = {"cargo", "docker", "export", "alias", "which", "nix", "podman", "make"}


def highlight(code: str, lang: str) -> str:
    out = []
    for line in code.rstrip("\n").split("\n"):
        esc = html.escape(line, quote=False)
        stripped = esc.lstrip()

        if stripped.startswith("#") and lang != "yaml":
            out.append(f'<span class="c-dim">{esc}</span>')
            continue
        if lang == "yaml" and stripped.startswith("#"):
            out.append(f'<span class="c-dim">{esc}</span>')
            continue

        esc = re.sub(r'("[^"]*")', r'<span class="c-str">\1</span>', esc)
        esc = re.sub(r"('[^']*')", r'<span class="c-str">\1</span>', esc)
        esc = re.sub(r"\b([A-Z][A-Z0-9_]{2,})(?==)", r'<span class="c-var">\1</span>', esc)

        if lang in ("sh", "bash", "shell"):
            first = stripped.split(" ")[0] if stripped else ""
            if first in CMD_WORDS:
                esc = esc.replace(first, f'<span class="c-cmd">{first}</span>', 1)
        elif lang == "yaml":
            esc = re.sub(r"^(\s*-?\s*)([a-zA-Z_][\w.-]*)(:)", r'\1<span class="c-var">\2</span>\3', esc)
        elif lang == "toml":
            esc = re.sub(r"^(\s*)(\[[^\]]+\])", r'\1<span class="c-cmd">\2</span>', esc)
            esc = re.sub(r"^(\s*)([a-z][\w.-]*)(\s*=)", r'\1<span class="c-var">\2</span>\3', esc)

        out.append(esc)
    return "\n".join(out)


# ─────────────────────────────  small helpers  ─────────────────────────────

def icon(name: str, cls: str) -> str:
    return f'<i data-lucide="{name}" class="{cls}"></i>'


def check(text: str, text_cls: str = "") -> str:
    body = f'<span class="{text_cls}">{text}</span>' if text_cls else text
    return (f'<li class="flex gap-3">{icon("check", "mt-0.5 h-[18px] w-[18px] shrink-0 text-moss-400")}'
            f"{body}</li>")


def button(spec: str, style: str) -> str:
    label, href = split_pipe(spec)
    styles = {
        "solid": ("inline-flex items-center justify-center gap-2 rounded-xl bg-moss-500 px-5 py-3 "
                  "text-[14.5px] font-semibold text-ink-950 shadow-[0_10px_40px_-12px_rgba(16,185,129,.7)] "
                  "transition hover:bg-moss-400"),
        "ghost": ("inline-flex items-center justify-center gap-2 rounded-xl border border-white/[0.12] "
                  "bg-white/[.03] px-5 py-3 text-[14.5px] font-semibold text-white backdrop-blur "
                  "transition hover:border-moss-400/40 hover:bg-white/[.06]"),
    }
    arrow = icon("arrow-right", "h-4 w-4" + ("" if style == "solid" else " text-moss-400"))
    return f'<a href="{href}" class="{styles[style]}">{esc(label)} {arrow}</a>'


def section_head(block: Block, extra_link: bool = True) -> str:
    eyebrow = block.get("eyebrow")
    link = block.get("link")
    head = ""
    if eyebrow:
        head += f'<p class="eyebrow text-moss-400">{esc(eyebrow)}</p>\n'
    head += (f'<h2 class="mt-4 font-display text-4xl font-semibold leading-[1.1] tracking-[-0.025em] '
             f'text-white sm:text-[2.75rem]">{inline(block.get("heading"), "grad")}</h2>\n')
    head += prose(block, "mt-5 text-[16.5px] leading-relaxed text-slate-400")

    if link and extra_link:
        label, href = split_pipe(link)
        return (f'<div class="reveal flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">'
                f'<div class="max-w-2xl">{head}</div>'
                f'<a href="{href}" class="inline-flex shrink-0 items-center gap-2 text-[14px] font-medium '
                f'text-moss-400 transition hover:text-moss-300">{esc(label)} '
                f'{icon("external-link", "h-4 w-4")}</a></div>')
    return f'<div class="reveal max-w-2xl">{head}</div>'


# ─────────────────────────────  sections  ─────────────────────────────

def render_nav(nav: Block, meta: Block) -> str:
    links = "".join(
        f'<a href="{href}" class="text-[13.5px] font-medium text-slate-400 transition hover:text-white">'
        f"{esc(label)}</a>"
        for label, href in (split_pipe(l) for l in nav.list("links"))
    )
    label, href = split_pipe(nav.get("cta"))
    return f"""<header id="nav" class="fixed top-0 inset-x-0 z-40 transition-colors duration-300">
  <div class="mx-auto max-w-screen px-6">
    <nav class="flex h-16 items-center justify-between">
      <a href="#" class="flex items-center gap-2.5 group">
        <svg width="26" height="26" viewBox="0 0 32 32" fill="none" aria-hidden="true" class="transition-transform duration-300 group-hover:rotate-[8deg]">
          <path d="M16 3.2 27.4 9.6v12.8L16 28.8 4.6 22.4V9.6L16 3.2Z" stroke="#34D399" stroke-width="1.6" stroke-linejoin="round"/>
          <path d="M4.6 9.6 16 16m0 0 11.4-6.4M16 16v12.8" stroke="#34D399" stroke-width="1.6" stroke-opacity=".45" stroke-linejoin="round"/>
          <circle cx="16" cy="16" r="2.6" fill="#34D399"/>
        </svg>
        <span class="font-display text-[15px] font-semibold tracking-tight text-white">cargo<span class="text-moss-400">.green</span></span>
      </a>
      <div class="hidden items-center gap-8 lg:flex">{links}</div>
      <div class="flex items-center gap-2">
        <a href="{meta.get('repo')}" class="hidden items-center gap-2 rounded-lg border border-white/10 px-3 py-1.5 text-[13px] font-medium text-slate-300 transition hover:border-white/20 hover:text-white sm:flex">
          {icon('github', 'h-4 w-4')} GitHub
        </a>
        <a href="{href}" class="rounded-lg bg-white px-3.5 py-1.5 text-[13px] font-semibold text-ink-950 transition hover:bg-moss-400">{esc(label)}</a>
      </div>
    </nav>
  </div>
</header>"""


def render_hero(hero: Block, term: Block) -> str:
    badge_label, badge_href = split_pipe(hero.get("badge"))
    stats = "".join(
        f'<div><dt class="eyebrow text-slate-600">{esc(s.name)}</dt>'
        f'<dd class="mt-1.5 font-display text-xl font-semibold text-white">{esc(s.get("value"))}</dd></div>'
        for s in hero.items
    )
    return f"""<section class="relative pt-36 pb-20 sm:pt-44 sm:pb-28">
  <div class="mx-auto max-w-screen px-6">
    <div class="grid items-center gap-14 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)]">
      <div class="reveal">
        <a href="{badge_href}" class="inline-flex items-center gap-2 rounded-full border border-moss-400/25 bg-moss-500/10 px-3 py-1 text-[12px] font-medium text-moss-400 transition hover:border-moss-400/50">
          <span class="relative flex h-1.5 w-1.5">
            <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-moss-400 opacity-70"></span>
            <span class="relative inline-flex h-1.5 w-1.5 rounded-full bg-moss-400"></span>
          </span>
          {esc(badge_label)} {icon('arrow-right', 'h-3.5 w-3.5')}
        </a>
        <h1 class="mt-6 font-display text-[2.6rem] font-semibold leading-[1.05] tracking-[-0.03em] text-white sm:text-6xl">{inline(hero.get('headline'), 'grad')}</h1>
        {prose(hero, 'mt-7 max-w-xl text-[17px] leading-relaxed text-slate-400')}
        <div class="mt-9 flex flex-col gap-3 sm:flex-row sm:items-center">
          {button(hero.get('cta_primary'), 'solid')}
          {button(hero.get('cta_secondary'), 'ghost')}
        </div>
        <dl class="mt-12 grid max-w-lg grid-cols-3 gap-6 border-t border-white/[0.08] pt-7">{stats}</dl>
      </div>

      <div class="reveal">
        <div class="glass edge-lit rounded-2xl p-1.5">
          <div class="rounded-[13px] bg-[#070A0E]/90">
            <div class="flex items-center justify-between border-b border-white/[0.08] px-4 py-2.5">
              <div class="flex items-center gap-2">
                <span class="h-2.5 w-2.5 rounded-full bg-white/12"></span>
                <span class="h-2.5 w-2.5 rounded-full bg-white/12"></span>
                <span class="h-2.5 w-2.5 rounded-full bg-white/12"></span>
                <span class="ml-3 font-mono text-[11px] text-slate-500">{esc(hero.get('repo_label'))}</span>
              </div>
              <span class="flex items-center gap-1.5 font-mono text-[11px] text-moss-400">
                {icon('cloud-download', 'h-3.5 w-3.5')} {esc(hero.get('registry_label'))}
              </span>
            </div>
            <div id="term" class="h-[356px] overflow-hidden px-4 py-4 font-mono text-[12.5px] leading-[1.75] sm:text-[13px]"></div>
            <div class="grid grid-cols-3 divide-x divide-white/[0.08] border-t border-white/[0.08]">
              <div class="px-4 py-3">
                <div class="eyebrow text-slate-600">Restored</div>
                <div class="mt-1 font-mono text-[15px] font-medium text-white"><span id="stat-hits">0</span> / {esc(hero.get('crate_total'))}</div>
              </div>
              <div class="px-4 py-3">
                <div class="eyebrow text-slate-600">Hit rate</div>
                <div class="mt-1 font-mono text-[15px] font-medium text-moss-400"><span id="stat-rate">0.0</span>%</div>
              </div>
              <div class="px-4 py-3">
                <div class="eyebrow text-slate-600">Wall clock</div>
                <div class="mt-1 font-mono text-[15px] font-medium text-white"><span id="stat-time">0.0</span>s</div>
              </div>
            </div>
          </div>
        </div>
        <p class="mt-3 text-center font-mono text-[11px] text-slate-600">{esc(hero.get('caption'))}</p>
      </div>
    </div>
  </div>
</section>"""


def render_registries(block: Block) -> str:
    sep = '<span class="hidden h-3 w-px bg-white/10 sm:block"></span>'
    items = sep.join(f"<span>{esc(i)}</span>" for i in block.list("items"))
    return f"""<section class="border-y border-white/[0.08] bg-white/[.015] py-7">
  <div class="mx-auto max-w-screen px-6">
    <div class="flex flex-col items-center gap-5 sm:flex-row sm:justify-between">
      <p class="eyebrow shrink-0 text-slate-600">{esc(block.get('label'))}</p>
      <div class="flex flex-wrap items-center justify-center gap-x-8 gap-y-3 font-mono text-[13px] text-slate-500">{items}</div>
    </div>
  </div>
</section>"""


def render_problem(problem: Block, answer: Block, ci: Block) -> str:
    cards = "".join(f"""<article class="reveal glass glass-hover rounded-2xl p-7">
        <div class="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[.04]">{icon(c.get('icon'), 'h-5 w-5 text-slate-300')}</div>
        <h3 class="mt-5 font-display text-lg font-semibold text-white">{esc(c.name)}</h3>
        {prose(c, 'mt-2.5 text-[14.5px] leading-relaxed text-slate-400')}
      </article>""" for c in problem.items)

    points = "".join(check(inline(p), "") for p in answer.list("points"))
    ci_cards = "".join(f"""<div>
            {icon(c.get('icon'), 'h-5 w-5 text-moss-400')}
            <h4 class="mt-3.5 font-display text-[15.5px] font-semibold text-white">{esc(c.name)}</h4>
            {prose(c, 'mt-2 text-[13.5px] leading-relaxed text-slate-400')}
          </div>""" for c in ci.items)

    return f"""<section id="problem" class="py-24 sm:py-32">
  <div class="mx-auto max-w-screen px-6">
    <div class="reveal max-w-3xl">
      <p class="eyebrow text-moss-400">{esc(problem.get('eyebrow'))}</p>
      <h2 class="mt-4 font-display text-4xl font-semibold leading-[1.1] tracking-[-0.025em] text-white sm:text-5xl">{inline(problem.get('heading'))}</h2>
      {prose(problem, 'mt-6 text-[17px] leading-relaxed text-slate-400')}
    </div>

    <div class="mt-14 grid gap-5 md:grid-cols-3">{cards}</div>

    <div class="reveal glass edge-lit mt-8 overflow-hidden rounded-2xl">
      <div class="grid gap-10 p-8 sm:p-10 lg:grid-cols-[1.15fr_1fr] lg:items-center">
        <div>
          <p class="eyebrow text-moss-400">{esc(answer.get('eyebrow'))}</p>
          <h3 class="mt-3.5 font-display text-2xl font-semibold tracking-[-0.02em] text-white sm:text-[1.75rem]">{inline(answer.get('heading'))}</h3>
          {prose(answer, 'mt-4 text-[15.5px] leading-relaxed text-slate-400')}
          <p class="mt-5 font-display text-lg font-medium text-white">{esc(answer.get('kicker'))}</p>
        </div>
        <ul class="space-y-3.5 text-[14.5px] text-slate-300">{points}</ul>
      </div>
    </div>

    <div class="reveal glass mt-5 overflow-hidden rounded-2xl">
      <div class="grid gap-10 p-8 sm:p-10 lg:grid-cols-[1fr_1.25fr]">
        <div>
          <p class="eyebrow text-moss-400">{esc(ci.get('eyebrow'))}</p>
          <h3 class="mt-3.5 font-display text-2xl font-semibold tracking-[-0.02em] text-white sm:text-[1.75rem]">{inline(ci.get('heading'))}</h3>
          {prose(ci, 'mt-4 text-[15.5px] leading-relaxed text-slate-400')}
        </div>
        <div class="grid gap-5 sm:grid-cols-3">{ci_cards}</div>
      </div>
    </div>
  </div>
</section>"""


def render_install(install: Block, commands: Block) -> str:
    default = install.get("default_tab", install.items[0].name if install.items else "")
    tabs, panels = [], []
    for tab in install.items:
        tid = "t-" + re.sub(r"[^a-z0-9]+", "-", tab.name.lower()).strip("-")
        active = " active" if tab.name == default else ""
        hidden = "" if tab.name == default else " hidden"
        tabs.append(f'<button class="tab rounded-lg px-3.5 py-2 font-mono text-[12.5px] text-slate-400 transition{active}" '
                    f'data-tab="{tid}" role="tab" aria-selected="{"true" if active else "false"}">{esc(tab.name)}</button>')
        panels.append(f'<pre id="{tid}" class="panel{hidden} overflow-x-auto p-6 font-mono text-[13px] '
                      f'leading-[1.85] text-slate-300"><code>{highlight(tab.code, tab.lang)}</code></pre>')

    rows = []
    for i, cmd in enumerate(commands.items):
        border = "" if i == len(commands.items) - 1 else " border-b border-white/[0.08] pb-3.5"
        rows.append(f"""<div class="flex flex-col gap-1{border}">
            <dt class="font-mono text-[12.5px] text-moss-400"><span class="text-slate-600">$ </span>{esc(cmd.name)}</dt>
            <dd class="text-[13.5px] text-slate-400">{esc(cmd.get('desc'))}</dd>
          </div>""")

    return f"""<section id="install" class="py-24 sm:py-32">
  <div class="mx-auto max-w-screen px-6">
    {section_head(install)}
    <div class="mt-12 grid gap-5 lg:grid-cols-[1.05fr_1fr]">
      <div class="reveal glass rounded-2xl">
        <div class="flex flex-wrap gap-1 border-b border-white/[0.08] p-2" role="tablist">{''.join(tabs)}</div>
        <div class="relative">
          <button class="copy absolute right-3 top-3 z-10 inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[.04] px-2.5 py-1.5 font-mono text-[11px] text-slate-400 backdrop-blur transition hover:border-white/25 hover:text-white">
            {icon('copy', 'h-3.5 w-3.5')}<span>Copy</span>
          </button>
          {''.join(panels)}
        </div>
      </div>
      <div class="reveal glass rounded-2xl p-8">
        <h3 class="font-display text-lg font-semibold text-white">{esc(commands.get('heading'))}</h3>
        {prose(commands, 'mt-2 text-[14.5px] leading-relaxed text-slate-400')}
        <dl class="mt-7 space-y-3.5">{''.join(rows)}</dl>
      </div>
    </div>
  </div>
</section>"""


def render_how(how: Block, hits: Block, engines: Block) -> str:
    steps = "".join(f"""<li class="reveal glass glass-hover rounded-2xl p-7">
        <div class="flex items-center justify-between">
          <span class="font-mono text-[12px] text-moss-400">{i + 1:02d}</span>
          {icon(s.get('icon'), 'h-5 w-5 text-slate-500')}
        </div>
        <h3 class="mt-5 font-display text-lg font-semibold text-white">{inline(s.name)}</h3>
        {prose(s, 'mt-2.5 text-[14.5px] leading-relaxed text-slate-400')}
      </li>""" for i, s in enumerate(how.items))

    bullets = "".join(f'<li class="flex gap-3 text-[14px] text-slate-400">'
                      f'{icon("dot", "h-[18px] w-[18px] shrink-0 text-moss-400")}{inline(p)}</li>'
                      for p in hits.list("points"))

    engine_cards = "".join(f"""<div class="rounded-xl border border-white/[0.08] bg-white/[.02] p-5">
            <div class="flex items-center gap-2.5">
              {icon(e.get('icon'), 'h-[18px] w-[18px] text-moss-400')}
              <h4 class="font-display text-[15px] font-semibold text-white">{esc(e.name)}</h4>
            </div>
            {prose(e, 'mt-2.5 text-[13.5px] leading-relaxed text-slate-400')}
            <p class="mt-3 font-mono text-[11.5px] text-slate-500">{esc(e.get('config'))}</p>
          </div>""" for e in engines.items)

    return f"""<section id="how" class="border-y border-white/[0.08] bg-white/[.012] py-24 sm:py-32">
  <div class="mx-auto max-w-screen px-6">
    {section_head(how)}
    <ol class="mt-14 grid gap-5 md:grid-cols-2 xl:grid-cols-4">{steps}</ol>
    <div class="mt-8 grid gap-5 lg:grid-cols-[1fr_1fr]">
      <div class="reveal glass rounded-2xl p-8">
        <div class="flex items-center gap-3">{icon(hits.get('icon'), 'h-5 w-5 text-moss-400')}
          <h3 class="font-display text-lg font-semibold text-white">{esc(hits.get('heading'))}</h3>
        </div>
        {prose(hits, 'mt-3 text-[14.5px] leading-relaxed text-slate-400')}
        <ul class="mt-6 space-y-3">{bullets}</ul>
        <p class="mt-6 text-[13.5px] leading-relaxed text-slate-500">{inline(hits.get('footnote'))}</p>
      </div>
      <div class="reveal glass rounded-2xl p-8">
        <div class="flex items-center gap-3">{icon(engines.get('icon'), 'h-5 w-5 text-moss-400')}
          <h3 class="font-display text-lg font-semibold text-white">{esc(engines.get('heading'))}</h3>
        </div>
        {prose(engines, 'mt-3 text-[14.5px] leading-relaxed text-slate-400')}
        <div class="mt-6 grid gap-4 sm:grid-cols-2">{engine_cards}</div>
        <p class="mt-6 text-[13.5px] leading-relaxed text-slate-500">{inline(engines.get('footnote'))}</p>
      </div>
    </div>
  </div>
</section>"""


def render_config(config: Block) -> str:
    cards = []
    for c in config.items:
        chips = "".join(f'<span class="rounded-md border border-white/[0.08] bg-white/[.03] px-2 py-1">{esc(chip)}</span>'
                        for chip in c.list("chips"))
        cards.append(f"""<a href="{c.get('href')}" class="reveal glass glass-hover group block rounded-2xl p-7">
        <div class="flex items-start justify-between">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl border border-moss-400/20 bg-moss-500/10">{icon(c.get('icon'), 'h-5 w-5 text-moss-400')}</div>
          {icon('arrow-up-right', 'h-4 w-4 text-slate-600 transition group-hover:text-moss-400')}
        </div>
        <h3 class="mt-5 font-display text-lg font-semibold text-white">{esc(c.name)}</h3>
        {prose(c, 'mt-2 text-[14px] leading-relaxed text-slate-400')}
        <div class="mt-5 flex flex-wrap gap-1.5 font-mono text-[11.5px] text-slate-500">{chips}</div>
      </a>""")

    cards.append(f"""<a href="{config.get('reference_href')}" class="reveal glass glass-hover group flex flex-col justify-between rounded-2xl border-dashed p-7">
        <div>
          <div class="flex items-start justify-between">
            <div class="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[.04]">{icon('book-open', 'h-5 w-5 text-slate-300')}</div>
            {icon('arrow-up-right', 'h-4 w-4 text-slate-600 transition group-hover:text-moss-400')}
          </div>
          <h3 class="mt-5 font-display text-lg font-semibold text-white">{esc(config.get('reference_title'))}</h3>
          <p class="mt-2 text-[14px] leading-relaxed text-slate-400">{inline(config.get('reference_body'))}</p>
        </div>
        <span class="mt-6 inline-flex items-center gap-2 text-[13.5px] font-medium text-moss-400">{esc(config.get('reference_cta'))} {icon('arrow-right', 'h-4 w-4')}</span>
      </a>""")

    return f"""<section id="config" class="py-24 sm:py-32">
  <div class="mx-auto max-w-screen px-6">
    {section_head(config)}
    <div class="mt-12 grid gap-5 md:grid-cols-2 xl:grid-cols-3">{''.join(cards)}</div>
  </div>
</section>"""


def render_enterprise(block: Block) -> str:
    cards = "".join(f"""<div class="reveal glass rounded-2xl p-6">
          {icon(c.get('icon'), 'h-5 w-5 text-moss-400')}
          <h3 class="mt-4 font-display text-[15.5px] font-semibold text-white">{esc(c.name)}</h3>
          {prose(c, 'mt-2 text-[13.5px] leading-relaxed text-slate-400')}
        </div>""" for c in block.items)

    return f"""<section id="enterprise" class="border-y border-white/[0.08] bg-white/[.012] py-24 sm:py-32">
  <div class="mx-auto max-w-screen px-6">
    <div class="grid gap-14 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
      <div class="reveal">
        <p class="eyebrow text-moss-400">{esc(block.get('eyebrow'))}</p>
        <h2 class="mt-4 font-display text-4xl font-semibold leading-[1.1] tracking-[-0.025em] text-white sm:text-[2.75rem]">{inline(block.get('heading'))}</h2>
        {prose(block, 'mt-5 text-[16.5px] leading-relaxed text-slate-400')}
        <div class="mt-8">{button(block.get('cta'), 'ghost')}</div>
      </div>
      <div class="grid gap-5 sm:grid-cols-2">{cards}</div>
    </div>
  </div>
</section>"""


def render_pricing(pricing: Block, table: Block) -> str:
    tiers = []
    for t in pricing.items:
        featured = t.flag("featured")
        monthly, annual = t.get("price"), t.get("price_annual") or t.get("price")
        amount = (f'<span data-price-monthly="{html.escape(monthly, quote=True)}" data-price-annual="{html.escape(annual, quote=True)}">'
                  f"{esc(monthly)}</span>")
        period = f'<span class="text-[13.5px] text-slate-500">{esc(t.get("period"))}</span>' if t.get("period") else ""
        note = '<span class="annual-note hidden">, billed yearly</span>' if annual != monthly else ""
        sub = (f'<p class="mt-1.5 text-[12.5px] text-slate-500">{esc(t.get("sub"))}'
               f'{note}</p>') if t.get("sub") else ""
        badge = (f'<div class="absolute -top-3 left-7 rounded-full border border-moss-400/30 bg-ink-950 px-3 py-1 '
                 f'font-mono text-[11px] uppercase tracking-[.14em] text-moss-400">{esc(t.get("badge"))}</div>') if t.get("badge") else ""
        label, href = split_pipe(t.get("cta"))
        cta_cls = ("mt-5 inline-flex items-center justify-center gap-2 rounded-xl bg-moss-500 px-5 py-3 text-[14px] "
                   "font-semibold text-ink-950 shadow-[0_10px_40px_-14px_rgba(16,185,129,.8)] transition hover:bg-moss-400"
                   if featured else
                   "mt-5 inline-flex items-center justify-center gap-2 rounded-xl border border-white/[0.12] bg-white/[.04] "
                   "px-5 py-3 text-[14px] font-semibold text-white transition hover:border-moss-400/40 hover:bg-white/[.08]")
        arrow = icon("arrow-right", "h-4 w-4" + ("" if featured else " text-moss-400"))
        feats = "".join(check(inline(f)) for f in t.list("features"))
        card_cls = ("reveal glass edge-lit relative flex flex-col rounded-2xl p-7 shadow-[0_0_80px_-30px_rgba(16,185,129,.45)]"
                    if featured else "reveal glass flex flex-col rounded-2xl p-7")

        tiers.append(f"""<div class="{card_cls}">
        {badge}
        <h3 class="font-display text-xl font-semibold text-white">{esc(t.name)}</h3>
        <p class="mt-2 text-[13.5px] text-slate-400">{esc(t.get('blurb'))}</p>
        <div class="mt-6 flex items-baseline gap-2">
          <span class="font-display text-4xl font-semibold tracking-tight text-white">{amount}</span>
          {period}
        </div>
        {sub}
        <a href="{href}" class="{cta_cls}">{esc(label)} {arrow}</a>
        <div class="mt-7 rule-glow"></div>
        <ul class="mt-7 space-y-3 text-[13.5px] {'text-slate-300' if featured else 'text-slate-400'}">{feats}</ul>
      </div>""")

    cols = table.list("columns")
    head = "".join(f'<th scope="col" class="px-6 py-4 font-display text-[15px] font-semibold '
                   f'{"text-moss-400" if i == 1 else "text-white"}">{esc(c)}</th>'
                   for i, c in enumerate(cols))
    body = []
    for row in table.list("rows"):
        cells = [c.strip() for c in row.split("|")]
        tds = []
        for cell in cells[1:]:
            if cell == "yes":
                tds.append(f'<td class="px-6 py-3.5">{icon("check", "h-4 w-4 text-moss-400")}</td>')
            elif cell == "no":
                tds.append('<td class="px-6 py-3.5 text-slate-600">&mdash;</td>')
            else:
                tds.append(f'<td class="px-6 py-3.5">{inline(cell)}</td>')
        body.append(f'<tr><th scope="row" class="px-6 py-3.5 font-normal text-slate-300">'
                    f"{inline(cells[0])}</th>{''.join(tds)}</tr>")

    return f"""<section id="pricing" class="py-24 sm:py-32">
  <div class="mx-auto max-w-screen px-6">
    <div class="reveal mx-auto max-w-2xl text-center">
      <p class="eyebrow text-moss-400">{esc(pricing.get('eyebrow'))}</p>
      <h2 class="mt-4 font-display text-4xl font-semibold leading-[1.1] tracking-[-0.025em] text-white sm:text-[2.75rem]">{inline(pricing.get('heading'))}</h2>
      {prose(pricing, 'mt-5 text-[16.5px] leading-relaxed text-slate-400')}
      <p class="mt-4 text-[14px] text-slate-500">{inline(pricing.get('note'))}</p>
    </div>

    <div class="reveal mt-9 flex items-center justify-center gap-3">
      <span id="lbl-monthly" class="text-[13.5px] font-medium text-white">Monthly</span>
      <button id="billing-toggle" role="switch" aria-checked="false" aria-label="Switch to annual billing" class="switch relative h-6 w-11 rounded-full border border-white/[0.12] bg-white/[.06] transition-colors">
        <span class="knob absolute left-0.5 top-0.5 h-[18px] w-[18px] rounded-full bg-slate-300 transition-transform duration-200"></span>
      </button>
      <span id="lbl-annual" class="dim text-[13.5px] font-medium">Annual</span>
      <span class="rounded-full border border-moss-400/25 bg-moss-500/10 px-2.5 py-0.5 font-mono text-[11px] text-moss-400">{esc(pricing.get('discount'))}</span>
    </div>

    <div class="mt-12 grid gap-5 md:grid-cols-2 xl:grid-cols-{len(pricing.items)}">{''.join(tiers)}</div>

    <div class="reveal glass mt-8 overflow-hidden rounded-2xl">
      <div class="overflow-x-auto">
        <table class="w-full min-w-[820px] text-left text-[14px]">
          <thead><tr class="border-b border-white/[0.08] text-slate-500">
            <th scope="col" class="px-6 py-4 font-medium">{esc(table.get('heading'))}</th>{head}
          </tr></thead>
          <tbody class="divide-y divide-white/[0.06] text-slate-400">{''.join(body)}</tbody>
        </table>
      </div>
    </div>

    <p class="reveal mt-6 text-center text-[13.5px] text-slate-500">{inline(pricing.get('footnote'))}</p>
  </div>
</section>"""


def render_faq(block: Block) -> str:
    items = "".join(f"""<details class="reveal glass rounded-xl px-6 py-5">
        <summary class="flex items-center justify-between gap-4">
          <span class="font-display text-[16px] font-medium text-white">{inline(q.name)}</span>
          {icon('chevron-down', 'chev h-[18px] w-[18px] shrink-0 text-slate-500')}
        </summary>
        {prose(q, 'mt-4 text-[14.5px] leading-relaxed text-slate-400')}
      </details>""" for q in block.items)

    return f"""<section id="faq" class="border-t border-white/[0.08] py-24 sm:py-32">
  <div class="mx-auto max-w-3xl px-6">
    <div class="reveal text-center">
      <p class="eyebrow text-moss-400">{esc(block.get('eyebrow'))}</p>
      <h2 class="mt-4 font-display text-4xl font-semibold tracking-[-0.025em] text-white">{esc(block.get('heading'))}</h2>
    </div>
    <div class="mt-12 space-y-3">{items}</div>
  </div>
</section>"""


def render_cta(block: Block) -> str:
    cmd = block.get("command")
    return f"""<section class="pb-24 sm:pb-32">
  <div class="mx-auto max-w-screen px-6">
    <div class="reveal glass edge-lit relative overflow-hidden rounded-3xl px-8 py-16 text-center sm:px-16">
      <div class="pointer-events-none absolute inset-x-0 -top-40 h-80" style="background: radial-gradient(420px 200px at 50% 100%, rgba(16,185,129,.22), transparent 70%);"></div>
      <h2 class="relative font-display text-4xl font-semibold leading-[1.1] tracking-[-0.025em] text-white sm:text-5xl">{inline(block.get('heading'))}</h2>
      <div class="relative mx-auto mt-5 max-w-xl">{prose(block, 'text-[16.5px] leading-relaxed text-slate-400')}</div>
      <div class="relative mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
        <div class="group flex items-center gap-3 rounded-xl border border-white/10 bg-[#070A0E]/80 px-5 py-3 font-mono text-[14px]">
          <span class="text-slate-600">$</span>
          <span class="text-slate-200">{esc(cmd)}</span>
          <button class="copy-inline ml-1 text-slate-500 transition hover:text-moss-400" data-copy="{html.escape(cmd, quote=True)}" aria-label="Copy install command">{icon('copy', 'h-4 w-4')}</button>
        </div>
        {button(block.get('button'), 'solid')}
      </div>
    </div>
  </div>
</section>"""


def render_footer(footer: Block, meta: Block) -> str:
    cols = "".join(f"""<div>
        <p class="eyebrow text-slate-600">{esc(col.name)}</p>
        <ul class="mt-4 space-y-2.5 text-[13.5px]">{''.join(
            f'<li><a href="{href}" class="text-slate-400 transition hover:text-white">{esc(label)}</a></li>'
            for label, href in (split_pipe(l) for l in col.list('links')))}</ul>
      </div>""" for col in footer.items)

    legal = "".join(f'<a href="{href}" class="transition hover:text-slate-400">{esc(label)}</a>'
                    for label, href in (split_pipe(l) for l in footer.list("legal")))

    return f"""<footer class="border-t border-white/[0.08] py-14">
  <div class="mx-auto max-w-screen px-6">
    <div class="grid gap-10 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
      <div>
        <div class="flex items-center gap-2.5">
          <svg width="22" height="22" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <path d="M16 3.2 27.4 9.6v12.8L16 28.8 4.6 22.4V9.6L16 3.2Z" stroke="#34D399" stroke-width="1.6" stroke-linejoin="round"/>
            <circle cx="16" cy="16" r="2.6" fill="#34D399"/>
          </svg>
          <span class="font-display text-[14.5px] font-semibold text-white">cargo<span class="text-moss-400">.green</span></span>
        </div>
        <p class="mt-4 max-w-xs text-[13.5px] leading-relaxed text-slate-500">{inline(footer.get('tagline'))}</p>
      </div>
      {cols}
    </div>
    <div class="mt-12 flex flex-col gap-4 border-t border-white/[0.08] pt-7 sm:flex-row sm:items-center sm:justify-between">
      <p class="font-mono text-[12px] text-slate-600">{esc(meta.get('copyright'))}</p>
      <div class="flex items-center gap-6 font-mono text-[12px] text-slate-600">
        {legal}
        <span class="flex items-center gap-1.5"><span class="h-1.5 w-1.5 rounded-full bg-moss-400"></span>{esc(footer.get('status'))}</span>
      </div>
    </div>
  </div>
</footer>"""


# ─────────────────────────────  assembly  ─────────────────────────────

def build(out_path: Path) -> Path:
    sections = parse(CONTENT.read_text(encoding="utf-8"))

    required = ["meta", "nav", "hero", "terminal", "registries", "problem", "answer", "ci",
                "install", "commands", "how", "hits", "engines", "config", "enterprise",
                "pricing", "table", "faq", "cta", "footer"]
    missing = [name for name in required if name not in sections]
    if missing:
        raise SystemExit(f"content.md is missing section(s): {', '.join('## ' + m for m in missing)}")

    S = sections
    meta, hero, term = S["meta"], S["hero"], S["terminal"]

    lines = [split_pipe(l, 2) for l in term.list("lines")]
    line_js = ",\n    ".join(f'["{kind}", {kind_text!r}]'.replace("'", '"')
                             for kind, kind_text in ((k, t) for k, t in lines))

    config_js = f"""window.CG = {{
    lines: [
    {line_js}
    ],
    total: {hero.get('crate_total', '0')},
    cached: {hero.get('crates_cached', '0')},
    wall: {hero.get('wall_clock', '0')}
  }};"""

    body = "\n\n".join([
        render_nav(S["nav"], meta),
        '<main id="main">',
        render_hero(hero, term),
        render_registries(S["registries"]),
        render_problem(S["problem"], S["answer"], S["ci"]),
        render_install(S["install"], S["commands"]),
        render_how(S["how"], S["hits"], S["engines"]),
        render_config(S["config"]),
        render_enterprise(S["enterprise"]),
        render_pricing(S["pricing"], S["table"]),
        render_faq(S["faq"]),
        render_cta(S["cta"]),
        "</main>",
        render_footer(S["footer"], meta),
    ])

    doc = f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(meta.get('title'))}</title>
<meta name="description" content="{html.escape(meta.get('description'), quote=True)}" />
<meta name="theme-color" content="#05070A" />

<meta property="og:title" content="{html.escape(meta.get('og_title'), quote=True)}" />
<meta property="og:description" content="{html.escape(meta.get('og_description'), quote=True)}" />
<meta property="og:type" content="website" />
<meta property="og:url" content="{meta.get('url')}" />

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:ital,wght@0,400..700;1,400..700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">

<script src="https://cdn.tailwindcss.com"></script>
<script>
{(ASSETS / 'tailwind.config.js').read_text(encoding='utf-8').rstrip()}
</script>

<style>
{(ASSETS / 'theme.css').read_text(encoding='utf-8').rstrip()}
</style>
</head>

<body class="font-sans text-slate-400 antialiased">
<div class="bg-stage"></div>
<div class="bg-grid"></div>
<div class="bg-grain"></div>

<a href="#main" class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:rounded-lg focus:bg-moss-500 focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-ink-950">Skip to content</a>

{body}

<script>
  {config_js}
</script>
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
<script>
{(ASSETS / 'app.js').read_text(encoding='utf-8').rstrip()}
</script>
</body>
</html>
"""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(doc, encoding="utf-8")
    return out_path


class DevServer(http.server.ThreadingHTTPServer):
    """Serves without shouting when a browser hangs up mid-response."""

    def handle_error(self, request, client_address) -> None:
        kind = sys.exc_info()[0]
        if kind is not None and issubclass(kind, (BrokenPipeError, ConnectionResetError)):
            return  # the browser navigated away or cancelled; not our problem
        super().handle_error(request, client_address)


class DevHandler(http.server.SimpleHTTPRequestHandler):
    """Quiet, no-cache handler so a reload always shows the latest build."""

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def log_message(self, format, *args) -> None:
        code = str(args[1]) if len(args) > 1 else ""
        if code.startswith(("4", "5")):
            sys.stderr.write(f"  {args[0]} -> {code}\n")


def open_browser(url: str) -> str:
    """xdg-open on Linux, open on macOS. Returns whichever one worked."""
    for command in ("xdg-open", "open"):
        try:
            subprocess.Popen([command, url],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return command
        except OSError:
            continue
    return ""


def stamp(paths) -> dict:
    return {p: p.stat().st_mtime for p in paths if p.exists()}


def watch(out_path: Path) -> None:
    """Build, serve, open a browser, and rebuild on every change."""
    try:
        build(out_path)
    except SystemExit as err:
        print(err, file=sys.stderr)  # serve anyway so the error is visible in the browser
    stamps = stamp(SOURCES)

    root = out_path.parent
    root.mkdir(parents=True, exist_ok=True)
    handler = functools.partial(DevHandler, directory=str(root))
    try:
        # Binding here means the port is already listening when the browser opens.
        httpd = DevServer(("127.0.0.1", PORT), handler)
    except OSError as err:
        raise SystemExit(f"cannot serve on port {PORT}: {err}")

    opener = open_browser(URL)
    server_thread = threading.Thread(target=httpd.serve_forever, name="http", daemon=True)
    server_thread.start()

    print(f"serving {root.name}/ at {URL}")
    print(f"watching {CONTENT.name} and {ASSETS.name}/ — ctrl-c to stop")
    if not opener:
        print(f"could not open a browser — visit {URL}")

    try:
        while True:
            current = stamp(SOURCES)
            if current != stamps:
                stamps = current
                try:
                    build(out_path)
                    print(f"[{time.strftime('%H:%M:%S')}] built {out_path.relative_to(ROOT)}")
                except SystemExit as err:
                    print(f"[{time.strftime('%H:%M:%S')}] {err}")
                except Exception as err:  # keep the watcher alive through typos
                    print(f"[{time.strftime('%H:%M:%S')}] build failed: {err}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nstopping")
    finally:
        httpd.shutdown()
        httpd.server_close()
        server_thread.join(timeout=2)


def main() -> None:
    args = sys.argv[1:]
    out = DEFAULT_OUT
    if "--out" in args:
        out = Path(args[args.index("--out") + 1]).resolve()
    if "--watch" in args:
        watch(out)
    else:
        path = build(out)
        size = path.stat().st_size
        print(f"built {path} ({size // 1024} KB)")


if __name__ == "__main__":
    main()
