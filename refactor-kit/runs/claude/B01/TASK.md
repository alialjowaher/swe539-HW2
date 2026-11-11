# TASK - refactor smell B01 (Feature Envy) in Apache Commons CLI 1.9.0

| | |
|---|---|
| Run | Claude · Claude Opus 5.5 (claude-opus-5-5) · mode: agent · started 2026-11-10 10:00 |
| Workspace (edit only here) | `workspace/claude/commons-cli` |
| Branch | `refactor/B01`, created from `rel/commons-cli-1.9.0` (commit 698b238276) |
| Your process notes | `runs/claude/B01/process.md` |
| Original code saved in | `runs/claude/B01/original/` |

## 1. The smell

| Field | Value |
|---|---|
| ID | B01 |
| Smell type | Between classes |
| Code smell | Feature Envy |
| Class(es) | HelpFormatter → Option (also OptionGroup → Option) |
| Method / member | HelpFormatter.appendOption; label block of appendOptions; getDescription(Option); OptionGroup.toString |
| Lines (1.9.0) | HF 346–364, 421–440, 226–229; OptionGroup 143–168 |
| Priority |  |

**Evidence.** appendOption makes 9 calls on its Option argument (getOpt ×3, getArgName ×4, getLongOpt, hasArg) and uses only 2 HelpFormatter members (getArgName(), longOptSeparator). The label block of appendOptions makes 9 more Option calls to build "-a,--aaa <arg>". getDescription(Option) is a static method that reads only Option. OptionGroup.toString (149–159) rebuilds the same "-opt or --longOpt" label from Option getters. How an option is displayed is decided in two classes, neither of them Option.


## 2. The refactoring to apply

**Technique:** Extract Method, then Move Method (to Option)

_Source: review sheet suggestion (column 'Suggested refactoring')._

**How (outline):** Extract the label logic into a package-private method on Option, e.g. toLabel(String optPrefix, String longOptPrefix), plus a null-safe description accessor. HelpFormatter calls it with its configured prefixes (appendOptions) or with "-"/"--" (appendOption, which ignores the configured prefixes today; keep that). OptionGroup.toString calls it with "-"/"--".

**Risks to watch:** Low–Medium. Output is pinned by HelpFormatterTest and OptionGroupTest. The usage line hard-codes "-"/"--" while the options table uses getOptPrefix()/getLongOptPrefix(); a move that unifies them changes output when a custom prefix is set.

**Expected effect on metrics:** Coupling: fewer HelpFormatter→Option and OptionGroup→Option method calls (RFC / message-passing coupling drop); CBO unchanged because both still reference Option. Cohesion: HelpFormatter improves slightly; Option gains a method that works on its own fields.


Apply **this** technique and nothing else. If you believe it cannot be applied without breaking a rule below, stop, explain why in process.md section 5, and run `finish` without making a different refactoring.

## 3. Where the code is (original, before refactoring)

- `src/main/java/org/apache/commons/cli/HelpFormatter.java` > `HelpFormatter.getDescription(Option)` (lines 220-229)
- `src/main/java/org/apache/commons/cli/HelpFormatter.java` > `HelpFormatter.appendOption(StringBuilder,Option,boolean)` (lines 339-364)
- `src/main/java/org/apache/commons/cli/HelpFormatter.java` > `HelpFormatter.appendOptions(A,int,Options,int,int)` (lines 396-478)
- `src/main/java/org/apache/commons/cli/OptionGroup.java` > `OptionGroup.toString()` (lines 137-168)
- `src/main/java/org/apache/commons/cli/Option.java` (file is involved; no specific member)

Most relevant test classes: HelpFormatterTest, OptionGroupTest, OptionTest

#### `HelpFormatter.java` > `HelpFormatter.getDescription(Option)` (lines 220-229)

```java
    /**
     * Gets the option description or an empty string if the description is {@code null}.
     * @param option The option to get the description from.
     * @return the option description or an empty string if the description is {@code null}.
     * @since 1.8.0
     */
    public static String getDescription(final Option option) {
        final String desc = option.getDescription();
        return desc == null ? "" : desc;
    }
```

#### `HelpFormatter.java` > `HelpFormatter.appendOption(StringBuilder,Option,boolean)` (lines 339-364)

```java
    /**
     * Appends the usage clause for an Option to a StringBuffer.
     *
     * @param buff the StringBuffer to append to
     * @param option the Option to append
     * @param required whether the Option is required or not
     */
    private void appendOption(final StringBuilder buff, final Option option, final boolean required) {
        if (!required) {
            buff.append("[");
        }
        if (option.getOpt() != null) {
            buff.append("-").append(option.getOpt());
        } else {
            buff.append("--").append(option.getLongOpt());
        }
        // if the Option has a value and a non blank argname
        if (option.hasArg() && (option.getArgName() == null || !option.getArgName().isEmpty())) {
            buff.append(option.getOpt() == null ? longOptSeparator : " ");
            buff.append("<").append(option.getArgName() != null ? option.getArgName() : getArgName()).append(">");
        }
        // if the Option is not a required option
        if (!required) {
            buff.append("]");
        }
    }
```

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

#### `OptionGroup.java` > `OptionGroup.toString()` (lines 137-168)

```java
    /**
     * Returns the stringified version of this OptionGroup.
     *
     * @return the stringified representation of this group
     */
    @Override
    public String toString() {
        final StringBuilder buff = new StringBuilder();
        final Iterator<Option> iter = getOptions().iterator();
        buff.append("[");
        while (iter.hasNext()) {
            final Option option = iter.next();
            if (option.getOpt() != null) {
                buff.append("-");
                buff.append(option.getOpt());
            } else {
                buff.append("--");
                buff.append(option.getLongOpt());
            }

            if (option.getDescription() != null) {
                buff.append(Char.SP);
                buff.append(option.getDescription());
            }

            if (iter.hasNext()) {
                buff.append(", ");
            }
        }
        buff.append("]");
        return buff.toString();
    }
```


## 4. Rules (non-negotiable)

1. **One smell, one technique.** Change only what is needed to remove smell B01 with the technique given in "The refactoring to apply". No other refactorings, renames, reformatting, comment edits or improvements anywhere else.
2. **Behaviour must not change.** Same return values, same printed text (including spaces, line breaks and order), same exceptions and messages, same side effects. If the existing code looks wrong, keep its behaviour and note it under "Observations" in the process notes. Fixing bugs is out of scope.
3. **The original tests are the judge, so don't touch them.** Do not modify, add, delete, skip or disable anything under `src/test/`.
4. **Keep the public and protected API.** Do not remove, rename or change the signature, visibility or modifiers of any public or protected class, constructor, method or field. If the technique moves or renames one, keep the old one and make it delegate to the new one. New members should be `private` or package-private unless the technique needs otherwise.
5. **Java 8, no new dependencies.** Do not edit `pom.xml` or any build file. Use only Java 8 language features and APIs (no `var`, records, switch expressions, text blocks, `List.of`, `String.isBlank`, ...).
6. **New classes** go in package `org.apache.commons.cli` under `src/main/java`, start with the same Apache License header as the existing files, have a class Javadoc, and are package-private unless they must be public.
7. **Keep the house style:** 4-space indentation; `final` on parameters and locals, as in the surrounding code; a short Javadoc on every new method.
8. **Small steps.** Compile and run the tests after every step. If a step breaks a test, undo or fix that step before moving on; don't pile changes on top of a failure.
9. **Stay in your lane.** Edit only inside your own workspace clone (`workspace/claude/commons-cli`). Don't commit, push or switch branches; `kit.py` does that. Don't open other LLMs' folders under `runs/` or `workspace/`. Don't edit the kit, the Excel files, or anything in the run folder except `process.md`.


## 5. Definition of done

- `python kit.py test --llm "Claude"` shows the same number of passing tests as the original run (see `runs/claude/B01/tests_original.json`).
- No file under `src/test/` changed, and no public or protected API was removed or changed.
- The smell is addressed with the technique in section 2, and nothing else changed.
- `process.md` is complete: every _italic guidance line_ has been replaced.
- `python kit.py finish --smell B01 --llm "Claude"` has run and printed a verdict.

## 6. Commands

| Purpose | Command |
|---|---|
| Quick test (one class) | `python kit.py test --llm "Claude" --only HelpFormatterTest` |
| Full test suite | `python kit.py test --llm "Claude"` |
| Finish the run | `python kit.py finish --smell B01 --llm "Claude"` |
