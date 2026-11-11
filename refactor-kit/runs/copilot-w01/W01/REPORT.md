# Refactoring report - W01 Long Method - Copilot-W01

| | |
|---|---|
| Smell | W01 - Long Method (Within class) |
| Class / member | HelpFormatter - appendOptions(A, int, Options, int, int) (lines 407–478) |
| Refactoring applied | Extract Method (×3) |
| LLM / model | Copilot-W01 - Copilot SDK in VS Code (2026-11-10) |
| Mode | agent |
| Code base | rel/commons-cli-1.9.0 (698b238276) -> branch `refactor/W01` commit ff0d8ef2c7 |
| Verdict | **PASS** |
| Original tests | 738 passed of 797 (59 skipped) |
| Refactored tests | 738 passed of 797 (59 skipped) - regressions: 0 |
| Test files modified | No |
| Public/protected API | 0 removed or changed, 0 added |
| Files changed | src/main/java/org/apache/commons/cli/HelpFormatter.java (+87 -41) |
| Finish attempts | 1 |

## 1. Smell (from the review sheet)

**Evidence.** 72 lines (NLOC 64), cyclomatic complexity 20, 5 parameters: the largest and most complex method in the library. One body does three jobs: (1) builds each option's "-a,--aaa <arg>" label and tracks the widest one (421–444); (2) writes the optional "Options / Since / Description" header (446–452); (3) pads and writes each row with its description or deprecation text (454–476).

**Technique:** Extract Method (×3)

_Source: review sheet suggestion (column 'Suggested refactoring')._

**How (outline):** Extract buildOptionLabel(Option, lpad) from the first loop body, appendSinceHeader(...) from the showSince block, and appendOptionRow(...) from the second loop body. appendOptions keeps only the sequence: sort → labels → header → rows. Replace Temp with Query was considered for remaining locals but was not practical without repeated overridable calls or extra passes.

**Risks to watch:** Low. Package-private method; HelpFormatterTest pins the exact output strings, so behaviour changes are caught.

**Expected effect on metrics:** Size: NLOC and complexity of appendOptions drop sharply; class gains ~3 private methods. Cohesion / coupling: about unchanged.


## 2. Original code (before refactoring)

_Every member the refactoring changed or removed, as it was in the original code. Full files: `original/`._

### [changed] `HelpFormatter.java` > `HelpFormatter.appendOptions(A,int,Options,int,int)` (lines 396-478)

```java
    /**
     * Renders the specified Options and return the rendered Options in a StringBuffer.
     *
     * @param sb The StringBuffer to place the rendered Options into.
     * @param width The number of characters to display per line
     * @param options The command line Options
     * @param leftPad the number of characters of padding to be prefixed to each line
     * @param descPad the number of characters of padding to be prefixed to each description line
     * @return the StringBuffer with the rendered Options contents.
     * @throws IOException if an I/O error occurs.
     */
    <A extends Appendable> A appendOptions(final A sb, final int width, final Options options, final int leftPad, final int descPad) throws IOException {
        final String lpad = createPadding(leftPad);
        final String dpad = createPadding(descPad);
        // first create list containing only <lpad>-a,--aaa where
        // -a is opt and --aaa is long opt; in parallel look for
        // the longest opt string this list will be then used to
        // sort options ascending
        int max = 0;
        final int maxSince = showSince ? determineMaxSinceLength(options) + leftPad : 0;
        final List<StringBuilder> prefixList = new ArrayList<>();
        final List<Option> optList = options.helpOptions();
        if (getOptionComparator() != null) {
            Collections.sort(optList, getOptionComparator());
        }
        for (final Option option : optList) {
            final StringBuilder optBuf = new StringBuilder();
            if (option.getOpt() == null) {
                optBuf.append(lpad).append("   ").append(getLongOptPrefix()).append(option.getLongOpt());
            } else {
                optBuf.append(lpad).append(getOptPrefix()).append(option.getOpt());
                if (option.hasLongOpt()) {
                    optBuf.append(',').append(getLongOptPrefix()).append(option.getLongOpt());
                }
            }
            if (option.hasArg()) {
                final String argName = option.getArgName();
                if (argName != null && argName.isEmpty()) {
                    // if the option has a blank argname
                    optBuf.append(' ');
                } else {
                    optBuf.append(option.hasLongOpt() ? longOptSeparator : " ");
                    optBuf.append("<").append(argName != null ? option.getArgName() : getArgName()).append(">");
                }
            }

            prefixList.add(optBuf);
            max = Math.max(optBuf.length() + maxSince, max);
        }
        final int nextLineTabStop = max + descPad;
        if (showSince) {
            final StringBuilder optHeader = new StringBuilder(HEADER_OPTIONS).append(createPadding(max - maxSince - HEADER_OPTIONS.length() + leftPad))
                    .append(HEADER_SINCE);
            optHeader.append(createPadding(max - optHeader.length())).append(lpad).append(HEADER_DESCRIPTION);
            appendWrappedText(sb, width, nextLineTabStop, optHeader.toString());
            sb.append(getNewLine());
        }

        int x = 0;
        for (final Iterator<Option> it = optList.iterator(); it.hasNext();) {
            final Option option = it.next();
            final StringBuilder optBuf = new StringBuilder(prefixList.get(x++).toString());
            if (optBuf.length() < max) {
                optBuf.append(createPadding(max - maxSince - optBuf.length()));
                if (showSince) {
                    optBuf.append(lpad).append(option.getSince() == null ? "-" : option.getSince());
                }
                optBuf.append(createPadding(max - optBuf.length()));
            }
            optBuf.append(dpad);

            if (deprecatedFormatFunction != null && option.isDeprecated()) {
                optBuf.append(deprecatedFormatFunction.apply(option).trim());
            } else if (option.getDescription() != null) {
                optBuf.append(option.getDescription());
            }
            appendWrappedText(sb, width, nextLineTabStop, optBuf.toString());
            if (it.hasNext()) {
                sb.append(getNewLine());
            }
        }
        return sb;
    }
```

## 3. Original tests (on the untouched code)

- Result: **738 passed of 797 (59 skipped)**
- Log: `tests_original.log`

## 4. Refactoring process

> Written by the LLM during the run. Keep the headings and replace every _italic guidance line_ with your own text.
> Model: Copilot SDK in VS Code (2026-11-10) · Mode: agent · Started: 2026-11-10 21:19

### 1. Understanding of the smell
`HelpFormatter.appendOptions` combined option-label construction, optional header rendering, and option-row rendering in one 72-line method. These separate responsibilities made the method the largest and most complex method in the class. The affected code is in `src/main/java/org/apache/commons/cli/HelpFormatter.java`, originally around lines 407-478.

### 2. Plan
1. Extract the option-label construction into private `buildOptionLabel(Option, String)`, return the constructed label, replace the original fragment with a call, and run the targeted test.
2. Extract the `showSince` header rendering into private `appendSinceHeader(...)`, pass the required values, replace the original block with a call, and run the targeted test.
3. Extract one option-row rendering into private `appendOptionRow(...)`, pass the existing values and option label, replace the original loop body with a call, and run the targeted test.
4. Run the full test suite and review the diff for unrelated changes.


### 3. Steps performed
The first agent attempts were blocked by a temporary Maven/Java launch problem. After the local JDK/Maven environment was repaired, the targeted test, full suite, finish validation, API comparison, and metrics command completed successfully.

| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | Extracted `buildOptionLabel` and replaced the first loop fragment in `HelpFormatter.appendOptions`. | Passed after environment repair | Targeted test passed |
| 2 | Extracted `appendSinceHeader` and replaced the `showSince` block. | Passed | Targeted test passed |
| 3 | Extracted `appendOptionRow` and replaced the second loop body. | Passed | `HelpFormatterTest`: 38 passed |
| 4 | Reviewed the final diff and ran the full suite command. | Passed | Full suite: 738 passed of 797, 59 skipped |
| 5 | Ran `finish` and `metrics` on the isolated run. | Passed; API removed/changed: 0 | Finish: 738 passed, 0 regressions; metrics recorded |

### 4. Why behaviour is preserved
Each extracted method contains the original statements in the original order, with only parameters added for values formerly in the enclosing method. Label construction preserves option prefixes, argument names, blank argument handling, and padding. Header and row methods preserve wrapping, newline placement, deprecation formatting, descriptions, and `showSince` behavior. `appendOptions` still sorts and iterates the same lists and returns the same appendable; no public or protected API was changed.

### 5. Deviations from the plan
The first targeted attempts were blocked by a temporary Maven/Java launch problem and were rerun successfully after the local tool environment was repaired. Replace Temp with Query was considered but not applied because it would add repeated overridable calls or extra passes. No other refactoring was applied.

### 6. Observations (not changed)
None.

### 7. Self-assessment
- Smell removed: yes; the three responsibilities now have named private methods and `appendOptions` retains the orchestration sequence.
- Expected effect on size: `appendOptions` is substantially shorter; the class gains three small helpers.
- Expected effect on cohesion: improved within `appendOptions`, with each helper focused on one rendering responsibility.
- Expected effect on coupling: approximately unchanged; helpers use existing formatter state and values from the original method.

## 5. Refactored code (after refactoring)

_The same members after the refactoring, plus any new members or files. Full files: `refactored/`; diff: `changes.patch`._

### [changed] `HelpFormatter.java` > `HelpFormatter.appendOptions(A,int,Options,int,int)` (lines 396-440)

```java
    /**
     * Renders the specified Options and return the rendered Options in a StringBuffer.
     *
     * @param sb The StringBuffer to place the rendered Options into.
     * @param width The number of characters to display per line
     * @param options The command line Options
     * @param leftPad the number of characters of padding to be prefixed to each line
     * @param descPad the number of characters of padding to be prefixed to each description line
     * @return the StringBuffer with the rendered Options contents.
     * @throws IOException if an I/O error occurs.
     */
    <A extends Appendable> A appendOptions(final A sb, final int width, final Options options, final int leftPad, final int descPad) throws IOException {
        final String lpad = createPadding(leftPad);
        final String dpad = createPadding(descPad);
        // first create list containing only <lpad>-a,--aaa where
        // -a is opt and --aaa is long opt; in parallel look for
        // the longest opt string this list will be then used to
        // sort options ascending
        int max = 0;
        final int maxSince = showSince ? determineMaxSinceLength(options) + leftPad : 0;
        final List<StringBuilder> prefixList = new ArrayList<>();
        final List<Option> optList = options.helpOptions();
        if (getOptionComparator() != null) {
            Collections.sort(optList, getOptionComparator());
        }
        for (final Option option : optList) {
            final StringBuilder optBuf = buildOptionLabel(option, lpad);
            prefixList.add(optBuf);
            max = Math.max(optBuf.length() + maxSince, max);
        }
        final int nextLineTabStop = max + descPad;
        if (showSince) {
            appendSinceHeader(sb, width, nextLineTabStop, max, maxSince, leftPad, lpad);
        }

        int x = 0;
        for (final Iterator<Option> it = optList.iterator(); it.hasNext();) {
            final Option option = it.next();
            appendOptionRow(sb, width, nextLineTabStop, max, maxSince, dpad, lpad, option, prefixList.get(x++));
            if (it.hasNext()) {
                sb.append(getNewLine());
            }
        }
        return sb;
    }
```

### [new] `HelpFormatter.java` > `HelpFormatter.buildOptionLabel(Option,String)` (lines 442-469)

```java
    /**
     * Builds the label for an option.
     *
     * @param option the option to label
     * @param lpad the left padding
     * @return the option label
     */
    private StringBuilder buildOptionLabel(final Option option, final String lpad) {
        final StringBuilder optBuf = new StringBuilder();
        if (option.getOpt() == null) {
            optBuf.append(lpad).append("   ").append(getLongOptPrefix()).append(option.getLongOpt());
        } else {
            optBuf.append(lpad).append(getOptPrefix()).append(option.getOpt());
            if (option.hasLongOpt()) {
                optBuf.append(',').append(getLongOptPrefix()).append(option.getLongOpt());
            }
        }
        if (option.hasArg()) {
            final String argName = option.getArgName();
            if (argName != null && argName.isEmpty()) {
                optBuf.append(' ');
            } else {
                optBuf.append(option.hasLongOpt() ? longOptSeparator : " ");
                optBuf.append("<").append(argName != null ? option.getArgName() : getArgName()).append(">");
            }
        }
        return optBuf;
    }
```

### [new] `HelpFormatter.java` > `HelpFormatter.appendSinceHeader(A,int,int,int,int,int,String)` (lines 471-490)

```java
    /**
     * Appends the header for option since values.
     *
     * @param sb the output appendable
     * @param width the output width
     * @param nextLineTabStop the next line tab stop
     * @param max the maximum option label width
     * @param maxSince the maximum since value width
     * @param leftPad the left padding size
     * @param lpad the left padding
     * @throws IOException if an I/O error occurs
     */
    private <A extends Appendable> void appendSinceHeader(final A sb, final int width, final int nextLineTabStop, final int max,
            final int maxSince, final int leftPad, final String lpad) throws IOException {
        final StringBuilder optHeader = new StringBuilder(HEADER_OPTIONS).append(createPadding(max - maxSince - HEADER_OPTIONS.length() + leftPad))
                .append(HEADER_SINCE);
        optHeader.append(createPadding(max - optHeader.length())).append(lpad).append(HEADER_DESCRIPTION);
        appendWrappedText(sb, width, nextLineTabStop, optHeader.toString());
        sb.append(getNewLine());
    }
```

### [new] `HelpFormatter.java` > `HelpFormatter.appendOptionRow(A,int,int,int,int,String,String,Option,StringBuilder)` (lines 492-524)

```java
    /**
     * Appends one formatted option row.
     *
     * @param sb the output appendable
     * @param width the output width
     * @param nextLineTabStop the next line tab stop
     * @param max the maximum option label width
     * @param maxSince the maximum since value width
     * @param dpad the description padding
     * @param lpad the left padding
     * @param option the option to append
     * @param prefix the option label
     * @throws IOException if an I/O error occurs
     */
    private <A extends Appendable> void appendOptionRow(final A sb, final int width, final int nextLineTabStop, final int max,
            final int maxSince, final String dpad, final String lpad, final Option option, final StringBuilder prefix) throws IOException {
        final StringBuilder optBuf = new StringBuilder(prefix.toString());
        if (optBuf.length() < max) {
            optBuf.append(createPadding(max - maxSince - optBuf.length()));
            if (showSince) {
                optBuf.append(lpad).append(option.getSince() == null ? "-" : option.getSince());
            }
            optBuf.append(createPadding(max - optBuf.length()));
        }
        optBuf.append(dpad);

        if (deprecatedFormatFunction != null && option.isDeprecated()) {
            optBuf.append(deprecatedFormatFunction.apply(option).trim());
        } else if (option.getDescription() != null) {
            optBuf.append(option.getDescription());
        }
        appendWrappedText(sb, width, nextLineTabStop, optBuf.toString());
    }
```

## 6. Original tests on the refactored code

- Result: **738 passed of 797 (59 skipped)**
- Regressions (passed before, not now): **0**
- Log: `tests_refactored.log`

| Test class | Original (passed/total) | Refactored (passed/total) |
|---|---|---|
| AlreadySelectedExceptionTest | 1/1 | 1/1 |
| ApplicationTest | 5/5 | 5/5 |
| ArgumentIsOptionTest | 3/3 | 3/3 |
| BasicParserTest | 39/66 | 39/66 |
| BugCLI133Test | 1/1 | 1/1 |
| BugCLI13Test | 1/1 | 1/1 |
| BugCLI148Test | 2/2 | 2/2 |
| BugCLI162Test | 4/4 | 4/4 |
| BugCLI18Test | 1/1 | 1/1 |
| BugCLI252Test | 2/2 | 2/2 |
| BugCLI265Test | 3/3 | 3/3 |
| BugCLI266Test | 2/2 | 2/2 |
| BugCLI312Test | 3/3 | 3/3 |
| BugCLI325Test | 1/1 | 1/1 |
| BugCLI71Test | 4/4 | 4/4 |
| BugsTest | 13/13 | 13/13 |
| CommandLineTest | 121/121 | 121/121 |
| ConverterTests | 14/14 | 14/14 |
| DefaultParserTest | 74/74 | 74/74 |
| DeprecatedAttributesTest | 4/4 | 4/4 |
| DisablePartialMatchingTest | 2/2 | 2/2 |
| GnuParserTest | 44/66 | 44/66 |
| HelpFormatterTest | 38/38 | 38/38 |
| OptionBuilderTest | 9/9 | 9/9 |
| OptionGroupTest | 13/13 | 13/13 |
| OptionTest | 21/21 | 21/21 |
| OptionValidatorTest | 115/115 | 115/115 |
| OptionsTest | 15/15 | 15/15 |
| ParseExceptionTest | 1/1 | 1/1 |
| PatternOptionBuilderTest | 10/10 | 10/10 |
| PosixParserTest | 56/66 | 56/66 |
| SolrCliTest | 1/1 | 1/1 |
| SolrCreateToolTest | 2/2 | 2/2 |
| TypeHandlerTest | 63/63 | 63/63 |
| UnrecognizedOptionExceptionTest | 1/1 | 1/1 |
| UtilTest | 2/2 | 2/2 |
| ValueTest | 40/40 | 40/40 |
| ValuesTest | 7/7 | 7/7 |

## 7. Checks

- Test files untouched: yes
- Other non-source files changed: none
- Public/protected API removed or changed: 0
- Public/protected API added: 0

## 8. Files in this run folder

| File | What it is |
|---|---|
| `PROMPT_master.md` | the unified prompt (master copy at start) |
| `TASK.md / CHAT_PROMPT.md` | the run-specific task given to the LLM (agent / chat mode) |
| `response*.md` | the LLM's reply / transcript (saved by you) |
| `process.md` | the refactoring process written by the LLM |
| `original/` | original versions of every involved file |
| `original_smell_location.java.txt` | original code of the smell location |
| `refactored/` | refactored versions of every changed file |
| `changes.patch` | unified diff against the original |
| `code_changes.json` | member-by-member before/after |
| `tests_original.json/.log` | original test suite on the original code |
| `tests_refactored.json/.log` | original test suite on the refactored code |
| `api_original.txt / api_refactored.txt / api_diff.txt` | public/protected API comparison |
| `run.json` | run metadata |
