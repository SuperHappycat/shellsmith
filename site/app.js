(() => {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const tt = (t) => esc(t).replace(/`([^`]+)`/g, "<code>$1</code>");
  let stages = [], results = null, repo = null, pollTimer = null;

  // ---------------------------------------------------------------- data
  async function getJSON(url) {
    const r = await fetch(`${url}?t=${Date.now()}`, { cache: "no-store" });
    if (!r.ok) throw new Error(url + " " + r.status);
    return r.json();
  }

  function inferRepo() {
    if (results && results.repository) return results.repository;
    const host = location.hostname;
    if (host.endsWith(".github.io")) {
      const owner = host.split(".")[0];
      const first = location.pathname.split("/").filter(Boolean)[0];
      return `${owner}/${first || host}`;
    }
    return null;
  }

  function statusOf(stage) {
    const r = (results?.results || []).find((x) => x.slug === stage.slug);
    if (r && r.passed) return "passed";
    if (r && !r.passed) return "failed";
    if (results?.current === stage.slug || (!results?.current && stage.number === 1 && !results?.passed)) return "current";
    return "locked";
  }
  const resultOf = (slug) => (results?.results || []).find((x) => x.slug === slug);
  const currentStage = () => stages.find((s) => ["current", "failed"].includes(statusOf(s)));

  // ---------------------------------------------------------------- render
  function renderHeader() {
    const passed = results?.passed || 0;
    $("meter-fill").style.width = `${(100 * passed) / stages.length}%`;
    $("meter-text").textContent = `${passed} / ${stages.length}`;
    $("repo").innerHTML = repo
      ? `<a href="https://github.com/${esc(repo)}" target="_blank" rel="noopener">${esc(repo)}</a>`
      : "not published yet";
    $("updated").textContent = results?.generated_at
      ? `results from ${ago(results.generated_at)}` + (results.seconds ? ` · tests took ${results.seconds}s` : "") +
        (results.seed ? ` · replay with ./smith test --seed ${results.seed}` : "")
      : "no test run yet";
  }

  function renderSide(selSlug) {
    const chapters = [];
    for (const s of stages) {
      let ch = chapters.find((c) => c.name === s.chapter);
      if (!ch) chapters.push((ch = { name: s.chapter, items: [] }));
      ch.items.push(s);
    }
    $("side").innerHTML = chapters.map((ch) => {
      const done = ch.items.filter((s) => statusOf(s) === "passed").length;
      return `<div class="chapter"><h4><span>${esc(ch.name)}</span><span>${done}/${ch.items.length}</span></h4><ol>` +
        ch.items.map((s) => {
          const st = statusOf(s);
          const glyph = st === "passed" ? "✓" : st === "failed" ? "!" : "";
          return `<li><a href="#/stage/${s.slug}" class="${st}${s.slug === selSlug ? " sel" : ""}">` +
            `<span class="n">${s.number}</span><span class="dot">${glyph}</span><span>${tt(s.title)}</span></a></li>`;
        }).join("") + "</ol></div>";
    }).join("");
  }

  function renderHome() {
    const cur = currentStage();
    const passed = results?.passed || 0;
    const done = passed === stages.length;
    $("stage").innerHTML = `<div class="hero">
      <div class="eyebrow"><span class="chip">build your own shell</span></div>
      <h1>${done ? "You built a shell." : "Build a real shell, one stage at a time."}</h1>
      <div class="big">${passed}<span style="color:var(--ink-3);font-size:.45em"> / ${stages.length} stages</span></div>
      <p>You write the code; the tester types into your shell through a real terminal and checks what comes back.
      Every <code>./smith submit</code> pushes to GitHub, the tests run there, and this page updates.</p>
      ${results?.build_error ? `<div class="note err"><strong>The last submission didn't compile</strong><pre>${esc(results.build_error)}</pre></div>` : ""}
      ${cur ? `<p><strong>Up next:</strong> stage ${cur.number} · ${tt(cur.title)}</p>
      <a class="cta" href="#/stage/${cur.slug}">Open stage ${cur.number} →</a>` : ""}
    </div>`;
    renderSide(null);
    $("logpanel").hidden = true;
  }

  function renderStage(slug) {
    const s = stages.find((x) => x.slug === slug);
    if (!s) return renderHome();
    const st = statusOf(s);
    const r = resultOf(slug);
    const chip = { passed: '<span class="chip ok">passed</span>', failed: '<span class="chip bad">failing</span>',
      current: '<span class="chip cur">current stage</span>', locked: '<span class="chip">locked</span>' }[st];
    const prev = stages[s.number - 2], next = stages[s.number];
    $("stage").innerHTML = `
      <div class="eyebrow"><span class="chip">Stage ${s.number} of ${stages.length}</span>
        <span class="chip">${esc(s.chapter)}</span><span class="chip">${esc(s.difficulty)}</span>${chip}</div>
      <h1>${tt(s.title)}</h1>
      ${s.html}
      ${st === "locked" ? '<div class="note locked-note">You can read ahead, but the tester will reach this stage only after the earlier ones pass.</div>' : ""}
      ${st === "failed" && r ? `<div class="note err"><strong>Last run failed here</strong><pre>${esc(r.error)}</pre></div>` : ""}
      ${results?.build_error && st === "current" ? `<div class="note err"><strong>Your shell didn't compile, so no tests ran</strong><pre>${esc(results.build_error)}</pre></div>` : ""}
      <div class="nav">${prev ? `<a href="#/stage/${prev.slug}">← ${tt(prev.title)}</a>` : "<span></span>"}
        ${next ? `<a href="#/stage/${next.slug}">${tt(next.title)} →</a>` : ""}</div>`;
    renderSide(slug);
    if (r) {
      $("logpanel").hidden = false;
      $("logtitle").textContent = `stage ${s.number} · ${r.passed ? "passed" : "failed"} in ${r.seconds}s` +
        (results.commit ? ` · commit ${results.commit.slice(0, 7)}` : "");
      $("log").innerHTML = r.log.map((l) => `<span class="k-${l.kind}">${esc(l.text)}</span>`).join("\n");
    } else {
      $("logpanel").hidden = true;
    }
    window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" });
  }

  function route() {
    const m = location.hash.match(/^#\/stage\/([\w-]+)/);
    renderHeader();
    m ? renderStage(m[1]) : renderHome();
  }

  // ---------------------------------------------------------------- live GitHub status
  function ago(iso) {
    const s = Math.max(1, (Date.now() - new Date(iso)) / 1000);
    if (s < 60) return `${Math.round(s)}s ago`;
    if (s < 3600) return `${Math.round(s / 60)} min ago`;
    if (s < 86400) return `${Math.round(s / 3600)} h ago`;
    return `${Math.round(s / 86400)} d ago`;
  }

  async function poll() {
    if (!repo) return;
    let runs;
    try {
      const data = await getJSON(`https://api.github.com/repos/${repo}/actions/workflows/smith.yml/runs`);
      runs = data.workflow_runs || [];
    } catch { return; }
    $("runs-panel").hidden = !runs.length;
    $("runs").innerHTML = runs.slice(0, 8).map((r) => {
      const cls = r.status !== "completed" ? "running" : r.conclusion;
      const msg = (r.head_commit?.message || r.display_title || "").split("\n")[0];
      return `<li><span class="s ${esc(cls)}"></span><a href="${esc(r.html_url)}" target="_blank" rel="noopener">` +
        `<code>${esc(r.head_sha.slice(0, 7))}</code> ${esc(msg)}</a><time>${ago(r.created_at)}</time></li>`;
    }).join("");

    const latest = runs[0];
    const live = $("live");
    let next = 120000;
    if (latest && latest.status !== "completed") {
      live.hidden = false; live.className = "live";
      live.innerHTML = `<span class="pulse"></span><span>Testing <code>${latest.head_sha.slice(0, 7)}</code> on GitHub… (${esc(latest.status.replace("_", " "))})</span>`;
      next = 10000;
    } else if (latest && results && latest.head_sha !== results.commit && Date.now() - new Date(latest.updated_at) < 15 * 60000) {
      live.hidden = false; live.className = "live done";
      live.innerHTML = `<span class="pulse"></span><span>Tests for <code>${latest.head_sha.slice(0, 7)}</code> finished; publishing results…</span><button id="reload">Refresh now</button>`;
      $("reload").onclick = refreshResults;
      next = 8000;
      refreshResults(true);
    } else {
      live.hidden = true;
    }
    clearTimeout(pollTimer);
    pollTimer = setTimeout(poll, next);
  }

  async function refreshResults(quiet) {
    try {
      const fresh = await getJSON("results.json");
      if (!results || fresh.commit !== results.commit || fresh.generated_at !== results.generated_at) {
        results = fresh; route();
      } else if (quiet !== true) { route(); }
    } catch { /* not published yet */ }
  }

  // ---------------------------------------------------------------- boot
  async function boot() {
    stages = await getJSON("stages.json");
    try { results = await getJSON("results.json"); } catch { results = null; }
    repo = inferRepo();
    window.addEventListener("hashchange", route);
    route();
    poll();
  }
  boot().catch((e) => { $("stage").innerHTML = `<p>Could not load the course: ${esc(e.message)}</p>`; });
})();
