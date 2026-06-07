#!/usr/bin/env python3
"""
Injects code blocks into index.html and updates the solution card UI.
"""

import json
import re
import sys

def main():
    try:
        with open("code_generated.json") as f:
            code_map = json.load(f)
    except FileNotFoundError:
        print("code_generated.json not found.")
        sys.exit(1)

    print(f"Loaded {len(code_map)} code blocks")

    with open("index.html") as f:
        html = f.read()

    # ── 1. Inject CODE_MAP constant ──────────────────────────────────────────
    code_js_lines = ["const CODE_MAP = {"]
    for key, code in sorted(code_map.items()):
        # Escape backticks and backslashes for template literal
        escaped = code.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        code_js_lines.append(f"  {json.dumps(key)}: `{escaped}`,")
    code_js_lines.append("};")
    code_block = "\n".join(code_js_lines)

    MARKER = "// ─── Problem lookup map"
    if "const CODE_MAP" in html:
        html = re.sub(r'const CODE_MAP = \{[\s\S]*?\};', code_block, html)
        print("Replaced existing CODE_MAP")
    else:
        html = html.replace(MARKER, code_block + "\n\n" + MARKER)
        print("Inserted CODE_MAP")

    # ── 2. Add CSS for code blocks ───────────────────────────────────────────
    CODE_CSS = """
  /* Code blocks in solution cards */
  .sol-code { margin-top:8px; border-radius:5px; overflow:hidden; border:1px solid var(--border2); }
  .sol-code pre { margin:0; padding:10px 12px; background:#0a0a0a; overflow-x:auto; font-size:11.5px; line-height:1.6; }
  .sol-code pre::-webkit-scrollbar { height:3px; }
  .sol-code pre::-webkit-scrollbar-thumb { background:var(--border2); border-radius:2px; }
  .sol-code code { font-family:'SF Mono','Fira Code',Consolas,monospace; color:#e2e8f0; white-space:pre; }
  /* Python syntax highlight — lightweight hand-rolled */
  .kw  { color:#c792ea; }   /* keywords */
  .fn  { color:#82aaff; }   /* function names */
  .cm  { color:#546e7a; font-style:italic; }   /* comments */
  .st  { color:#c3e88d; }   /* strings */
  .nu  { color:#f78c6c; }   /* numbers */
  .bi  { color:#ffcb6b; }   /* builtins */
  .copy-btn {
    display:flex; align-items:center; justify-content:flex-end;
    padding:4px 8px; background:#111; border-bottom:1px solid var(--border2);
    cursor:pointer;
  }
  .copy-btn span { font-size:10px; color:var(--text3); padding:2px 6px; border-radius:3px; border:1px solid var(--border2); transition:all 0.15s; }
  .copy-btn:hover span { color:var(--text2); border-color:var(--border2); }
  .copy-btn span.copied { color:var(--green); border-color:var(--green); }"""

    if ".sol-code {" not in html:
        html = html.replace("  .sol-no-data {", CODE_CSS + "\n  .sol-no-data {")
        print("Injected CSS")

    # ── 3. Update renderSolution JS to include code ──────────────────────────
    # Replace the sol-card template in renderSolution
    old_card = """    cardsHtml = sol.steps.map(s => {
      const cls = s.label === 'optimal' ? 'optimal' : s.label === 'better' ? 'better' : s.label === 'brute' ? 'brute' : 'optimal';
      return `<div class="sol-card">
        <div class="sol-card-head">
          <span class="sol-label ${cls}">${s.label}</span>
          <span class="sol-complexity">TC: ${s.tc} &nbsp;|&nbsp; SC: ${s.sc}</span>
        </div>
        <div class="sol-desc">${escHtml(s.desc)}</div>
      </div>`;
    }).join('');"""

    new_card = """    cardsHtml = sol.steps.map((s, i) => {
      const cls = s.label === 'optimal' ? 'optimal' : s.label === 'better' ? 'better' : s.label === 'brute' ? 'brute' : 'optimal';
      const codeKey = `${id}_${i}`;
      const rawCode = CODE_MAP[codeKey] || '';
      const codeBlock = rawCode ? `
        <div class="sol-code">
          <div class="copy-btn" onclick="copyCode(this, ${JSON.stringify(rawCode)})">
            <span>copy</span>
          </div>
          <pre><code>${highlightPython(escHtml(rawCode))}</code></pre>
        </div>` : '';
      return `<div class="sol-card">
        <div class="sol-card-head">
          <span class="sol-label ${cls}">${s.label}</span>
          <span class="sol-complexity">TC: ${s.tc} &nbsp;|&nbsp; SC: ${s.sc}</span>
        </div>
        <div class="sol-desc">${escHtml(s.desc)}</div>
        ${codeBlock}
      </div>`;
    }).join('');"""

    if old_card in html:
        html = html.replace(old_card, new_card)
        print("Updated renderSolution card template")
    else:
        print("WARNING: Could not find old card template — check manually")

    # ── 4. Add helper functions (highlightPython + copyCode) ─────────────────
    HELPERS = """
function highlightPython(code) {
  // Lightweight Python syntax highlighting
  const keywords = /\\b(def|return|if|elif|else|for|while|in|not|and|or|is|None|True|False|import|from|class|pass|break|continue|yield|lambda|with|as|try|except|finally|raise|del|global|nonlocal|assert)\\b/g;
  const builtins = /\\b(len|range|print|int|str|float|list|dict|set|tuple|min|max|sum|sorted|reversed|enumerate|zip|map|filter|abs|round|type|isinstance|append|pop|push|heapq|defaultdict|Counter|deque|inf|math)\\b/g;
  const funcDef  = /\\bdef (\\w+)/g;
  const comments = /(#[^\\n]*)/g;
  const strings  = /("[^"]*"|'[^']*')/g;
  const numbers  = /\\b(\\d+\\.?\\d*)\\b/g;
  // Order matters: comments first, then strings, then rest
  return code
    .replace(comments, '<span class="cm">$1</span>')
    .replace(strings,  '<span class="st">$1</span>')
    .replace(keywords, '<span class="kw">$1</span>')
    .replace(builtins, '<span class="bi">$1</span>')
    .replace(funcDef,  'def <span class="fn">$1</span>')
    .replace(numbers,  '<span class="nu">$1</span>');
}

window.copyCode = (btn, code) => {
  navigator.clipboard.writeText(code).then(() => {
    const s = btn.querySelector('span');
    s.textContent = 'copied!';
    s.classList.add('copied');
    setTimeout(() => { s.textContent = 'copy'; s.classList.remove('copied'); }, 1500);
  });
};"""

    if "function highlightPython" not in html:
        # Insert before the closing </script>
        html = html.replace("document.getElementById('notes-textarea')", HELPERS + "\ndocument.getElementById('notes-textarea')")
        print("Injected helper functions")

    with open("index.html", "w") as f:
        f.write(html)

    print("Done! index.html updated with code blocks.")

if __name__ == "__main__":
    main()
