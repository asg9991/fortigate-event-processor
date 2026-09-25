# AGENTS.md

Python 3 daemon that tails a FortiGate syslog file, classifies events by LogID, and sends the interesting ones to Zabbix via `zabbix_sender`. No tests, no linter config, no packaging, no CI.

## Run / verify

- Run: `python3 fortigate_parser.py` (blocks forever, tails with `tail -F`).
- Only check: `python3 -m py_compile *.py` — there are no tests or lint setup.
- Requires `pyyaml` (`pip install pyyaml`) and `zabbix_sender` on PATH. Both are undocumented in the repo.

## Gotchas

- **Hardcoded absolute paths**: `fortigate_parser.py` loads `/opt/fortigate-event-processor/config/parser.yaml` and logs to `/opt/fortigate-event-processor/logs/parser.log` at import time. Running from the repo fails unless those files exist (or the path is edited). No CLI args, no env vars.
- **No `if __name__ == "__main__"` guard**: importing `fortigate_parser` (or anything importing it) runs the full event loop. Never import it for testing.
- **Config in `config/parser.yaml`**: the `log_directory` key is dead — logging path is hardcoded in `logging.basicConfig`.
- `state/` and `logs/` are gitignored and created at runtime; the threshold state JSON (`state/thresholds.json`) is safe to delete.

## Behavior

- Pipeline: `fortigate_parser.parse` → `classifier.classify` → IGNORE/AUDIT/THRESHOLD/IMMEDIATE → `notifier.send`.
- **Unknown LogIDs default to AUDIT + enabled** (`classifier.py`), i.e. they ARE sent to Zabbix and logged as "AUDIT sent" — deliberate, not a bug.
- `config/classification.csv` columns: `logid,classification,count,window,enabled`. `enabled` must be lowercase `true`/`false`; `classification` is case-insensitive (upper-cased); `count`/`window` are parsed as ints.
- THRESHOLD fires **once per window** (an `alerted` flag in the persisted state suppresses repeats until the window resets).
- New LogIDs are added via the CSV only; no code change needed.
- Comments: none in the code; README/CHANGELOG are written in Spanish.
