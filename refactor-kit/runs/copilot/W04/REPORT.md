# Refactoring report - W04 Long Parameter List - Copilot

| | |
|---|---|
| Smell | W04 - Long Parameter List (Within class) |
| Class / member | HelpFormatter - printHelp(PrintWriter, int, String, String, Options, int, int, String, boolean) (lines 736–753 (also 717–720)) |
| Refactoring applied | Introduce Parameter Object; Preserve Whole Object |
| LLM / model | Copilot - Copilot SDK in VS Code (2026-11-10) |
| Mode | agent |
| Code base | rel/commons-cli-1.9.0 (698b238276) -> branch `refactor/W04` commit 462dc8c7fb |
| Verdict | **PASS** |
| Original tests | 738 passed of 797 (59 skipped) |
| Refactored tests | 738 passed of 797 (59 skipped) - regressions: 0 |
| Test files modified | No |
| Public/protected API | 0 removed or changed, 0 added |
| Files changed | src/main/java/org/apache/commons/cli/HelpFormatter.java (+43 -14) |
| Finish attempts | 1 |

## 1. Smell (from the review sheet)

**Evidence.** 9 parameters (the overload at 717–720 has 8). Three of them, width / leftPad / descPad, travel together through printHelp (717, 736), printOptions (815), renderOptions (918) and appendOptions (407), while the class already stores the same values as fields (defaultWidth, defaultLeftPad, defaultDescPad).

**Technique:** Introduce Parameter Object; Preserve Whole Object

_Source: review sheet suggestion (column 'Suggested refactoring')._

**How (outline):** Add a small value class for the layout (width, leftPad, descPad) and route the long overloads through one internal method that takes it. Keep every public printHelp overload as a one-line delegate so the public API does not change.

**Risks to watch:** Medium. Public API: the existing overloads must stay. Output is pinned by HelpFormatterTest.

**Expected effect on metrics:** Size: parameter count on the internal path drops; public method count unchanged. Coupling: +1 (new parameter class).


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

### [changed] `HelpFormatter.java` > `HelpFormatter.printHelp(PrintWriter,int,String,String,Options,int,int,String,boolean)` (lines 722-753)

```java
    /**
     * Prints the help for {@code options} with the specified command line syntax.
     *
     * @param pw the writer to which the help will be written
     * @param width the number of characters to be displayed on each line
     * @param cmdLineSyntax the syntax for this application
     * @param header the banner to display at the beginning of the help
     * @param options the Options instance
     * @param leftPad the number of characters of padding to be prefixed to each line
     * @param descPad the number of characters of padding to be prefixed to each description line
     * @param footer the banner to display at the end of the help
     * @param autoUsage whether to print an automatically generated usage statement
     * @throws IllegalStateException if there is no room to print a line
     */
    public void printHelp(final PrintWriter pw, final int width, final String cmdLineSyntax, final String header, final Options options, final int leftPad,
        final int descPad, final String footer, final boolean autoUsage) {
        if (Util.isEmpty(cmdLineSyntax)) {
            throw new IllegalArgumentException("cmdLineSyntax not provided");
        }
        if (autoUsage) {
            printUsage(pw, width, cmdLineSyntax, options);
        } else {
            printUsage(pw, width, cmdLineSyntax);
        }
        if (header != null && !header.isEmpty()) {
            printWrapped(pw, width, header);
        }
        printOptions(pw, width, options, leftPad, descPad);
        if (footer != null && !footer.isEmpty()) {
            printWrapped(pw, width, footer);
        }
    }
```

### [changed] `HelpFormatter.java` > `HelpFormatter.printOptions(PrintWriter,int,Options,int,int)` (lines 805-822)

```java
    /**
     * Prints the help for the specified Options to the specified writer, using the specified width, left padding and
     * description padding.
     *
     * @param pw The printWriter to write the help to
     * @param width The number of characters to display per line
     * @param options The command line Options
     * @param leftPad the number of characters of padding to be prefixed to each line
     * @param descPad the number of characters of padding to be prefixed to each description line
     */
    public void printOptions(final PrintWriter pw, final int width, final Options options, final int leftPad, final int descPad) {
        try {
            pw.println(appendOptions(new StringBuilder(), width, options, leftPad, descPad));
        } catch (final IOException e) {
            // Cannot happen
            throw new UncheckedIOException(e);
        }
    }
```

### [changed] `HelpFormatter.java` > `HelpFormatter.renderOptions(StringBuffer,int,Options,int,int)` (lines 907-925)

```java
    /**
     * Renders the specified Options and return the rendered Options in a StringBuffer.
     *
     * @param sb The StringBuffer to place the rendered Options into.
     * @param width The number of characters to display per line
     * @param options The command line Options
     * @param leftPad the number of characters of padding to be prefixed to each line
     * @param descPad the number of characters of padding to be prefixed to each description line
     *
     * @return the StringBuffer with the rendered Options contents.
     */
    protected StringBuffer renderOptions(final StringBuffer sb, final int width, final Options options, final int leftPad, final int descPad) {
        try {
            return appendOptions(sb, width, options, leftPad, descPad);
        } catch (final IOException e) {
            // Cannot happen
            throw new UncheckedIOException(e);
        }
    }
```

## 3. Original tests (on the untouched code)

- Result: **738 passed of 797 (59 skipped)**
- Log: `tests_original.log`

## 4. Refactoring process

> Written by the LLM during the run. Keep the headings and replace every _italic guidance line_ with your own text.
> Model: Copilot SDK in VS Code (2026-11-10) · Mode: agent · Started: 2026-11-10 21:02

### 1. Understanding of the smell
`HelpFormatter.printHelp(PrintWriter, int, String, String, Options, int, int, String, boolean)` carried nine arguments, with width, leftPad, and descPad representing one layout concern. Those values were unpacked and passed through `printHelp`, `printOptions`, `renderOptions`, and `appendOptions`, even though the formatter already treats them as a related group. This is a Long Parameter List in `HelpFormatter.java` (the original implementation was around lines 717-753).

### 2. Plan
The plan uses small, independently testable steps: introduce the value object, route the internal path through it, and verify behavior.

1. Add a private immutable `Layout` value object containing width, leftPad, and descPad; route the long `printHelp` overload through one internal method that accepts it.
2. Preserve all existing public overloads while adding internal Layout-based paths for option printing, rendering, and appending; keep the existing parameterized methods as delegates.
3. Run the required targeted test after each coherent change, then run the full Copilot test suite.

### 3. Steps performed
Each row records the implementation step and its validation result in order.

| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | Added `Layout` and routed the nine-parameter `printHelp` implementation through an internal Layout-based method. | Maven test invocation initially blocked by a corrupt cached SPDX plugin artifact. | `HelpFormatterTest`: blocked; Maven could not parse the cached plugin jar. |
| 2 | Routed `printOptions`, `renderOptions`, and `appendOptions` through Layout-based internal methods while preserving their existing signatures. | Compiled after the Maven cache/process issue was cleared. | First retry was blocked by a stale Java process/file lock; subsequent required targeted run passed: 285 run, 0 failures, 0 errors, 59 skipped. |
| 3 | Retried the required targeted test with the bundled JDK/Maven environment. | Pass. | `python kit.py test --llm Copilot --only HelpFormatterTest`: 285 run, 0 failures, 0 errors, 59 skipped. |
| 4 | Adjusted the compatibility delegate so the existing overridable `appendOptions` hook remains observable by `renderOptions` spies/subclasses. | Pass after correction. | Required targeted test rerun: 38 passed. |
| 5 | Ran the final full Copilot test suite after the targeted run. | Pass. | 738 passed, 59 skipped, 0 failures. |

### 4. Why behaviour is preserved
The public `printHelp` overloads remain unchanged and continue to construct the same values; they now create one Layout object before entering the implementation. The old `appendOptions`, `printOptions`, and `renderOptions` signatures remain delegates, and `renderOptions` continues to call the overridable append hook, so existing callers and subclasses retain behavior. The risky spots were padding arithmetic, wrapping width, validation order, and exception interception; the same values and call order are preserved. HelpFormatterTest passed with no failures.

### 5. Deviations from the plan
The first full-suite attempt exposed a compatibility regression in `testRenderSince`; the delegate was corrected to preserve the overridable hook, then the targeted and full suites were rerun successfully. No finish or metrics command was run.

### 6. Observations (not changed)
The repository's test harness initially encountered a corrupt cached Maven plugin and a stale Java process locking test output; these were environment issues, not source changes. No unrelated code smells or behavior were changed.

### 7. Self-assessment
- Smell removed: **yes**; the internal formatting path receives the related layout values as one object, while public overloads are preserved.
- Expected effect on size: Slight increase from the small value class and delegates; internal parameter lists are shorter.
- Expected effect on cohesion: Improved; layout data and layout-dependent operations are grouped.
- Expected effect on coupling: Slight increase due to the new Layout type, as expected.

## 5. Refactored code (after refactoring)

_The same members after the refactoring, plus any new members or files. Full files: `refactored/`; diff: `changes.patch`._

### [new] `HelpFormatter.java` > `HelpFormatter.Layout (declaration)` (lines 70-70)

```java
    private static final class Layout {
```

### [new] `HelpFormatter.java` > `HelpFormatter.Layout#width` (lines 71-71)

```java
        private final int width;
```

### [new] `HelpFormatter.java` > `HelpFormatter.Layout#leftPad` (lines 72-72)

```java
        private final int leftPad;
```

### [new] `HelpFormatter.java` > `HelpFormatter.Layout#descPad` (lines 73-73)

```java
        private final int descPad;
```

### [new] `HelpFormatter.java` > `HelpFormatter.Layout.Layout(int,int,int)` (lines 75-79)

```java
        private Layout(final int width, final int leftPad, final int descPad) {
            this.width = width;
            this.leftPad = leftPad;
            this.descPad = descPad;
        }
```

### [changed] `HelpFormatter.java` > `HelpFormatter.appendOptions(A,int,Options,int,int)` (lines 408-421)

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
        return appendOptions(sb, options, new Layout(width, leftPad, descPad));
    }
```

### [new] `HelpFormatter.java` > `HelpFormatter.appendOptions(A,Options,Layout)` (lines 423-494)

```java
    private <A extends Appendable> A appendOptions(final A sb, final Options options, final Layout layout) throws IOException {
        final String lpad = createPadding(layout.leftPad);
        final String dpad = createPadding(layout.descPad);
        // first create list containing only <lpad>-a,--aaa where
        // -a is opt and --aaa is long opt; in parallel look for
        // the longest opt string this list will be then used to
        // sort options ascending
        int max = 0;
        final int maxSince = showSince ? determineMaxSinceLength(options) + layout.leftPad : 0;
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
        final int nextLineTabStop = max + layout.descPad;
        if (showSince) {
            final StringBuilder optHeader = new StringBuilder(HEADER_OPTIONS).append(createPadding(max - maxSince - HEADER_OPTIONS.length() + layout.leftPad))
                    .append(HEADER_SINCE);
            optHeader.append(createPadding(max - optHeader.length())).append(lpad).append(HEADER_DESCRIPTION);
            appendWrappedText(sb, layout.width, nextLineTabStop, optHeader.toString());
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
            appendWrappedText(sb, layout.width, nextLineTabStop, optBuf.toString());
            if (it.hasNext()) {
                sb.append(getNewLine());
            }
        }
        return sb;
    }
```

### [changed] `HelpFormatter.java` > `HelpFormatter.printHelp(PrintWriter,int,String,String,Options,int,int,String,boolean)` (lines 738-755)

```java
    /**
     * Prints the help for {@code options} with the specified command line syntax.
     *
     * @param pw the writer to which the help will be written
     * @param width the number of characters to be displayed on each line
     * @param cmdLineSyntax the syntax for this application
     * @param header the banner to display at the beginning of the help
     * @param options the Options instance
     * @param leftPad the number of characters of padding to be prefixed to each line
     * @param descPad the number of characters of padding to be prefixed to each description line
     * @param footer the banner to display at the end of the help
     * @param autoUsage whether to print an automatically generated usage statement
     * @throws IllegalStateException if there is no room to print a line
     */
    public void printHelp(final PrintWriter pw, final int width, final String cmdLineSyntax, final String header, final Options options, final int leftPad,
        final int descPad, final String footer, final boolean autoUsage) {
        printHelp(pw, cmdLineSyntax, header, options, footer, autoUsage, new Layout(width, leftPad, descPad));
    }
```

### [new] `HelpFormatter.java` > `HelpFormatter.printHelp(PrintWriter,String,String,Options,String,boolean,Layout)` (lines 757-774)

```java
    private void printHelp(final PrintWriter pw, final String cmdLineSyntax, final String header, final Options options, final String footer,
        final boolean autoUsage, final Layout layout) {
        if (Util.isEmpty(cmdLineSyntax)) {
            throw new IllegalArgumentException("cmdLineSyntax not provided");
        }
        if (autoUsage) {
            printUsage(pw, layout.width, cmdLineSyntax, options);
        } else {
            printUsage(pw, layout.width, cmdLineSyntax);
        }
        if (header != null && !header.isEmpty()) {
            printWrapped(pw, layout.width, header);
        }
        printOptions(pw, options, layout);
        if (footer != null && !footer.isEmpty()) {
            printWrapped(pw, layout.width, footer);
        }
    }
```

### [changed] `HelpFormatter.java` > `HelpFormatter.printOptions(PrintWriter,int,Options,int,int)` (lines 826-838)

```java
    /**
     * Prints the help for the specified Options to the specified writer, using the specified width, left padding and
     * description padding.
     *
     * @param pw The printWriter to write the help to
     * @param width The number of characters to display per line
     * @param options The command line Options
     * @param leftPad the number of characters of padding to be prefixed to each line
     * @param descPad the number of characters of padding to be prefixed to each description line
     */
    public void printOptions(final PrintWriter pw, final int width, final Options options, final int leftPad, final int descPad) {
        printOptions(pw, options, new Layout(width, leftPad, descPad));
    }
```

### [new] `HelpFormatter.java` > `HelpFormatter.printOptions(PrintWriter,Options,Layout)` (lines 840-847)

```java
    private void printOptions(final PrintWriter pw, final Options options, final Layout layout) {
        try {
            pw.println(appendOptions(new StringBuilder(), options, layout));
        } catch (final IOException e) {
            // Cannot happen
            throw new UncheckedIOException(e);
        }
    }
```

### [changed] `HelpFormatter.java` > `HelpFormatter.renderOptions(StringBuffer,int,Options,int,int)` (lines 932-945)

```java
    /**
     * Renders the specified Options and return the rendered Options in a StringBuffer.
     *
     * @param sb The StringBuffer to place the rendered Options into.
     * @param width The number of characters to display per line
     * @param options The command line Options
     * @param leftPad the number of characters of padding to be prefixed to each line
     * @param descPad the number of characters of padding to be prefixed to each description line
     *
     * @return the StringBuffer with the rendered Options contents.
     */
    protected StringBuffer renderOptions(final StringBuffer sb, final int width, final Options options, final int leftPad, final int descPad) {
        return renderOptions(sb, options, new Layout(width, leftPad, descPad));
    }
```

### [new] `HelpFormatter.java` > `HelpFormatter.renderOptions(StringBuffer,Options,Layout)` (lines 947-954)

```java
    private StringBuffer renderOptions(final StringBuffer sb, final Options options, final Layout layout) {
        try {
            return appendOptions(sb, layout.width, options, layout.leftPad, layout.descPad);
        } catch (final IOException e) {
            // Cannot happen
            throw new UncheckedIOException(e);
        }
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
