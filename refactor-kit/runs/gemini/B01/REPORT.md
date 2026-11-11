# Refactoring report - B01 Feature Envy - Gemini

| | |
|---|---|
| Smell | B01 - Feature Envy (Between classes) |
| Class / member | HelpFormatter → Option (also OptionGroup → Option) - HelpFormatter.appendOption; label block of appendOptions; getDescription(Option); OptionGroup.toString (lines HF 346–364, 421–440, 226–229; OptionGroup 143–168) |
| Refactoring applied | Extract Method, then Move Method (to Option) |
| LLM / model | Gemini - Gemini 3.1 Pro |
| Mode | agent |
| Code base | rel/commons-cli-1.9.0 (698b238276) -> branch `refactor/B01` commit 9ec9e9fdf9 |
| Verdict | **PASS** |
| Original tests | 738 passed of 797 (59 skipped) |
| Refactored tests | 738 passed of 797 (59 skipped) - regressions: 0 |
| Test files modified | No |
| Public/protected API | 0 removed or changed, 0 added |
| Files changed | src/main/java/org/apache/commons/cli/HelpFormatter.java (+5 -34)<br>src/main/java/org/apache/commons/cli/Option.java (+72 -0)<br>src/main/java/org/apache/commons/cli/OptionGroup.java (+1 -7) |
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
> Model: Gemini 3.1 Pro · Mode: agent · Started: 2026-11-10 13:24

### 1. Understanding of the smell
`HelpFormatter` and `OptionGroup` exhibit Feature Envy toward `Option`: `HelpFormatter.appendOption` (lines 346–364) makes 9 getter/query calls on `Option` (`getOpt`, `getLongOpt`, `hasArg`, `getArgName`) while using only two `HelpFormatter` members; the option-label loop in `HelpFormatter.appendOptions` (lines 421–440) makes 9 more `Option` calls to build `<lpad>-a,--aaa <arg>`; `HelpFormatter.getDescription(Option)` (lines 226–229) is a static method reading only `Option.getDescription()`; and `OptionGroup.toString()` (lines 143–168) repeats the `-opt` / `--longOpt` selection from `Option` getters. Formatting an `Option`'s label and null-safe description relies almost entirely on `Option`'s state and belongs on `Option`.

### 2. Plan
1. Add package-private `getDescriptionOrEmpty()` to `Option` and update `HelpFormatter.getDescription(Option)` and the description branch in `HelpFormatter.appendOptions` to delegate to it; compile and run `HelpFormatterTest` and `OptionTest`.
2. Add package-private `toLabel(String optPrefix, String longOptPrefix)` to `Option` (returning `<optPrefix><opt>` when `option != null`, or `<longOptPrefix><longOption>` otherwise) and update `OptionGroup.toString()` to call `option.toLabel("-", "--")`; compile and run `OptionGroupTest` and `OptionTest`.
3. Add package-private `toLabel(String optPrefix, String longOptPrefix, String longOptSeparator, String defaultArgName)` to `Option` for usage-clause formatting (including the `<arg>` suffix) and update `HelpFormatter.appendOption` to delegate to `option.toLabel("-", "--", longOptSeparator, getArgName())`; compile and run `HelpFormatterTest`.
4. Add package-private `toLabel(String lpad, String optPrefix, String longOptPrefix, String longOptSeparator, String defaultArgName)` to `Option` for help-table option label formatting and update the first loop of `HelpFormatter.appendOptions` to call it; compile and run `HelpFormatterTest`, `OptionGroupTest`, `OptionTest`, and the full test suite.

### 3. Steps performed

| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | `Option.java` (`getDescriptionOrEmpty()`), `HelpFormatter.java` (`getDescription`, `appendOptions`) | PASS | `HelpFormatterTest` 38/38 passed |
| 2 | `Option.java` (`toLabel(String, String)`), `OptionGroup.java` (`toString()`) | PASS | `OptionGroupTest` 13/13 passed |
| 3 | `Option.java` (`toLabel(String, String, String, String)`), `HelpFormatter.java` (`appendOption`) | PASS | `HelpFormatterTest` 38/38 passed |
| 4 | `Option.java` (`toLabel(String, String, String, String, String)`), `HelpFormatter.java` (`appendOptions`) | PASS | `HelpFormatterTest` 38/38, `OptionGroupTest` 13/13, `OptionTest` 21/21, full suite 738/797 passed |

### 4. Why behaviour is preserved
- `Option.getDescriptionOrEmpty()` returns `description == null ? "" : description`, which is identical to `HelpFormatter.getDescription(Option)` and has the same effect in `HelpFormatter.appendOptions` where appending `""` to `optBuf` when `description == null` leaves `optBuf` unchanged. `OptionGroup.toString()` retains its `if (option.getDescription() != null)` check so a space is only prefixed when a description is non-null.
- `Option.toLabel(optPrefix, longOptPrefix)` returns `option != null ? optPrefix + option : longOptPrefix + longOption`. `OptionGroup.toString()` calls `option.toLabel("-", "--")`, matching its previous `-opt` / `--longOpt` branching.
- `Option.toLabel(optPrefix, longOptPrefix, longOptSeparator, defaultArgName)` builds the usage-line option label and appends the `<arg>` clause under the exact same condition (`hasArg() && (argName == null || !argName.isEmpty())`) and separator choice (`option == null ? longOptSeparator : " "`). `HelpFormatter.appendOption` passes `"-"` and `"--"`, preserving the existing hard-coded prefixes in the usage line even when custom prefixes are configured on `HelpFormatter`.
- `Option.toLabel(lpad, optPrefix, longOptPrefix, longOptSeparator, defaultArgName)` builds the help-table option label using `HelpFormatter`'s configured `getOptPrefix()`, `getLongOptPrefix()`, `longOptSeparator`, and `getArgName()`, preserving the `"   "` indentation for long-only options, the `','` separator when both short and long options exist, the trailing `' '` when `argName` is empty, and `hasLongOpt() ? longOptSeparator : " "` before `<arg>`.

### 5. Deviations from the plan
None.

### 6. Observations (not changed)
- `HelpFormatter.appendOption` hard-codes `"-"` and `"--"` instead of using `getOptPrefix()` and `getLongOptPrefix()`, and uses `option.getOpt() == null ? longOptSeparator : " "` (whereas `appendOptions` uses `option.hasLongOpt() ? longOptSeparator : " "`). Both differences were preserved as required.

### 7. Self-assessment
- Smell removed: yes — `HelpFormatter` and `OptionGroup` no longer reach into `Option`'s getters (`getOpt`, `getLongOpt`, `hasLongOpt`, `hasArg`, `getArgName`, `getDescription`) to assemble option labels; `Option` now formats its own labels and null-safe description using its own fields.
- Expected effect on size: `HelpFormatter` and `OptionGroup` shrink; `Option` grows by the 4 new package-private helper methods.
- Expected effect on cohesion: `Option` and `HelpFormatter` cohesion improve or remain stable since `Option`'s new methods operate directly on `Option`'s fields (`option`, `longOption`, `argName`, `description`).
- Expected effect on coupling: Message-passing coupling (RFC) in `HelpFormatter` and `OptionGroup` decreases because multiple `Option` getter calls are replaced by single calls to `toLabel` / `getDescriptionOrEmpty`; CBO is unchanged because both classes still reference `Option`.

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

### [changed] `HelpFormatter.java` > `HelpFormatter.appendOption(StringBuilder,Option,boolean)` (lines 338-354)

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
        buff.append(option.toLabel("-", "--", longOptSeparator, getArgName()));
        // if the Option is not a required option
        if (!required) {
            buff.append("]");
        }
    }
```

### [changed] `HelpFormatter.java` > `HelpFormatter.appendOptions(A,int,Options,int,int)` (lines 386-449)

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
            final StringBuilder optBuf = option.toLabel(lpad, getOptPrefix(), getLongOptPrefix(), longOptSeparator, getArgName());
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
            } else {
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
     * Gets the self-documenting description of this Option, or an empty string if the description is {@code null}.
     *
     * @return The string description of this option, or an empty string if {@code null}.
     */
    String getDescriptionOrEmpty() {
        return description == null ? "" : description;
    }
```

### [new] `Option.java` > `Option.toLabel(String,String)` (lines 1004-1013)

```java
    /**
     * Formats the short or long option name using the given prefixes.
     *
     * @param optPrefix The prefix for a short option.
     * @param longOptPrefix The prefix for a long option.
     * @return The formatted option label.
     */
    String toLabel(final String optPrefix, final String longOptPrefix) {
        return option != null ? optPrefix + option : longOptPrefix + longOption;
    }
```

### [new] `Option.java` > `Option.toLabel(String,String,String,String)` (lines 1015-1032)

```java
    /**
     * Formats the usage clause label for this Option (short or long option name and optional argument name).
     *
     * @param optPrefix The prefix for a short option.
     * @param longOptPrefix The prefix for a long option.
     * @param longOptSeparator The separator between a long option and its argument.
     * @param defaultArgName The default argument name when none is set on this option.
     * @return The formatted usage option label.
     */
    String toLabel(final String optPrefix, final String longOptPrefix, final String longOptSeparator, final String defaultArgName) {
        final StringBuilder buff = new StringBuilder(toLabel(optPrefix, longOptPrefix));
        // if the Option has a value and a non blank argname
        if (hasArg() && (argName == null || !argName.isEmpty())) {
            buff.append(option == null ? longOptSeparator : " ");
            buff.append("<").append(argName != null ? argName : defaultArgName).append(">");
        }
        return buff.toString();
    }
```

### [new] `Option.java` > `Option.toLabel(String,String,String,String,String)` (lines 1034-1065)

```java
    /**
     * Builds the padded help table prefix label for this Option (short/long option names and optional argument name).
     *
     * @param lpad The left padding string.
     * @param optPrefix The prefix for a short option.
     * @param longOptPrefix The prefix for a long option.
     * @param longOptSeparator The separator between a long option and its argument.
     * @param defaultArgName The default argument name when none is set on this option.
     * @return A StringBuilder containing the formatted help option label.
     */
    StringBuilder toLabel(final String lpad, final String optPrefix, final String longOptPrefix, final String longOptSeparator,
            final String defaultArgName) {
        final StringBuilder optBuf = new StringBuilder();
        if (option == null) {
            optBuf.append(lpad).append("   ").append(longOptPrefix).append(longOption);
        } else {
            optBuf.append(lpad).append(optPrefix).append(option);
            if (hasLongOpt()) {
                optBuf.append(',').append(longOptPrefix).append(longOption);
            }
        }
        if (hasArg()) {
            if (argName != null && argName.isEmpty()) {
                // if the option has a blank argname
                optBuf.append(' ');
            } else {
                optBuf.append(hasLongOpt() ? longOptSeparator : " ");
                optBuf.append("<").append(argName != null ? argName : defaultArgName).append(">");
            }
        }
        return optBuf;
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
            buff.append(option.toLabel("-", "--"));

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
