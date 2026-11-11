# Refactoring report - B01 Feature Envy - Copilot-B01

| | |
|---|---|
| Smell | B01 - Feature Envy (Between classes) |
| Class / member | HelpFormatter → Option (also OptionGroup → Option) - HelpFormatter.appendOption; label block of appendOptions; getDescription(Option); OptionGroup.toString (lines HF 346–364, 421–440, 226–229; OptionGroup 143–168) |
| Refactoring applied | Extract Method, then Move Method (to Option) |
| LLM / model | Copilot-B01 - Copilot SDK in VS Code (2026-11-10) |
| Mode | agent |
| Code base | rel/commons-cli-1.9.0 (698b238276) -> branch `refactor/B01` commit 99b5beacf7 |
| Verdict | **PASS** |
| Original tests | 738 passed of 797 (59 skipped) |
| Refactored tests | 738 passed of 797 (59 skipped) - regressions: 0 |
| Test files modified | No |
| Public/protected API | 0 removed or changed, 0 added |
| Files changed | src/main/java/org/apache/commons/cli/HelpFormatter.java (+7 -15)<br>src/main/java/org/apache/commons/cli/Option.java (+29 -0)<br>src/main/java/org/apache/commons/cli/OptionGroup.java (+2 -8) |
| Finish attempts | 1 |

## 1. Smell (from the review sheet)

**Evidence.** appendOption makes 9 calls on its Option argument (getOpt ×3, getArgName ×4, getLongOpt, hasArg) and uses only 2 HelpFormatter members (getArgName(), longOptSeparator). The label block of appendOptions makes 9 more Option calls to build "-a,--aaa <arg>". getDescription(Option) is a static method that reads only Option. OptionGroup.toString (149–159) rebuilds the same "-opt or --longOpt" label from Option getters. How an option is displayed is decided in two classes, neither of them Option.

**Technique:** Extract Method, then Move Method (to Option)

_Source: review sheet suggestion (column 'Suggested refactoring')._

**How (outline):** Extract the label logic into a package-private method on Option, e.g. toLabel(String optPrefix, String longOptPrefix), plus a null-safe description accessor. HelpFormatter calls it with its configured prefixes (appendOptions) or with "-"/"--" (appendOption, which ignores the configured prefixes today; keep that). OptionGroup.toString calls it with "-"/"--".

**Risks to watch:** Low–Medium. Output is pinned by HelpFormatterTest and OptionGroupTest. The usage line hard-codes "-"/"--" while the options table uses getOptPrefix()/getLongOptPrefix(); a move that unifies them changes output when a custom prefix is set.

**Expected effect on metrics:** Coupling: fewer HelpFormatter→Option and OptionGroup→Option method calls (RFC / message-passing coupling drop); CBO unchanged because both still reference Option. Cohesion: HelpFormatter improves slightly; Option gains a method that works on its own fields.


## 2. Original code (before refactoring)

_Every member the refactoring changed or removed, as it was in the original code. Full files: `original/`._

### [changed] `HelpFormatter.java` > `HelpFormatter.getDescription(Option)` (lines 220-229)

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

### [changed] `HelpFormatter.java` > `HelpFormatter.appendOption(StringBuilder,Option,boolean)` (lines 339-364)

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

### [changed] `OptionGroup.java` > `OptionGroup.toString()` (lines 137-168)

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

## 3. Original tests (on the untouched code)

- Result: **738 passed of 797 (59 skipped)**
- Log: `tests_original.log`

## 4. Refactoring process

> Written by the LLM during the run. Keep the headings and replace every _italic guidance line_ with your own text.
> Model: Copilot SDK in VS Code (2026-11-10) · Mode: agent · Started: 2026-11-10 21:19

### 1. Understanding of the smell
HelpFormatter builds option labels and reads option descriptions in several places, while OptionGroup.toString repeats the same label construction. These methods make many decisions from Option's fields, so the display behavior is feature envy of Option. The relevant code is HelpFormatter.appendOption, appendOptions, and getDescription, plus OptionGroup.toString.

### 2. Plan
1. Extract the option label and null-safe description behavior into package-private methods on Option, and make HelpFormatter.getDescription delegate to the new description accessor.
2. Move the extracted label logic into Option usage from HelpFormatter.appendOption and appendOptions, preserving hard-coded usage prefixes and configured table prefixes.
3. Replace OptionGroup.toString's label construction with Option's package-private label method, using the null-safe description accessor without changing spacing.


### 3. Steps performed
| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | Added package-private Option.toLabel and Option.getDescriptionOrEmpty; delegated HelpFormatter.getDescription. | Passed via targeted Maven run | HelpFormatterTest, OptionGroupTest, OptionTest: 72/72 passed |
| 2 | Replaced HelpFormatter usage and table label construction with Option.toLabel, retaining hard-coded usage prefixes and configured table prefixes. | Passed via targeted Maven run | HelpFormatterTest, OptionGroupTest, OptionTest: 72/72 passed |
| 3 | Replaced OptionGroup.toString label and description reads with the Option methods while retaining its existing spacing. | Passed via targeted Maven run | HelpFormatterTest, OptionGroupTest, OptionTest: 72/72 passed |

### 4. Why behaviour is preserved
The new label method applies the same short-versus-long selection and comma formatting as the original callers. HelpFormatter.appendOption still uses literal "-" and "--", while appendOptions still passes the formatter's configured prefixes, so custom table prefixes and usage output remain distinct. The description accessor returns the same description or an empty string; callers preserve the original null checks and spacing, including OptionGroup's empty-description case.

### 5. Deviations from the plan
None.

### 6. Observations (not changed)
None.

### 7. Self-assessment
- Smell removed: yes; option label and null-safe description behavior now reside on Option.
- Expected effect on size: small reduction in duplicated label and description logic in the client classes.
- Expected effect on cohesion: HelpFormatter and OptionGroup become more focused on rendering and grouping.
- Expected effect on coupling: fewer message sends from HelpFormatter and OptionGroup to Option for label and description details; class-level coupling remains.

## 5. Refactored code (after refactoring)

_The same members after the refactoring, plus any new members or files. Full files: `refactored/`; diff: `changes.patch`._

### [changed] `HelpFormatter.java` > `HelpFormatter.getDescription(Option)` (lines 220-228)

```java
    /**
     * Gets the option description or an empty string if the description is {@code null}.
     * @param option The option to get the description from.
     * @return the option description or an empty string if the description is {@code null}.
     * @since 1.8.0
     */
    public static String getDescription(final Option option) {
        return option.getDescriptionOrEmpty();
    }
```

### [changed] `HelpFormatter.java` > `HelpFormatter.appendOption(StringBuilder,Option,boolean)` (lines 338-359)

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
        buff.append(option.getOpt() == null ? option.toLabel("-", "--") : option.toLabel("-", null));
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

### [changed] `HelpFormatter.java` > `HelpFormatter.appendOptions(A,int,Options,int,int)` (lines 391-470)

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
            optBuf.append(lpad);
            if (option.getOpt() == null) {
                optBuf.append("   ");
            }
            optBuf.append(option.toLabel(getOptPrefix(), getLongOptPrefix()));
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
            } else if (!option.getDescriptionOrEmpty().isEmpty()) {
                optBuf.append(option.getDescriptionOrEmpty());
            }
            appendWrappedText(sb, width, nextLineTabStop, optBuf.toString());
            if (it.hasNext()) {
                sb.append(getNewLine());
            }
        }
        return sb;
    }
```

### [new] `Option.java` > `Option.getDescriptionOrEmpty()` (lines 622-629)

```java
    /**
     * Gets the option description or an empty string if the description is null.
     *
     * @return the option description or an empty string if the description is null.
     */
    String getDescriptionOrEmpty() {
        return description == null ? "" : description;
    }
```

### [new] `Option.java` > `Option.toLabel(String,String)` (lines 672-690)

```java
    /**
     * Gets the option label using the supplied short and long option prefixes.
     *
     * @param optPrefix the prefix for the short option.
     * @param longOptPrefix the prefix for the long option.
     * @return the formatted option label.
     */
    String toLabel(final String optPrefix, final String longOptPrefix) {
        final StringBuilder label = new StringBuilder();
        if (option != null) {
            label.append(optPrefix).append(option);
            if (longOption != null && longOptPrefix != null) {
                label.append(',').append(longOptPrefix).append(longOption);
            }
        } else {
            label.append(longOptPrefix).append(longOption);
        }
        return label.toString();
    }
```

### [changed] `OptionGroup.java` > `OptionGroup.toString()` (lines 137-162)

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
            buff.append(option.getOpt() == null ? option.toLabel("-", "--") : option.toLabel("-", null));

            if (option.getDescription() != null) {
                buff.append(Char.SP);
                buff.append(option.getDescriptionOrEmpty());
            }

            if (iter.hasNext()) {
                buff.append(", ");
            }
        }
        buff.append("]");
        return buff.toString();
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
