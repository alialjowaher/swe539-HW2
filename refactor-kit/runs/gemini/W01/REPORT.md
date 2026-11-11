# Refactoring report - W01 Long Method - Gemini

| | |
|---|---|
| Smell | W01 - Long Method (Within class) |
| Class / member | HelpFormatter - appendOptions(A, int, Options, int, int) (lines 407–478) |
| Refactoring applied | Extract Method (×3); Replace Temp with Query where practical |
| LLM / model | Gemini - Gemini 3.1 Pro |
| Mode | agent |
| Code base | rel/commons-cli-1.9.0 (698b238276) -> branch `refactor/W01` commit d1fd3cfe9c |
| Verdict | **PASS** |
| Original tests | 738 passed of 797 (59 skipped) |
| Refactored tests | 738 passed of 797 (59 skipped) - regressions: 0 |
| Test files modified | No |
| Public/protected API | 0 removed or changed, 0 added |
| Files changed | src/main/java/org/apache/commons/cli/HelpFormatter.java (+90 -41) |
| Finish attempts | 1 |

## 1. Smell (from the review sheet)

**Evidence.** 72 lines (NLOC 64), cyclomatic complexity 20, 5 parameters: the largest and most complex method in the library. One body does three jobs: (1) builds each option's "-a,--aaa <arg>" label and tracks the widest one (421–444); (2) writes the optional "Options / Since / Description" header (446–452); (3) pads and writes each row with its description or deprecation text (454–476).

**Technique:** Extract Method (×3); Replace Temp with Query where practical

_Source: review sheet suggestion (column 'Suggested refactoring')._

**How (outline):** Extract buildOptionLabel(Option, lpad) from the first loop body, appendSinceHeader(...) from the showSince block, and appendOptionRow(...) from the second loop body. appendOptions keeps only the sequence: sort → labels → header → rows.

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
> Model: Gemini 3.1 Pro · Mode: agent · Started: 2026-11-10 13:10

### 1. Understanding of the smell
`HelpFormatter.appendOptions(A, int, Options, int, int)` (lines 407–478 in `HelpFormatter.java`) is a Long Method with 72 lines (64 NLOC), cyclomatic complexity 20, and 5 parameters. Rather than doing a single cohesive task at one level of abstraction, its body mixes three distinct responsibilities: (1) building each option's prefix label (`<lpad>-a,--aaa <arg>`) and tracking the maximum column width, (2) formatting and appending the optional "Options / Since / Description" table header when `showSince` is enabled, and (3) padding each option row with its optional `since` value and description/deprecation text and writing the wrapped line.

### 2. Plan
1. Extract `buildOptionLabel(final Option option, final String lpad)` from the first loop body in `appendOptions` to construct and return the `StringBuilder` prefix label for a single `Option`, replacing the loop body with a call to `buildOptionLabel`, then compile and run `HelpFormatterTest`.
2. Extract `appendSinceHeader(final A sb, final int width, final int nextLineTabStop, final int max, final int maxSince, final int leftPad, final String lpad)` from the `if (showSince)` header block in `appendOptions`, replace the block body with a call to `appendSinceHeader`, then compile and run `HelpFormatterTest`.
3. Extract `appendOptionRow(final A sb, final int width, final int nextLineTabStop, final Option option, final StringBuilder prefix, final int max, final int maxSince, final String lpad, final String dpad)` from the second loop body in `appendOptions` so `appendOptions` retains only the high-level sequence (sort → labels → header → rows), then compile and run `HelpFormatterTest` and the full test suite.

### 3. Steps performed

| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | `HelpFormatter.java`: extracted `buildOptionLabel(Option, String)` from the first loop of `appendOptions` | PASS | `HelpFormatterTest` 38/38 passed |
| 2 | `HelpFormatter.java`: extracted `appendSinceHeader(A, int, int, int, int, int, String)` from the `showSince` block of `appendOptions` | PASS | `HelpFormatterTest` 38/38 passed |
| 3 | `HelpFormatter.java`: extracted `appendOptionRow(A, int, int, Option, StringBuilder, int, int, String, String)` from the second loop of `appendOptions` | PASS | `HelpFormatterTest` 38/38 passed; full suite 738/797 passed (59 skipped) |

### 4. Why behaviour is preserved
Each of the three extracted methods (`buildOptionLabel`, `appendSinceHeader`, and `appendOptionRow`) is a direct extraction of the original statements in `appendOptions` with identical control flow, operators, padding calculations, and method calls. All local variables read by each block (`lpad`, `dpad`, `leftPad`, `max`, `maxSince`, `nextLineTabStop`, `width`, `sb`, `option`, `prefixList.get(x++)`) are passed unchanged, and instance fields/methods (`showSince`, `deprecatedFormatFunction`, `longOptSeparator`, `createPadding`, `appendWrappedText`, `getNewLine`, `getOptPrefix`, `getLongOptPrefix`, `getArgName`) are accessed on `this` in the exact same order. In particular:
- `leftPad` and `lpad` are both passed to `appendSinceHeader` so subclasses overriding `createPadding(int)` observe identical calls and arguments.
- `prefixList` still stores `StringBuilder` instances created per option, and `appendOptionRow` constructs a new `StringBuilder(prefix.toString())` before padding, matching the original code.
- Line separator appending between option rows (`if (it.hasNext()) { sb.append(getNewLine()); }`) remains in the outer loop of `appendOptions`.

### 5. Deviations from the plan
None.

### 6. Observations (not changed)
- In `buildOptionLabel` (original line 438), `argName != null ? option.getArgName() : getArgName()` calls `option.getArgName()` a second time even though its result is already stored in the local `argName`. Left unchanged to preserve exact call counts on `Option`.
- In `appendOptionRow` (original line 457), `new StringBuilder(prefixList.get(x++).toString())` copies a `StringBuilder` that is never reused afterwards. Left unchanged.

### 7. Self-assessment
- Smell removed: yes — `appendOptions` now delegates the three detailed formatting tasks to `buildOptionLabel`, `appendSinceHeader`, and `appendOptionRow`, leaving only the high-level coordination sequence (sort options, build labels and compute max width, append optional header, append rows).
- Expected effect on size: NLOC and cyclomatic complexity of `appendOptions` decrease substantially, while total class LOC increases slightly due to the 3 new private method signatures and Javadocs.
- Expected effect on cohesion: Slightly improved or unchanged (LCOM* stays low as the new helper methods access `HelpFormatter`'s formatting fields and methods).
- Expected effect on coupling: Unchanged (CBO remains the same as no new external types are referenced).

## 5. Refactored code (after refactoring)

_The same members after the refactoring, plus any new members or files. Full files: `refactored/`; diff: `changes.patch`._

### [new] `HelpFormatter.java` > `HelpFormatter.appendOptionRow(A,int,int,Option,StringBuilder,int,int,String,String)` (lines 396-429)

```java
    /**
     * Pads and appends a single formatted option row, including its optional since value and description.
     *
     * @param <A> The Appendable implementation.
     * @param sb The Appendable to write to.
     * @param width The number of characters to display per line.
     * @param nextLineTabStop The position on the next line for the first tab.
     * @param option The Option being rendered.
     * @param prefix The pre-built option prefix label.
     * @param max The maximum option column width including the since column.
     * @param maxSince The width reserved for the since column.
     * @param lpad The left padding string.
     * @param dpad The description padding string.
     * @throws IOException if an I/O error occurs.
     */
    private <A extends Appendable> void appendOptionRow(final A sb, final int width, final int nextLineTabStop, final Option option,
            final StringBuilder prefix, final int max, final int maxSince, final String lpad, final String dpad) throws IOException {
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

### [changed] `HelpFormatter.java` > `HelpFormatter.appendOptions(A,int,Options,int,int)` (lines 431-475)

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
            appendOptionRow(sb, width, nextLineTabStop, option, prefixList.get(x++), max, maxSince, lpad, dpad);
            if (it.hasNext()) {
                sb.append(getNewLine());
            }
        }
        return sb;
    }
```

### [new] `HelpFormatter.java` > `HelpFormatter.appendSinceHeader(A,int,int,int,int,int,String)` (lines 477-497)

```java
    /**
     * Appends the "Options / Since / Description" header line when {@code showSince} is enabled.
     *
     * @param <A> The Appendable implementation.
     * @param sb The Appendable to write to.
     * @param width The number of characters to display per line.
     * @param nextLineTabStop The position on the next line for the first tab.
     * @param max The maximum option column width including the since column.
     * @param maxSince The width reserved for the since column.
     * @param leftPad The number of characters of left padding.
     * @param lpad The left padding string.
     * @throws IOException if an I/O error occurs.
     */
    private <A extends Appendable> void appendSinceHeader(final A sb, final int width, final int nextLineTabStop, final int max, final int maxSince,
            final int leftPad, final String lpad) throws IOException {
        final StringBuilder optHeader = new StringBuilder(HEADER_OPTIONS).append(createPadding(max - maxSince - HEADER_OPTIONS.length() + leftPad))
                .append(HEADER_SINCE);
        optHeader.append(createPadding(max - optHeader.length())).append(lpad).append(HEADER_DESCRIPTION);
        appendWrappedText(sb, width, nextLineTabStop, optHeader.toString());
        sb.append(getNewLine());
    }
```

### [new] `HelpFormatter.java` > `HelpFormatter.buildOptionLabel(Option,String)` (lines 539-567)

```java
    /**
     * Builds the option prefix label containing the left padding, short/long option names, and optional argument name.
     *
     * @param option The Option to format.
     * @param lpad The left padding string.
     * @return A StringBuilder with the formatted option label.
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
                // if the option has a blank argname
                optBuf.append(' ');
            } else {
                optBuf.append(option.hasLongOpt() ? longOptSeparator : " ");
                optBuf.append("<").append(argName != null ? option.getArgName() : getArgName()).append(">");
            }
        }
        return optBuf;
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
