# Verification gate

A small evidence harness. `verify.sh` runs the gates listed in `.evidence/gates.txt` and writes a JSON record per run. `check_evidence.py` confirms a recent successful run exists; use it in pre-commit hooks, CI guards, or the Stop hook in [`../04-stop-hook/`](../04-stop-hook).

## Layout

After a run the `.evidence/` directory looks like:

```
.evidence/
├── gates.txt                      # gate definitions: name: command
├── 20260504T193149Z.json          # run record
├── 20260504T193149Z-typecheck.log
├── 20260504T193149Z-lint.log
└── 20260504T193149Z-test.log
```

## Use

Drop `verify.sh` into `scripts/` (or wherever you keep ops scripts) and copy `gates.example.txt` to `.evidence/gates.txt`. Edit it to match your project. Then:

```bash
chmod +x scripts/verify.sh
./scripts/verify.sh
```

Confirm recent evidence exists:

```bash
python3 scripts/check_evidence.py --max-age-minutes 30
```

`check_evidence.py` exits 0 when a recent ok=true record exists, non-zero otherwise. Wire that into hooks, CI, or anything else that needs a "this is verified" gate.

## Why

The article's tenth lesson: the dangerous failure mode is not that the model cannot do the work; it is that the model does most of it, narrates the rest convincingly, and stops. Evidence is what makes "done" non-negotiable.

Article references: §10 (plausible completion), §11 (loop design).
