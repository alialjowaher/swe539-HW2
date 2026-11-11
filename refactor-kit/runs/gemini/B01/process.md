# Refactoring process - B01 Feature Envy - Gemini

> Written by the LLM during the run. Keep the headings and replace every _italic guidance line_ with your own text.
> Model: Gemini 3.1 Pro · Mode: agent · Started: 2026-11-10 13:24

## 1. Understanding of the smell
`HelpFormatter` and `OptionGroup` exhibit Feature Envy toward `Option`: `HelpFormatter.appendOption` (lines 346–364) makes 9 getter/query calls on `Option` (`getOpt`, `getLongOpt`, `hasArg`, `getArgName`) while using only two `HelpFormatter` members; the option-label loop in `HelpFormatter.appendOptions` (lines 421–440) makes 9 more `Option` calls to build `<lpad>-a,--aaa <arg>`; `HelpFormatter.getDescription(Option)` (lines 226–229) is a static method reading only `Option.getDescription()`; and `OptionGroup.toString()` (lines 143–168) repeats the `-opt` / `--longOpt` selection from `Option` getters. Formatting an `Option`'s label and null-safe description relies almost entirely on `Option`'s state and belongs on `Option`.

## 2. Plan
1. Add package-private `getDescriptionOrEmpty()` to `Option` and update `HelpFormatter.getDescription(Option)` and the description branch in `HelpFormatter.appendOptions` to delegate to it; compile and run `HelpFormatterTest` and `OptionTest`.
2. Add package-private `toLabel(String optPrefix, String longOptPrefix)` to `Option` (returning `<optPrefix><opt>` when `option != null`, or `<longOptPrefix><longOption>` otherwise) and update `OptionGroup.toString()` to call `option.toLabel("-", "--")`; compile and run `OptionGroupTest` and `OptionTest`.
3. Add package-private `toLabel(String optPrefix, String longOptPrefix, String longOptSeparator, String defaultArgName)` to `Option` for usage-clause formatting (including the `<arg>` suffix) and update `HelpFormatter.appendOption` to delegate to `option.toLabel("-", "--", longOptSeparator, getArgName())`; compile and run `HelpFormatterTest`.
4. Add package-private `toLabel(String lpad, String optPrefix, String longOptPrefix, String longOptSeparator, String defaultArgName)` to `Option` for help-table option label formatting and update the first loop of `HelpFormatter.appendOptions` to call it; compile and run `HelpFormatterTest`, `OptionGroupTest`, `OptionTest`, and the full test suite.

## 3. Steps performed

| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | `Option.java` (`getDescriptionOrEmpty()`), `HelpFormatter.java` (`getDescription`, `appendOptions`) | PASS | `HelpFormatterTest` 38/38 passed |
| 2 | `Option.java` (`toLabel(String, String)`), `OptionGroup.java` (`toString()`) | PASS | `OptionGroupTest` 13/13 passed |
| 3 | `Option.java` (`toLabel(String, String, String, String)`), `HelpFormatter.java` (`appendOption`) | PASS | `HelpFormatterTest` 38/38 passed |
| 4 | `Option.java` (`toLabel(String, String, String, String, String)`), `HelpFormatter.java` (`appendOptions`) | PASS | `HelpFormatterTest` 38/38, `OptionGroupTest` 13/13, `OptionTest` 21/21, full suite 738/797 passed |

## 4. Why behaviour is preserved
- `Option.getDescriptionOrEmpty()` returns `description == null ? "" : description`, which is identical to `HelpFormatter.getDescription(Option)` and has the same effect in `HelpFormatter.appendOptions` where appending `""` to `optBuf` when `description == null` leaves `optBuf` unchanged. `OptionGroup.toString()` retains its `if (option.getDescription() != null)` check so a space is only prefixed when a description is non-null.
- `Option.toLabel(optPrefix, longOptPrefix)` returns `option != null ? optPrefix + option : longOptPrefix + longOption`. `OptionGroup.toString()` calls `option.toLabel("-", "--")`, matching its previous `-opt` / `--longOpt` branching.
- `Option.toLabel(optPrefix, longOptPrefix, longOptSeparator, defaultArgName)` builds the usage-line option label and appends the `<arg>` clause under the exact same condition (`hasArg() && (argName == null || !argName.isEmpty())`) and separator choice (`option == null ? longOptSeparator : " "`). `HelpFormatter.appendOption` passes `"-"` and `"--"`, preserving the existing hard-coded prefixes in the usage line even when custom prefixes are configured on `HelpFormatter`.
- `Option.toLabel(lpad, optPrefix, longOptPrefix, longOptSeparator, defaultArgName)` builds the help-table option label using `HelpFormatter`'s configured `getOptPrefix()`, `getLongOptPrefix()`, `longOptSeparator`, and `getArgName()`, preserving the `"   "` indentation for long-only options, the `','` separator when both short and long options exist, the trailing `' '` when `argName` is empty, and `hasLongOpt() ? longOptSeparator : " "` before `<arg>`.

## 5. Deviations from the plan
None.

## 6. Observations (not changed)
- `HelpFormatter.appendOption` hard-codes `"-"` and `"--"` instead of using `getOptPrefix()` and `getLongOptPrefix()`, and uses `option.getOpt() == null ? longOptSeparator : " "` (whereas `appendOptions` uses `option.hasLongOpt() ? longOptSeparator : " "`). Both differences were preserved as required.

## 7. Self-assessment
- Smell removed: yes — `HelpFormatter` and `OptionGroup` no longer reach into `Option`'s getters (`getOpt`, `getLongOpt`, `hasLongOpt`, `hasArg`, `getArgName`, `getDescription`) to assemble option labels; `Option` now formats its own labels and null-safe description using its own fields.
- Expected effect on size: `HelpFormatter` and `OptionGroup` shrink; `Option` grows by the 4 new package-private helper methods.
- Expected effect on cohesion: `Option` and `HelpFormatter` cohesion improve or remain stable since `Option`'s new methods operate directly on `Option`'s fields (`option`, `longOption`, `argName`, `description`).
- Expected effect on coupling: Message-passing coupling (RFC) in `HelpFormatter` and `OptionGroup` decreases because multiple `Option` getter calls are replaced by single calls to `toLabel` / `getDescriptionOrEmpty`; CBO is unchanged because both classes still reference `Option`.
