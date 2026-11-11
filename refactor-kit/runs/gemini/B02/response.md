RUN: B02 / Gemini / Gemini 3.1 Pro
Verdict: PASS
Original tests: 738/797   Refactored tests: 738/797   Regressions: 0
Metrics (before -> after): Size 676 -> 681   Cohesion 0.7285 -> 0.5751   Coupling 32 -> 34
Files changed: src/main/java/org/apache/commons/cli/DefaultParser.java (+7 -19), src/main/java/org/apache/commons/cli/Parser.java (+6 -23), src/main/java/org/apache/commons/cli/RequiredOptions.java (+78 -0)
What I did:
- Extract Class: created package-private final class `RequiredOptions` owning the mutable per-parse list of still-expected required option keys and `OptionGroup` instances initialized from `options.getRequiredOptions()`.
- Move Field: moved the per-parse required-options list tracking into `RequiredOptions` (`Parser.requiredOptions` became a `RequiredOptions` instance, and `DefaultParser` gained a private `RequiredOptions` field while keeping `protected List expectedOpts` pointing to the tracker's live list).
- Move Method: moved the duplicated `updateRequiredOptions` and `checkRequiredOptions` logic from `DefaultParser` and `Parser` into `RequiredOptions.markSeen(Option, OptionGroup)` and `RequiredOptions.checkAllPresent()`.
- Preserved all public and protected subclass API members (`DefaultParser.expectedOpts`, `DefaultParser.checkRequiredOptions()`, `Parser.getRequiredOptions()`, `Parser.checkRequiredOptions()`, `Options.getRequiredOptions()`, and `MissingOptionException.getMissingOptions()`) as delegates.
Reviewer should check:
- Both `DefaultParser` and `Parser` dropped in size (377 -> 368 and 159 -> 148 LOC), WMC (121 -> 117 and 51 -> 48), and CBO (14 -> 13 and 12 -> 11), while `RequiredOptions` has LCOM* = 0 and CBO = 4.
- `Options.requiredOpts` and `MissingOptionException.getMissingOptions()` retain their existing list elements and order as required by the public API and test assertions.
