#!/usr/bin/env python3
"""
Injects Ollama-generated solutions from solutions_generated.json into index.html.
Appends GENERATED_SOLUTIONS inside the module script block, then merges at runtime.
"""

import json
import re
import sys

def main():
    try:
        with open("solutions_generated.json") as f:
            generated = json.load(f)
    except FileNotFoundError:
        print("solutions_generated.json not found. Run gen_solutions.py first.")
        sys.exit(1)

    print(f"Loaded {len(generated)} generated solutions")

    with open("index.html") as f:
        html = f.read()

    # Build compact JS for GENERATED_SOLUTIONS
    lines = ["const GENERATED_SOLUTIONS = {"]
    for pid, data in sorted(generated.items()):
        steps = data.get("steps", [])
        # Compact each step
        steps_compact = []
        for s in steps:
            steps_compact.append({
                "label": s.get("label","optimal"),
                "tc": s.get("tc","O(?)"),
                "sc": s.get("sc","O(?)"),
                "desc": s.get("desc","")
            })
        lines.append(f'  {pid}:{{steps:{json.dumps(steps_compact)}}},')
    lines.append("};")
    generated_block = "\n".join(lines)

    # --- Insert/replace GENERATED_SOLUTIONS inside the module script ---
    MARKER = "// ─── Problem lookup map"
    if "const GENERATED_SOLUTIONS" in html:
        html = re.sub(
            r'const GENERATED_SOLUTIONS = \{[\s\S]*?\};',
            generated_block,
            html
        )
        print("Replaced existing GENERATED_SOLUTIONS.")
    else:
        if MARKER not in html:
            print("ERROR: Could not find insertion marker in index.html")
            sys.exit(1)
        html = html.replace(
            MARKER,
            generated_block + "\n\n" + MARKER
        )
        print("Inserted GENERATED_SOLUTIONS block.")

    # --- Patch renderSolution to use merged lookup ---
    html = html.replace(
        "const sol = SOLUTIONS[id];",
        "const sol = SOLUTIONS[id] || GENERATED_SOLUTIONS[id];"
    )
    # --- Patch renderMain to use merged lookup for note indicator ---
    html = html.replace(
        "const sol = SOLUTIONS[p.id];",
        "const sol = SOLUTIONS[p.id] || GENERATED_SOLUTIONS[p.id];"
    )

    with open("index.html", "w") as f:
        f.write(html)

    print("Done. index.html updated with generated solutions.")

if __name__ == "__main__":
    main()
