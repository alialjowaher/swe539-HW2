# Refactoring starter kit - Apache Commons CLI 1.9.0 (SWE 539, HW2)

This kit makes three different LLMs refactor the **same code smell** in the **same way**, and records everything in one Excel log and one Markdown report per run. The LLM only does the refactoring. Cloning, saving the original code, running the tests, saving the refactored code and logging are all done by `kit.py`, so every LLM is measured identically.

```text
 kit.py show W01        kit.py start ...                LLM refactors          kit.py finish ...
 (pick the smell)  -->  - fresh clone at the tag   -->  (small steps,     -->  - same original tests on refactored code
                        - original code saved            tests after each)     - refactored code + diff saved
                        - ORIGINAL tests run                                   - API and test-file checks
                        - Excel row started                                    - REPORT.md + Excel row completed
```

## What's inside

```text
refactor-kit/
├── README.md               <- this guide (for you)
├── PROMPT.md               <- the unified prompt: paste it into each LLM (agent mode)
├── kit.py                  <- the helper that does all the mechanical steps
├── config.json             <- repo/tag, Maven command, metric names
├── requirements.txt        <- Python dependency (openpyxl)
├── smells/
│   ├── CommonsCLI_1.9.0_Code_Smells.xlsx   <- the smell review sheet (replace with your reviewed copy)
│   └── targets.json        <- where each smell ID lives in the code (file + members)
├── templates/              <- RULES, TASK, CHAT_PROMPT and process templates
├── Refactoring_Log.xlsx    <- created on the first run: one row per smell x LLM
├── workspace/<llm>/commons-cli/   <- created: one clone per LLM, one branch per smell
└── runs/<llm>/<SMELL_ID>/  <- created: everything about one run (see section 6)
```

## 1. One-time setup

1. Install **Git**, a **JDK 8 or newer** (11, 17 and 21 all work), **Maven 3.6.3+** and **Python 3.8+**.
2. `pip install -r requirements.txt`
3. Put your reviewed smell sheet in `smells/` under the same file name, or point `smells_workbook` in `config.json` at it. The kit reads each row by its **ID**. When **Your refactoring approach** is filled in, that text is the technique the LLM must apply; otherwise the sheet's **Suggested refactoring** and **How to apply** columns are used. Rows marked **Reject** are refused.
4. `python kit.py check` should end with `All good.` (On Windows use `py` instead of `python`.)
5. The first Maven run downloads the build's dependencies and takes a few minutes. Behind a proxy, add your Maven settings file to `maven_extra_args` in `config.json`, e.g. `["-s", "C:/Users/me/.m2/settings-proxy.xml"]`.

## 2. Choose the smells (before any LLM run)

HW2 needs at least **2 within-class and 2 between-class** refactorings. Choose the IDs, and write **Your refactoring approach** for each one *before* the first run. **Don't change it after that**: every LLM must get the same instruction. You can preview what an LLM will see with `python kit.py show W01`.

## 3. Fairness checklist (same for all three LLMs)

- The same smell IDs, in the same order, for every LLM.
- A **new session** for every run, so the LLM has no memory of earlier runs or other LLMs' answers.
- `PROMPT.md` (agent) or `CHAT_PROMPT.md` (chat) pasted **unchanged**; only the three values at the top of `PROMPT.md` differ.
- The same repair budget: agent mode allows at most 3 `finish` attempts (the prompt says so). In chat mode, allow at most 2 follow-up messages that contain only the failure summary from `REPORT.md` section 6, never hints.
- Record the **exact model and version** (`--model`).
- Save the full reply or transcript as `runs/<llm>/<ID>/response.md`.
- Run one LLM at a time in a kit folder.
- Don't hand-fix LLM code. If you have to, write it in the **Your notes** column; it then counts as your work, not the LLM's.

## 4. Mode A - agent LLMs (they can run commands)

Examples: Claude Code, OpenAI Codex CLI, Gemini CLI, Cursor or Copilot in agent mode.

1. Open the agent with the **kit folder** as its working folder.
2. Paste `PROMPT.md` with `SMELL_ID`, `LLM_NAME` and `MODEL_VERSION` filled in.
3. Approve its commands when asked. It runs `check -> show -> start -> (refactor + test) -> finish` and ends with a fixed-format summary.
4. Save the transcript as `runs/<llm>/<ID>/response.md`.

## 5. Mode B - chat LLMs (no command access)

Examples: ChatGPT, Gemini or Claude in the browser.

```bash
python kit.py start  --smell W01 --llm "Gemini" --model "Gemini 3 Pro (Nov 2026)" --mode chat
#   open a NEW chat, paste or attach runs/gemini/W01/CHAT_PROMPT.md
#   save ONLY the reply as runs/gemini/W01/response.md (if it says CONTINUE, ask it to continue and append)
python kit.py apply  --smell W01 --llm "Gemini"     # writes its files into the workspace + process.md
python kit.py finish --smell W01 --llm "Gemini"
```

If the verdict is **REVIEW** and you allow a repair round, paste the *Compilation errors / Regressions* part of `REPORT.md` section 6 into the **same chat** with: *"The original tests report these failures. Fix them while keeping the same refactoring, and resend the complete changed files in the same format."* Save that reply as `response_2.md`, then run `apply --response response_2.md` and `finish` again.

If your three LLMs don't all use the same mode, say so in the report, because it affects the results.

## 6. Where everything goes

**Per run: `runs/<llm>/<SMELL_ID>/`**

| File | Contents |
|---|---|
| `REPORT.md` | **The Markdown record:** smell, original code, original tests, refactoring process, refactored code, tests on the refactored code, checks |
| `original/`, `original_smell_location.java.txt` | Original files and the original code at the smell location |
| `refactored/`, `changes.patch` | Refactored files and the unified diff |
| `code_changes.json` | Every changed, new or removed member, before and after |
| `tests_original.json/.log` | Original test suite on the **original** code |
| `tests_refactored.json/.log` | The same, unmodified suite on the **refactored** code |
| `api_*.txt` | Public/protected API before and after, and the difference |
| `PROMPT_master.md`, `TASK.md`, `CHAT_PROMPT.md`, `response*.md` | Prompts sent and replies received |
| `process.md` | The refactoring process, written by the LLM |
| `run.json` | LLM, model, mode, dates, commit, verdict |

The refactored code is also committed in `workspace/<llm>/commons-cli` on branch `refactor/<SMELL_ID>`.

**`Refactoring_Log.xlsx`** (rebuilt from `runs/` after every start and finish; only yellow cells are yours, and they're kept):

| Sheet | Contents |
|---|---|
| **Runs** | One row per smell x LLM: technique, LLM and model, **Original code**, **Refactored code**, **original tests passed/total**, **refactored tests passed/total**, regressions, build, test files touched, API removed, verdict, your notes |
| **Code Changes** | The same code one member per row, original next to refactored, with line numbers |
| **Comparison** | Each smell across the LLMs: verdict, tests, regressions, lines +/-, members changed |
| **Metrics** | Size / cohesion / coupling before and after, for you to fill in; the change is calculated |
| **About** | How the log is filled |

**Verdict PASS** = compiles, 0 regressions, no test file changed, no public/protected API removed or changed, and the code did change. **REVIEW** = look at the reasons in `REPORT.md`. A PASS shows the tests still pass; it doesn't prove the smell is gone or that the code is better. That judgement and the metrics are yours.

## 7. Commands

| Command | What it does |
|---|---|
| `python kit.py check` | Checks Git, Java, javac, javap, Maven, openpyxl and the smell sheet |
| `python kit.py show W01` | Prints the smell and the refactoring to apply |
| `python kit.py start --smell W01 --llm "X" --model "Y" [--mode chat] [--base BRANCH] [--force] [--fresh-baseline]` | Fresh branch, original code saved, original tests run, task written, log row started |
| `python kit.py test --llm "X" [--only TestClass]` | Runs the tests in X's workspace |
| `python kit.py apply --smell W01 --llm "X" [--response file]` | Chat mode: writes the files from the reply into the workspace |
| `python kit.py finish --smell W01 --llm "X"` | Tests the refactored code, saves everything, writes REPORT.md, updates the log |
| `python kit.py log` | Rebuilds `Refactoring_Log.xlsx` (e.g. after closing it in Excel) |
| `python kit.py status` | Lists all runs with their test results |

## 8. HW2 deliverables in the kit

| HW2 asks for | Where it is |
|---|---|
| Original code | Tag `rel/commons-cli-1.9.0`; `runs/*/*/original/` |
| The three refactored versions | `workspace/<llm>/commons-cli`, branches `refactor/<ID>`; `runs/<llm>/*/refactored/` |
| Refactoring applied and the code change | `REPORT.md` sections 2, 4 and 5; `changes.patch`; Excel **Code Changes** |
| Saved prompts and responses | `PROMPT_master.md`, `TASK.md` / `CHAT_PROMPT.md`, `response*.md` |
| Testing process (behaviour preserved) | `tests_original.*`, `tests_refactored.*`; Excel **Runs** |
| Metrics before and after, per LLM | Excel **Metrics** (fill in from your metric tool) |
| LLM names and versions | `run.json`; Excel **Runs** |

## 9. Options and troubleshooting

- **Each run starts from the original code** at the tag, so every refactoring is measured on its own. To stack refactorings instead, start the next one from an earlier result: `start --smell W05 ... --base refactor/W01`.
- **Restart a run:** `start ... --force` deletes that run folder and starts over.
- **Original tests are cached** per commit: they're identical for every run on the same code. Use `--fresh-baseline` to run them again.
- **"could not write Refactoring_Log.xlsx":** it's open in Excel. Close it and run `python kit.py log`.
- **Original tests don't all pass on your machine:** don't refactor. Check `tests_original.log` (usually the JDK or Maven version, or a proxy problem).
- **The chat reply was cut off or contains `// ...`:** `apply` warns you. Ask the LLM for the complete file and apply again.
- **A different metric set:** rename the metrics in `config.json` (`"metrics"`) and run `python kit.py log`.
