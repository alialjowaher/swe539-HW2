# Refactoring report - B01 Feature Envy - Claude

| | |
|---|---|
| Smell | B01 - Feature Envy (Between classes) |
| Class / member | HelpFormatter → Option (also OptionGroup → Option) - HelpFormatter.appendOption; label block of appendOptions; getDescription(Option); OptionGroup.toString (lines HF 346–364, 421–440, 226–229; OptionGroup 143–168) |
| Refactoring applied | Extract Method, then Move Method (to Option) |
| LLM / model | Claude - Claude Opus 5.5 (claude-opus-5-5) |
| Mode | agent |
| Code base | rel/commons-cli-1.9.0 (698b238276) -> branch `refactor/B01` commit 3df3d342f5 |
| Verdict | **PASS** |
| Original tests | 738 passed of 797 (59 skipped) |
| Refactored tests | 738 passed of 797 (59 skipped) - regressions: 0 |
| Test files modified | No |
| Public/protected API | 0 removed or changed, 0 added |
| Files changed | src/main/java/org/apache/commons/cli/HelpFormatter.java (+3 -30)<br>src/main/java/org/apache/commons/cli/Option.java (+78 -0)<br>src/main/java/org/apache/commons/cli/OptionGroup.java (+1 -7) |
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
> Model: Claude Opus 5.5 (claude-opus-5-5) · Mode: agent · Started: 2026-11-10 10:00

### 1. Understanding of the smell
Two classes decide how an `Option` is displayed, and neither of them is `Option`. In `HelpFormatter.java`:
- `appendOption` (lines 346–364) makes about 9 calls on its `Option` argument (`getOpt`, `getLongOpt`, `hasArg`, `getArgName` ×4) to build the usage clause `-a <arg>`.
- The label block of `appendOptions` (lines 421–440) makes about 9 more to build the options-table label `-a,--aaa <arg>`.
- The static `getDescription(Option)` (lines 226–229) reads nothing but its `Option`.

`OptionGroup.toString` (`OptionGroup.java` lines 149–155) rebuilds the same `-opt` / `--longOpt` name from `Option` getters. These methods are more interested in `Option`'s data than in their own class's, which is Feature Envy. The cure is to move the display logic onto `Option`.

### 2. Plan
Technique: Extract Method, then Move Method (to `Option`). For each envious fragment, the mechanics are:
- Extract it into a method that depends only on the `Option` and on explicit parameters (made `static` in the source class to prove that).
- Compile and test.
- Move it to `Option`, where the `option` parameter becomes `this` and fields are read through the same getters the original called.
- Make the caller use it, then delete the temporary helper, or keep it as a delegator if it is public API.
- Compile and test.

1. **Extract Method (HelpFormatter, usage clause).** Move the name + arg fragment of `appendOption` into `private static String usageLabel(Option, String optPrefix, String longOptPrefix, String longOptSeparator, String defaultArgName)`. `appendOption` calls it with `"-"`, `"--"`, `longOptSeparator` and `getArgName()`; the `-`/`--` stay hard-coded, as today. Test HelpFormatterTest.
2. **Move Method → `Option.toUsageLabel(optPrefix, longOptPrefix, longOptSeparator, defaultArgName)`** (package-private). `appendOption` calls `option.toUsageLabel(...)`, and the temporary `HelpFormatter.usageLabel` is deleted. Test HelpFormatterTest, OptionTest.
3. **Extract Method (Option, shared name label).** Pull the `-opt`-or-`--longOpt` part of `toUsageLabel` out into package-private `Option.toLabel(optPrefix, longOptPrefix)`. This is the label the sheet names. Test HelpFormatterTest, OptionTest.
4. **Use the moved method in `OptionGroup.toString`.** Replace its duplicated name fragment with `option.toLabel("-", "--")`. The `getDescription() != null` check stays as it is. Test OptionGroupTest.
5. **Extract Method (HelpFormatter, options-table label).** Move the label fragment of `appendOptions` (without `lpad`) into `private static String helpLabel(Option, String optPrefix, String longOptPrefix, String longOptSeparator, String defaultArgName)`. `appendOptions` calls it with `getOptPrefix()`, `getLongOptPrefix()`, `longOptSeparator` and `getArgName()`. Test HelpFormatterTest.
6. **Move Method → `Option.toHelpLabel(...)`** (package-private), moved verbatim, and delete the temporary `HelpFormatter.helpLabel`. Test HelpFormatterTest, OptionTest.
7. **Move Method: null-safe description.** Move the body of `HelpFormatter.getDescription(Option)` into package-private `Option.getDescriptionOrEmpty()`. The public static `HelpFormatter.getDescription(Option)` stays (API rule) and delegates to it. Test HelpFormatterTest, OptionTest.
8. Run the full suite with `python kit.py test --llm "Claude"`: expect 738 passed, 0 failed, 59 skipped, the same as the baseline.

### 3. Steps performed
Focused tests = `--only "HelpFormatterTest,OptionGroupTest,OptionTest"` (72 tests).

| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | `HelpFormatter`: Extract Method. The name + arg fragment of `appendOption` moved verbatim into a temporary `private static usageLabel(Option, String, String, String, String)`. `appendOption` calls it with `"-"`, `"--"`, `longOptSeparator`, `getArgName()`. | OK | 72/72 |
| 2 | Move Method: `usageLabel` → package-private `Option.toUsageLabel(optPrefix, longOptPrefix, longOptSeparator, defaultArgName)` (`option.` → own getters). `appendOption` calls `option.toUsageLabel(...)`. The temporary `HelpFormatter.usageLabel` was deleted. | OK | 72/72 |
| 3 | `Option`: Extract Method. The `-opt`/`--longOpt` name part of `toUsageLabel` became package-private `Option.toLabel(optPrefix, longOptPrefix)`, and `toUsageLabel` now starts from `toLabel(...)`. | OK | 72/72 |
| 4 | `OptionGroup.toString`: the duplicated name fragment was replaced by `buff.append(option.toLabel("-", "--"))`. The description check is unchanged. | OK | 72/72 |
| 5 | `HelpFormatter`: Extract Method. The label block of `appendOptions` (without `lpad`) moved verbatim into a temporary `private static helpLabel(Option, String, String, String, String)`, called with `getOptPrefix()`, `getLongOptPrefix()`, `longOptSeparator`, `getArgName()`. | OK | 72/72 |
| 6 | Move Method: `helpLabel` → package-private `Option.toHelpLabel(optPrefix, longOptPrefix, longOptSeparator, defaultArgName)`, verbatim. `appendOptions` calls `option.toHelpLabel(...)`. The temporary `HelpFormatter.helpLabel` was deleted. | OK | 72/72 |
| 7 | Move Method: the body of `HelpFormatter.getDescription(Option)` moved to package-private `Option.getDescriptionOrEmpty()`. The public static `HelpFormatter.getDescription(Option)` keeps its signature and Javadoc and delegates to it. | OK | 72/72 |
| 8 | Full suite. | OK | 738 passed / 0 failed / 0 errors / 59 skipped of 797 (identical to the baseline) |

### 4. Why behaviour is preserved
- **Every moved body is the original fragment, verbatim.** It has the same literals (`"   "`, `','`, `' '`, `"<"`, `">"`), the same branch conditions and the same append order. The usage form still picks its separator with `getOpt() == null` and skips blank arg names. The table form still picks its separator with `hasLongOpt()` and appends `' '` for a blank arg name. The two formats were **not** unified (see section 5).
- **Field access inside `Option` goes through the same getters.** Inside `Option` the moved code calls `getOpt()`, `getLongOpt()`, `getArgName()`, `hasArg()`, `hasLongOpt()` and `getDescription()`, never the fields directly. `Option` is not final, so a subclass that overrides a getter sees exactly the calls it saw before. The double `getArgName()` call in the table label is kept too.
- **The prefixes are unchanged.** `appendOption` and `OptionGroup.toString` pass the hard-coded `"-"`/`"--"` they used before, so the usage line still ignores custom prefixes, as the sheet requires. `appendOptions` passes `getOptPrefix()`/`getLongOptPrefix()`, as before. `lpad` and the `[`/`]` brackets stay in `HelpFormatter`, because they are layout, not option data.
- **`OptionGroup.toString` keeps `getDescription() != null`.** It does not use the new null-safe accessor. With a description of `""`, the original prints `-a ` (with a trailing space), and an empty-check rewrite would drop that space.
- **`HelpFormatter.getDescription(Option)` still exists** (public static, `@since 1.8.0`) and returns the same value. A null argument still throws `NullPointerException`, now from `option.getDescriptionOrEmpty()`. `DEFAULT_DEPRECATED_FORMAT` still calls it unchanged.
- **The one intended call-pattern difference: eager arguments.** Move Method needs the formatter's settings passed as arguments, as in the sheet's own `toLabel(optPrefix, longOptPrefix)` design. So `getOptPrefix()`, `getLongOptPrefix()` and `getArgName()` (and in `appendOption`, `getArgName()`) are now evaluated once per option before the call. The original called them only on some branches, for example `getArgName()` only when the option had no arg name. They are plain getters, so the values and the printed text are identical. Only a `HelpFormatter` subclass that overrides those getters with side effects could tell the difference.
- **Nothing else changed.** No exception paths were added or removed, the new members are package-private, and `Option`'s explicit `serialVersionUID = 1L` means its serialized form is unaffected. No test file was touched.

### 5. Deviations from the plan
- **More than one label method on `Option` (a deviation from the sheet's outline, not from the technique).** The sheet suggests a single `toLabel(String optPrefix, String longOptPrefix)` for all three callers. The three callers actually print different formats, so one method can't serve all of them without changing output:

  | Caller | Name part | Arg part |
  |---|---|---|
  | `HelpFormatter.appendOption` (usage line) | `-a` **or** `--aaa` (hard-coded `-`/`--`) | only if the arg name is not blank; separator is `longOptSeparator` if `getOpt() == null`, else `" "` |
  | `HelpFormatter.appendOptions` (options table) | `-a,--aaa`, `-a`, or `   --aaa` (configured prefixes) | blank arg name → `' '`; otherwise separator is `longOptSeparator` if `hasLongOpt()`, else `" "` |
  | `OptionGroup.toString` | `-a` **or** `--aaa` (`-`/`--`) | none |

  So `toLabel` holds the truly shared name part, used by `OptionGroup.toString` and, through `toUsageLabel`, by `appendOption`. `toUsageLabel` adds the usage-line arg part, and `toHelpLabel` is the table form, moved verbatim. All three use the same Extract Method → Move Method technique. No other refactoring was applied.
- Process: the temporary private helpers created in steps 1 and 5 were deleted in steps 2 and 6, which is Fowler's last step for a private source method that no longer has callers.
- `finish` attempts: 1 (see the verdict in REPORT.md).

### 6. Observations (not changed)
- **Remaining envy outside the cited lines:** the row part of `appendOptions` still reads `option.getSince()`, `option.isDeprecated()` and `option.getDescription()` (×2, `else if (option.getDescription() != null)`). It could use `getDescriptionOrEmpty()`, but it is outside the cited lines (421–440), so I left it.
- **Inconsistent separator rules:** the usage line puts `longOptSeparator` before the argument only when the option has **no** short name, while the table uses it whenever the option **has** a long name. For an option with both names, the usage line shows `-a <arg>` and the table shows `-a,--aaa=<arg>`. This may be intended, so I kept it.
- **Usage line ignores custom prefixes:** `appendOption` (and so `printUsage`) always prints `-`/`--`, even after `setOptPrefix`/`setLongOptPrefix`. I kept this, as the sheet instructs.
- **Blank arg names are handled differently:** a blank arg name (`""`) prints nothing in the usage line but a single space in the table. I kept this.
- **Baseline:** 59 of the 797 original tests are skipped by the project itself (`@Disabled` cases in BasicParserTest, GnuParserTest and PosixParserTest). None fail.
- **Session:** at the user's request, this run and the W01 run were done in the same agent session, not in separate fresh sessions.

### 7. Self-assessment
- Smell removed: **yes, for the cited members.**
  - `appendOption` went from about 9 calls on `Option` to 1 (`toUsageLabel`).
  - The `appendOptions` label block went from about 9 to 1 (`toHelpLabel`).
  - `HelpFormatter.getDescription(Option)` is now a one-line delegator.
  - `OptionGroup.toString` no longer rebuilds the name label (it keeps 2 `getDescription()` reads, for behaviour reasons).
  - How an option's label is built is now decided in `Option`. The remaining envy is in the row block of `appendOptions` (section 6), which is outside the cited lines.
- Expected effect on size: `HelpFormatter` −31 lines (`appendOption` and `appendOptions` get shorter and simpler, with lower CC), `OptionGroup` −6 lines, `Option` +78 lines (4 new package-private methods with Javadoc). Total NLOC goes up slightly because of the new signatures and Javadoc.
- Expected effect on cohesion: `HelpFormatter` improves slightly, since the code that only used `Option` data is gone. `Option` gains methods that work only on its own state, so its cohesion stays the same or improves.
- Expected effect on coupling: message-passing coupling and RFC from `HelpFormatter` and `OptionGroup` to `Option` drop, because they replace many getter calls with one label call. CBO is unchanged, since both classes still reference `Option`. There are no new dependencies.

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
        buff.append(option.toUsageLabel("-", "--", longOptSeparator, getArgName()));
        // if the Option is not a required option
        if (!required) {
            buff.append("]");
        }
    }
```

### [changed] `HelpFormatter.java` > `HelpFormatter.appendOptions(A,int,Options,int,int)` (lines 386-451)

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
            optBuf.append(lpad).append(option.toHelpLabel(getOptPrefix(), getLongOptPrefix(), longOptSeparator, getArgName()));

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

### [new] `Option.java` > `Option.getDescriptionOrEmpty()` (lines 622-630)

```java
    /**
     * Gets the description of this Option, or an empty string if the description is {@code null}.
     *
     * @return the description, or an empty string if the description is {@code null}.
     */
    String getDescriptionOrEmpty() {
        final String desc = getDescription();
        return desc == null ? "" : desc;
    }
```

### [new] `Option.java` > `Option.toHelpLabel(String,String,String,String)` (lines 1005-1035)

```java
    /**
     * Builds the label of this option for the options table of the help, for example {@code -a,--aaa <arg>} or {@code    --aaa <arg>}.
     *
     * @param optPrefix the prefix for the short option name.
     * @param longOptPrefix the prefix for the long option name.
     * @param longOptSeparator the separator between a long option and its argument.
     * @param defaultArgName the argument name to use when this option has none.
     * @return the options-table label.
     */
    String toHelpLabel(final String optPrefix, final String longOptPrefix, final String longOptSeparator, final String defaultArgName) {
        final StringBuilder optBuf = new StringBuilder();
        if (getOpt() == null) {
            optBuf.append("   ").append(longOptPrefix).append(getLongOpt());
        } else {
            optBuf.append(optPrefix).append(getOpt());
            if (hasLongOpt()) {
                optBuf.append(',').append(longOptPrefix).append(getLongOpt());
            }
        }
        if (hasArg()) {
            final String argName = getArgName();
            if (argName != null && argName.isEmpty()) {
                // if the option has a blank argname
                optBuf.append(' ');
            } else {
                optBuf.append(hasLongOpt() ? longOptSeparator : " ");
                optBuf.append("<").append(argName != null ? getArgName() : defaultArgName).append(">");
            }
        }
        return optBuf.toString();
    }
```

### [new] `Option.java` > `Option.toLabel(String,String)` (lines 1037-1052)

```java
    /**
     * Builds the name label of this option: the short name with {@code optPrefix} if it has one, otherwise the long name with {@code longOptPrefix}.
     *
     * @param optPrefix the prefix for the short option name, for example {@code "-"}.
     * @param longOptPrefix the prefix for the long option name, for example {@code "--"}.
     * @return the name label, for example {@code -a} or {@code --aaa}.
     */
    String toLabel(final String optPrefix, final String longOptPrefix) {
        final StringBuilder buff = new StringBuilder();
        if (getOpt() != null) {
            buff.append(optPrefix).append(getOpt());
        } else {
            buff.append(longOptPrefix).append(getLongOpt());
        }
        return buff.toString();
    }
```

### [new] `Option.java` > `Option.toUsageLabel(String,String,String,String)` (lines 1086-1103)

```java
    /**
     * Builds the label of this option for a usage line, for example {@code -a <arg>} or {@code --aaa=<arg>}.
     *
     * @param optPrefix the prefix for the short option name.
     * @param longOptPrefix the prefix for the long option name.
     * @param longOptSeparator the separator between a long option and its argument.
     * @param defaultArgName the argument name to use when this option has none.
     * @return the usage label.
     */
    String toUsageLabel(final String optPrefix, final String longOptPrefix, final String longOptSeparator, final String defaultArgName) {
        final StringBuilder buff = new StringBuilder(toLabel(optPrefix, longOptPrefix));
        // if the Option has a value and a non blank argname
        if (hasArg() && (getArgName() == null || !getArgName().isEmpty())) {
            buff.append(getOpt() == null ? longOptSeparator : " ");
            buff.append("<").append(getArgName() != null ? getArgName() : defaultArgName).append(">");
        }
        return buff.toString();
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
