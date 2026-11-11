RUN: W04 / Claude / Claude Opus 5.5 (claude-opus-5-5)
Verdict: PASS
Original tests: 738/797 (59 skipped)   Refactored tests: 738/797 (59 skipped)   Regressions: 0
Metrics (before -> after): Size 425 -> 447   Cohesion 0.9549 -> 0.7279   Coupling 9 -> 10
Files changed: src/main/java/org/apache/commons/cli/HelpFormatter.java (+22 -5), src/main/java/org/apache/commons/cli/HelpLayout.java (+74 -0, new file)
What I did:
- Introduce Parameter Object: created `HelpLayout`, a new package-private, immutable class with final fields width, leftPad and descPad, a constructor with no validation, and package-private getters. Its license header is byte-identical to the other source files.
- Change Function Declaration / Preserve Whole Object: added a private `printHelp(PrintWriter, HelpLayout, String, String, Options, String, boolean)` that takes the whole layout object instead of three ints (7 parameters instead of 9). Its body is the old 9-arg body, unchanged except that it reads the three values from the layout.
- Pointed the caller at the new object: the public 9-arg `printHelp` is now a one-line delegate, `printHelp(pw, new HelpLayout(width, leftPad, descPad), ...)`. Its signature and Javadoc are unchanged, and no public or protected API was added or removed.
- Left the 8-arg and 6-arg `printHelp` overloads, `printOptions`, `renderOptions` and `appendOptions` unchanged. This keeps subclass overrides reachable, and the Mockito stub in `HelpFormatterTest.testRenderSince` (on the 5-arg `appendOptions`) still works.
- Ran `HelpFormatterTest` after each step (38/38 every time), then the full suite (738/797, the same as the original).
Reviewer should check:
- Cohesion: the mean only improved because the new `HelpLayout` (LCOM* 0.5) is now part of the average. `HelpFormatter` itself went slightly worse, LCOM* 0.9549 -> 0.9558 and RFC 77 -> 81.
- `finish` was run twice and both runs gave PASS. The second run changed no code. It was only to clear one leftover italic guidance line in process.md, so that REPORT.md and the log contain the completed notes. This is recorded in process.md section 5.
- The smell is only partly removed. The width/leftPad/descPad clump is still in the signatures of `printOptions`, `renderOptions` and `appendOptions`, for three reasons: those signatures are public, protected or pinned by a test; a Mockito stub depends on `appendOptions`; and subclass overrides must stay reachable. The public 8-arg and 9-arg `printHelp` signatures stay long because they are public API.
- One ordering change: `new HelpLayout(...)` now runs before the `cmdLineSyntax` check. This is harmless because the constructor only assigns fields and cannot throw.
- Not changed, noted in process.md section 6: the Javadoc of the `printHelp(PrintWriter, ...)` overloads documents an `IllegalStateException` that is never thrown, and does not mention the `IllegalArgumentException` that is.
