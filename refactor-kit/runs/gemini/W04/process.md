# Refactoring process - W04 Long Parameter List - Gemini

> Written by the LLM during the run. Keep the headings and replace every _italic guidance line_ with your own text.
> Model: Gemini 3.1 Pro · Mode: agent · Started: 2026-11-11 10:05

## 1. Understanding of the smell
In `HelpFormatter.java`, `printHelp(PrintWriter, int, String, String, Options, int, int, String, boolean)` (lines 736–753) takes 9 parameters, and its overload at lines 717–720 takes 8 parameters. Three of those parameters (`width`, `leftPad`, and `descPad`) form a recurring data clump representing layout dimensions that travel together through `printHelp`, `printOptions` (line 815), `renderOptions` (line 918), and `appendOptions` (line 407), even though `HelpFormatter` already holds default values for these three layout properties (`defaultWidth`, `defaultLeftPad`, `defaultDescPad`). This makes the parameter lists overly long and harder to read and maintain (Long Parameter List).

## 2. Plan
1. **Introduce Parameter Object (`HelpLayout`):** Create a package-private immutable value class `HelpLayout` in `org.apache.commons.cli` encapsulating `width`, `leftPad`, and `descPad` with final fields, a constructor, and package-private getters (`getWidth()`, `getLeftPad()`, `getDescPad()`). Compile and run `HelpFormatterTest`.
2. **Change Function Declaration / Preserve Whole Object on `printHelp` and `printOptions`:** Add an internal helper `printOptions(PrintWriter, Options, HelpLayout)` that preserves the whole `HelpLayout` object and delegates to the public 5-argument `printOptions` (preserving subclass override hooks), and add a private `printHelp(PrintWriter, HelpLayout, String, String, Options, String, boolean)` method that accepts `HelpLayout` instead of the three separate layout integers. Compile and run `HelpFormatterTest`.
3. **Route the long `printHelp` overload through the parameter-object method:** Replace the body of the 9-parameter `printHelp` overload with a one-line delegation call `printHelp(pw, new HelpLayout(width, leftPad, descPad), cmdLineSyntax, header, options, footer, autoUsage)` (while the 8-parameter `printHelp` overload remains a one-line delegate to the 9-parameter overload). Compile and run `HelpFormatterTest` and the full test suite.

## 3. Steps performed

| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | Added `HelpLayout.java` (`HelpLayout` constructor, `getWidth()`, `getLeftPad()`, `getDescPad()`) | OK | `HelpFormatterTest` 38/38 passed |
| 2 | Added private `HelpFormatter.printHelp(PrintWriter, HelpLayout, String, String, Options, String, boolean)` and private `HelpFormatter.printOptions(PrintWriter, Options, HelpLayout)` | OK | `HelpFormatterTest` 38/38 passed |
| 3 | Updated `HelpFormatter.printHelp(PrintWriter, int, String, String, Options, int, int, String, boolean)` to delegate to the `HelpLayout` overload | OK | `HelpFormatterTest` 38/38 passed; full suite 738/797 passed (59 skipped) |

## 4. Why behaviour is preserved
- **Public and protected API unchanged:** Every existing `printHelp`, `printOptions`, and `renderOptions` overload retains its exact signature, visibility, and modifiers.
- **Identical control flow and exceptions:** `new HelpLayout(width, leftPad, descPad)` performs only three field assignments and cannot throw; `printHelp(PrintWriter, HelpLayout, ...)` immediately checks `Util.isEmpty(cmdLineSyntax)` and throws the same `IllegalArgumentException("cmdLineSyntax not provided")` when empty, then invokes `printUsage`, `printWrapped`, and `printOptions` in the exact same order with the exact same `width`, `leftPad`, and `descPad` values.
- **Subclass and Mockito spy compatibility:** `printOptions(PrintWriter, Options, HelpLayout)` delegates to the public `printOptions(PrintWriter, int, Options, int, int)`, ensuring any subclass override of `printOptions`, `renderOptions`, or package-private `appendOptions` (such as the Mockito spy in `HelpFormatterTest.testRenderSince`) continues to be invoked identically.

## 5. Deviations from the plan
None

## 6. Observations (not changed)
- The Javadoc on the 8-argument and 9-argument `printHelp(PrintWriter, ...)` methods declares `@throws IllegalStateException if there is no room to print a line`, which is never thrown, while omitting `@throws IllegalArgumentException` when `cmdLineSyntax` is null or empty.
- `HelpFormatter` still stores mutable default layout fields (`defaultWidth`, `defaultLeftPad`, `defaultDescPad`), which are noted in a `Builder` TODO for 2.0 immutability.

## 7. Self-assessment
- Smell removed: partly — the internal `printHelp` implementation and `printOptions` call path now accept a `HelpLayout` parameter object (reducing the internal `printHelp` parameter count from 9 to 7 and grouping the `width`/`leftPad`/`descPad` clump), while the public 8- and 9-parameter `printHelp` overloads and `printOptions`/`renderOptions`/`appendOptions` signatures remain in place as required to preserve the public/protected API and test spies.
- Expected effect on size: Slight increase in total LOC due to the new `HelpLayout` parameter class and delegating methods, while reducing parameter count on the internal `printHelp` method from 9 to 7.
- Expected effect on cohesion: Improved mean cohesion (lower LCOM*) across the affected classes because `HelpLayout` is a cohesive value class encapsulating the three layout fields.
- Expected effect on coupling: Slight increase (+1 CBO on `HelpFormatter`) due to the reference to the new `HelpLayout` parameter object class.
