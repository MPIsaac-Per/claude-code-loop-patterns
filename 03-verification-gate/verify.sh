#!/usr/bin/env bash
# verify.sh: run all required gates and write structured evidence.
#
# 'Done' must mean 'verified', not 'the model says so.' This script encodes
# the gates for a project and writes one evidence file per run. Downstream
# tooling (or a Stop hook) can refuse to mark a task complete unless evidence
# from the last N minutes exists.
#
# Adjust the gates list (.evidence/gates.txt) to match your project. Each
# gate must:
#   - exit 0 on success
#   - exit non-zero on failure
#   - print human-readable output to stdout/stderr (captured to a per-gate log)
#
# Output: writes .evidence/<timestamp>.json with a run summary.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EVIDENCE_DIR="$ROOT/.evidence"
GATES_FILE="$EVIDENCE_DIR/gates.txt"

if [[ ! -f "$GATES_FILE" ]]; then
  echo "No gates file at $GATES_FILE. Copy gates.example.txt to get started." >&2
  exit 2
fi

mkdir -p "$EVIDENCE_DIR"
ts="$(date -u +%Y%m%dT%H%M%SZ)"
out="$EVIDENCE_DIR/$ts.json"

gates_json="["
fail=0
first=1
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  name="${line%%:*}"
  cmd="${line#*:}"
  cmd="${cmd# }"

  start=$(date +%s)
  if eval "$cmd" >"$EVIDENCE_DIR/$ts-$name.log" 2>&1; then
    status="ok"
  else
    status="fail"
    fail=1
  fi
  end=$(date +%s)
  dur=$((end - start))

  [[ $first -eq 0 ]] && gates_json+=","
  first=0
  gates_json+="{\"name\":\"$name\",\"status\":\"$status\",\"duration_s\":$dur,\"log\":\"$ts-$name.log\"}"
done < "$GATES_FILE"

gates_json+="]"

ok_str="false"
[[ $fail -eq 0 ]] && ok_str="true"

cat > "$out" <<EOF
{
  "timestamp": "$ts",
  "ok": $ok_str,
  "gates": $gates_json
}
EOF

echo "Evidence: $out"
if [[ $fail -eq 0 ]]; then
  echo "All gates passed."
else
  echo "One or more gates failed." >&2
  exit 1
fi
