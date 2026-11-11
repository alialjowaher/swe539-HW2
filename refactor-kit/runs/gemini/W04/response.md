RUN: W04 / Gemini / Gemini 3.1 Pro
Verdict: PASS
Original tests: 738/797   Refactored tests: 738/797   Regressions: 0
Metrics (before -> after): Size 425 -> 451   Cohesion 0.9549 -> 0.7284   Coupling 9 -> 10
Files changed: src/main/java/org/apache/commons/cli/HelpFormatter.java (+43 -15), src/main/java/org/apache/commons/cli/HelpLayout.java (+73 -0)
What I did:
- Introduce Parameter Object: created package-private immutable value class `HelpLayout` holding `width`, `leftPad`, and `descPad` with final fields and package-private getters.
- Change Function Declaration / Preserve Whole Object: added private `printHelp(PrintWriter, HelpLayout, String, String, Options, String, boolean)` and private `printOptions(PrintWriter, Options, HelpLayout)` taking the whole `HelpLayout` parameter object instead of separate `width`, `leftPad`, and `descPad` parameters.
- Replaced the 9-parameter `printHelp` body with a one-line delegation call `printHelp(pw, new HelpLayout(width, leftPad, descPad), cmdLineSyntax, header, options, footer, autoUsage)` while keeping the 8-parameter `printHelp` overload as a one-line delegate.
- Preserved subclass and Mockito spy compatibility by having `printOptions(PrintWriter, Options, HelpLayout)` delegate to the public 5-argument `printOptions`.
Reviewer should check:
- The public 8- and 9-parameter `printHelp` overloads and `printOptions`/`renderOptions`/`appendOptions` signatures remain in place to preserve the public/protected API and `HelpFormatterTest.testRenderSince` spy behavior.
- Mean LCOM* improved from 0.9549 to 0.7284 due to the cohesive `HelpLayout` class (LCOM* 0.5) being averaged with `HelpFormatter` (LCOM* 0.9568).
