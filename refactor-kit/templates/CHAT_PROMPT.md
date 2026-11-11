# Refactoring task - smell {{SMELL_ID}} ({{SMELL_NAME}}) in Apache Commons CLI 1.9.0

You are a careful Java engineer doing **one behaviour-preserving refactoring** (Fowler, *Refactoring*, 2nd ed.) on Apache Commons CLI 1.9.0 (tag `{{TAG}}`). This is part of a controlled experiment: several LLMs get exactly this task, and the results are judged by the project's original test suite, a public-API check and code metrics. You cannot run code here. The user will apply your files, compile them and run the original tests.

## 1. The smell

{{SMELL_TABLE}}

## 2. The refactoring to apply

{{TECHNIQUE}}
Apply **this** technique and nothing else. If you believe it cannot be applied without breaking a rule below, say so in section 5 of your process notes and return no files.

## 3. Where the code is

{{TARGET_LIST}}

The full original source of these files is in section 6. Other files in the package: {{PACKAGE_FILES}}. If you need one of them, ask for it by name and stop.

## 4. Rules (non-negotiable)

{{RULES}}

## 5. What to send back (strict format)

Reply with exactly these two parts and nothing after them.

**Part A**, starting with the heading `## Refactoring process`, containing these sub-headings in this order:
`### 1. Understanding of the smell`, `### 2. Plan`, `### 3. Steps performed` (a table: # | What changed | Compile | Tests; write "not run" in the last two columns), `### 4. Why behaviour is preserved`, `### 5. Deviations from the plan`, `### 6. Observations (not changed)`, `### 7. Self-assessment` (smell removed? expected effect on size, cohesion and coupling).

**Part B**, starting with the heading `## Changed files`, containing one block per file you changed or created:

### FILE: {{SOURCE_ROOT}}/Example.java
```java
(the COMPLETE content of the file, from the license header to the last closing brace)
```

- Send complete files only. Never use "...", "// rest unchanged", "// existing code" or partial snippets.
- If your reply would be cut off, stop at the end of a file block and write `CONTINUE`; the user will ask you to continue.
- Do not include files you did not change, and never include test files.

## 6. Original source code

{{SOURCE_FILES}}
