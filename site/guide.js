// "Start here" guide: how to get going with the terminal (CLI), with desktop apps, or in the browser.
(() => {
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  const TABS = [
    { id: "cli", label: "Terminal", sub: "fastest feedback" },
    { id: "desktop", label: "Desktop apps", sub: "no terminal needed" },
    { id: "browser", label: "Browser", sub: "nothing to install" },
  ];
  const OSES = [{ id: "mac", label: "macOS" }, { id: "win", label: "Windows" }, { id: "linux", label: "Linux" }];

  let os = guessOS();

  function guessOS() {
    try {
      const saved = localStorage.getItem("smith-os");
      if (saved) return saved;
    } catch { /* storage unavailable */ }
    const p = (navigator.userAgentData?.platform || navigator.platform || "").toLowerCase();
    if (p.includes("win")) return "win";
    if (p.includes("mac")) return "mac";
    return "linux";
  }

  const code = (text) => `<div class="codebox"><pre><code>${esc(text)}</code></pre>` +
    `<button class="copy" type="button" data-copy="${esc(text)}">Copy</button></div>`;

  const step = (title, body) => `<li class="gstep"><h3>${title}</h3>${body}</li>`;

  const note = (kind, html) => `<div class="gnote ${kind}">${html}</div>`;

  // ------------------------------------------------------------------ Terminal
  function cli(ctx) {
    const install = {
      mac: `<p>Open <strong>Terminal</strong> (⌘ Space, type "Terminal"). Install Apple's developer tools, which include <code>git</code> and <code>python3</code>:</p>
        ${code("xcode-select --install")}
        <p>Then the GitHub CLI. With <a href="https://brew.sh" target="_blank" rel="noopener">Homebrew</a>:</p>
        ${code("brew install gh")}
        ${note("tip", "macOS Python handles the TAB key a little differently, so the completion stages (26–30) may act up locally. The official result on GitHub is what counts, and it uses Linux.")}`,
      win: `<p>The tester drives your shell through a real Unix terminal, so on Windows you work inside <strong>WSL</strong> (a built-in Linux). Open <strong>PowerShell as administrator</strong> and run:</p>
        ${code("wsl --install")}
        <p>Restart when asked, then open <strong>Ubuntu</strong> from the Start menu, pick a username and password, and install the tools:</p>
        ${code("sudo apt update && sudo apt install -y git python3 gh")}
        ${note("tip", "Run every command below inside that Ubuntu window, not PowerShell. Don't want WSL? The <strong>Desktop apps</strong> tab works on plain Windows, because the tests run on GitHub.")}`,
      linux: `<p>On Ubuntu or Debian:</p>
        ${code("sudo apt update && sudo apt install -y git python3 gh")}
        <p>Other distributions: install <code>git</code>, <code>python3</code> and the <a href="https://cli.github.com" target="_blank" rel="noopener">GitHub CLI</a> from your package manager.</p>`,
    }[os];

    return `
      <div class="ospick" role="tablist" aria-label="Your computer">
        <span>Your computer:</span>
        ${OSES.map((o) => `<button type="button" data-os="${o.id}" class="${o.id === os ? "on" : ""}">${o.label}</button>`).join("")}
      </div>
      <ol class="gsteps">
        ${step("Install the tools", install)}
        ${step("Log in to GitHub", `<p>This lets <code>./smith submit</code> push your code and stream the test results back:</p>
          ${code("gh auth login")}
          <p>Answer: <em>GitHub.com</em> → <em>HTTPS</em> → <em>Yes</em> (authenticate Git) → <em>Login with a web browser</em>, then paste the code it shows into the page that opens.</p>`)}
        ${step("Get the code", `${code(`git clone https://github.com/${ctx.repo}.git\ncd ${ctx.name}`)}
          ${ctx.ownerNote}`)}
        ${step("Pick a language <span class=\"opt\">optional</span>", `<p>Python is the default. To switch:</p>
          ${code("./smith language          # list the choices\n./smith language go       # python, c, go, rust or javascript")}`)}
        ${step("Read your stage", `${code("./smith stage")}<p>Same instructions as on this dashboard, right in the terminal. Your code goes in the <code>app/</code> folder.</p>`)}
        ${step("Code and test on your computer", `${code("./smith test        # run once\n./smith test -w     # re-run every time you save")}
          <p>Tests stop at the first stage that fails and tell you exactly what they typed and what came back.</p>`)}
        ${step("Submit", `${code("./smith submit")}
          <p>Commits and pushes your work, then shows GitHub running the official tests and prints the result in your terminal. This dashboard updates about a minute later.</p>`)}
      </ol>
      <h3 class="ghead">Cheat sheet</h3>
      <table class="cheat">
        <tr><td><code>./smith stage [N]</code></td><td>instructions for your current stage, or stage N</td></tr>
        <tr><td><code>./smith stages</code></td><td>all stages with your progress</td></tr>
        <tr><td><code>./smith test [N] [-w]</code></td><td>run tests (one stage, watch mode)</td></tr>
        <tr><td><code>./smith test --seed S</code></td><td>replay a run with the same random words</td></tr>
        <tr><td><code>./smith submit [message]</code></td><td>commit, push, and stream GitHub's result</td></tr>
        <tr><td><code>./smith status</code></td><td>local and GitHub progress at a glance</td></tr>
        <tr><td><code>./smith language [name]</code></td><td>list or switch languages</td></tr>
        <tr><td><code>./smith open</code></td><td>open this dashboard</td></tr>
      </table>`;
  }

  // ------------------------------------------------------------------ Desktop
  function desktop(ctx) {
    return `
      <p class="lead">Edit in VS Code, send your work to GitHub with GitHub Desktop, and read the results here. Works on Windows, macOS and Linux, because the official tests run on GitHub.</p>
      <ol class="gsteps">
        ${step("Install two free apps", `<div class="appgrid">
            <a class="appcard" href="https://desktop.github.com" target="_blank" rel="noopener"><b>GitHub Desktop</b><span>sends your code to GitHub</span></a>
            <a class="appcard" href="https://code.visualstudio.com" target="_blank" rel="noopener"><b>Visual Studio Code</b><span>where you write the code</span></a>
          </div>
          <p>Open GitHub Desktop and sign in with your GitHub account (<em>File → Options → Accounts</em> on Windows, <em>GitHub Desktop → Settings → Accounts</em> on macOS).</p>`)}
        ${step("Clone your repository", `<p><a class="btn" href="x-github-client://openRepo/https://github.com/${esc(ctx.repo)}">Open in GitHub Desktop</a></p>
          <p>If the button does nothing: in GitHub Desktop choose <em>File → Clone repository → URL</em>, paste the address below, choose a folder, and click <em>Clone</em>.</p>
          ${code(`https://github.com/${ctx.repo}`)}
          ${ctx.ownerNote}`)}
        ${step("Open it in VS Code", `<p>In GitHub Desktop: <em>Repository → Open in Visual Studio Code</em>. Your shell lives in the <code>app/</code> folder (Python by default: <code>app/main.py</code>).</p>`)}
        ${step("Read your stage", `<p>The instructions are on this dashboard. ${ctx.current ? `You're on <a href="#/stage/${ctx.current.slug}">stage ${ctx.current.number}: ${esc(ctx.current.title.replace(/`/g, ""))}</a>.` : ""} Write the code, save the file.</p>`)}
        ${step("Commit and push", `<div class="flow"><span>Back in GitHub Desktop, your changed files are listed on the left</span>
            <span>Type a summary, e.g. <code>stage 1: show the prompt</code></span>
            <span>Click <strong>Commit to main</strong></span>
            <span>Click <strong>Push origin</strong> at the top</span></div>`)}
        ${step("Watch the result here", `<p>A pulsing <strong>Testing…</strong> bar appears at the top of this page. After a minute or two the results arrive: green ticks for passed stages, and on the failing stage the error plus the full test log showing exactly what the tester typed and what your shell printed. Fix, save, commit, push, repeat.</p>`)}
        ${step("Faster feedback <span class=\"opt\">optional</span>", `<p>Waiting for GitHub each time gets slow in later stages. VS Code has a terminal built in (<em>Terminal → New Terminal</em>); on macOS or Linux run:</p>
          ${code("./smith test -w")}
          <p>It re-tests on every save, in seconds. On Windows this needs WSL (see the Terminal tab). The same terminal runs <code>./smith language go</code> if you want to switch languages.</p>`)}
      </ol>`;
  }

  // ------------------------------------------------------------------ Browser
  function browser(ctx) {
    return `
      <p class="lead">GitHub Codespaces gives you VS Code and a Linux terminal in your browser, with your repo already cloned and GitHub login already set up. Personal accounts get a free monthly allowance.</p>
      <ol class="gsteps">
        ${step("Open a codespace", `<p><a class="btn" href="https://codespaces.new/${esc(ctx.repo)}" target="_blank" rel="noopener">Create codespace on ${esc(ctx.repo)}</a></p>
          <p>Or on the repo page: green <em>Code</em> button → <em>Codespaces</em> → <em>Create codespace on main</em>. The first start takes a minute.</p>`)}
        ${step("Use the terminal at the bottom", `${code("./smith stage\n./smith test -w")}<p>Everything from the Terminal tab works here unchanged.</p>`)}
        ${step("Submit", `${code("./smith submit")}<p>Your results show up on this dashboard as usual.</p>`)}
        ${step("Stop it when you're done", `<p>Codespaces stop by themselves after 30 idle minutes. To save your free hours, stop it yourself from <a href="https://github.com/codespaces" target="_blank" rel="noopener">github.com/codespaces</a>. Your work is kept.</p>`)}
      </ol>`;
  }

  // ------------------------------------------------------------------ page
  function render(el, opts) {
    const tab = TABS.some((t) => t.id === opts.tab) ? opts.tab : "cli";
    const repo = opts.repo || "YOUR-NAME/shellsmith";
    const name = repo.split("/")[1];
    const ownerNote = note("info", `<details><summary>Not your repo? Start your own copy</summary>
      <p>1. <a href="https://github.com/${esc(repo)}/fork" target="_blank" rel="noopener">Fork ${esc(repo)}</a> to your account and use <em>your</em> fork's address in these steps.</p>
      <p>2. In your fork's <em>Actions</em> tab, click <em>I understand my workflows, go ahead and enable them</em>.</p>
      <p>3. <em>Settings → Pages → Source: GitHub Actions</em>, so you get your own dashboard.</p></details>`);
    const ctx = { repo, name, ownerNote, current: opts.current };
    const body = { cli, desktop, browser }[tab](ctx);

    el.innerHTML = `
      <div class="eyebrow"><span class="chip">Start here</span></div>
      <h1>Set up in a few minutes</h1>
      <p class="lead">Choose how you'd like to work. You can mix them later; they all use the same repo and this dashboard.</p>
      <div class="gtabs" role="tablist">
        ${TABS.map((t) => `<a role="tab" aria-selected="${t.id === tab}" class="${t.id === tab ? "on" : ""}" href="#/start/${t.id}">
          <b>${t.label}</b><span>${t.sub}</span></a>`).join("")}
      </div>
      <div class="gbody">${body}</div>
      <div class="gnext">${opts.current ? `<a class="cta" href="#/stage/${opts.current.slug}">Go to stage ${opts.current.number} →</a>` : ""}</div>`;

    el.querySelectorAll("[data-os]").forEach((b) => b.addEventListener("click", () => {
      os = b.dataset.os;
      try { localStorage.setItem("smith-os", os); } catch { /* ignore */ }
      render(el, opts);
    }));
    el.querySelectorAll("button.copy").forEach((b) => b.addEventListener("click", async () => {
      const text = b.dataset.copy;
      try {
        await navigator.clipboard.writeText(text);
      } catch {
        const t = document.createElement("textarea");
        t.value = text; document.body.appendChild(t); t.select();
        try { document.execCommand("copy"); } catch { /* ignore */ }
        t.remove();
      }
      b.textContent = "Copied";
      setTimeout(() => { b.textContent = "Copy"; }, 1500);
    }));
  }

  window.ShellsmithGuide = { render };
})();
