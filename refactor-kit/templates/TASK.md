# TASK - refactor smell {{SMELL_ID}} ({{SMELL_NAME}}) in Apache Commons CLI 1.9.0

| | |
|---|---|
| Run | {{LLM_NAME}} · {{MODEL}} · mode: {{MODE}} · started {{DATE}} |
| Workspace (edit only here) | `{{WORKSPACE}}` |
| Branch | `{{BRANCH}}`, created from `{{BASE_REF}}` (commit {{BASE_SHORT}}) |
| Your process notes | `{{RUN_DIR}}/process.md` |
| Original code saved in | `{{RUN_DIR}}/original/` |

## 1. The smell

{{SMELL_TABLE}}

## 2. The refactoring to apply

{{TECHNIQUE}}
Apply **this** technique and nothing else. If you believe it cannot be applied without breaking a rule below, stop, explain why in process.md section 5, and run `finish` without making a different refactoring.

## 3. Where the code is (original, before refactoring)

{{TARGET_LIST}}

Most relevant test classes: {{TESTS}}

{{TARGET_CODE}}

## 4. Rules (non-negotiable)

{{RULES}}

## 5. Definition of done

- `python kit.py test --llm "{{LLM_NAME}}"` shows the same number of passing tests as the original run (see `{{RUN_DIR}}/tests_original.json`).
- No file under `src/test/` changed, and no public or protected API was removed or changed.
- The smell is addressed with the technique in section 2, and nothing else changed.
- `process.md` is complete: every _italic guidance line_ has been replaced.
- `python kit.py finish --smell {{SMELL_ID}} --llm "{{LLM_NAME}}"` has run and printed a verdict.

## 6. Commands

| Purpose | Command |
|---|---|
| Quick test (one class) | `python kit.py test --llm "{{LLM_NAME}}" --only {{FIRST_TEST}}` |
| Full test suite | `python kit.py test --llm "{{LLM_NAME}}"` |
| Finish the run | `python kit.py finish --smell {{SMELL_ID}} --llm "{{LLM_NAME}}"` |
