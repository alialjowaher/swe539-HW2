# Refactoring task - smell B01 (Feature Envy) in Apache Commons CLI 1.9.0

You are a careful Java engineer doing **one behaviour-preserving refactoring** (Fowler, *Refactoring*, 2nd ed.) on Apache Commons CLI 1.9.0 (tag `rel/commons-cli-1.9.0`). This is part of a controlled experiment: several LLMs get exactly this task, and the results are judged by the project's original test suite, a public-API check and code metrics. You cannot run code here. The user will apply your files, compile them and run the original tests.

## 1. The smell

| Field | Value |
|---|---|
| ID | B01 |
| Smell type | Between classes |
| Code smell | Feature Envy |
| Class(es) | HelpFormatter → Option (also OptionGroup → Option) |
| Method / member | HelpFormatter.appendOption; label block of appendOptions; getDescription(Option); OptionGroup.toString |
| Lines (1.9.0) | HF 346–364, 421–440, 226–229; OptionGroup 143–168 |
| Priority |  |

**Evidence.** appendOption makes 9 calls on its Option argument (getOpt ×3, getArgName ×4, getLongOpt, hasArg) and uses only 2 HelpFormatter members (getArgName(), longOptSeparator). The label block of appendOptions makes 9 more Option calls to build "-a,--aaa <arg>". getDescription(Option) is a static method that reads only Option. OptionGroup.toString (149–159) rebuilds the same "-opt or --longOpt" label from Option getters. How an option is displayed is decided in two classes, neither of them Option.


## 2. The refactoring to apply

**Technique:** Extract Method, then Move Method (to Option)

_Source: review sheet suggestion (column 'Suggested refactoring')._

**How (outline):** Extract the label logic into a package-private method on Option, e.g. toLabel(String optPrefix, String longOptPrefix), plus a null-safe description accessor. HelpFormatter calls it with its configured prefixes (appendOptions) or with "-"/"--" (appendOption, which ignores the configured prefixes today; keep that). OptionGroup.toString calls it with "-"/"--".

**Risks to watch:** Low–Medium. Output is pinned by HelpFormatterTest and OptionGroupTest. The usage line hard-codes "-"/"--" while the options table uses getOptPrefix()/getLongOptPrefix(); a move that unifies them changes output when a custom prefix is set.

**Expected effect on metrics:** Coupling: fewer HelpFormatter→Option and OptionGroup→Option method calls (RFC / message-passing coupling drop); CBO unchanged because both still reference Option. Cohesion: HelpFormatter improves slightly; Option gains a method that works on its own fields.


Apply **this** technique and nothing else. If you believe it cannot be applied without breaking a rule below, say so in section 5 of your process notes and return no files.

## 3. Where the code is

- `src/main/java/org/apache/commons/cli/HelpFormatter.java` > `HelpFormatter.getDescription(Option)` (lines 220-229)
- `src/main/java/org/apache/commons/cli/HelpFormatter.java` > `HelpFormatter.appendOption(StringBuilder,Option,boolean)` (lines 339-364)
- `src/main/java/org/apache/commons/cli/HelpFormatter.java` > `HelpFormatter.appendOptions(A,int,Options,int,int)` (lines 396-478)
- `src/main/java/org/apache/commons/cli/OptionGroup.java` > `OptionGroup.toString()` (lines 137-168)
- `src/main/java/org/apache/commons/cli/Option.java` (file is involved; no specific member)

The full original source of these files is in section 6. Other files in the package: AlreadySelectedException.java, AmbiguousOptionException.java, BasicParser.java, Char.java, CommandLine.java, CommandLineParser.java, Converter.java, DefaultParser.java, DeprecatedAttributes.java, GnuParser.java, HelpFormatter.java, MissingArgumentException.java, MissingOptionException.java, Option.java, OptionBuilder.java, OptionGroup.java, OptionValidator.java, Options.java, ParseException.java, Parser.java, PatternOptionBuilder.java, PosixParser.java, TypeHandler.java, UnrecognizedOptionException.java, Util.java, package-info.java. If you need one of them, ask for it by name and stop.

## 4. Rules (non-negotiable)

1. **One smell, one technique.** Change only what is needed to remove smell B01 with the technique given in "The refactoring to apply". No other refactorings, renames, reformatting, comment edits or improvements anywhere else.
2. **Behaviour must not change.** Same return values, same printed text (including spaces, line breaks and order), same exceptions and messages, same side effects. If the existing code looks wrong, keep its behaviour and note it under "Observations" in the process notes. Fixing bugs is out of scope.
3. **The original tests are the judge, so don't touch them.** Do not modify, add, delete, skip or disable anything under `src/test/`.
4. **Keep the public and protected API.** Do not remove, rename or change the signature, visibility or modifiers of any public or protected class, constructor, method or field. If the technique moves or renames one, keep the old one and make it delegate to the new one. New members should be `private` or package-private unless the technique needs otherwise.
5. **Java 8, no new dependencies.** Do not edit `pom.xml` or any build file. Use only Java 8 language features and APIs (no `var`, records, switch expressions, text blocks, `List.of`, `String.isBlank`, ...).
6. **New classes** go in package `org.apache.commons.cli` under `src/main/java`, start with the same Apache License header as the existing files, have a class Javadoc, and are package-private unless they must be public.
7. **Keep the house style:** 4-space indentation; `final` on parameters and locals, as in the surrounding code; a short Javadoc on every new method.
8. **Small steps.** Compile and run the tests after every step. If a step breaks a test, undo or fix that step before moving on; don't pile changes on top of a failure.
9. **Stay in your lane.** Edit only inside your own workspace clone (`workspace/gemini/commons-cli`). Don't commit, push or switch branches; `kit.py` does that. Don't open other LLMs' folders under `runs/` or `workspace/`. Don't edit the kit or the Excel files by hand, or anything in the run folder except `process.md`; `kit.py` writes them. You **are allowed** to run `python kit.py metrics --smell B01 --llm "<your LLM name>"` after your last `finish`: it measures size, cohesion and coupling before and after with CK and fills your run's row of the Excel **Metrics** sheet.


## 5. What to send back (strict format)

Reply with exactly these two parts and nothing after them.

**Part A**, starting with the heading `## Refactoring process`, containing these sub-headings in this order:
`### 1. Understanding of the smell`, `### 2. Plan`, `### 3. Steps performed` (a table: # | What changed | Compile | Tests; write "not run" in the last two columns), `### 4. Why behaviour is preserved`, `### 5. Deviations from the plan`, `### 6. Observations (not changed)`, `### 7. Self-assessment` (smell removed? expected effect on size, cohesion and coupling).

**Part B**, starting with the heading `## Changed files`, containing one block per file you changed or created:

### FILE: src/main/java/org/apache/commons/cli/Example.java
```java
(the COMPLETE content of the file, from the license header to the last closing brace)
```

- Send complete files only. Never use "...", "// rest unchanged", "// existing code" or partial snippets.
- If your reply would be cut off, stop at the end of a file block and write `CONTINUE`; the user will ask you to continue.
- Do not include files you did not change, and never include test files.

## 6. Original source code

### FILE: src/main/java/org/apache/commons/cli/HelpFormatter.java

```java
/*
  Licensed to the Apache Software Foundation (ASF) under one or more
  contributor license agreements.  See the NOTICE file distributed with
  this work for additional information regarding copyright ownership.
  The ASF licenses this file to You under the Apache License, Version 2.0
  (the "License"); you may not use this file except in compliance with
  the License.  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
 */

package org.apache.commons.cli;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.PrintWriter;
import java.io.Serializable;
import java.io.StringReader;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.Iterator;
import java.util.List;
import java.util.Objects;
import java.util.function.Function;
import java.util.function.Supplier;

/**
 * A formatter of help messages for command line options.
 * <p>
 * Example:
 * </p>
 * <pre>
 * Options options = new Options();
 * options.addOption(OptionBuilder.withLongOpt("file").withDescription("The file to be processed").hasArg().withArgName("FILE").isRequired().create('f'));
 * options.addOption(OptionBuilder.withLongOpt("version").withDescription("Print the version of the application").create('v'));
 * options.addOption(OptionBuilder.withLongOpt("help").create('h'));
 *
 * String header = "Do something useful with an input file\n\n";
 * String footer = "\nPlease report issues at https://example.com/issues";
 *
 * HelpFormatter formatter = new HelpFormatter();
 * formatter.printHelp("myapp", header, options, footer, true);
 * </pre>
 * <p>
 * This produces the following output:
 * </p>
 * <pre>
 * usage: myapp -f &lt;FILE&gt; [-h] [-v]
 * Do something useful with an input file
 *
 *  -f,--file &lt;FILE&gt;   The file to be processed
 *  -h,--help
 *  -v,--version       Print the version of the application
 *
 * Please report issues at https://example.com/issues
 * </pre>
 */
public class HelpFormatter {

    /**
     * Builds {@link HelpFormatter}.
     *
     * @since 1.7.0
     */
    public static class Builder implements Supplier<HelpFormatter> {
        // TODO All other instance HelpFormatter instance variables.
        // Make HelpFormatter immutable for 2.0

        /**
         * A function to convert a description (not null) and a deprecated Option (not null) to help description
         */
        private static final Function<Option, String> DEFAULT_DEPRECATED_FORMAT = o -> "[Deprecated] " + getDescription(o);

        /**
         * Formatter for deprecated options.
         */
        private Function<Option, String> deprecatedFormatFunction = DEFAULT_DEPRECATED_FORMAT;

        /**
         * The output PrintWriter, defaults to wrapping {@link System#out}.
         */
        private PrintWriter printStream = createDefaultPrintWriter();

        /** The flag to determine if the since values should be dispalyed */
        private boolean showSince;

        @Override
        public HelpFormatter get() {
            return new HelpFormatter(deprecatedFormatFunction, printStream, showSince);
        }

        /**
         * Sets the output PrintWriter, defaults to wrapping {@link System#out}.
         *
         * @param printWriter the output PrintWriter, not null.
         * @return {@code this} instance.
         */
        public Builder setPrintWriter(final PrintWriter printWriter) {
            this.printStream = Objects.requireNonNull(printWriter, "printWriter");
            return this;
        }

        /**
         * Sets whether to show deprecated options.
         *
         * @param useDefaultFormat if {@code true} use the default format, otherwise clear the formatter.
         * @return {@code this} instance.
         */
        public Builder setShowDeprecated(final boolean useDefaultFormat) {
            return setShowDeprecated(useDefaultFormat ? DEFAULT_DEPRECATED_FORMAT : null);
        }

        /**
         * Sets whether to show deprecated options.
         *
         * @param deprecatedFormatFunction Specify the format for the deprecated options.
         * @return {@code this} instance.
         * @since 1.8.0
         */
        public Builder setShowDeprecated(final Function<Option, String> deprecatedFormatFunction) {
            this.deprecatedFormatFunction = deprecatedFormatFunction;
            return this;
        }

        /**
         * Sets whether to show the date the option was first added.
         * @param showSince if @{code true} the date the options was first added will be shown.
         * @return this builder.
         * @since 1.9.0
         */
        public Builder setShowSince(final boolean showSince) {
            this.showSince = showSince;
            return this;
        }
    }

    /**
     * This class implements the {@code Comparator} interface for comparing Options.
     */
    private static final class OptionComparator implements Comparator<Option>, Serializable {

        /** The serial version UID. */
        private static final long serialVersionUID = 5305467873966684014L;

        /**
         * Compares its two arguments for order. Returns a negative integer, zero, or a positive integer as the first argument
         * is less than, equal to, or greater than the second.
         *
         * @param opt1 The first Option to be compared.
         * @param opt2 The second Option to be compared.
         * @return a negative integer, zero, or a positive integer as the first argument is less than, equal to, or greater than
         *         the second.
         */
        @Override
        public int compare(final Option opt1, final Option opt2) {
            return opt1.getKey().compareToIgnoreCase(opt2.getKey());
        }
    }
    /** "Options" text for options header */
    private static final String HEADER_OPTIONS = "Options";

    /** "Since" text for options header */
    private static final String HEADER_SINCE = "Since";

    /** "Description" test for options header */
    private static final String HEADER_DESCRIPTION = "Description";

    /** Default number of characters per line */
    public static final int DEFAULT_WIDTH = 74;

    /** Default padding to the left of each line */
    public static final int DEFAULT_LEFT_PAD = 1;

    /** Number of space characters to be prefixed to each description line */
    public static final int DEFAULT_DESC_PAD = 3;

    /** The string to display at the beginning of the usage statement */
    public static final String DEFAULT_SYNTAX_PREFIX = "usage: ";

    /** Default prefix for shortOpts */
    public static final String DEFAULT_OPT_PREFIX = "-";

    /** Default prefix for long Option */
    public static final String DEFAULT_LONG_OPT_PREFIX = "--";

    /**
     * Default separator displayed between a long Option and its value
     *
     * @since 1.3
     */
    public static final String DEFAULT_LONG_OPT_SEPARATOR = " ";

    /** Default name for an argument */
    public static final String DEFAULT_ARG_NAME = "arg";

    /**
     * Creates a new builder.
     *
     * @return a new builder.
     * @since 1.7.0
     */
    public static Builder builder() {
        return new Builder();
    }

    private static PrintWriter createDefaultPrintWriter() {
        return new PrintWriter(System.out);
    }

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

    /**
     * Number of characters per line
     *
     * @deprecated Scope will be made private for next major version - use get/setWidth methods instead.
     */
    @Deprecated
    public int defaultWidth = DEFAULT_WIDTH;

    /**
     * Amount of padding to the left of each line
     *
     * @deprecated Scope will be made private for next major version - use get/setLeftPadding methods instead.
     */
    @Deprecated
    public int defaultLeftPad = DEFAULT_LEFT_PAD;

    /**
     * The number of characters of padding to be prefixed to each description line
     *
     * @deprecated Scope will be made private for next major version - use get/setDescPadding methods instead.
     */
    @Deprecated
    public int defaultDescPad = DEFAULT_DESC_PAD;

    /**
     * The string to display at the beginning of the usage statement
     *
     * @deprecated Scope will be made private for next major version - use get/setSyntaxPrefix methods instead.
     */
    @Deprecated
    public String defaultSyntaxPrefix = DEFAULT_SYNTAX_PREFIX;

    /**
     * The new line string
     *
     * @deprecated Scope will be made private for next major version - use get/setNewLine methods instead.
     */
    @Deprecated
    public String defaultNewLine = System.lineSeparator();

    /**
     * The shortOpt prefix
     *
     * @deprecated Scope will be made private for next major version - use get/setOptPrefix methods instead.
     */
    @Deprecated
    public String defaultOptPrefix = DEFAULT_OPT_PREFIX;

    /**
     * The long Opt prefix
     *
     * @deprecated Scope will be made private for next major version - use get/setLongOptPrefix methods instead.
     */
    @Deprecated
    public String defaultLongOptPrefix = DEFAULT_LONG_OPT_PREFIX;

    /**
     * The name of the argument
     *
     * @deprecated Scope will be made private for next major version - use get/setArgName methods instead.
     */
    @Deprecated
    public String defaultArgName = DEFAULT_ARG_NAME;

    /**
     * Comparator used to sort the options when they output in help text
     *
     * Defaults to case-insensitive alphabetical sorting by option key
     */
    protected Comparator<Option> optionComparator = new OptionComparator();

    /**
     * Function to format the description for a deprecated option.
     */
    private final Function<Option, String> deprecatedFormatFunction;

    /**
     * Where to print help.
     */
    private final PrintWriter printWriter;

    /** Flag to determine if since field should be displayed */
    private final boolean showSince;

    /**
     * The separator displayed between the long option and its value.
     */
    private String longOptSeparator = DEFAULT_LONG_OPT_SEPARATOR;

    /**
     * Constructs a new instance.
     */
    public HelpFormatter() {
        this(null, createDefaultPrintWriter(), false);
    }

    /**
     * Constructs a new instance.
     * @param printWriter TODO
     */
    private HelpFormatter(final Function<Option, String> deprecatedFormatFunction, final PrintWriter printWriter, final boolean showSince) {
        // TODO All other instance HelpFormatter instance variables.
        // Make HelpFormatter immutable for 2.0
        this.deprecatedFormatFunction = deprecatedFormatFunction;
        this.printWriter = printWriter;
        this.showSince = showSince;
    }

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

    /**
     * Appends the usage clause for an OptionGroup to a StringBuffer. The clause is wrapped in square brackets if the group
     * is required. The display of the options is handled by appendOption
     *
     * @param buff the StringBuilder to append to
     * @param group the group to append
     * @see #appendOption(StringBuilder,Option,boolean)
     */
    private void appendOptionGroup(final StringBuilder buff, final OptionGroup group) {
        if (!group.isRequired()) {
            buff.append("[");
        }
        final List<Option> optList = new ArrayList<>(group.getOptions());
        if (getOptionComparator() != null) {
            Collections.sort(optList, getOptionComparator());
        }
        // for each option in the OptionGroup
        for (final Iterator<Option> it = optList.iterator(); it.hasNext();) {
            // whether the option is required or not is handled at group level
            appendOption(buff, it.next(), true);

            if (it.hasNext()) {
                buff.append(" | ");
            }
        }
        if (!group.isRequired()) {
            buff.append("]");
        }
    }

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

    /**
     * Renders the specified text and return the rendered Options in a StringBuffer.
     *
     * @param <A> The Appendable implementation.
     * @param appendable The StringBuffer to place the rendered text into.
     * @param width The number of characters to display per line
     * @param nextLineTabStop The position on the next line for the first tab.
     * @param text The text to be rendered.
     * @return the StringBuffer with the rendered Options contents.
     * @throws IOException if an I/O error occurs.
     */
    <A extends Appendable> A appendWrappedText(final A appendable, final int width, final int nextLineTabStop, final String text) throws IOException {
        String render = text;
        int nextLineTabStopPos = nextLineTabStop;
        int pos = findWrapPos(render, width, 0);
        if (pos == -1) {
            appendable.append(rtrim(render));
            return appendable;
        }
        appendable.append(rtrim(render.substring(0, pos))).append(getNewLine());
        if (nextLineTabStopPos >= width) {
            // stops infinite loop happening
            nextLineTabStopPos = 1;
        }
        // all following lines must be padded with nextLineTabStop space characters
        final String padding = createPadding(nextLineTabStopPos);
        while (true) {
            render = padding + render.substring(pos).trim();
            pos = findWrapPos(render, width, 0);
            if (pos == -1) {
                appendable.append(render);
                return appendable;
            }
            if (render.length() > width && pos == nextLineTabStopPos - 1) {
                pos = width;
            }
            appendable.append(rtrim(render.substring(0, pos))).append(getNewLine());
        }
    }

    /**
     * Creates a String of padding of length {@code len}.
     *
     * @param len The length of the String of padding to create.
     *
     * @return The String of padding
     */
    protected String createPadding(final int len) {
        final char[] padding = new char[len];
        Arrays.fill(padding, ' ');
        return new String(padding);
    }

    private int determineMaxSinceLength(final Options options) {
        final int minLen = HEADER_SINCE.length();
        final int len = options.getOptions().stream().map(o -> o.getSince() == null ? minLen : o.getSince().length()).max(Integer::compareTo).orElse(minLen);
        return len < minLen ? minLen : len;
    }

    /**
     * Finds the next text wrap position after {@code startPos} for the text in {@code text} with the column width
     * {@code width}. The wrap point is the last position before startPos+width having a whitespace character (space,
     * \n, \r). If there is no whitespace character before startPos+width, it will return startPos+width.
     *
     * @param text The text being searched for the wrap position
     * @param width width of the wrapped text
     * @param startPos position from which to start the lookup whitespace character
     * @return position on which the text must be wrapped or -1 if the wrap position is at the end of the text
     */
    protected int findWrapPos(final String text, final int width, final int startPos) {
        // the line ends before the max wrap pos or a new line char found
        int pos = text.indexOf(Char.LF, startPos);
        if (pos != -1 && pos <= width) {
            return pos + 1;
        }
        pos = text.indexOf(Char.TAB, startPos);
        if (pos != -1 && pos <= width) {
            return pos + 1;
        }
        if (startPos + width >= text.length()) {
            return -1;
        }
        // look for the last whitespace character before startPos+width
        for (pos = startPos + width; pos >= startPos; --pos) {
            final char c = text.charAt(pos);
            if (c == Char.SP || c == Char.LF || c == Char.CR) {
                break;
            }
        }
        // if we found it - just return
        if (pos > startPos) {
            return pos;
        }
        // if we didn't find one, simply chop at startPos+width
        pos = startPos + width;
        return pos == text.length() ? -1 : pos;
    }

    /**
     * Gets the 'argName'.
     *
     * @return the 'argName'
     */
    public String getArgName() {
        return defaultArgName;
    }

    /**
     * Gets the 'descPadding'.
     *
     * @return the 'descPadding'
     */
    public int getDescPadding() {
        return defaultDescPad;
    }

    /**
     * Gets the 'leftPadding'.
     *
     * @return the 'leftPadding'
     */
    public int getLeftPadding() {
        return defaultLeftPad;
    }

    /**
     * Gets the 'longOptPrefix'.
     *
     * @return the 'longOptPrefix'
     */
    public String getLongOptPrefix() {
        return defaultLongOptPrefix;
    }

    /**
     * Gets the separator displayed between a long option and its value.
     *
     * @return the separator
     * @since 1.3
     */
    public String getLongOptSeparator() {
        return longOptSeparator;
    }

    /**
     * Gets the 'newLine'.
     *
     * @return the 'newLine'
     */
    public String getNewLine() {
        return defaultNewLine;
    }

    /**
     * Comparator used to sort the options when they output in help text. Defaults to case-insensitive alphabetical sorting
     * by option key.
     *
     * @return the {@link Comparator} currently in use to sort the options
     * @since 1.2
     */
    public Comparator<Option> getOptionComparator() {
        return optionComparator;
    }

    /**
     * Gets the 'optPrefix'.
     *
     * @return the 'optPrefix'
     */
    public String getOptPrefix() {
        return defaultOptPrefix;
    }

    /**
     * Gets the 'syntaxPrefix'.
     *
     * @return the 'syntaxPrefix'
     */
    public String getSyntaxPrefix() {
        return defaultSyntaxPrefix;
    }

    /**
     * Gets the 'width'.
     *
     * @return the 'width'
     */
    public int getWidth() {
        return defaultWidth;
    }

    /**
     * Prints the help for {@code options} with the specified command line syntax. This method prints help information
     * to  {@link System#out}  by default.
     *
     * @param width the number of characters to be displayed on each line
     * @param cmdLineSyntax the syntax for this application
     * @param header the banner to display at the beginning of the help
     * @param options the Options instance
     * @param footer the banner to display at the end of the help
     */
    public void printHelp(final int width, final String cmdLineSyntax, final String header, final Options options, final String footer) {
        printHelp(width, cmdLineSyntax, header, options, footer, false);
    }

    /**
     * Prints the help for {@code options} with the specified command line syntax. This method prints help information
     * to {@link System#out} by default.
     *
     * @param width the number of characters to be displayed on each line
     * @param cmdLineSyntax the syntax for this application
     * @param header the banner to display at the beginning of the help
     * @param options the Options instance
     * @param footer the banner to display at the end of the help
     * @param autoUsage whether to print an automatically generated usage statement
     */
    public void printHelp(final int width, final String cmdLineSyntax, final String header, final Options options, final String footer,
        final boolean autoUsage) {
        final PrintWriter pw = new PrintWriter(printWriter);
        printHelp(pw, width, cmdLineSyntax, header, options, getLeftPadding(), getDescPadding(), footer, autoUsage);
        pw.flush();
    }

    /**
     * Prints the help for {@code options} with the specified command line syntax.
     *
     * @param pw the writer to which the help will be written
     * @param width the number of characters to be displayed on each line
     * @param cmdLineSyntax the syntax for this application
     * @param header the banner to display at the beginning of the help
     * @param options the Options instance
     * @param leftPad the number of characters of padding to be prefixed to each line
     * @param descPad the number of characters of padding to be prefixed to each description line
     * @param footer the banner to display at the end of the help
     *
     * @throws IllegalStateException if there is no room to print a line
     */
    public void printHelp(final PrintWriter pw, final int width, final String cmdLineSyntax, final String header, final Options options, final int leftPad,
        final int descPad, final String footer) {
        printHelp(pw, width, cmdLineSyntax, header, options, leftPad, descPad, footer, false);
    }

    /**
     * Prints the help for {@code options} with the specified command line syntax.
     *
     * @param pw the writer to which the help will be written
     * @param width the number of characters to be displayed on each line
     * @param cmdLineSyntax the syntax for this application
     * @param header the banner to display at the beginning of the help
     * @param options the Options instance
     * @param leftPad the number of characters of padding to be prefixed to each line
     * @param descPad the number of characters of padding to be prefixed to each description line
     * @param footer the banner to display at the end of the help
     * @param autoUsage whether to print an automatically generated usage statement
     * @throws IllegalStateException if there is no room to print a line
     */
    public void printHelp(final PrintWriter pw, final int width, final String cmdLineSyntax, final String header, final Options options, final int leftPad,
        final int descPad, final String footer, final boolean autoUsage) {
        if (Util.isEmpty(cmdLineSyntax)) {
            throw new IllegalArgumentException("cmdLineSyntax not provided");
        }
        if (autoUsage) {
            printUsage(pw, width, cmdLineSyntax, options);
        } else {
            printUsage(pw, width, cmdLineSyntax);
        }
        if (header != null && !header.isEmpty()) {
            printWrapped(pw, width, header);
        }
        printOptions(pw, width, options, leftPad, descPad);
        if (footer != null && !footer.isEmpty()) {
            printWrapped(pw, width, footer);
        }
    }

    /**
     * Prints the help for {@code options} with the specified command line syntax. This method prints help information
     * to {@link System#out} by default.
     *
     * @param cmdLineSyntax the syntax for this application
     * @param options the Options instance
     */
    public void printHelp(final String cmdLineSyntax, final Options options) {
        printHelp(getWidth(), cmdLineSyntax, null, options, null, false);
    }

    /**
     * Prints the help for {@code options} with the specified command line syntax. This method prints help information
     * to {@link System#out} by default.
     *
     * @param cmdLineSyntax the syntax for this application
     * @param options the Options instance
     * @param autoUsage whether to print an automatically generated usage statement
     */
    public void printHelp(final String cmdLineSyntax, final Options options, final boolean autoUsage) {
        printHelp(getWidth(), cmdLineSyntax, null, options, null, autoUsage);
    }

    /**
     * Prints the help for {@code options} with the specified command line syntax. This method prints help information
     * to {@link System#out} by default.
     *
     * @param cmdLineSyntax the syntax for this application
     * @param header the banner to display at the beginning of the help
     * @param options the Options instance
     * @param footer the banner to display at the end of the help
     */
    public void printHelp(final String cmdLineSyntax, final String header, final Options options, final String footer) {
        printHelp(cmdLineSyntax, header, options, footer, false);
    }

    /**
     * Prints the help for {@code options} with the specified command line syntax. This method prints help information
     * to {@link System#out} by default.
     *
     * @param cmdLineSyntax the syntax for this application
     * @param header the banner to display at the beginning of the help
     * @param options the Options instance
     * @param footer the banner to display at the end of the help
     * @param autoUsage whether to print an automatically generated usage statement
     */
    public void printHelp(final String cmdLineSyntax, final String header, final Options options, final String footer, final boolean autoUsage) {
        printHelp(getWidth(), cmdLineSyntax, header, options, footer, autoUsage);
    }

    /**
     * Prints the help for the specified Options to the specified writer, using the specified width, left padding and
     * description padding.
     *
     * @param pw The printWriter to write the help to
     * @param width The number of characters to display per line
     * @param options The command line Options
     * @param leftPad the number of characters of padding to be prefixed to each line
     * @param descPad the number of characters of padding to be prefixed to each description line
     */
    public void printOptions(final PrintWriter pw, final int width, final Options options, final int leftPad, final int descPad) {
        try {
            pw.println(appendOptions(new StringBuilder(), width, options, leftPad, descPad));
        } catch (final IOException e) {
            // Cannot happen
            throw new UncheckedIOException(e);
        }
    }

    /**
     * Prints the cmdLineSyntax to the specified writer, using the specified width.
     *
     * @param pw The printWriter to write the help to
     * @param width The number of characters per line for the usage statement.
     * @param cmdLineSyntax The usage statement.
     */
    public void printUsage(final PrintWriter pw, final int width, final String cmdLineSyntax) {
        final int argPos = cmdLineSyntax.indexOf(' ') + 1;
        printWrapped(pw, width, getSyntaxPrefix().length() + argPos, getSyntaxPrefix() + cmdLineSyntax);
    }

    /**
     * Prints the usage statement for the specified application.
     *
     * @param pw The PrintWriter to print the usage statement
     * @param width The number of characters to display per line
     * @param app The application name
     * @param options The command line Options
     */
    public void printUsage(final PrintWriter pw, final int width, final String app, final Options options) {
        // initialize the string buffer
        final StringBuilder buff = new StringBuilder(getSyntaxPrefix()).append(app).append(Char.SP);
        // create a list for processed option groups
        final Collection<OptionGroup> processedGroups = new ArrayList<>();
        final List<Option> optList = new ArrayList<>(options.getOptions());
        if (getOptionComparator() != null) {
            Collections.sort(optList, getOptionComparator());
        }
        // iterate over the options
        for (final Iterator<Option> it = optList.iterator(); it.hasNext();) {
            // get the next Option
            final Option option = it.next();
            // check if the option is part of an OptionGroup
            final OptionGroup group = options.getOptionGroup(option);
            // if the option is part of a group
            if (group != null) {
                // and if the group has not already been processed
                if (!processedGroups.contains(group)) {
                    // add the group to the processed list
                    processedGroups.add(group);
                    // add the usage clause
                    appendOptionGroup(buff, group);
                }
                // otherwise the option was displayed in the group
                // previously so ignore it.
            }
            // if the Option is not part of an OptionGroup
            else {
                appendOption(buff, option, option.isRequired());
            }
            if (it.hasNext()) {
                buff.append(Char.SP);
            }
        }

        // call printWrapped
        printWrapped(pw, width, buff.toString().indexOf(' ') + 1, buff.toString());
    }

    /**
     * Prints the specified text to the specified PrintWriter.
     *
     * @param pw The printWriter to write the help to
     * @param width The number of characters to display per line
     * @param nextLineTabStop The position on the next line for the first tab.
     * @param text The text to be written to the PrintWriter
     */
    public void printWrapped(final PrintWriter pw, final int width, final int nextLineTabStop, final String text) {
        pw.println(renderWrappedTextBlock(new StringBuilder(text.length()), width, nextLineTabStop, text));
    }

    /**
     * Prints the specified text to the specified PrintWriter.
     *
     * @param pw The printWriter to write the help to
     * @param width The number of characters to display per line
     * @param text The text to be written to the PrintWriter
     */
    public void printWrapped(final PrintWriter pw, final int width, final String text) {
        printWrapped(pw, width, 0, text);
    }

    /**
     * Renders the specified Options and return the rendered Options in a StringBuffer.
     *
     * @param sb The StringBuffer to place the rendered Options into.
     * @param width The number of characters to display per line
     * @param options The command line Options
     * @param leftPad the number of characters of padding to be prefixed to each line
     * @param descPad the number of characters of padding to be prefixed to each description line
     *
     * @return the StringBuffer with the rendered Options contents.
     */
    protected StringBuffer renderOptions(final StringBuffer sb, final int width, final Options options, final int leftPad, final int descPad) {
        try {
            return appendOptions(sb, width, options, leftPad, descPad);
        } catch (final IOException e) {
            // Cannot happen
            throw new UncheckedIOException(e);
        }
    }

    /**
     * Renders the specified text and return the rendered Options in a StringBuffer.
     *
     * @param sb The StringBuffer to place the rendered text into.
     * @param width The number of characters to display per line
     * @param nextLineTabStop The position on the next line for the first tab.
     * @param text The text to be rendered.
     *
     * @return the StringBuffer with the rendered Options contents.
     */
    protected StringBuffer renderWrappedText(final StringBuffer sb, final int width, final int nextLineTabStop, final String text) {
        try {
            return appendWrappedText(sb, width, nextLineTabStop, text);
        } catch (final IOException e) {
            // Cannot happen.
            throw new UncheckedIOException(e);
        }
    }

    /**
     * Renders the specified text width a maximum width. This method differs from renderWrappedText by not removing leading
     * spaces after a new line.
     *
     * @param appendable The StringBuffer to place the rendered text into.
     * @param width The number of characters to display per line
     * @param nextLineTabStop The position on the next line for the first tab.
     * @param text The text to be rendered.
     */
    private <A extends Appendable> A renderWrappedTextBlock(final A appendable, final int width, final int nextLineTabStop, final String text) {
        try {
            final BufferedReader in = new BufferedReader(new StringReader(text));
            String line;
            boolean firstLine = true;
            while ((line = in.readLine()) != null) {
                if (!firstLine) {
                    appendable.append(getNewLine());
                } else {
                    firstLine = false;
                }
                appendWrappedText(appendable, width, nextLineTabStop, line);
            }
        } catch (final IOException e) { // NOPMD
            // cannot happen
        }
        return appendable;
    }

    /**
     * Removes the trailing whitespace from the specified String.
     *
     * @param s The String to remove the trailing padding from.
     * @return The String of without the trailing padding
     */
    protected String rtrim(final String s) {
        if (Util.isEmpty(s)) {
            return s;
        }
        int pos = s.length();
        while (pos > 0 && Character.isWhitespace(s.charAt(pos - 1))) {
            --pos;
        }
        return s.substring(0, pos);
    }

    /**
     * Sets the 'argName'.
     *
     * @param name the new value of 'argName'
     */
    public void setArgName(final String name) {
        this.defaultArgName = name;
    }

    /**
     * Sets the 'descPadding'.
     *
     * @param padding the new value of 'descPadding'
     */
    public void setDescPadding(final int padding) {
        this.defaultDescPad = padding;
    }

    /**
     * Sets the 'leftPadding'.
     *
     * @param padding the new value of 'leftPadding'
     */
    public void setLeftPadding(final int padding) {
        this.defaultLeftPad = padding;
    }

    /**
     * Sets the 'longOptPrefix'.
     *
     * @param prefix the new value of 'longOptPrefix'
     */
    public void setLongOptPrefix(final String prefix) {
        this.defaultLongOptPrefix = prefix;
    }

    /**
     * Sets the separator displayed between a long option and its value. Ensure that the separator specified is supported by
     * the parser used, typically ' ' or '='.
     *
     * @param longOptSeparator the separator, typically ' ' or '='.
     * @since 1.3
     */
    public void setLongOptSeparator(final String longOptSeparator) {
        this.longOptSeparator = longOptSeparator;
    }

    /**
     * Sets the 'newLine'.
     *
     * @param newline the new value of 'newLine'
     */
    public void setNewLine(final String newline) {
        this.defaultNewLine = newline;
    }

    /**
     * Sets the comparator used to sort the options when they output in help text. Passing in a null comparator will keep the
     * options in the order they were declared.
     *
     * @param comparator the {@link Comparator} to use for sorting the options
     * @since 1.2
     */
    public void setOptionComparator(final Comparator<Option> comparator) {
        this.optionComparator = comparator;
    }

    /**
     * Sets the 'optPrefix'.
     *
     * @param prefix the new value of 'optPrefix'
     */
    public void setOptPrefix(final String prefix) {
        this.defaultOptPrefix = prefix;
    }

    /**
     * Sets the 'syntaxPrefix'.
     *
     * @param prefix the new value of 'syntaxPrefix'
     */
    public void setSyntaxPrefix(final String prefix) {
        this.defaultSyntaxPrefix = prefix;
    }

    /**
     * Sets the 'width'.
     *
     * @param width the new value of 'width'
     */
    public void setWidth(final int width) {
        this.defaultWidth = width;
    }

}
```

### FILE: src/main/java/org/apache/commons/cli/OptionGroup.java

```java
/*
  Licensed to the Apache Software Foundation (ASF) under one or more
  contributor license agreements.  See the NOTICE file distributed with
  this work for additional information regarding copyright ownership.
  The ASF licenses this file to You under the Apache License, Version 2.0
  (the "License"); you may not use this file except in compliance with
  the License.  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
 */

package org.apache.commons.cli;

import java.io.Serializable;
import java.util.Collection;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * A group of mutually exclusive options.
 */
public class OptionGroup implements Serializable {

    /** The serial version UID. */
    private static final long serialVersionUID = 1L;

    /** Hold the options */
    private final Map<String, Option> optionMap = new LinkedHashMap<>();

    /** The name of the selected option */
    private String selected;

    /** Specified whether this group is required */
    private boolean required;

    /**
     * Adds the given {@code Option} to this group.
     *
     * @param option the option to add to this group
     * @return this option group with the option added
     */
    public OptionGroup addOption(final Option option) {
        // key - option name
        // value - the option
        optionMap.put(option.getKey(), option);
        return this;
    }

    /**
     * Gets the names of the options in this group as a {@code Collection}.
     *
     * @return the names of the options in this group as a {@code Collection}.
     */
    public Collection<String> getNames() {
        // the key set is the collection of names
        return optionMap.keySet();
    }

    /**
     * Gets the options in this group as a {@code Collection}.
     *
     * @return the options in this group as a {@code Collection}.
     */
    public Collection<Option> getOptions() {
        // the values are the collection of options
        return optionMap.values();
    }

    /**
     * Gets the selected option name.
     *
     * If the selected option is deprecated <em>no warning is logged</em>.
     * @return the selected option name.
     */
    public String getSelected() {
        return selected;
    }

    /**
     * Tests whether this option group is required.
     *
     * @return whether this option group is required
     */
    public boolean isRequired() {
        return required;
    }

    /**
     * Tests whether an option is selected.
     *
     *  If an option is selected and is deprecated <em>no warning is logged</em>.
     * @return whether whether an option is selected.
     * @since 1.9.0
     */
    public boolean isSelected() {
        return selected != null;
    }

    /**
     * Sets whether this group is required.
     *
     * @param required whether this group is required.
     */
    public void setRequired(final boolean required) {
        this.required = required;
    }

    /**
     * Sets the selected option of this group to {@code name}.
     *
     * If the selected option is deprecated <em>no warning is logged</em>.
     * @param option the option that is selected
     * @throws AlreadySelectedException if an option from this group has already been selected.
     */
    public void setSelected(final Option option) throws AlreadySelectedException {
        if (option == null) {
            // reset the option previously selected
            selected = null;
            return;
        }
        // if no option has already been selected or the
        // same option is being reselected then set the
        // selected member variable
        if (selected != null && !selected.equals(option.getKey())) {
            throw new AlreadySelectedException(this, option);
        }
        selected = option.getKey();
    }

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
}
```

### FILE: src/main/java/org/apache/commons/cli/Option.java

```java
/*
  Licensed to the Apache Software Foundation (ASF) under one or more
  contributor license agreements.  See the NOTICE file distributed with
  this work for additional information regarding copyright ownership.
  The ASF licenses this file to You under the Apache License, Version 2.0
  (the "License"); you may not use this file except in compliance with
  the License.  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
 */

package org.apache.commons.cli;

import static org.apache.commons.cli.Util.EMPTY_STRING_ARRAY;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * Describes a single command-line option. It maintains information regarding the short-name of the option, the long-name, if any exists, a flag indicating if
 * an argument is required for this option, and a self-documenting description of the option.
 * <p>
 * An Option is not created independently, but is created through an instance of {@link Options}. An Option is required to have at least a short or a long-name.
 * </p>
 * <p>
 * <b>Note:</b> once an {@link Option} has been added to an instance of {@link Options}, its required flag cannot be changed.
 * </p>
 *
 * @see org.apache.commons.cli.Options
 * @see org.apache.commons.cli.CommandLine
 */
public class Option implements Cloneable, Serializable {

    /**
     * Builds {@code Option} instances using descriptive methods.
     * <p>
     * Example usage:
     * </p>
     *
     * <pre>
     * Option option = Option.builder("a").required(true).longOpt("arg-name").build();
     * </pre>
     *
     * @since 1.3
     */
    public static final class Builder {

        /** The default type. */
        private static final Class<String> DEFAULT_TYPE = String.class;

        /**
         * Returns the input Class or the default type (String) if null.
         *
         * @param type the candidate Class.
         * @return the input Class or the default type (String) if null.
         */
        private static Class<?> toType(final Class<?> type) {
            return type != null ? type : DEFAULT_TYPE;
        }

        /** The number of argument values this option can have. */
        private int argCount = UNINITIALIZED;

        /** The name of the argument for this option. */
        private String argName;

        /** The converter to convert to type. **/
        private Converter<?, ?> converter;

        /** Specifies whether this option is deprecated. */
        private DeprecatedAttributes deprecated;

        /** Description of the option. */
        private String description;

        /** The long representation of the option. */
        private String longOption;

        /** The name of the option. */
        private String option;

        /** Specifies whether the argument value of this Option is optional. */
        private boolean optionalArg;

        /** Specifies whether this option is required to be present. */
        private boolean required;

        /** Specifies the version when this option was added.  May be null */
        private String since;

        /** The type of this Option. */
        private Class<?> type = DEFAULT_TYPE;

        /** The character that is the value separator. */
        private char valueSeparator;

        /**
         * Constructs a new {@code Builder} with the minimum required parameters for an {@code Option} instance.
         *
         * @param option short representation of the option.
         * @throws IllegalArgumentException if there are any non valid Option characters in {@code opt}.
         */
        private Builder(final String option) throws IllegalArgumentException {
            option(option);
        }

        /**
         * Sets the display name for the argument value.
         *
         * @param argName the display name for the argument value.
         * @return this builder, to allow method chaining.
         */
        public Builder argName(final String argName) {
            this.argName = argName;
            return this;
        }

        /**
         * Constructs an Option with the values declared by this {@link Builder}.
         *
         * @return the new {@link Option}.
         * @throws IllegalArgumentException if neither {@code opt} or {@code longOpt} has been set.
         */
        public Option build() {
            if (option == null && longOption == null) {
                throw new IllegalArgumentException("Either opt or longOpt must be specified");
            }
            return new Option(this);
        }

        /**
         * Sets the converter for the option.
         * <p>
         * Note: See {@link TypeHandler} for serialization discussion.
         * </p>
         *
         * @param converter the Converter to use.
         * @return this builder, to allow method chaining.
         * @since 1.7.0
         */
        public Builder converter(final Converter<?, ?> converter) {
            this.converter = converter;
            return this;
        }

        /**
         * Marks this Option as deprecated.
         *
         * @return this builder.
         * @since 1.7.0
         */
        public Builder deprecated() {
            return deprecated(DeprecatedAttributes.DEFAULT);
        }

        /**
         * Sets whether the Option is deprecated.
         *
         * @param deprecated specifies whether the Option is deprecated.
         * @return this builder.
         * @since 1.7.0
         */
        public Builder deprecated(final DeprecatedAttributes deprecated) {
            this.deprecated = deprecated;
            return this;
        }

        /**
         * Sets the description for this option.
         *
         * @param description the description of the option.
         * @return this builder, to allow method chaining.
         */
        public Builder desc(final String description) {
            this.description = description;
            return this;
        }

        /**
         * Tests whether the Option will require an argument.
         *
         * @return this builder, to allow method chaining.
         */
        public Builder hasArg() {
            return hasArg(true);
        }

        /**
         * Tests whether the Option has an argument or not.
         *
         * @param hasArg specifies whether the Option takes an argument or not.
         * @return this builder, to allow method chaining.
         */
        public Builder hasArg(final boolean hasArg) {
            // set to UNINITIALIZED when no arg is specified to be compatible with OptionBuilder
            argCount = hasArg ? 1 : UNINITIALIZED;
            return this;
        }

        /**
         * Tests whether the Option can have unlimited argument values.
         *
         * @return this builder.
         */
        public Builder hasArgs() {
            argCount = UNLIMITED_VALUES;
            return this;
        }

        /**
         * Sets the long name of the Option.
         *
         * @param longOption the long name of the Option
         * @return this builder.
         */
        public Builder longOpt(final String longOption) {
            this.longOption = longOption;
            return this;
        }

        /**
         * Sets the number of argument values the Option can take.
         *
         * @param argCount the number of argument values
         * @return this builder.
         */
        public Builder numberOfArgs(final int argCount) {
            this.argCount = argCount;
            return this;
        }

        /**
         * Sets the name of the Option.
         *
         * @param option the name of the Option.
         * @return this builder.
         * @throws IllegalArgumentException if there are any non valid Option characters in {@code opt}.
         * @since 1.5.0
         */
        public Builder option(final String option) throws IllegalArgumentException {
            this.option = OptionValidator.validate(option);
            return this;
        }

        /**
         * Sets whether the Option can have an optional argument.
         *
         * @param optionalArg specifies whether the Option can have an optional argument.
         * @return this builder.
         */
        public Builder optionalArg(final boolean optionalArg) {
            if (optionalArg && argCount == UNINITIALIZED) {
                argCount = 1;
            }
            this.optionalArg = optionalArg;
            return this;
        }

        /**
         * Marks this Option as required.
         *
         * @return this builder.
         */
        public Builder required() {
            return required(true);
        }

        /**
         * Sets whether the Option is required.
         *
         * @param required specifies whether the Option is required.
         * @return this builder.
         */
        public Builder required(final boolean required) {
            this.required = required;
            return this;
        }

        /** Sets the version number when this option was first defined."
         *
         * @param since the version number when this option was first defined.
         * @return this builder.
         */
        public Builder since(final String since) {
            this.since = since;
            return this;
        }

        /**
         * Sets the type of the Option.
         *
         * @param type the type of the Option.
         * @return this builder.
         */
        public Builder type(final Class<?> type) {
            this.type = toType(type);
            return this;
        }

        /**
         * The Option will use '=' as a means to separate argument value.
         *
         * @return this builder.
         */
        public Builder valueSeparator() {
            return valueSeparator(Char.EQUAL);
        }

        /**
         * The Option will use {@code sep} as a means to separate argument values.
         * <p>
         * <b>Example:</b>
         * </p>
         *
         * <pre>
         * Option opt = Option.builder("D").hasArgs().valueSeparator('=').build();
         * Options options = new Options();
         * options.addOption(opt);
         * String[] args = { "-Dkey=value" };
         * CommandLineParser parser = new DefaultParser();
         * CommandLine line = parser.parse(options, args);
         * String propertyName = line.getOptionValues("D")[0]; // will be "key"
         * String propertyValue = line.getOptionValues("D")[1]; // will be "value"
         * </pre>
         *
         * @param valueSeparator The value separator.
         * @return this builder.
         */
        public Builder valueSeparator(final char valueSeparator) {
            this.valueSeparator = valueSeparator;
            return this;
        }

    }

    /** Empty array. */
    static final Option[] EMPTY_ARRAY = {};

    /** The serial version UID. */
    private static final long serialVersionUID = 1L;

    /** Specifies the number of argument values has not been specified. */
    public static final int UNINITIALIZED = -1;

    /** Specifies the number of argument values is infinite. */
    public static final int UNLIMITED_VALUES = -2;

    /**
     * Returns a {@link Builder} to create an {@link Option} using descriptive methods.
     *
     * @return a new {@link Builder} instance.
     * @since 1.3
     */
    public static Builder builder() {
        return builder(null);
    }

    /**
     * Returns a {@link Builder} to create an {@link Option} using descriptive methods.
     *
     * @param option short representation of the option.
     * @return a new {@link Builder} instance.
     * @throws IllegalArgumentException if there are any non valid Option characters in {@code opt}.
     * @since 1.3
     */
    public static Builder builder(final String option) {
        return new Builder(option);
    }

    /** The number of argument values this option can have. */
    private int argCount = UNINITIALIZED;

    /** The name of the argument for this option. */
    private String argName;

    /** The explicit converter for this option. May be null. */
    private transient Converter<?, ?> converter;

    /**
     * Specifies whether this option is deprecated, may be null.
     * <p>
     * If you want to serialize this field, use a serialization proxy.
     * </p>
     */
    private final transient DeprecatedAttributes deprecated;

    /** Description of the option. */
    private String description;

    /** The long representation of the option. */
    private String longOption;

    /** The name of the option. */
    private final String option;

    /** Specifies whether the argument value of this Option is optional. */
    private boolean optionalArg;

    /** Specifies whether this option is required to be present. */
    private boolean required;

    /** Specifies the version when this option was added.  May be null */
    private String since;

    /** The type of this Option. */
    private Class<?> type = String.class;

    /** The list of argument values. **/
    private List<String> values = new ArrayList<>();

    /** The character that is the value separator. */
    private char valueSeparator;

    /**
     * Private constructor used by the nested Builder class.
     *
     * @param builder builder used to create this option.
     */
    private Option(final Builder builder) {
        this.argName = builder.argName;
        this.description = builder.description;
        this.longOption = builder.longOption;
        this.argCount = builder.argCount;
        this.option = builder.option;
        this.optionalArg = builder.optionalArg;
        this.deprecated = builder.deprecated;
        this.required = builder.required;
        this.since = builder.since;
        this.type = builder.type;
        this.valueSeparator = builder.valueSeparator;
        this.converter = builder.converter;
    }

    /**
     * Creates an Option using the specified parameters.
     *
     * @param option      short representation of the option.
     * @param hasArg      specifies whether the Option takes an argument or not.
     * @param description describes the function of the option.
     *
     * @throws IllegalArgumentException if there are any non valid Option characters in {@code opt}.
     */
    public Option(final String option, final boolean hasArg, final String description) throws IllegalArgumentException {
        this(option, null, hasArg, description);
    }

    /**
     * Creates an Option using the specified parameters. The option does not take an argument.
     *
     * @param option      short representation of the option.
     * @param description describes the function of the option.
     *
     * @throws IllegalArgumentException if there are any non valid Option characters in {@code opt}.
     */
    public Option(final String option, final String description) throws IllegalArgumentException {
        this(option, null, false, description);
    }

    /**
     * Creates an Option using the specified parameters.
     *
     * @param option      short representation of the option.
     * @param longOption  the long representation of the option.
     * @param hasArg      specifies whether the Option takes an argument or not.
     * @param description describes the function of the option.
     *
     * @throws IllegalArgumentException if there are any non valid Option characters in {@code opt}.
     */
    public Option(final String option, final String longOption, final boolean hasArg, final String description) throws IllegalArgumentException {
        // ensure that the option is valid
        this.deprecated = null;
        this.option = OptionValidator.validate(option);
        this.longOption = longOption;
        // if hasArg is set then the number of arguments is 1
        if (hasArg) {
            this.argCount = 1;
        }
        this.description = description;
    }

    /**
     * Tests whether the option can accept more arguments.
     *
     * @return false if the maximum number of arguments is reached.
     * @since 1.3
     */
    boolean acceptsArg() {
        return (hasArg() || hasArgs() || hasOptionalArg()) && (argCount <= 0 || values.size() < argCount);
    }

    /**
     * Adds the value to this Option. If the number of arguments is greater than zero and there is enough space in the list then add the value. Otherwise, throw
     * a runtime exception.
     *
     * @param value The value to be added to this Option.
     */
    private void add(final String value) {
        if (!acceptsArg()) {
            throw new IllegalArgumentException("Cannot add value, list full.");
        }
        // store value
        values.add(value);
    }

    /**
     * This method is not intended to be used. It was a piece of internal API that was made public in 1.0. It currently throws an UnsupportedOperationException.
     *
     * @param value the value to add.
     * @return always throws an {@link UnsupportedOperationException}.
     * @throws UnsupportedOperationException always.
     * @deprecated Unused.
     */
    @Deprecated
    public boolean addValue(final String value) {
        throw new UnsupportedOperationException(
                "The addValue method is not intended for client use. Subclasses should use the processValue method instead.");
    }

    /**
     * Clears the Option values. After a parse is complete, these are left with data in them and they need clearing if another parse is done.
     *
     * See: <a href="https://issues.apache.org/jira/browse/CLI-71">CLI-71</a>
     */
    void clearValues() {
        values.clear();
    }

    /**
     * A rather odd clone method - due to incorrect code in 1.0 it is public and in 1.1 rather than throwing a CloneNotSupportedException it throws a
     * RuntimeException so as to maintain backwards compatible at the API level.
     *
     * After calling this method, it is very likely you will want to call clearValues().
     *
     * @return a clone of this Option instance.
     * @throws RuntimeException if a {@link CloneNotSupportedException} has been thrown by {@code super.clone()}.
     */
    @Override
    public Object clone() {
        try {
            final Option option = (Option) super.clone();
            option.values = new ArrayList<>(values);
            return option;
        } catch (final CloneNotSupportedException e) {
            throw new UnsupportedOperationException(e.getMessage(), e);
        }
    }

    @Override
    public boolean equals(final Object obj) {
        if (this == obj) {
            return true;
        }
        if (!(obj instanceof Option)) {
            return false;
        }
        final Option other = (Option) obj;
        return Objects.equals(longOption, other.longOption) && Objects.equals(option, other.option);
    }

    /**
     * Gets the display name for the argument value.
     *
     * @return the display name for the argument value.
     */
    public String getArgName() {
        return argName;
    }

    /**
     * Gets the number of argument values this Option can take.
     *
     * <p>
     * A value equal to the constant {@link #UNINITIALIZED} (= -1) indicates the number of arguments has not been specified. A value equal to the constant
     * {@link #UNLIMITED_VALUES} (= -2) indicates that this options takes an unlimited amount of values.
     * </p>
     *
     * @return num the number of argument values.
     * @see #UNINITIALIZED
     * @see #UNLIMITED_VALUES
     */
    public int getArgs() {
        return argCount;
    }

    /**
     * Gets the value to type converter.
     *
     * @return the value to type converter.
     * @since 1.7.0
     */
    public Converter<?, ?> getConverter() {
        return converter == null ? TypeHandler.getDefault().getConverter(type) : converter;
    }

    /**
     * Gets deprecated attributes if any.
     *
     * @return boolean deprecated attributes or null.
     * @since 1.7.0
     */
    public DeprecatedAttributes getDeprecated() {
        return deprecated;
    }

    /**
     * Gets the self-documenting description of this Option.
     *
     * @return The string description of this option.
     */
    public String getDescription() {
        return description;
    }

    /**
     * Gets the id of this Option. This is only set when the Option shortOpt is a single character. This is used for switch statements.
     *
     * @return the id of this Option.
     */
    public int getId() {
        return getKey().charAt(0);
    }

    /**
     * Gets the 'unique' Option identifier. This is the option value if set or the long value if the options value is not set.
     *
     * @return the 'unique' Option identifier.
     * @since 1.7.0
     */
    public String getKey() {
        // if 'opt' is null, then it is a 'long' option
        return option == null ? longOption : option;
    }

    /**
     * Gets the long name of this Option.
     *
     * @return Long name of this option, or null, if there is no long name.
     */
    public String getLongOpt() {
        return longOption;
    }

    /**
     * Gets the name of this Option.
     *
     * It is this String which can be used with {@link CommandLine#hasOption(String opt)} and {@link CommandLine#getOptionValue(String opt)} to check for
     * existence and argument.
     *
     * @return The name of this option.
     */
    public String getOpt() {
        return option;
    }

    /**
     * Gets the version when this option was added.
     * @return the version when this option was added, or {@code null} if not set.
     */
    public String getSince() {
        return since;
    }


    /**
     * Gets the type of this Option.
     *
     * @return The type of this option.
     */
    public Object getType() {
        return type;
    }

    /**
     * Gets the specified value of this Option or {@code null} if there is no value.
     *
     * @return the value/first value of this Option or {@code null} if there is no value.
     */
    public String getValue() {
        return hasNoValues() ? null : values.get(0);
    }

    /**
     * Gets the specified value of this Option or {@code null} if there is no value.
     *
     * @param index The index of the value to be returned.
     *
     * @return the specified value of this Option or {@code null} if there is no value.
     *
     * @throws IndexOutOfBoundsException if index is less than 1 or greater than the number of the values for this Option.
     */
    public String getValue(final int index) throws IndexOutOfBoundsException {
        return hasNoValues() ? null : values.get(index);
    }

    /**
     * Gets the value/first value of this Option or the {@code defaultValue} if there is no value.
     *
     * @param defaultValue The value to be returned if there is no value.
     *
     * @return the value/first value of this Option or the {@code defaultValue} if there are no values.
     */
    public String getValue(final String defaultValue) {
        final String value = getValue();
        return value != null ? value : defaultValue;
    }

    /**
     * Gets the values of this Option as a String array or null if there are no values.
     *
     * @return the values of this Option as a String array or null if there are no values.
     */
    public String[] getValues() {
        return hasNoValues() ? null : values.toArray(EMPTY_STRING_ARRAY);
    }

    /**
     * Gets the value separator character.
     *
     * @return the value separator character.
     */
    public char getValueSeparator() {
        return valueSeparator;
    }

    /**
     * Gets the values of this Option as a List or null if there are no values.
     *
     * @return the values of this Option as a List or null if there are no values.
     */
    public List<String> getValuesList() {
        return values;
    }

    /**
     * Tests whether this Option requires an argument.
     *
     * @return boolean flag indicating if an argument is required.
     */
    public boolean hasArg() {
        return argCount > 0 || argCount == UNLIMITED_VALUES;
    }

    /**
     * Tests whether the display name for the argument value has been set.
     *
     * @return if the display name for the argument value has been set.
     */
    public boolean hasArgName() {
        return argName != null && !argName.isEmpty();
    }

    /**
     * Tests whether this Option can take many values.
     *
     * @return boolean flag indicating if multiple values are allowed.
     */
    public boolean hasArgs() {
        return argCount > 1 || argCount == UNLIMITED_VALUES;
    }

    @Override
    public int hashCode() {
        return Objects.hash(longOption, option);
    }

    /**
     * Tests whether this Option has a long name.
     *
     * @return boolean flag indicating existence of a long name.
     */
    public boolean hasLongOpt() {
        return longOption != null;
    }

    /**
     * Tests whether this Option has any values.
     *
     * @return whether this Option has any values.
     */
    private boolean hasNoValues() {
        return values.isEmpty();
    }

    /**
     * Tests whether this Option can have an optional argument.
     *
     * @return whether this Option can have an optional argument.
     */
    public boolean hasOptionalArg() {
        return optionalArg;
    }

    /**
     * Tests whether this Option has specified a value separator.
     *
     * @return whether this Option has specified a value separator.
     * @since 1.1
     */
    public boolean hasValueSeparator() {
        return valueSeparator > 0;
    }

    /**
     * Tests whether this Option is deprecated.
     *
     * @return boolean flag indicating whether this Option is deprecated.
     * @since 1.7.0
     */
    public boolean isDeprecated() {
        return deprecated != null;
    }

    /**
     * Tests whether this Option is required.
     *
     * @return boolean flag indicating whether this Option is required.
     */
    public boolean isRequired() {
        return required;
    }

    /**
     * Processes the value. If this Option has a value separator the value will have to be parsed into individual tokens. When n-1 tokens have been processed
     * and there are more value separators in the value, parsing is ceased and the remaining characters are added as a single token.
     *
     * @param value The String to be processed.
     */
    void processValue(final String value) {
        if (argCount == UNINITIALIZED) {
            throw new IllegalArgumentException("NO_ARGS_ALLOWED");
        }
        String add = value;
        // this Option has a separator character
        if (hasValueSeparator()) {
            // get the separator character
            final char sep = getValueSeparator();
            // store the index for the value separator
            int index = add.indexOf(sep);
            // while there are more value separators
            while (index != -1) {
                // next value to be added
                if (values.size() == argCount - 1) {
                    break;
                }
                // store
                add(add.substring(0, index));
                // parse
                add = add.substring(index + 1);
                // get new index
                index = add.indexOf(sep);
            }
        }
        // store the actual value or the last value that has been parsed
        add(add);
    }

    /**
     * Tests whether the option requires more arguments to be valid.
     *
     * @return false if the option doesn't require more arguments.
     */
    boolean requiresArg() {
        if (optionalArg) {
            return false;
        }
        if (argCount == UNLIMITED_VALUES) {
            return values.isEmpty();
        }
        return acceptsArg();
    }

    /**
     * Sets the display name for the argument value.
     *
     * @param argName the display name for the argument value.
     */
    public void setArgName(final String argName) {
        this.argName = argName;
    }

    /**
     * Sets the number of argument values this Option can take.
     *
     * @param num the number of argument values.
     */
    public void setArgs(final int num) {
        this.argCount = num;
    }

    /**
     * Sets the value to type converter.
     *
     * @param converter The converter to convert the string value to the type.
     * @since 1.7.0
     */
    public void setConverter(final Converter<?, ?> converter) {
        this.converter = converter;
    }

    /**
     * Sets the self-documenting description of this Option.
     *
     * @param description The description of this option.
     * @since 1.1
     */
    public void setDescription(final String description) {
        this.description = description;
    }

    /**
     * Sets the long name of this Option.
     *
     * @param longOpt the long name of this Option.
     */
    public void setLongOpt(final String longOpt) {
        this.longOption = longOpt;
    }

    /**
     * Sets whether this Option can have an optional argument.
     *
     * @param optionalArg specifies whether the Option can have an optional argument.
     */
    public void setOptionalArg(final boolean optionalArg) {
        this.optionalArg = optionalArg;
    }

    /**
     * Sets whether this Option is mandatory.
     *
     * @param required specifies whether this Option is mandatory.
     */
    public void setRequired(final boolean required) {
        this.required = required;
    }

    /**
     * Sets the type of this Option.
     *
     * @param type the type of this Option.
     * @since 1.3
     */
    public void setType(final Class<?> type) {
        this.type = Builder.toType(type);
    }

    /**
     * Sets the type of this Option.
     * <p>
     * <b>Note:</b> this method is kept for binary compatibility and the input type is supposed to be a {@link Class} object.
     * </p>
     *
     * @param type the type of this Option.
     * @deprecated since 1.3, use {@link #setType(Class)} instead.
     */
    @Deprecated
    public void setType(final Object type) {
        setType((Class<?>) type);
    }

    /**
     * Sets the value separator. For example if the argument value was a Java property, the value separator would be '='.
     *
     * @param valueSeparator The value separator.
     */
    public void setValueSeparator(final char valueSeparator) {
        this.valueSeparator = valueSeparator;
    }

    String toDeprecatedString() {
        if (!isDeprecated()) {
            return "";
        }
        // @formatter:off
        final StringBuilder buf = new StringBuilder()
                .append("Option '")
                .append(option)
                .append(Char.APOS);
        // @formatter:on
        if (longOption != null) {
            buf.append(Char.APOS).append(longOption).append(Char.APOS);
        }
        buf.append(": ").append(deprecated);
        return buf.toString();
    }

    /**
     * Creates a String suitable for debugging.
     *
     * @return a String suitable for debugging.
     */
    @Override
    public String toString() {
        final StringBuilder buf = new StringBuilder().append("[ ");
        buf.append("Option ");
        buf.append(option);
        if (longOption != null) {
            buf.append(Char.SP).append(longOption);
        }
        if (isDeprecated()) {
            buf.append(Char.SP);
            buf.append(deprecated.toString());
        }
        if (hasArgs()) {
            buf.append("[ARG...]");
        } else if (hasArg()) {
            buf.append(" [ARG]");
        }
        // @formatter:off
        return buf.append(" :: ")
            .append(description)
            .append(" :: ")
            .append(type)
            .append(" ]")
            .toString();
        // @formatter:on
    }
}
```

