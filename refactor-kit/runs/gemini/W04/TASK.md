# TASK - refactor smell W04 (Long Parameter List) in Apache Commons CLI 1.9.0

| | |
|---|---|
| Run | Gemini · Gemini 3.1 Pro · mode: agent · started 2026-11-11 10:05 |
| Workspace (edit only here) | `workspace/gemini/commons-cli` |
| Branch | `refactor/W04`, created from `rel/commons-cli-1.9.0` (commit 698b238276) |
| Your process notes | `runs/gemini/W04/process.md` |
| Original code saved in | `runs/gemini/W04/original/` |

## 1. The smell

| Field | Value |
|---|---|
| ID | W04 |
| Smell type | Within class |
| Code smell | Long Parameter List |
| Class(es) | HelpFormatter |
| Method / member | printHelp(PrintWriter, int, String, String, Options, int, int, String, boolean) |
| Lines (1.9.0) | 736–753 (also 717–720) |
| Priority |  |

**Evidence.** 9 parameters (the overload at 717–720 has 8). Three of them, width / leftPad / descPad, travel together through printHelp (717, 736), printOptions (815), renderOptions (918) and appendOptions (407), while the class already stores the same values as fields (defaultWidth, defaultLeftPad, defaultDescPad).


## 2. The refactoring to apply

**Technique:** Introduce Parameter Object; Preserve Whole Object

_Source: review sheet suggestion (column 'Suggested refactoring')._

**How (outline):** Add a small value class for the layout (width, leftPad, descPad) and route the long overloads through one internal method that takes it. Keep every public printHelp overload as a one-line delegate so the public API does not change.

**Risks to watch:** Medium. Public API: the existing overloads must stay. Output is pinned by HelpFormatterTest.

**Expected effect on metrics:** Size: parameter count on the internal path drops; public method count unchanged. Coupling: +1 (new parameter class).


Apply **this** technique and nothing else. If you believe it cannot be applied without breaking a rule below, stop, explain why in process.md section 5, and run `finish` without making a different refactoring.

## 3. Where the code is (original, before refactoring)

- `src/main/java/org/apache/commons/cli/HelpFormatter.java` > `HelpFormatter.appendOptions(A,int,Options,int,int)` (lines 396-478)
- `src/main/java/org/apache/commons/cli/HelpFormatter.java` > `HelpFormatter.printHelp(PrintWriter,int,String,String,Options,int,int,String)` (lines 703-720)
- `src/main/java/org/apache/commons/cli/HelpFormatter.java` > `HelpFormatter.printHelp(PrintWriter,int,String,String,Options,int,int,String,boolean)` (lines 722-753)
- `src/main/java/org/apache/commons/cli/HelpFormatter.java` > `HelpFormatter.printOptions(PrintWriter,int,Options,int,int)` (lines 805-822)
- `src/main/java/org/apache/commons/cli/HelpFormatter.java` > `HelpFormatter.renderOptions(StringBuffer,int,Options,int,int)` (lines 907-925)

Most relevant test classes: HelpFormatterTest

#### `HelpFormatter.java` > `HelpFormatter.appendOptions(A,int,Options,int,int)` (lines 396-478)

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

#### `HelpFormatter.java` > `HelpFormatter.printHelp(PrintWriter,int,String,String,Options,int,int,String)` (lines 703-720)

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
     *
     * @throws IllegalStateException if there is no room to print a line
     */
    public void printHelp(final PrintWriter pw, final int width, final String cmdLineSyntax, final String header, final Options options, final int leftPad,
        final int descPad, final String footer) {
        printHelp(pw, width, cmdLineSyntax, header, options, leftPad, descPad, footer, false);
    }
```

#### `HelpFormatter.java` > `HelpFormatter.printHelp(PrintWriter,int,String,String,Options,int,int,String,boolean)` (lines 722-753)

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

#### `HelpFormatter.java` > `HelpFormatter.printOptions(PrintWriter,int,Options,int,int)` (lines 805-822)

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

#### `HelpFormatter.java` > `HelpFormatter.renderOptions(StringBuffer,int,Options,int,int)` (lines 907-925)

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


## 4. Rules (non-negotiable)

1. **One smell, one technique.** Change only what is needed to remove smell W04 with the technique given in "The refactoring to apply". No other refactorings, renames, reformatting, comment edits or improvements anywhere else.
2. **Behaviour must not change.** Same return values, same printed text (including spaces, line breaks and order), same exceptions and messages, same side effects. If the existing code looks wrong, keep its behaviour and note it under "Observations" in the process notes. Fixing bugs is out of scope.
3. **The original tests are the judge, so don't touch them.** Do not modify, add, delete, skip or disable anything under `src/test/`.
4. **Keep the public and protected API.** Do not remove, rename or change the signature, visibility or modifiers of any public or protected class, constructor, method or field. If the technique moves or renames one, keep the old one and make it delegate to the new one. New members should be `private` or package-private unless the technique needs otherwise.
5. **Java 8, no new dependencies.** Do not edit `pom.xml` or any build file. Use only Java 8 language features and APIs (no `var`, records, switch expressions, text blocks, `List.of`, `String.isBlank`, ...).
6. **New classes** go in package `org.apache.commons.cli` under `src/main/java`, start with the same Apache License header as the existing files, have a class Javadoc, and are package-private unless they must be public.
7. **Keep the house style:** 4-space indentation; `final` on parameters and locals, as in the surrounding code; a short Javadoc on every new method.
8. **Small steps.** Compile and run the tests after every step. If a step breaks a test, undo or fix that step before moving on; don't pile changes on top of a failure.
9. **Stay in your lane.** Edit only inside your own workspace clone (`workspace/gemini/commons-cli`). Don't commit, push or switch branches; `kit.py` does that. Don't open other LLMs' folders under `runs/` or `workspace/`. Don't edit the kit or the Excel files by hand, or anything in the run folder except `process.md`; `kit.py` writes them. You **are allowed** to run `python kit.py metrics --smell W04 --llm "<your LLM name>"` after your last `finish`: it measures size, cohesion and coupling before and after with CK and fills your run's row of the Excel **Metrics** sheet.


## 5. Definition of done

- `python kit.py test --llm "Gemini"` shows the same number of passing tests as the original run (see `runs/gemini/W04/tests_original.json`).
- No file under `src/test/` changed, and no public or protected API was removed or changed.
- The smell is addressed with the technique in section 2, and nothing else changed.
- `process.md` is complete: every _italic guidance line_ has been replaced.
- `python kit.py finish --smell W04 --llm "Gemini"` has run and printed a verdict.

## 6. Commands

| Purpose | Command |
|---|---|
| Quick test (one class) | `python kit.py test --llm "Gemini" --only HelpFormatterTest` |
| Full test suite | `python kit.py test --llm "Gemini"` |
| Finish the run | `python kit.py finish --smell W04 --llm "Gemini"` |
