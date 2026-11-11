# Refactoring process - B01 Feature Envy - Claude

> Written by the LLM during the run. Keep the headings and replace every _italic guidance line_ with your own text.
> Model: Claude Opus 5.5 (claude-opus-5-5) · Mode: agent · Started: 2026-11-10 10:00

## 1. Understanding of the smell
Two classes decide how an `Option` is displayed, and neither of them is `Option`. In `HelpFormatter.java`:
- `appendOption` (lines 346–364) makes about 9 calls on its `Option` argument (`getOpt`, `getLongOpt`, `hasArg`, `getArgName` ×4) to build the usage clause `-a <arg>`.
- The label block of `appendOptions` (lines 421–440) makes about 9 more to build the options-table label `-a,--aaa <arg>`.
- The static `getDescription(Option)` (lines 226–229) reads nothing but its `Option`.

`OptionGroup.toString` (`OptionGroup.java` lines 149–155) rebuilds the same `-opt` / `--longOpt` name from `Option` getters. These methods are more interested in `Option`'s data than in their own class's, which is Feature Envy. The cure is to move the display logic onto `Option`.

## 2. Plan
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

## 3. Steps performed
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

## 4. Why behaviour is preserved
- **Every moved body is the original fragment, verbatim.** It has the same literals (`"   "`, `','`, `' '`, `"<"`, `">"`), the same branch conditions and the same append order. The usage form still picks its separator with `getOpt() == null` and skips blank arg names. The table form still picks its separator with `hasLongOpt()` and appends `' '` for a blank arg name. The two formats were **not** unified (see section 5).
- **Field access inside `Option` goes through the same getters.** Inside `Option` the moved code calls `getOpt()`, `getLongOpt()`, `getArgName()`, `hasArg()`, `hasLongOpt()` and `getDescription()`, never the fields directly. `Option` is not final, so a subclass that overrides a getter sees exactly the calls it saw before. The double `getArgName()` call in the table label is kept too.
- **The prefixes are unchanged.** `appendOption` and `OptionGroup.toString` pass the hard-coded `"-"`/`"--"` they used before, so the usage line still ignores custom prefixes, as the sheet requires. `appendOptions` passes `getOptPrefix()`/`getLongOptPrefix()`, as before. `lpad` and the `[`/`]` brackets stay in `HelpFormatter`, because they are layout, not option data.
- **`OptionGroup.toString` keeps `getDescription() != null`.** It does not use the new null-safe accessor. With a description of `""`, the original prints `-a ` (with a trailing space), and an empty-check rewrite would drop that space.
- **`HelpFormatter.getDescription(Option)` still exists** (public static, `@since 1.8.0`) and returns the same value. A null argument still throws `NullPointerException`, now from `option.getDescriptionOrEmpty()`. `DEFAULT_DEPRECATED_FORMAT` still calls it unchanged.
- **The one intended call-pattern difference: eager arguments.** Move Method needs the formatter's settings passed as arguments, as in the sheet's own `toLabel(optPrefix, longOptPrefix)` design. So `getOptPrefix()`, `getLongOptPrefix()` and `getArgName()` (and in `appendOption`, `getArgName()`) are now evaluated once per option before the call. The original called them only on some branches, for example `getArgName()` only when the option had no arg name. They are plain getters, so the values and the printed text are identical. Only a `HelpFormatter` subclass that overrides those getters with side effects could tell the difference.
- **Nothing else changed.** No exception paths were added or removed, the new members are package-private, and `Option`'s explicit `serialVersionUID = 1L` means its serialized form is unaffected. No test file was touched.

## 5. Deviations from the plan
- **More than one label method on `Option` (a deviation from the sheet's outline, not from the technique).** The sheet suggests a single `toLabel(String optPrefix, String longOptPrefix)` for all three callers. The three callers actually print different formats, so one method can't serve all of them without changing output:

  | Caller | Name part | Arg part |
  |---|---|---|
  | `HelpFormatter.appendOption` (usage line) | `-a` **or** `--aaa` (hard-coded `-`/`--`) | only if the arg name is not blank; separator is `longOptSeparator` if `getOpt() == null`, else `" "` |
  | `HelpFormatter.appendOptions` (options table) | `-a,--aaa`, `-a`, or `   --aaa` (configured prefixes) | blank arg name → `' '`; otherwise separator is `longOptSeparator` if `hasLongOpt()`, else `" "` |
  | `OptionGroup.toString` | `-a` **or** `--aaa` (`-`/`--`) | none |

  So `toLabel` holds the truly shared name part, used by `OptionGroup.toString` and, through `toUsageLabel`, by `appendOption`. `toUsageLabel` adds the usage-line arg part, and `toHelpLabel` is the table form, moved verbatim. All three use the same Extract Method → Move Method technique. No other refactoring was applied.
- Process: the temporary private helpers created in steps 1 and 5 were deleted in steps 2 and 6, which is Fowler's last step for a private source method that no longer has callers.
- `finish` attempts: 1 (see the verdict in REPORT.md).

## 6. Observations (not changed)
- **Remaining envy outside the cited lines:** the row part of `appendOptions` still reads `option.getSince()`, `option.isDeprecated()` and `option.getDescription()` (×2, `else if (option.getDescription() != null)`). It could use `getDescriptionOrEmpty()`, but it is outside the cited lines (421–440), so I left it.
- **Inconsistent separator rules:** the usage line puts `longOptSeparator` before the argument only when the option has **no** short name, while the table uses it whenever the option **has** a long name. For an option with both names, the usage line shows `-a <arg>` and the table shows `-a,--aaa=<arg>`. This may be intended, so I kept it.
- **Usage line ignores custom prefixes:** `appendOption` (and so `printUsage`) always prints `-`/`--`, even after `setOptPrefix`/`setLongOptPrefix`. I kept this, as the sheet instructs.
- **Blank arg names are handled differently:** a blank arg name (`""`) prints nothing in the usage line but a single space in the table. I kept this.
- **Baseline:** 59 of the 797 original tests are skipped by the project itself (`@Disabled` cases in BasicParserTest, GnuParserTest and PosixParserTest). None fail.
- **Session:** at the user's request, this run and the W01 run were done in the same agent session, not in separate fresh sessions.

## 7. Self-assessment
- Smell removed: **yes, for the cited members.**
  - `appendOption` went from about 9 calls on `Option` to 1 (`toUsageLabel`).
  - The `appendOptions` label block went from about 9 to 1 (`toHelpLabel`).
  - `HelpFormatter.getDescription(Option)` is now a one-line delegator.
  - `OptionGroup.toString` no longer rebuilds the name label (it keeps 2 `getDescription()` reads, for behaviour reasons).
  - How an option's label is built is now decided in `Option`. The remaining envy is in the row block of `appendOptions` (section 6), which is outside the cited lines.
- Expected effect on size: `HelpFormatter` −31 lines (`appendOption` and `appendOptions` get shorter and simpler, with lower CC), `OptionGroup` −6 lines, `Option` +78 lines (4 new package-private methods with Javadoc). Total NLOC goes up slightly because of the new signatures and Javadoc.
- Expected effect on cohesion: `HelpFormatter` improves slightly, since the code that only used `Option` data is gone. `Option` gains methods that work only on its own state, so its cohesion stays the same or improves.
- Expected effect on coupling: message-passing coupling and RFC from `HelpFormatter` and `OptionGroup` to `Option` drop, because they replace many getter calls with one label call. CBO is unchanged, since both classes still reference `Option`. There are no new dependencies.
