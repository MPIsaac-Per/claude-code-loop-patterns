# Verification gate

A small evidence runner. `verify.sh` delegates to `verify.py`, which validates the gate configuration, applies a per-gate timeout, captures logs, and writes an atomic JSON record. `check_evidence.py` requires the newest recent record to pass. Use it in pre-commit hooks, CI guards, or the Stop hook in [`../04-stop-hook/`](../04-stop-hook).

## Layout

After a run the `.evidence/` directory looks like:

```
.evidence/
├── gates.txt                      # gate definitions: name: command
├── 20260504T193149.123456Z-4312.json          # run record
├── 20260504T193149.123456Z-4312-typecheck.log
├── 20260504T193149.123456Z-4312-lint.log
└── 20260504T193149.123456Z-4312-test.log
```

## Use

Drop `verify.sh` into `scripts/` (or wherever you keep ops scripts) and copy `gates.example.txt` to `.evidence/gates.txt`. Edit it to match your project. Then:

```bash
chmod +x scripts/verify.sh
./scripts/verify.sh

# Optional: change the default 10-minute timeout for each gate
./scripts/verify.sh --gate-timeout-seconds 900
```

Confirm recent evidence exists:

```bash
python3 scripts/check_evidence.py --max-age-minutes 30
```

`check_evidence.py` exits 0 when the newest recent record has `ok=true`, non-zero otherwise. A newer failure invalidates an older success.

Gate commands are operator-authored shell commands and run through the user's shell. Do not populate `gates.txt` from untrusted input. Gate names are restricted to lowercase letters, digits, hyphens, and underscores so they cannot escape the evidence directory.

## Why

The article's tenth lesson: the dangerous failure mode is not that the model cannot do the work; it is that the model does most of it, narrates the rest convincingly, and stops. Evidence is what makes "done" non-negotiable.

Article references: §10 (plausible completion), §11 (loop design).
