#!/usr/bin/env python3
"""
Generate Python code for all DSA solution approaches using Ollama.
Batches 3 problems per call to cut total API calls by 3x.
Runs parallel workers on the batches.
"""

import json, re, subprocess, sys, time, os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

MODEL   = "qwen2.5-coder:7b"
WORKERS = 1   # Ollama is single-threaded; >1 just causes queue timeouts
BATCH   = 3   # problems per Ollama call
OUT     = "code_generated.json"
lock    = Lock()

BATCH_PROMPT = """You are a Python DSA expert. Generate Python code for these problems.
Return ONLY a valid JSON array — no markdown, no explanation:

[
  {{"key": "KEY", "code": "def solve(): ..."}},
  ...
]

Problems:
PROBLEMS_LIST"""


def call_ollama(prompt: str) -> str:
    r = subprocess.run(["ollama", "run", MODEL],
                       input=prompt, capture_output=True, text=True, timeout=180)
    return r.stdout.strip()


def clean_code(code: str) -> str:
    code = code.strip()
    code = re.sub(r'^```[\w]*\n?', '', code)
    code = re.sub(r'\n?```$', '', code)
    return code.strip()


def generate_batch(tasks: list) -> dict:
    """tasks: list of (key, name, label, tc, sc, desc)"""
    lines = []
    for i, (key, name, label, tc, sc, desc) in enumerate(tasks, 1):
        lines.append(
            f'{i}. key="{key}": "{name}" — {label.upper()} (TC:{tc} SC:{sc}): {desc}'
        )
    prompt = BATCH_PROMPT.replace("PROBLEMS_LIST", "\n".join(lines))

    for attempt in range(3):
        try:
            raw = call_ollama(prompt)
            # Extract JSON array
            start = raw.find('[')
            end   = raw.rfind(']') + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON array found")
            arr = json.loads(raw[start:end])
            result = {}
            for item in arr:
                k = item.get('key', '')
                c = clean_code(item.get('code', ''))
                if k and c:
                    result[k] = c
            if result:
                return result
        except Exception as e:
            print(f"  Batch attempt {attempt+1} failed: {e}", file=sys.stderr)
            time.sleep(2)

    # Fallback: generate individually
    result = {}
    for key, name, label, tc, sc, desc in tasks:
        try:
            p = f'Write Python code for "{name}" ({label} approach, TC:{tc} SC:{sc}). Return ONLY the Python function, no explanation:\n'
            raw = call_ollama(p)
            result[key] = clean_code(raw)
        except:
            result[key] = f"def solve():\n    # {label} approach for {name}\n    pass"
    return result


# ── Load existing ────────────────────────────────────────────────────────────
existing = {}
if os.path.exists(OUT):
    with open(OUT) as f:
        existing = json.load(f)
print(f"Already done: {len(existing)}", file=sys.stderr)

# ── Load all problems + steps ────────────────────────────────────────────────
with open("index.html") as f:
    html = f.read()
with open("solutions_generated.json") as f:
    gen_sol = json.load(f)

# Problem names
PNAME = {}
data_m = re.findall(r'\{id:"(\w+)",name:"([^"]+)"', html)
for pid, name in data_m:
    PNAME[pid] = name

# Build work items: (key, pid, name, label, tc, sc, desc)
all_items = []

# From generated solutions
for pid, data in gen_sol.items():
    name = PNAME.get(pid, pid)
    for i, s in enumerate(data.get('steps', [])):
        key = f"{pid}_{i}"
        if key not in existing:
            all_items.append((key, pid, name, s['label'], s['tc'], s['sc'], s.get('desc','')))

# From hardcoded SOLUTIONS in HTML
sol_m = re.search(r'const SOLUTIONS = \{([\s\S]*?)\};\s*\n// ─── Problem lookup', html)
if sol_m:
    blk = sol_m.group(1)
    entries = re.findall(r'(\w+):\{[^{]*?steps:\[([^\]]*(?:\[[^\]]*\][^\]]*)*)\]', blk)
    for pid, steps_raw in entries:
        name = PNAME.get(pid, pid)
        step_objs = re.findall(
            r'\{label:"([^"]+)",tc:"([^"]+)",sc:"([^"]+)",desc:"([^"]+)"\}', steps_raw)
        for i, (label, tc, sc, desc) in enumerate(step_objs):
            key = f"{pid}_{i}"
            if key not in existing:
                all_items.append((key, pid, name, label, tc, sc, desc))

print(f"Code blocks to generate: {len(all_items)}", file=sys.stderr)

# ── Split into batches ───────────────────────────────────────────────────────
batches = []
for i in range(0, len(all_items), BATCH):
    chunk = all_items[i:i+BATCH]
    batches.append([(k, n, l, tc, sc, d) for k, _, n, l, tc, sc, d in chunk])

print(f"Total batches: {len(batches)} (batch size {BATCH}, workers {WORKERS})", file=sys.stderr)

if not batches:
    print("Nothing to do!", file=sys.stderr)
    sys.exit(0)

# ── Run ──────────────────────────────────────────────────────────────────────
results = dict(existing)
done_batches = [0]
start_t = time.time()

def process_batch(batch):
    return generate_batch(batch)

with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futs = {ex.submit(process_batch, b): b for b in batches}
    for fut in as_completed(futs):
        try:
            res = fut.result()
            with lock:
                results.update(res)
                done_batches[0] += 1
                elapsed = time.time() - start_t
                rate = done_batches[0] / elapsed if elapsed > 0 else 0.01
                left = (len(batches) - done_batches[0]) / rate / 60
                pct  = done_batches[0] / len(batches) * 100
                print(
                    f"Batch {done_batches[0]}/{len(batches)} ({pct:.0f}%) "
                    f"— {len(results)} codes — {left:.1f}min left",
                    file=sys.stderr
                )
                if done_batches[0] % 10 == 0:
                    with open(OUT, 'w') as f:
                        json.dump(results, f)
        except Exception as e:
            print(f"  Batch FAILED: {e}", file=sys.stderr)

with open(OUT, 'w') as f:
    json.dump(results, f, indent=2)

total = len(results)
print(f"\nFinished! {total} code blocks in {OUT}", file=sys.stderr)
