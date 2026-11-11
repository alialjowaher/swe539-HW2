# Refactoring process - W01 Long Method - Gemini

> Written by the LLM during the run. Keep the headings and replace every _italic guidance line_ with your own text.
> Model: Gemini 3.1 Pro · Mode: agent · Started: 2026-11-10 13:10

## 1. Understanding of the smell
`HelpFormatter.appendOptions(A, int, Options, int, int)` (lines 407–478 in `HelpFormatter.java`) is a Long Method with 72 lines (64 NLOC), cyclomatic complexity 20, and 5 parameters. Rather than doing a single cohesive task at one level of abstraction, its body mixes three distinct responsibilities: (1) building each option's prefix label (`<lpad>-a,--aaa <arg>`) and tracking the maximum column width, (2) formatting and appending the optional "Options / Since / Description" table header when `showSince` is enabled, and (3) padding each option row with its optional `since` value and description/deprecation text and writing the wrapped line.

## 2. Plan
1. Extract `buildOptionLabel(final Option option, final String lpad)` from the first loop body in `appendOptions` to construct and return the `StringBuilder` prefix label for a single `Option`, replacing the loop body with a call to `buildOptionLabel`, then compile and run `HelpFormatterTest`.
2. Extract `appendSinceHeader(final A sb, final int width, final int nextLineTabStop, final int max, final int maxSince, final int leftPad, final String lpad)` from the `if (showSince)` header block in `appendOptions`, replace the block body with a call to `appendSinceHeader`, then compile and run `HelpFormatterTest`.
3. Extract `appendOptionRow(final A sb, final int width, final int nextLineTabStop, final Option option, final StringBuilder prefix, final int max, final int maxSince, final String lpad, final String dpad)` from the second loop body in `appendOptions` so `appendOptions` retains only the high-level sequence (sort → labels → header → rows), then compile and run `HelpFormatterTest` and the full test suite.

## 3. Steps performed

| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | `HelpFormatter.java`: extracted `buildOptionLabel(Option, String)` from the first loop of `appendOptions` | PASS | `HelpFormatterTest` 38/38 passed |
| 2 | `HelpFormatter.java`: extracted `appendSinceHeader(A, int, int, int, int, int, String)` from the `showSince` block of `appendOptions` | PASS | `HelpFormatterTest` 38/38 passed |
| 3 | `HelpFormatter.java`: extracted `appendOptionRow(A, int, int, Option, StringBuilder, int, int, String, String)` from the second loop of `appendOptions` | PASS | `HelpFormatterTest` 38/38 passed; full suite 738/797 passed (59 skipped) |

## 4. Why behaviour is preserved
Each of the three extracted methods (`buildOptionLabel`, `appendSinceHeader`, and `appendOptionRow`) is a direct extraction of the original statements in `appendOptions` with identical control flow, operators, padding calculations, and method calls. All local variables read by each block (`lpad`, `dpad`, `leftPad`, `max`, `maxSince`, `nextLineTabStop`, `width`, `sb`, `option`, `prefixList.get(x++)`) are passed unchanged, and instance fields/methods (`showSince`, `deprecatedFormatFunction`, `longOptSeparator`, `createPadding`, `appendWrappedText`, `getNewLine`, `getOptPrefix`, `getLongOptPrefix`, `getArgName`) are accessed on `this` in the exact same order. In particular:
- `leftPad` and `lpad` are both passed to `appendSinceHeader` so subclasses overriding `createPadding(int)` observe identical calls and arguments.
- `prefixList` still stores `StringBuilder` instances created per option, and `appendOptionRow` constructs a new `StringBuilder(prefix.toString())` before padding, matching the original code.
- Line separator appending between option rows (`if (it.hasNext()) { sb.append(getNewLine()); }`) remains in the outer loop of `appendOptions`.

## 5. Deviations from the plan
None.

## 6. Observations (not changed)
- In `buildOptionLabel` (original line 438), `argName != null ? option.getArgName() : getArgName()` calls `option.getArgName()` a second time even though its result is already stored in the local `argName`. Left unchanged to preserve exact call counts on `Option`.
- In `appendOptionRow` (original line 457), `new StringBuilder(prefixList.get(x++).toString())` copies a `StringBuilder` that is never reused afterwards. Left unchanged.

## 7. Self-assessment
- Smell removed: yes — `appendOptions` now delegates the three detailed formatting tasks to `buildOptionLabel`, `appendSinceHeader`, and `appendOptionRow`, leaving only the high-level coordination sequence (sort options, build labels and compute max width, append optional header, append rows).
- Expected effect on size: NLOC and cyclomatic complexity of `appendOptions` decrease substantially, while total class LOC increases slightly due to the 3 new private method signatures and Javadocs.
- Expected effect on cohesion: Slightly improved or unchanged (LCOM* stays low as the new helper methods access `HelpFormatter`'s formatting fields and methods).
- Expected effect on coupling: Unchanged (CBO remains the same as no new external types are referenced).
