# Refactoring report - W01 Long Method - Claude

| | |
|---|---|
| Smell | W01 - Long Method (Within class) |
| Class / member | HelpFormatter - appendOptions(A, int, Options, int, int) (lines 407–478) |
| Refactoring applied | Extract Method (×3); Replace Temp with Query where practical |
| LLM / model | Claude - Claude Opus 5.5 (claude-opus-5-5) |
| Mode | agent |
| Code base | rel/commons-cli-1.9.0 (698b238276) -> branch `refactor/W01` commit 85c082a0fb |
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
> Model: Claude Opus 5.5 (claude-opus-5-5) · Mode: agent · Started: 2026-11-10 09:47

### 1. Understanding of the smell
`HelpFormatter.appendOptions(A, int, Options, int, int)` (`HelpFormatter.java`, lines 407–478) is a Long Method: 72 lines with cyclomatic complexity 20, and one body doing three separate jobs. Lines 421–444 build each option's `<lpad>-a,--aaa <arg>` label and track the widest one. Lines 446–452 write the optional `Options / Since / Description` header. Lines 454–476 pad each label, add the since column and the description (or deprecation text), and write the row. You have to read every branch of all three jobs to see the method's overall shape (sort → labels → header → rows). That is why it is a Long Method and why Extract Method is the right cure.

### 2. Plan
Technique: Extract Method ×3, plus Replace Temp with Query where practical. Each extraction follows Fowler's mechanics: create a private method named after the intention, copy the fragment verbatim, pass the locals it reads as parameters (and return the one it produces), replace the fragment with a call, then compile and run `HelpFormatterTest`.

1. **Extract `buildOptionLabel(Option, String lpad)`** from the body of the first loop (lines 422–440). It reads `option` and `lpad` and returns the label `StringBuilder`. The loop keeps `prefixList.add(...)` and the `max` update, because those accumulate across iterations.
2. **Extract `appendSinceHeader(sb, width, nextLineTabStop, max, maxSince, leftPad, lpad)`** from the body of the `if (showSince)` block (lines 447–451). The `if (showSince)` stays in `appendOptions`, so the call sequence stays visible there.
3. **Extract `appendOptionRow(sb, width, nextLineTabStop, option, label, max, maxSince, lpad, dpad)`** from the body of the second loop (lines 456–472). The `if (it.hasNext()) sb.append(getNewLine())` separator stays in the loop, because it depends on the iterator and not on the row.
4. **Replace Temp with Query: check each remaining temp** (`lpad`, `dpad`, `max`, `maxSince`, `nextLineTabStop`, `prefixList`) and apply it only where the query adds no calls to overridable methods and no extra passes over the options. See section 4/5 for the outcome.
5. Run the full suite with `python kit.py test --llm "Claude"` and confirm 738 passed / 0 failed / 59 skipped, the same as the baseline.

### 3. Steps performed

| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | `HelpFormatter.java`: Extract Method. New private `buildOptionLabel(Option, String)` holds the first loop's label-building body verbatim and returns the label `StringBuilder`. In `appendOptions`, the loop body is now `buildOptionLabel(option, lpad)` + `prefixList.add` + the `max` update. | OK | HelpFormatterTest 38/38 |
| 2 | `HelpFormatter.java`: Extract Method. New private `appendSinceHeader(A, int, int, int, int, int, String)` holds the body of the `if (showSince)` block verbatim (header build, `appendWrappedText`, new line). The `if (showSince)` guard stays in `appendOptions`. | OK | HelpFormatterTest 38/38 |
| 3 | `HelpFormatter.java`: Extract Method. New private `appendOptionRow(A, int, int, Option, String, int, int, String, String)` holds the second loop's row body verbatim (padding, since column, description or deprecation text, `appendWrappedText`). The between-rows `getNewLine()` stays in the loop, because it depends on the iterator. | OK | HelpFormatterTest 38/38 |
| 4 | Replace Temp with Query: checked every remaining temp in `appendOptions` and applied none (reasons in sections 4 and 5). No code change. | n/a | n/a |
| 5 | Full suite on the finished refactoring. | OK | 738 passed / 0 failed / 0 errors / 59 skipped of 797 (identical to the baseline) |

### 4. Why behaviour is preserved
- **The code was moved verbatim.** Each extracted method contains exactly the statements that were in the fragment, in the same order, with the same literals (`"   "`, `','`, `' '`, `"<"`, `">"`, `"-"`), the same `trim()` on the deprecation text, and the same deprecated-before-description precedence. The output is therefore built from the same appends in the same sequence.
- **Every value the fragments read goes in as a parameter, and nothing is recomputed.** `lpad`, `dpad`, `max`, `maxSince`, `nextLineTabStop` and `leftPad` are computed once in `appendOptions`, exactly as before. This matters because `createPadding` (protected), `getOptPrefix`, `getLongOptPrefix`, `getArgName`, `getNewLine` and `getOptionComparator` (public) can all be overridden by subclasses. The refactored code calls each of them the same number of times, in the same order and with the same arguments as the original, so subclasses see no difference. The double `option.getArgName()` call in the label code was also kept.
- **Copy semantics are the same.** The original created each row as `new StringBuilder(prefixList.get(x++).toString())`. The call now evaluates `prefixList.get(x++).toString()` at the same point, right after `it.next()`, and `appendOptionRow` wraps it in `new StringBuilder(label)`. The stored labels are still never mutated.
- **The control flow is the same.** The `if (showSince)` guard, the `if (optBuf.length() < max)` padding guard and the `if (it.hasNext())` row separator are unchanged, so header presence, the padding cases and the lack of a trailing new line after the last row all stay the same.
- **Exceptions are the same.** The two new methods that write to the `Appendable` declare `throws IOException` and propagate it unchanged. No catch blocks were added.
- **The API is unchanged.** All new members are `private`. The signature, visibility and Javadoc of `appendOptions` are untouched, and no test file was modified.
- **Replace Temp with Query: why it was not applied.** `lpad` and `dpad` as queries would add calls to the overridable `createPadding` (one per row, not one per table). `maxSince` as a query would re-run `determineMaxSinceLength`, a full pass over the options, on every use. `max` is accumulated inside the label loop, so it can't be a side-effect-free query without a second pass. `nextLineTabStop` and `prefixList` depend on those. Each candidate would add calls a subclass can observe, or extra work, so none was practical. The temps stay as locals and are passed to the extracted methods as parameters.

### 5. Deviations from the plan
- None in the refactoring itself. The steps were done as planned. Step 4 (Replace Temp with Query) ended with "not practical for any temp", as the plan allowed ("only where…"). The reasons are in section 4.
- Process note: my first attempt at step 1 was blocked by the agent's own sandbox before anything was written to disk. The HelpFormatterTest run from that attempt therefore ran on unchanged code and is not counted above. After the user changed the session setting, step 1 was re-applied and tested normally. This had no effect on the code.
- `finish` attempts: 1 (see the verdict in REPORT.md).

### 6. Observations (not changed)
- **New Long Parameter List:** `appendOptionRow` takes 9 parameters and `appendSinceHeader` takes 7. The shared table layout (`max`, `maxSince`, `lpad`, `dpad`, `nextLineTabStop`) is held in locals, and Extract Method has to pass them in. Introduce Parameter Object (for example a small table-layout holder) would fix this, but it is a different technique and outside this run.
- **Redundant call:** in the label code, `option.getArgName()` is stored in `argName` and then called again in `argName != null ? option.getArgName() : getArgName()`. I kept both calls to preserve behaviour.
- **Stale comment:** the comment above the label loop says the list "will be then used to sort options ascending", but sorting happens earlier, through `getOptionComparator()`. I left it, because comment edits are out of scope.
- **Javadoc:** the `appendOptions` Javadoc still talks about "StringBuffer" and has no `@param <A>`. Left unchanged.
- **Duplicated label logic** (smell B01): the same "-opt / --longOpt / <arg>" label logic is also built in `appendOption` and in `OptionGroup.toString`.
- **Baseline:** 59 of the 797 original tests are skipped by the project itself (`@Disabled` cases in BasicParserTest, GnuParserTest and PosixParserTest). None fail.
- **Session:** at the user's request, this run and the B01 run were done in the same agent session, not in separate fresh sessions.

### 7. Self-assessment
- Smell removed: **yes.** `appendOptions` went from 72 lines (NLOC 64, CC 20) to about 34 lines that only sequence the steps (sort → labels → header → rows). Each of its three former jobs is now a named private method. What remains is the long parameter lists of the helpers (section 6).
- Expected effect on size: `appendOptions` NLOC and cyclomatic complexity drop sharply (CC roughly 20 → 6). The three new methods have about CC 7, 1 and 6. Class NLOC goes up slightly (new signatures and Javadoc), and the method count grows by 3.
- Expected effect on cohesion: about unchanged. The new private methods use the same fields as before (`showSince`, `longOptSeparator`, `deprecatedFormatFunction`). A per-method metric such as LCOM may move slightly because there are more methods.
- Expected effect on coupling: unchanged. No new types are referenced, and `HelpFormatter` still depends on the same classes (`Option`, `Options`, `Appendable`, etc.).

## 5. Refactored code (after refactoring)

_The same members after the refactoring, plus any new members or files. Full files: `refactored/`; diff: `changes.patch`._

### [new] `HelpFormatter.java` > `HelpFormatter.appendOptionRow(A,int,int,Option,String,int,int,String,String)` (lines 396-429)

```java
    /**
     * Appends one row of the options table: the padded label, the optional since column and the description (or the deprecation text).
     *
     * @param <A> The Appendable implementation.
     * @param sb The Appendable to place the row into.
     * @param width The number of characters to display per line.
     * @param nextLineTabStop The position on the next line for the first tab.
     * @param option the Option to render.
     * @param label the label of the option, as built by {@link #buildOptionLabel(Option, String)}.
     * @param max The width of the label and since columns together.
     * @param maxSince The width of the since column, including the left padding.
     * @param lpad the left padding string.
     * @param dpad the description padding string.
     * @throws IOException if an I/O error occurs.
     */
    private <A extends Appendable> void appendOptionRow(final A sb, final int width, final int nextLineTabStop, final Option option, final String label,
            final int max, final int maxSince, final String lpad, final String dpad) throws IOException {
        final StringBuilder optBuf = new StringBuilder(label);
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
            appendOptionRow(sb, width, nextLineTabStop, option, prefixList.get(x++).toString(), max, maxSince, lpad, dpad);
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
     * Appends the "Options / Since / Description" header line of the options table, followed by a new line.
     *
     * @param <A> The Appendable implementation.
     * @param sb The Appendable to place the header into.
     * @param width The number of characters to display per line.
     * @param nextLineTabStop The position on the next line for the first tab.
     * @param max The width of the label and since columns together.
     * @param maxSince The width of the since column, including the left padding.
     * @param leftPad the number of characters of padding to be prefixed to each line.
     * @param lpad the left padding string.
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
     * Builds the left-hand label of an option row in the options table, for example {@code <lpad>-a,--aaa <arg>}.
     *
     * @param option the Option to build the label for.
     * @param lpad the left padding to prefix the label with.
     * @return a new StringBuilder holding the label.
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
