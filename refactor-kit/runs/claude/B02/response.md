RUN: B02 / Claude / Claude Opus 5.5 (claude-opus-5-5)
Verdict: PASS
Original tests: 738/797   Refactored tests: 738/797   Regressions: 0
Metrics (before -> after): Size 676 -> 675   Cohesion 0.7285 -> 0.5623   Coupling 32 -> 34
Files changed: src/main/java/org/apache/commons/cli/DefaultParser.java (+7 -28), src/main/java/org/apache/commons/cli/Parser.java (+7 -33), src/main/java/org/apache/commons/cli/RequiredOptions.java (+87 -0, new)
What I did:
- Extract Class: added the package-private final class `RequiredOptions`. It owns the per-parse "still expected" list, built with the same `new ArrayList<>(options.getRequiredOptions())` copy that both parsers used.
- Move Field: the raw expected list moved out of both parsers into `RequiredOptions`. `Parser.requiredOptions` is now a private `RequiredOptions`, and `DefaultParser` gained a private `requiredOptions` tracker.
- Move Method: both cloned `updateRequiredOptions` bodies became `RequiredOptions.markSeen(Option, OptionGroup)`, with the statement order unchanged (remove the key, then the group, then `setSelected`). Both `checkRequiredOptions` bodies became `checkAllPresent()`, which still throws `MissingOptionException` with the live list.
- Kept the protected members as delegates. `DefaultParser.expectedOpts` points to the tracker's live list. `Parser.getRequiredOptions()` delegates and still returns null before `setOptions`. Both `checkRequiredOptions()` methods delegate.
- Removed the two private `updateRequiredOptions` clones and changed their call sites to `markSeen`. Removed Parser's unused `ArrayList` import. `Options` and `MissingOptionException` are unchanged, so the list contents, their order and the messages stay the same.
Reviewer should check:
- Subclass hooks: before, a subclass that reassigned `DefaultParser.expectedOpts` in the middle of a parse, or overrode `Parser.getRequiredOptions()`, changed which list the check and removal logic used. Now the tracker's own list is always used. Changing the list in place still behaves as before. No code in the library or in `src/test` does either.
- Group lookup: `getOptionGroup` is now called once at the call site instead of twice inside the method. It is a plain map lookup, so the difference cannot be observed.
- Cohesion: most of the mean LCOM* drop comes from adding a class with LCOM* 0 to the average. Parser improved (0.6923 -> 0.5833). DefaultParser's LCOM* rose slightly (0.7968 -> 0.803), although its raw LCOM fell from 149 to 131.
- Coupling: the +2 comes from the new class (CBO 4). Each parser dropped by 1 (DefaultParser 14 -> 13, Parser 12 -> 11). My predictions in process.md section 7 (parser CBO flat or +1, cohesion better for both parsers) do not match these measured numbers.
- Scope: the smell is only partly removed. The String/OptionGroup list in `Options` (with its TODO) and the `toString()`-based message in `MissingOptionException` were left as they are, because the outline requires their contents to stay the same. The `processProperties`/`handleProperties` duplication is noted under Observations and was not changed.
- Run notes: runs/claude/B02/process.md, runs/claude/B02/REPORT.md, runs/claude/B02/metrics.md
