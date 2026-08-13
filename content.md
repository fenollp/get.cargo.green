# cargo.green landing page

content.md              all copy and structured content — the file you edit
build.py                parser + renderers; owns the markup
check.py                post-build sanity checks
assets/theme.css        custom CSS: background layers, glass, JS-toggled states
assets/app.js           nav, scroll reveal, tabs, copy buttons, pricing toggle, terminal replay
assets/tailwind.config  colour and font tokens
dist/index.html         generated — never edit this by hand

Format, in three rules:

1. `## key` starts a section. `### Name` starts a repeated item inside it.
2. `field: value` sets a field. A field with no value followed by `- ` lines is a list.
3. Anything else is prose. `**bold**`, `` `code` ``, `[links](url)` and `{highlight}` work.


Inline formatting in prose and fields: `**bold**`, `*emphasis*`, `` `code` ``, `[links](url)`, and
`{braces}` for the highlighted value in a feature line or the gradient word in a headline.

Values that contain a `|` are two-part — `Label | href` for links and buttons, and one table row
per line.

Fenced code blocks belong to the item that contains them; `sh`, `toml` and `yaml` get syntax
colouring. That's what the install tabs are.

`default_tab:` in `## install` decides which code tab opens first, by name.

The pricing toggle reads `price` and `price_annual` off each tier via data attributes, so adding a
fifth tier needs no JavaScript changes. Tiers without an annual price simply don't change when
toggled.

The hero terminal replay is driven by `## terminal`. Each line is `kind | text`, where kind is one
of `cmd`, `dim`, `hit`, `run`, `ok`, `blank` — those control colour and pacing. The counters below
it come from `crate_total`, `crates_cached` and `wall_clock` in `## hero`.

## meta
title: cargo.green — Rust builds that never start cold
description: cargo-green runs every rustc call through BuildKit or Nix, so each crate becomes a cacheable, shareable build step. Compile once — reuse across your team, your CI, and every machine.
og_title: cargo.green — Rust builds that never start cold
og_description: Crate-level remote build cache for Rust, backed by BuildKit or Nix and any registry you already run.
url: https://cargo.green
repo: https://github.com/fenollp/supergreen
sales_email: sales@cargo.green
copyright: © 2026 cargo.green · CLI licensed AGPL-3.0

## nav
cta: Start free | #pricing
links:
  - Why | #problem
  - Install | #install
  - How it works | #how
  - Configuration | #config
  - Enterprise | #enterprise
  - Pricing | #pricing

## hero
badge: Crate-level caching, powered by BuildKit or Nix | #how
headline: Rust builds that never start {cold}
cta_primary: Install the CLI | #install
cta_secondary: Talk to sales | #enterprise
repo_label: acme/payments-api — main
registry_label: ghcr.io
caption: Illustrative replay · same workspace, cold build: 8m 42s
crate_total: 419
crates_cached: 412
wall_clock: 11.3

`cargo green` sends every `rustc` call to a real build engine — BuildKit or Nix — so each crate
becomes its own individually cached build step. Compile a dependency once, on a laptop or a big
remote box or CI, and every other machine pulls the result instead of rebuilding it.

### Cache granularity
value: Per crate

### Build engine
value: BuildKit or Nix

### Cache store
value: Any OCI registry

## terminal
lines:
  - cmd | $ cargo green build --release
  - dim | #1  [internal] load build definition
  - dim | #2  preparing pinned build environment
  - dim | #3  streaming cache from ghcr.io/acme/payments-api
  - blank |
  - hit | #12  CACHED   rustc   serde v1.0.219
  - hit | #13  CACHED   rustc   tokio v1.46.0
  - hit | #14  CACHED   rustc   clap v4.5.45
  - hit | #15  CACHED   rustc   reqwest v0.12.9
  - hit | #16  CACHED   rustc   hyper v1.5.1
  - hit | #17  CACHED   rustc   sqlx-core v0.8.2
  - dim |      … 406 more crates restored from cache
  - blank |
  - run | #414 rustc   payments-core v0.4.0        2.1s
  - run | #415 rustc   payments-http v0.4.0        3.4s
  - run | #416 rustc   payments-api  v0.4.0        4.8s
  - dim | => exporting cache to ghcr.io/acme/payments-api
  - blank |
  - ok |     Finished `release` profile in 11.3s

## registries
label: Stores cache where you already keep artifacts
items:
  - GitHub Container Registry
  - Amazon ECR
  - Google Artifact Registry
  - Harbor
  - Quay
  - Docker Hub
  - Nix binary cache

## problem
eyebrow: The problem
heading: Your team compiles the same code hundreds of times a day.

Every Rust build starts from scratch somewhere. Your laptop remembers *your* last build — your
teammate's laptop doesn't, and CI forgets everything the moment a job ends. So the same `serde`,
the same `tokio`, the same four hundred dependencies get rebuilt again and again: on every
machine, on every branch, on every pull request. That is minutes per build, hours per engineer
per week, and a CI bill for recompiling code nobody changed.

### Local caches don't travel
icon: hard-drive

`target/` lives and dies on one machine. A fresh checkout, a new worktree, or a CI runner means
starting over from zero.

### Shared caches are brittle
icon: unplug

Tools that ship raw compiled artifacts around tend to miss — or worse, misbehave — when paths,
toolchains, or system libraries differ between machines.

### CI caches are all-or-nothing
icon: archive-restore

Most CI caches key one big archive on your `Cargo.lock`. Bump a single dependency and the whole
thing misses — after your job already spent minutes downloading and unpacking it.

## answer
eyebrow: The answer
heading: Give the compilation to a real build engine.
kicker: Build once, anywhere. Reuse everywhere.
points:
  - Crate-level granularity — one changed crate rebuilds one crate
  - Cache keys that match across machines and CI runners
  - Works with proc-macros, build scripts, and linking
  - Offload compilation to any remote machine over SSH
  - No new build system — it is still `cargo`

cargo-green turns each `rustc` call into its own build step and hands it to BuildKit or Nix. Each
step is sealed off from whatever is unique about your machine, so the same crate produces the same
key everywhere — and the cache actually hits. Results live as ordinary content in a registry you
control, shared by every developer and every CI job.

## ci
eyebrow: Day one
heading: Every CI job gets faster immediately.

There is no cache to warm up and no lockfile to match. The first job you run against a shared
cache already skips most of its work.

### Not keyed on Cargo.lock
icon: unlink

Each crate is cached on its own. Bumping one dependency invalidates that crate and whatever
depends on it — not the other four hundred.

### Fetched as the build runs
icon: download-cloud

Cached crates stream in while compilation is already underway, instead of a restore step that
blocks the job before anything starts.

### No save/restore steps
icon: scissors

Delete the cache actions from your workflow. Nothing to tar, upload, or expire — and nothing to
rate-limit you on a busy morning.

## install
eyebrow: Install & use
heading: One install. One extra word.
link: Full installation docs | https://github.com/fenollp/supergreen#installation
default_tab: build

cargo-green is a cargo plugin, not a replacement. Your commands, your `Cargo.toml`, your CI —
unchanged.

### build

```sh
# Once: start from a clean slate
cargo clean

# Then use cargo, with one extra word
cargo green build
cargo green test
cargo green clippy

# Like it? Make it invisible
alias cargo='cargo green'

# Pick your engine: docker (default), podman, or nix
export CARGOGREEN_RUNNER=nix

# Plain `cargo build` keeps working afterwards.
```

### install

```sh
# From crates.io
cargo install cargo-green

# …or track the latest from git
cargo install --locked --force \
  --git https://github.com/fenollp/supergreen.git cargo-green

# Make sure $CARGO_HOME/bin is on your $PATH
which cargo-green

# Needs one build engine on the machine:
# a docker or podman client, or nix.
```

### remote

```sh
# Compile on the 96-core box, run the binary locally
DOCKER_HOST=ssh://build-farm-01 cargo green test

# Same idea with the Nix engine
CARGOGREEN_RUNNER=nix NIX_SSHOPTS="-A" \
  cargo green build --release

# Laptops stay quiet. Fans stay off.
```

### share cache

```toml
# Cargo.toml
[package.metadata.green]
cache-images = [
  "docker-image://ghcr.io/acme/payments-api",
]
cache-from-images = [
  "docker-image://ghcr.io/acme/global-cache",
]

# Push the cache for everyone else
cargo green supergreen push
```

### CI

```yaml
# .github/workflows/ci.yml
- run: cargo install cargo-green
- run: cargo green test
  env:
    CARGOGREEN_CACHE_IMAGES: docker-image://ghcr.io/acme/api

# Warm the cache for offline / air-gapped runners
- run: cargo green supergreen sync
```

## commands
heading: The command surface

Everything else lives under one subcommand, so nothing else pollutes your cargo namespace.

### cargo green supergreen setup
desc: Create the required symlinks

### cargo green supergreen env
desc: Show the values actually in use

### cargo green supergreen doc
desc: Documentation for those values

### cargo green supergreen sync
desc: Pull everything, for offline use

### cargo green supergreen push
desc: Push the shared cache, all tags

### cargo green supergreen builder
desc: Manage the local or remote builder

### cargo green supergreen show-rust-base
desc: Inspect the build environment in use

## how
eyebrow: How it works
heading: A wrapper, a build graph, a shared cache.

cargo-green slots in as the compiler wrapper cargo already supports. Four things happen between
`cargo green build` and your binary.

### Wrap
icon: git-fork

`cargo green` sets `$RUSTC_WRAPPER` and calls cargo. Cargo still resolves, still schedules, still
owns your build.

### Translate
icon: file-code-2

Every `rustc` call and build-script run becomes its own sealed build step, pinned to your exact
toolchain.

### Build
icon: cpu

BuildKit or Nix runs the graph with full parallelism — on your machine, or on any remote one you
point it at.

### Cache & share
icon: database-zap

Results are cached per crate and pulled in progressively as the build runs. Your team and your CI
read the same cache.

## hits
icon: lock
heading: Why the cache actually hits
points:
  - The build environment is pinned, not whatever happens to be installed
  - Paths are normalized, so your home directory never leaks into a key
  - Git dependencies are pinned to an exact revision
  - Build outputs are made reproducible, down to file timestamps
footnote: The same properties make a build auditable: you can show exactly what produced a binary, and rebuild it later to prove it.

A shared cache is only worth having if it hits on someone else's machine. cargo-green removes the
things that normally make two identical builds look different:

## engines
icon: split
heading: Two engines, one cache
footnote: No daemon on the laptop is required either way — point cargo-green at a shared machine and let it do the work.

Pick whichever engine your team already trusts. The workflow, the commands, and the cached results
are the same either way — teams can even mix both and still share hits.

### BuildKit
icon: container
config: runner = "docker" | "podman"

Through the docker or podman client you already have. Cache lives in any OCI registry.

### Nix
icon: hexagon
config: runner = "nix"

For teams already on Nix. Cache lives in a binary cache, with the same crate-level granularity.

## config
eyebrow: Configuration
heading: Defaults that work. Knobs when you need them.
link: Full reference | https://github.com/fenollp/supergreen#configuration
reference_title: Every option, documented
reference_body: Each setting has a page of its own in the README, with defaults, examples, and the environment variable that overrides it.
reference_cta: Read the configuration reference
reference_href: https://github.com/fenollp/supergreen#configuration

Set anything in `[package.metadata.green]` in your `Cargo.toml`, or with a `$CARGOGREEN_*`
environment variable — env vars win, which is what you want in CI.

### Cache & sharing
icon: database
href: https://github.com/fenollp/supergreen#caching
chips:
  - cache-images
  - cache-from-images
  - cache-to-images
  - registry-mirrors

Where cached crates are read from and written to, so a team, a fork, and CI can all draw on the
same pool.

### Build engine
icon: split
href: https://github.com/fenollp/supergreen#cargogreen_runner
chips:
  - runner
  - $DOCKER_HOST
  - $BUILDX_BUILDER

Which engine compiles your crates, and where it runs — docker, podman, or Nix, locally or on a
remote machine.

### Build environment
icon: box
href: https://github.com/fenollp/supergreen#cargogreen_base_image
chips:
  - base-image
  - with-network
  - components
  - add.apt
  - add.apk

What sits inside the sandbox each crate compiles in: base image, system packages, toolchain
components, network access.

### Diagnostics
icon: scroll-text
href: https://github.com/fenollp/supergreen#cargogreen_log
chips:
  - $CARGOGREEN_LOG
  - $CARGOGREEN_LOG_PATH
  - supergreen env

Turn on logging when a build surprises you, and see exactly which values cargo-green resolved and
used.

### Artifacts & provenance
icon: file-output
href: https://github.com/fenollp/supergreen#cargogreen_final_path
chips:
  - final-path

Export the finished build as a single file you can archive, review, or rebuild somewhere else
entirely.

## enterprise
eyebrow: Enterprise
heading: Runs inside your perimeter.
cta: Book a security review | #pricing

Nothing about the cache requires our servers. It is ordinary content in a registry or binary
cache, which means it can live wherever your compliance posture requires: your own cloud account,
your own VPC, or an air-gapped network with no egress at all.

### SOC 2 Type II
icon: shield-check

Annual audit, report available under NDA, plus a DPA and standard contractual clauses for EU data.

### SSO, SCIM & scoped tokens
icon: key-round

SAML and OIDC single sign-on, directory-synced groups, per-project read/write tokens with
rotation.

### BYOC & air-gapped
icon: cloud-cog

Bring your own cloud account and registry, run single-tenant, or sync a cache into a network with
no egress.

### 99.9% uptime SLA
icon: activity

Written availability commitment, a named support engineer, and a shared Slack channel with the
maintainers.

### Audit logs & attribution
icon: file-search

See who built what, when, and from which revision — and which teams are driving build spend,
before finance asks.

### Open source core
icon: scale

The CLI is AGPL-3.0 and auditable line by line. Self-hosted control plane and commercial licensing
available where the AGPL doesn't fit.

## pricing
eyebrow: Pricing
heading: The CLI is free, forever.
note: Your CI jobs and your coding agents build too. Charging by headcount stopped making sense.
discount: −20%
footnote: Soft limits, not hard walls. A burst month won't break your build — we'll get in touch if it becomes the new normal.

Point cargo-green at a registry you already run and pay nothing, ever. The hosted cache is for
teams who would rather not operate one — priced on what you actually use, per organization rather
than per developer.

### Developer
blurb: Individuals, side projects, open source.
price: $0
period: free forever
cta: Install the CLI | #install
features:
  - Unlimited local & remote builds
  - Bring your own registry — no limits
  - {500K} cache requests / month
  - {20 GB} cache storage
  - 50 core-hours of remote builds
  - 1 project, 7-day retention
  - Community support on GitHub

### Team
blurb: Startups shipping Rust every day.
price: $49
price_annual: $39
period: / month
sub: Per organization
badge: Most popular
featured: true
cta: Start 14-day trial | #
features:
  - Everything in Developer, plus:
  - {10 million} cache requests / month
  - {500 GB} cache storage
  - 200 core-hours of remote builds
  - Overage at $0.15/GB, $0.10/core-hour
  - Unlimited projects and seats
  - Prewarmed cache for popular crates
  - Build analytics: what's slow, what missed
  - Priority email support, 1 business day

### Scale
blurb: Engineering orgs of 20–100 developers.
price: $400
price_annual: $320
period: / month
sub: Per organization
cta: Start 14-day trial | #
features:
  - Everything in Team, plus:
  - {100 million} cache requests / month
  - {2 TB} cache storage
  - 2,000 core-hours of remote builds
  - Warm runners: pull requests never cold-start
  - Spend attribution per team and repo
  - 90-day retention, configurable per project
  - Shared Slack channel

### Enterprise
blurb: Platform and security orgs with their own rules.
price: Custom
sub: Annual contract, invoice billing
cta: Contact us | mailto:sales@cargo.green
features:
  - Everything in Scale, plus:
  - Unlimited requests, custom storage and compute
  - Self-hosted control plane, BYOC, or air-gapped
  - SSO/SAML, SCIM, audit log export
  - SOC 2 Type II report, DPA, security review
  - 99.9% uptime SLA
  - Dedicated support engineer
  - Commercial licensing & roadmap input

## table
heading: Compare plans
columns:
  - Developer
  - Team
  - Scale
  - Enterprise
rows:
  - cargo-green CLI (AGPL-3.0) | Unlimited | Unlimited | Unlimited | Unlimited
  - BuildKit & Nix engines | yes | yes | yes | yes
  - Bring your own registry | yes | yes | yes | yes
  - Cache requests / month | 500K | {10M} | {100M} | Unlimited
  - Cache storage | 20 GB | {500 GB} | {2 TB} | Custom
  - Remote build core-hours | 50 | 200 | 2,000 | Custom
  - Retention | 7 days | 30 days | 90 days | Custom
  - Projects / seats | 1 / 1 | Unlimited | Unlimited | Unlimited
  - Prewarmed crate cache | no | yes | yes | yes
  - Build analytics | no | yes | yes | yes
  - Spend attribution | no | no | yes | yes
  - SSO/SAML & SCIM | no | no | no | yes
  - Self-hosted / air-gapped | no | no | no | yes
  - Uptime SLA | no | no | no | 99.9%
  - Support | Community | Priority email | Shared Slack | Dedicated engineer

## faq
eyebrow: FAQ
heading: Before you install

### Do I have to change my workflow?

One `cargo clean` when you switch over, then `cargo green build` behaves like `cargo build` and
produces the same files. Plain `cargo build` keeps working afterwards, so you can back out at any
time.

### Does this lock us in?

No. The CLI is AGPL-3.0 open source, and the cache is ordinary content in a registry or binary
cache you choose. Swap in your own with one line of config and everything keeps working.

### Do we need Docker on every developer machine?

No. You need one engine available: a `docker` or `podman` client, or Nix. And the machine that
actually compiles doesn't have to be the laptop — point cargo-green at a shared build machine and
laptops just orchestrate.

### How is this different from sccache or cargo-chef?

sccache caches compiler output but expects matching paths and environments across machines, can't
cache linking, struggles with proc-macros, and gets chatty enough with a remote backend that
checking the cache can cost more than compiling. cargo-chef caches your dependency tree as Docker
layers, so one dependency bump rebuilds all of them. cargo-green compiles inside sealed, pinned
build steps: keys match across machines, granularity is per crate, and a partial match still
helps. A survey of the whole landscape lives in the
[alternatives section](https://github.com/fenollp/supergreen#alternatives) of the README.

### BuildKit or Nix — which should we pick?

Whichever your team already runs. Most teams have a docker or podman client on hand, so that is
the default. If you are already on Nix, use Nix and keep your existing binary cache. The commands,
the configuration, and the cached results are the same either way, and both engines can share
hits.

### How long before CI gets faster?

The first job. There is no lockfile to match and no archive to restore — cached crates are pulled
in progressively while compilation is already running, so a job benefits from whatever is in the
cache at the moment it starts. A branch that bumps a dependency still reuses everything else.

### Can it run with no network access?

Yes. `cargo green supergreen sync` pulls every image and crate you need up front, and builds
default to no network. Air-gapped environments are a supported Enterprise deployment.

### What counts as a cache request?

One read or write of a cached build step. A warm build of a 400-crate workspace is roughly 400
requests, so 10 million covers a busy team's laptops and CI with room to spare. Usage is visible
in the dashboard before it ever appears on an invoice.

## cta
heading: Stop paying for the same build twice.
command: cargo install cargo-green
button: Talk to sales | mailto:sales@cargo.green

Install the CLI, run `cargo green build`, and watch the second machine finish in seconds.

## footer
tagline: A cached, remote-ready builder for Rust projects. Part of the [supergreen](https://github.com/fenollp/supergreen) project.
status: All systems operational
legal:
  - Privacy | #
  - Terms | #
  - DPA | #

### Product
links:
  - Why cargo-green | #problem
  - Install | #install
  - How it works | #how
  - Pricing | #pricing

### Docs
links:
  - Configuration | https://github.com/fenollp/supergreen#configuration
  - Remote execution | https://github.com/fenollp/supergreen#remote-execution
  - Caching | https://github.com/fenollp/supergreen#caching
  - Alternatives | https://github.com/fenollp/supergreen#alternatives

### Company
links:
  - GitHub | https://github.com/fenollp/supergreen
  - Contact sales | mailto:sales@cargo.green
  - Security | #enterprise
  - Status | #
