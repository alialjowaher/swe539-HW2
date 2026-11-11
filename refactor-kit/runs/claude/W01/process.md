# Refactoring process - W01 Long Method - Claude

> Written by the LLM during the run. Keep the headings and replace every _italic guidance line_ with your own text.
> Model: Claude Opus 5.5 (claude-opus-5-5) · Mode: agent · Started: 2026-11-10 09:47

## 1. Understanding of the smell
`HelpFormatter.appendOptions(A, int, Options, int, int)` (`HelpFormatter.java`, lines 407–478) is a Long Method: 72 lines with cyclomatic complexity 20, and one body doing three separate jobs. Lines 421–444 build each option's `<lpad>-a,--aaa <arg>` label and track the widest one. Lines 446–452 write the optional `Options / Since / Description` header. Lines 454–476 pad each label, add the since column and the description (or deprecation text), and write the row. You have to read every branch of all three jobs to see the method's overall shape (sort → labels → header → rows). That is why it is a Long Method and why Extract Method is the right cure.

## 2. Plan
Technique: Extract Method ×3, plus Replace Temp with Query where practical. Each extraction follows Fowler's mechanics: create a private method named after the intention, copy the fragment verbatim, pass the locals it reads as parameters (and return the one it produces), replace the fragment with a call, then compile and run `HelpFormatterTest`.

1. **Extract `buildOptionLabel(Option, String lpad)`** from the body of the first loop (lines 422–440). It reads `option` and `lpad` and returns the label `StringBuilder`. The loop keeps `prefixList.add(...)` and the `max` update, because those accumulate across iterations.
2. **Extract `appendSinceHeader(sb, width, nextLineTabStop, max, maxSince, leftPad, lpad)`** from the body of the `if (showSince)` block (lines 447–451). The `if (showSince)` stays in `appendOptions`, so the call sequence stays visible there.
3. **Extract `appendOptionRow(sb, width, nextLineTabStop, option, label, max, maxSince, lpad, dpad)`** from the body of the second loop (lines 456–472). The `if (it.hasNext()) sb.append(getNewLine())` separator stays in the loop, because it depends on the iterator and not on the row.
4. **Replace Temp with Query: check each remaining temp** (`lpad`, `dpad`, `max`, `maxSince`, `nextLineTabStop`, `prefixList`) and apply it only where the query adds no calls to overridable methods and no extra passes over the options. See section 4/5 for the outcome.
5. Run the full suite with `python kit.py test --llm "Claude"` and confirm 738 passed / 0 failed / 59 skipped, the same as the baseline.

## 3. Steps performed

| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | `HelpFormatter.java`: Extract Method. New private `buildOptionLabel(Option, String)` holds the first loop's label-building body verbatim and returns the label `StringBuilder`. In `appendOptions`, the loop body is now `buildOptionLabel(option, lpad)` + `prefixList.add` + the `max` update. | OK | HelpFormatterTest 38/38 |
| 2 | `HelpFormatter.java`: Extract Method. New private `appendSinceHeader(A, int, int, int, int, int, String)` holds the body of the `if (showSince)` block verbatim (header build, `appendWrappedText`, new line). The `if (showSince)` guard stays in `appendOptions`. | OK | HelpFormatterTest 38/38 |
| 3 | `HelpFormatter.java`: Extract Method. New private `appendOptionRow(A, int, int, Option, String, int, int, String, String)` holds the second loop's row body verbatim (padding, since column, description or deprecation text, `appendWrappedText`). The between-rows `getNewLine()` stays in the loop, because it depends on the iterator. | OK | HelpFormatterTest 38/38 |
| 4 | Replace Temp with Query: checked every remaining temp in `appendOptions` and applied none (reasons in sections 4 and 5). No code change. | n/a | n/a |
| 5 | Full suite on the finished refactoring. | OK | 738 passed / 0 failed / 0 errors / 59 skipped of 797 (identical to the baseline) |

## 4. Why behaviour is preserved
- **The code was moved verbatim.** Each extracted method contains exactly the statements that were in the fragment, in the same order, with the same literals (`"   "`, `','`, `' '`, `"<"`, `">"`, `"-"`), the same `trim()` on the deprecation text, and the same deprecated-before-description precedence. The output is therefore built from the same appends in the same sequence.
- **Every value the fragments read goes in as a parameter, and nothing is recomputed.** `lpad`, `dpad`, `max`, `maxSince`, `nextLineTabStop` and `leftPad` are computed once in `appendOptions`, exactly as before. This matters because `createPadding` (protected), `getOptPrefix`, `getLongOptPrefix`, `getArgName`, `getNewLine` and `getOptionComparator` (public) can all be overridden by subclasses. The refactored code calls each of them the same number of times, in the same order and with the same arguments as the original, so subclasses see no difference. The double `option.getArgName()` call in the label code was also kept.
- **Copy semantics are the same.** The original created each row as `new StringBuilder(prefixList.get(x++).toString())`. The call now evaluates `prefixList.get(x++).toString()` at the same point, right after `it.next()`, and `appendOptionRow` wraps it in `new StringBuilder(label)`. The stored labels are still never mutated.
- **The control flow is the same.** The `if (showSince)` guard, the `if (optBuf.length() < max)` padding guard and the `if (it.hasNext())` row separator are unchanged, so header presence, the padding cases and the lack of a trailing new line after the last row all stay the same.
- **Exceptions are the same.** The two new methods that write to the `Appendable` declare `throws IOException` and propagate it unchanged. No catch blocks were added.
- **The API is unchanged.** All new members are `private`. The signature, visibility and Javadoc of `appendOptions` are untouched, and no test file was modified.
- **Replace Temp with Query: why it was not applied.** `lpad` and `dpad` as queries would add calls to the overridable `createPadding` (one per row, not one per table). `maxSince` as a query would re-run `determineMaxSinceLength`, a full pass over the options, on every use. `max` is accumulated inside the label loop, so it can't be a side-effect-free query without a second pass. `nextLineTabStop` and `prefixList` depend on those. Each candidate would add calls a subclass can observe, or extra work, so none was practical. The temps stay as locals and are passed to the extracted methods as parameters.

## 5. Deviations from the plan
- None in the refactoring itself. The steps were done as planned. Step 4 (Replace Temp with Query) ended with "not practical for any temp", as the plan allowed ("only where…"). The reasons are in section 4.
- Process note: my first attempt at step 1 was blocked by the agent's own sandbox before anything was written to disk. The HelpFormatterTest run from that attempt therefore ran on unchanged code and is not counted above. After the user changed the session setting, step 1 was re-applied and tested normally. This had no effect on the code.
- `finish` attempts: 1 (see the verdict in REPORT.md).

## 6. Observations (not changed)
- **New Long Parameter List:** `appendOptionRow` takes 9 parameters and `appendSinceHeader` takes 7. The shared table layout (`max`, `maxSince`, `lpad`, `dpad`, `nextLineTabStop`) is held in locals, and Extract Method has to pass them in. Introduce Parameter Object (for example a small table-layout holder) would fix this, but it is a different technique and outside this run.
- **Redundant call:** in the label code, `option.getArgName()` is stored in `argName` and then called again in `argName != null ? option.getArgName() : getArgName()`. I kept both calls to preserve behaviour.
- **Stale comment:** the comment above the label loop says the list "will be then used to sort options ascending", but sorting happens earlier, through `getOptionComparator()`. I left it, because comment edits are out of scope.
- **Javadoc:** the `appendOptions` Javadoc still talks about "StringBuffer" and has no `@param <A>`. Left unchanged.
- **Duplicated label logic** (smell B01): the same "-opt / --longOpt / <arg>" label logic is also built in `appendOption` and in `OptionGroup.toString`.
- **Baseline:** 59 of the 797 original tests are skipped by the project itself (`@Disabled` cases in BasicParserTest, GnuParserTest and PosixParserTest). None fail.
- **Session:** at the user's request, this run and the B01 run were done in the same agent session, not in separate fresh sessions.

## 7. Self-assessment
- Smell removed: **yes.** `appendOptions` went from 72 lines (NLOC 64, CC 20) to about 34 lines that only sequence the steps (sort → labels → header → rows). Each of its three former jobs is now a named private method. What remains is the long parameter lists of the helpers (section 6).
- Expected effect on size: `appendOptions` NLOC and cyclomatic complexity drop sharply (CC roughly 20 → 6). The three new methods have about CC 7, 1 and 6. Class NLOC goes up slightly (new signatures and Javadoc), and the method count grows by 3.
- Expected effect on cohesion: about unchanged. The new private methods use the same fields as before (`showSince`, `longOptSeparator`, `deprecatedFormatFunction`). A per-method metric such as LCOM may move slightly because there are more methods.
- Expected effect on coupling: unchanged. No new types are referenced, and `HelpFormatter` still depends on the same classes (`Option`, `Options`, `Appendable`, etc.).
