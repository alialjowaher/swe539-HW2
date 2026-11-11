# Unified refactoring prompt - Apache Commons CLI 1.9.0

> **How to use:** start a **new** session with the LLM, inside the starter-kit folder (the one containing `kit.py`). Paste this whole file as the first message, after filling in the three values below. Change nothing else, so every LLM gets identical instructions.

```text
SMELL_ID:      W01
LLM_NAME:      <short name, e.g. ChatGPT, Gemini, Claude>
MODEL_VERSION: <exact model and version, e.g. GPT-5.1 Thinking (Nov 2026)>
```

---

## Your role

You are a careful Java engineer doing **one behaviour-preserving refactoring** (Fowler, *Refactoring*, 2nd ed.) on Apache Commons CLI 1.9.0. This is a controlled experiment: three different LLMs do exactly the same task, and the results are compared using the project's original test suite, a public-API check and code metrics (size, cohesion, coupling). Follow the steps in order and don't improvise outside them.

All mechanical work is done by `kit.py`, so every LLM is treated the same: cloning the repository, saving the original code, running the original tests, saving the refactored code, running the tests again and logging everything to Excel and Markdown. **Your job is the refactoring itself and documenting how you did it.**

Run every command from the kit folder. If `python` is not found, use `python3` (macOS/Linux) or `py` (Windows).

---

## Step 1 - Check the tools

```bash
python kit.py check
```

If anything is reported missing, stop and tell me what is missing. Do not try to install or work around it.

## Step 2 - Read the smell

```bash
python kit.py show SMELL_ID
```

The smell comes from the review sheet (`smells/CommonsCLI_1.9.0_Code_Smells.xlsx`). The refactoring to apply is the reviewer's approach when one has been written, otherwise the sheet's suggestion. You must use that technique.

## Step 3 - Start the run (clone, save the original code, run the original tests)

```bash
python kit.py start --smell SMELL_ID --llm "LLM_NAME" --model "MODEL_VERSION"
```

This command:
1. clones `rel/commons-cli-1.9.0` into `workspace/<llm>/commons-cli` on a fresh branch `refactor/SMELL_ID`;
2. saves the original files in `runs/<llm>/SMELL_ID/original/` and the original code of the smell location in the Excel log;
3. runs the **original test suite on the untouched code** and saves the result (`tests_original.json`);
4. writes `TASK.md` and a `process.md` template in `runs/<llm>/SMELL_ID/`.

Check that it prints `Original tests: N passed of N`. **If the original tests do not all pass, stop and report it.** Do not refactor in that case.

## Step 4 - Read the task

Read `runs/<llm>/SMELL_ID/TASK.md` completely: the smell, the exact refactoring to apply, the target code with line numbers, and the **rules**. The rules are non-negotiable. Then open the target source files in the workspace and read them.

## Step 5 - Plan before you edit

Fill in sections **1 (Understanding)** and **2 (Plan)** of `runs/<llm>/SMELL_ID/process.md`. The plan is the mechanics of the given technique, split into small steps that can each be compiled and tested.

## Step 6 - Refactor in small steps

Edit only `src/main/java/...` inside `workspace/<llm>/commons-cli`. After **each** step:

```bash
python kit.py test --llm "LLM_NAME" --only <MostRelevantTestClass>   # quick check, listed in TASK.md
```

When all steps are done, run the full suite:

```bash
python kit.py test --llm "LLM_NAME"
```

If a step breaks a test, fix or undo that step before continuing. Add one row per step to section **3** of `process.md`.

## Step 7 - Document

Complete sections **4 to 7** of `process.md`: why behaviour is preserved, deviations from the plan, observations (bugs or smells you noticed but did not change) and your self-assessment. Replace every *italic guidance line*.

## Step 8 - Finish (save the refactored code, run the original tests again, log everything)

```bash
python kit.py finish --smell SMELL_ID --llm "LLM_NAME"
```

This saves the refactored files, the diff and the member-by-member code comparison. It runs the **same original test suite on the refactored code**, checks that no test file changed and that no public or protected API was removed, writes `REPORT.md`, commits on the run branch and updates `Refactoring_Log.xlsx`.

- **Verdict PASS:** go to Step 9.
- **Verdict REVIEW:** read the reasons it prints. If the cause is in your refactoring (a regression, a removed API element, a changed test file, a compile error), fix it and run `finish` again. You may repeat `finish` **at most 2 more times** (3 in total). Record each extra attempt and its reason in `process.md` section 5.

## Step 9 - Final answer

Reply with exactly this, and nothing else:

```text
RUN: SMELL_ID / LLM_NAME / MODEL_VERSION
Verdict: PASS | REVIEW (reasons)
Original tests: <passed>/<total>   Refactored tests: <passed>/<total>   Regressions: <n>
Files changed: <list with +/- lines>
What I did:
- <3 to 6 bullets: the steps, named after the technique's mechanics>
Reviewer should check:
- <risky spots, behaviour questions, or "nothing special">
```

---

### If you cannot run commands (chat-only LLM)

Do not attempt the steps above. Tell the user to use **chat mode**: they run `python kit.py start ... --mode chat` and paste `runs/<llm>/SMELL_ID/CHAT_PROMPT.md` into a new chat. That file holds the same task, the same rules and the source code, plus a strict reply format that `kit.py apply` reads.
