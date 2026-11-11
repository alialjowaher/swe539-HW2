# Refactoring task - smell B02 (Shotgun Surgery) in Apache Commons CLI 1.9.0

You are a careful Java engineer doing **one behaviour-preserving refactoring** (Fowler, *Refactoring*, 2nd ed.) on Apache Commons CLI 1.9.0 (tag `rel/commons-cli-1.9.0`). This is part of a controlled experiment: several LLMs get exactly this task, and the results are judged by the project's original test suite, a public-API check and code metrics. You cannot run code here. The user will apply your files, compile them and run the original tests.

## 1. The smell

| Field | Value |
|---|---|
| ID | B02 |
| Smell type | Between classes |
| Code smell | Shotgun Surgery |
| Class(es) | Options, DefaultParser, Parser, MissingOptionException |
| Method / member | Options.requiredOpts / addOption / addOptionGroup / getRequiredOptions; DefaultParser.expectedOpts / updateRequiredOptions / checkRequiredOptions; Parser.requiredOptions / updateRequiredOptions / checkRequiredOptions; MissingOptionException |
| Lines (1.9.0) | Options 52–54, 72–77, 138–140, 273–275; DefaultParser 179, 278–283, 708, 760–775; Parser 41, 48–53, 306, 314–329; MissingOptionException 35–83 |
| Priority |  |

**Evidence.** Tracking of required options and groups is spread over 4 classes. Options keeps them in a List<Object> that mixes String keys and OptionGroup objects (its own comment: "TODO this seems wrong"). Both parsers copy it into raw List fields, and each has its own near-identical updateRequiredOptions and checkRequiredOptions (Type III clones). MissingOptionException takes a raw List and builds its message from each element's toString(). Changing how a required option is identified or reported means editing Options, DefaultParser, Parser and MissingOptionException together. The same two parsers also duplicate properties handling (Parser.processProperties 264–297 vs DefaultParser.handleProperties 434–463).


## 2. The refactoring to apply

**Technique:** Extract Class + Move Method + Move Field

_Source: review sheet suggestion (column 'Suggested refactoring')._

**How (outline):** Create a package-private class (e.g. RequiredOptions) that owns the 'still expected' list, with markSeen(Option, OptionGroup) and checkAllPresent() (throws MissingOptionException). Move the updateRequiredOptions / checkRequiredOptions bodies from both parsers into it, and move the expectedOpts / requiredOptions state there. Keep the protected members as delegates, and keep Options.getRequiredOptions() and MissingOptionException.getMissingOptions() returning the same contents.

**Risks to watch:** Medium. Protected members (DefaultParser.expectedOpts, checkRequiredOptions; Parser.getRequiredOptions) are subclass API. Tests assert exact messages such as "Missing required options: b, c" (AbstractParserTestCase 398, OptionsTest 276), so element order must be preserved.

**Expected effect on metrics:** Size: duplicated logic removed from 2 parsers. Cohesion: parsers lose a side concern (LCOM drops). Coupling: parsers depend on one tracker instead of OptionGroup + MissingOptionException + Options internals (parser CBO may drop by 1–2), but the system gains one class.


Apply **this** technique and nothing else. If you believe it cannot be applied without breaking a rule below, say so in section 5 of your process notes and return no files.

## 3. Where the code is

- `src/main/java/org/apache/commons/cli/Options.java` > `Options#requiredOpts` (lines 51-54)
- `src/main/java/org/apache/commons/cli/Options.java` > `Options.addOption(Option)` (lines 59-80)
- `src/main/java/org/apache/commons/cli/Options.java` > `Options.addOptionGroup(OptionGroup)` (lines 131-150)
- `src/main/java/org/apache/commons/cli/Options.java` > `Options.getRequiredOptions()` (lines 268-275)
- `src/main/java/org/apache/commons/cli/DefaultParser.java` > `DefaultParser#expectedOpts` (lines 178-179)
- `src/main/java/org/apache/commons/cli/DefaultParser.java` > `DefaultParser.checkRequiredOptions()` (lines 273-283)
- `src/main/java/org/apache/commons/cli/DefaultParser.java` > `DefaultParser.parse(Options,String[],Properties,boolean)` (lines 689-725)
- `src/main/java/org/apache/commons/cli/DefaultParser.java` > `DefaultParser.updateRequiredOptions(Option)` (lines 755-775)
- `src/main/java/org/apache/commons/cli/Parser.java` > `Parser#requiredOptions` (lines 40-41)
- `src/main/java/org/apache/commons/cli/Parser.java` > `Parser.checkRequiredOptions()` (lines 43-53)
- `src/main/java/org/apache/commons/cli/Parser.java` > `Parser.getRequiredOptions()` (lines 75-82)
- `src/main/java/org/apache/commons/cli/Parser.java` > `Parser.setOptions(Options)` (lines 299-307)
- `src/main/java/org/apache/commons/cli/Parser.java` > `Parser.updateRequiredOptions(Option)` (lines 309-329)
- `src/main/java/org/apache/commons/cli/MissingOptionException.java` - whole file (lines 1-85)

The full original source of these files is in section 6. Other files in the package: AlreadySelectedException.java, AmbiguousOptionException.java, BasicParser.java, Char.java, CommandLine.java, CommandLineParser.java, Converter.java, DefaultParser.java, DeprecatedAttributes.java, GnuParser.java, HelpFormatter.java, MissingArgumentException.java, MissingOptionException.java, Option.java, OptionBuilder.java, OptionGroup.java, OptionValidator.java, Options.java, ParseException.java, Parser.java, PatternOptionBuilder.java, PosixParser.java, TypeHandler.java, UnrecognizedOptionException.java, Util.java, package-info.java. If you need one of them, ask for it by name and stop.

## 4. Rules (non-negotiable)

1. **One smell, one technique.** Change only what is needed to remove smell B02 with the technique given in "The refactoring to apply". No other refactorings, renames, reformatting, comment edits or improvements anywhere else.
2. **Behaviour must not change.** Same return values, same printed text (including spaces, line breaks and order), same exceptions and messages, same side effects. If the existing code looks wrong, keep its behaviour and note it under "Observations" in the process notes. Fixing bugs is out of scope.
3. **The original tests are the judge, so don't touch them.** Do not modify, add, delete, skip or disable anything under `src/test/`.
4. **Keep the public and protected API.** Do not remove, rename or change the signature, visibility or modifiers of any public or protected class, constructor, method or field. If the technique moves or renames one, keep the old one and make it delegate to the new one. New members should be `private` or package-private unless the technique needs otherwise.
5. **Java 8, no new dependencies.** Do not edit `pom.xml` or any build file. Use only Java 8 language features and APIs (no `var`, records, switch expressions, text blocks, `List.of`, `String.isBlank`, ...).
6. **New classes** go in package `org.apache.commons.cli` under `src/main/java`, start with the same Apache License header as the existing files, have a class Javadoc, and are package-private unless they must be public.
7. **Keep the house style:** 4-space indentation; `final` on parameters and locals, as in the surrounding code; a short Javadoc on every new method.
8. **Small steps.** Compile and run the tests after every step. If a step breaks a test, undo or fix that step before moving on; don't pile changes on top of a failure.
9. **Stay in your lane.** Edit only inside your own workspace clone (`workspace/copilot/commons-cli`). Don't commit, push or switch branches; `kit.py` does that. Don't open other LLMs' folders under `runs/` or `workspace/`. Don't edit the kit or the Excel files by hand, or anything in the run folder except `process.md`; `kit.py` writes them. You **are allowed** to run `python kit.py metrics --smell B02 --llm "<your LLM name>"` after your last `finish`: it measures size, cohesion and coupling before and after with CK and fills your run's row of the Excel **Metrics** sheet.


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

### FILE: src/main/java/org/apache/commons/cli/Options.java

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
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Main entry-point into the library.
 * <p>
 * Options represents a collection of {@link Option} objects, which describe the possible options for a command-line.
 * </p>
 * <p>
 * It may flexibly parse long and short options, with or without values. Additionally, it may parse only a portion of a
 * commandline, allowing for flexible multi-stage parsing.
 * </p>
 *
 * @see org.apache.commons.cli.CommandLine
 */
public class Options implements Serializable {
    /** The serial version UID. */
    private static final long serialVersionUID = 1L;

    /** A map of the options with the character key */
    private final Map<String, Option> shortOpts = new LinkedHashMap<>();

    /** A map of the options with the long key */
    private final Map<String, Option> longOpts = new LinkedHashMap<>();

    /** A map of the required options */
    // N.B. This can contain either a String (addOption) or an OptionGroup (addOptionGroup)
    // TODO this seems wrong
    private final List<Object> requiredOpts = new ArrayList<>();

    /** A map of the option groups */
    private final Map<String, OptionGroup> optionGroups = new LinkedHashMap<>();

    /**
     * Adds an option instance
     *
     * @param opt the option that is to be added
     * @return the resulting Options instance
     */
    public Options addOption(final Option opt) {
        final String key = opt.getKey();
        // add it to the long option list
        if (opt.hasLongOpt()) {
            longOpts.put(opt.getLongOpt(), opt);
        }
        // if the option is required add it to the required list
        if (opt.isRequired()) {
            if (requiredOpts.contains(key)) {
                requiredOpts.remove(requiredOpts.indexOf(key));
            }
            requiredOpts.add(key);
        }
        shortOpts.put(key, opt);
        return this;
    }

    /**
     * Adds an option that only contains a short-name.
     * <p>
     * It may be specified as requiring an argument.
     * </p>
     *
     * @param opt Short single-character name of the option.
     * @param hasArg flag signalling if an argument is required after this option
     * @param description Self-documenting description
     * @return the resulting Options instance
     */
    public Options addOption(final String opt, final boolean hasArg, final String description) {
        addOption(opt, null, hasArg, description);
        return this;
    }

    /**
     * Adds an option that only contains a short name.
     * <p>
     * The option does not take an argument.
     * </p>
     *
     * @param opt Short single-character name of the option.
     * @param description Self-documenting description
     * @return the resulting Options instance
     * @since 1.3
     */
    public Options addOption(final String opt, final String description) {
        addOption(opt, null, false, description);
        return this;
    }

    /**
     * Adds an option that contains a short-name and a long-name.
     * <p>
     * It may be specified as requiring an argument.
     * </p>
     *
     * @param opt Short single-character name of the option.
     * @param longOpt Long multi-character name of the option.
     * @param hasArg flag signalling if an argument is required after this option
     * @param description Self-documenting description
     * @return the resulting Options instance
     */
    public Options addOption(final String opt, final String longOpt, final boolean hasArg, final String description) {
        addOption(new Option(opt, longOpt, hasArg, description));
        return this;
    }

    /**
     * Adds the specified option group.
     *
     * @param group the OptionGroup that is to be added
     * @return the resulting Options instance
     */
    public Options addOptionGroup(final OptionGroup group) {
        if (group.isRequired()) {
            requiredOpts.add(group);
        }
        for (final Option option : group.getOptions()) {
            // an Option cannot be required if it is in an
            // OptionGroup, either the group is required or
            // nothing is required
            option.setRequired(false);
            addOption(option);
            optionGroups.put(option.getKey(), group);
        }
        return this;
    }

    /**
     * Adds options to this option.  If any Option in {@code options} already exists
     * in this Options an IllegalArgumentException is thrown
     *
     * @param options the options to add.
     * @return The resulting Options instance.
     * @since 1.7.0
     */
    public Options addOptions(final Options options) {
        for (final Option opt : options.getOptions()) {
            if (hasOption(opt.getKey())) {
                throw new IllegalArgumentException("Duplicate key: " + opt.getKey());
            }
            addOption(opt);
        }
        options.getOptionGroups().forEach(this::addOptionGroup);
        return this;
    }

    /**
     * Adds an option that contains a short-name and a long-name.
     * <p>
     * The added option is set as required. It may be specified as requiring an argument. This method is a shortcut for:
     * </p>
     * <pre>
     * <code>
     * Options option = new Option(opt, longOpt, hasArg, description);
     * option.setRequired(true);
     * options.add(option);
     * </code>
     * </pre>
     *
     * @param opt Short single-character name of the option.
     * @param longOpt Long multi-character name of the option.
     * @param hasArg flag signalling if an argument is required after this option
     * @param description Self-documenting description
     * @return the resulting Options instance
     * @since 1.4
     */
    public Options addRequiredOption(final String opt, final String longOpt, final boolean hasArg, final String description) {
        final Option option = new Option(opt, longOpt, hasArg, description);
        option.setRequired(true);
        addOption(option);
        return this;
    }

    /**
     * Gets the options with a long name starting with the name specified.
     *
     * @param opt the partial name of the option
     * @return the options matching the partial name specified, or an empty list if none matches
     * @since 1.3
     */
    public List<String> getMatchingOptions(final String opt) {
        final String clean = Util.stripLeadingHyphens(opt);
        final List<String> matchingOpts = new ArrayList<>();
        // for a perfect match return the single option only
        if (longOpts.containsKey(clean)) {
            return Collections.singletonList(clean);
        }
        for (final String longOpt : longOpts.keySet()) {
            if (longOpt.startsWith(clean)) {
                matchingOpts.add(longOpt);
            }
        }
        return matchingOpts;
    }

    /**
     * Gets the {@link Option} matching the long or short name specified.
     * <p>
     * The leading hyphens in the name are ignored (up to 2).
     * </p>
     *
     * @param opt short or long name of the {@link Option}
     * @return the option represented by opt
     */
    public Option getOption(final String opt) {
        final String clean = Util.stripLeadingHyphens(opt);
        final Option option = shortOpts.get(clean);
        return option != null ? option : longOpts.get(clean);
    }

    /**
     * Gets the OptionGroup the {@code opt} belongs to.
     *
     * @param opt the option whose OptionGroup is being queried.
     * @return the OptionGroup if {@code opt} is part of an OptionGroup, otherwise return null
     */
    public OptionGroup getOptionGroup(final Option opt) {
        return optionGroups.get(opt.getKey());
    }

    /**
     * Gets the OptionGroups that are members of this Options instance.
     *
     * @return a Collection of OptionGroup instances.
     */
    Collection<OptionGroup> getOptionGroups() {
        /* The optionGroups map will have duplicates in the values() results.  We
         * use the HashSet to filter out duplicates and return a collection of
         * OpitonGroup.  The decision to return a Collection rather than a set
         * was probably to keep symmetry with the getOptions() method.
         */
        return new HashSet<>(optionGroups.values());
    }

    /**
     * Gets a read-only list of options in this set
     *
     * @return read-only Collection of {@link Option} objects in this descriptor
     */
    public Collection<Option> getOptions() {
        return Collections.unmodifiableCollection(helpOptions());
    }

    /**
     * Gets the required options.
     *
     * @return read-only List of required options
     */
    public List<?> getRequiredOptions() {
        return Collections.unmodifiableList(requiredOpts);
    }

    /**
     * Tests whether the named {@link Option} is a member of this {@link Options}.
     *
     * @param opt long name of the {@link Option}
     * @return true if the named {@link Option} is a member of this {@link Options}
     * @since 1.3
     */
    public boolean hasLongOption(final String opt) {
        return longOpts.containsKey(Util.stripLeadingHyphens(opt));
    }

    /**
     * Tests whether the named {@link Option} is a member of this {@link Options}.
     *
     * @param opt short or long name of the {@link Option}
     * @return true if the named {@link Option} is a member of this {@link Options}
     */
    public boolean hasOption(final String opt) {
        final String clean = Util.stripLeadingHyphens(opt);
        return shortOpts.containsKey(clean) || longOpts.containsKey(clean);
    }

    /**
     * Tests whether the named {@link Option} is a member of this {@link Options}.
     *
     * @param opt short name of the {@link Option}
     * @return true if the named {@link Option} is a member of this {@link Options}
     * @since 1.3
     */
    public boolean hasShortOption(final String opt) {
        final String clean = Util.stripLeadingHyphens(opt);
        return shortOpts.containsKey(clean);
    }

    /**
     * Returns the Options for use by the HelpFormatter.
     *
     * @return the List of Options
     */
    List<Option> helpOptions() {
        return new ArrayList<>(shortOpts.values());
    }

    /**
     * Dump state, suitable for debugging.
     *
     * @return Stringified form of this object
     */
    @Override
    public String toString() {
        final StringBuilder buf = new StringBuilder();
        buf.append("[ Options: [ short ");
        buf.append(shortOpts.toString());
        buf.append(" ] [ long ");
        buf.append(longOpts);
        buf.append(" ]");
        return buf.toString();
    }
}
```

### FILE: src/main/java/org/apache/commons/cli/DefaultParser.java

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

import java.util.ArrayList;
import java.util.Enumeration;
import java.util.List;
import java.util.Properties;
import java.util.function.Consumer;

/**
 * Default parser.
 *
 * @since 1.3
 */
public class DefaultParser implements CommandLineParser {

    /**
     * A nested builder class to create {@code DefaultParser} instances
     * using descriptive methods.
     *
     * Example usage:
     * <pre>
     * DefaultParser parser = Option.builder()
     *     .setAllowPartialMatching(false)
     *     .setStripLeadingAndTrailingQuotes(false)
     *     .build();
     * </pre>
     *
     * @since 1.5.0
     */
    public static final class Builder {

        /** Flag indicating if partial matching of long options is supported. */
        private boolean allowPartialMatching = true;

        /**
         * The deprecated option handler.
         * <p>
         * If you want to serialize this field, use a serialization proxy.
         * </p>
         */
        private Consumer<Option> deprecatedHandler = CommandLine.Builder.DEPRECATED_HANDLER;

        /** Flag indicating if balanced leading and trailing double quotes should be stripped from option arguments. */
        private Boolean stripLeadingAndTrailingQuotes;

        /**
         * Constructs a new {@code Builder} for a {@code DefaultParser} instance.
         *
         * Both allowPartialMatching and stripLeadingAndTrailingQuotes are true by default,
         * mimicking the argument-less constructor.
         */
        private Builder() {
        }

        /**
         * Builds an DefaultParser with the values declared by this {@link Builder}.
         *
         * @return the new {@link DefaultParser}
         * @since 1.5.0
         */
        public DefaultParser build() {
            return new DefaultParser(allowPartialMatching, stripLeadingAndTrailingQuotes, deprecatedHandler);
        }

        /**
         * Sets if partial matching of long options is supported.
         *
         * By "partial matching" we mean that given the following code:
         *
         * <pre>
         * {
         *     &#64;code
         *     final Options options = new Options();
         *     options.addOption(new Option("d", "debug", false, "Turn on debug."));
         *     options.addOption(new Option("e", "extract", false, "Turn on extract."));
         *     options.addOption(new Option("o", "option", true, "Turn on option with argument."));
         * }
         * </pre>
         *
         * If "partial matching" is turned on, {@code -de} only matches the {@code "debug"} option. However, with
         * "partial matching" disabled, {@code -de} would enable both {@code debug} as well as {@code extract}
         *
         * @param allowPartialMatching whether to allow partial matching of long options
         * @return this builder, to allow method chaining
         * @since 1.5.0
         */
        public Builder setAllowPartialMatching(final boolean allowPartialMatching) {
            this.allowPartialMatching = allowPartialMatching;
            return this;
        }

        /**
         * Sets the deprecated option handler.
         *
         * @param deprecatedHandler the deprecated option handler.
         * @return {@code this} instance.
         * @since 1.7.0
         */
        public Builder setDeprecatedHandler(final Consumer<Option> deprecatedHandler) {
            this.deprecatedHandler = deprecatedHandler;
            return this;
        }

        /**
         * Sets if balanced leading and trailing double quotes should be stripped from option arguments.
         *
         * If "stripping of balanced leading and trailing double quotes from option arguments" is true,
         * the outermost balanced double quotes of option arguments values will be removed.
         * For example, {@code -o '"x"'} getValue() will return {@code x}, instead of {@code "x"}
         *
         * If "stripping of balanced leading and trailing double quotes from option arguments" is null,
         * then quotes will be stripped from option values separated by space from the option, but
         * kept in other cases, which is the historic behavior.
         *
         * @param stripLeadingAndTrailingQuotes whether balanced leading and trailing double quotes should be stripped from option arguments.
         * @return this builder, to allow method chaining
         * @since 1.5.0
         */
        public Builder setStripLeadingAndTrailingQuotes(final Boolean stripLeadingAndTrailingQuotes) {
            this.stripLeadingAndTrailingQuotes = stripLeadingAndTrailingQuotes;
            return this;
        }
    }

    /**
     * Creates a new {@link Builder} to create an {@link DefaultParser} using descriptive
     * methods.
     *
     * @return a new {@link Builder} instance
     * @since 1.5.0
     */
    public static Builder builder() {
        return new Builder();
    }

    static int indexOfEqual(final String token) {
        return token.indexOf(Char.EQUAL);
    }

    /** The command-line instance. */
    protected CommandLine cmd;

    /** The current options. */
    protected Options options;

    /**
     * Flag indicating how unrecognized tokens are handled. {@code true} to stop the parsing and add the remaining
     * tokens to the args list. {@code false} to throw an exception.
     */
    protected boolean stopAtNonOption;

    /** The token currently processed. */
    protected String currentToken;

    /** The last option parsed. */
    protected Option currentOption;

    /** Flag indicating if tokens should no longer be analyzed and simply added as arguments of the command line. */
    protected boolean skipParsing;

    /** The required options and groups expected to be found when parsing the command line. */
    protected List expectedOpts;

    /** Flag indicating if partial matching of long options is supported. */
    private final boolean allowPartialMatching;

    /** Flag indicating if balanced leading and trailing double quotes should be stripped from option arguments.
     * null represents the historic arbitrary behavior */
    private final Boolean stripLeadingAndTrailingQuotes;

    /**
     * The deprecated option handler.
     * <p>
     * If you want to serialize this field, use a serialization proxy.
     * </p>
     */
    private final Consumer<Option> deprecatedHandler;

    /**
     * Creates a new DefaultParser instance with partial matching enabled.
     *
     * By "partial matching" we mean that given the following code:
     *
     * <pre>
     * {
     *     &#64;code
     *     final Options options = new Options();
     *     options.addOption(new Option("d", "debug", false, "Turn on debug."));
     *     options.addOption(new Option("e", "extract", false, "Turn on extract."));
     *     options.addOption(new Option("o", "option", true, "Turn on option with argument."));
     * }
     * </pre>
     *
     * with "partial matching" turned on, {@code -de} only matches the {@code "debug"} option. However, with
     * "partial matching" disabled, {@code -de} would enable both {@code debug} as well as {@code extract}
     * options.
     */
    public DefaultParser() {
        this.allowPartialMatching = true;
        this.stripLeadingAndTrailingQuotes = null;
        this.deprecatedHandler = CommandLine.Builder.DEPRECATED_HANDLER;
    }

    /**
     * Create a new DefaultParser instance with the specified partial matching policy.
     *
     * By "partial matching" we mean that given the following code:
     *
     * <pre>
     * {
     *     &#64;code
     *     final Options options = new Options();
     *     options.addOption(new Option("d", "debug", false, "Turn on debug."));
     *     options.addOption(new Option("e", "extract", false, "Turn on extract."));
     *     options.addOption(new Option("o", "option", true, "Turn on option with argument."));
     * }
     * </pre>
     *
     * with "partial matching" turned on, {@code -de} only matches the {@code "debug"} option. However, with
     * "partial matching" disabled, {@code -de} would enable both {@code debug} as well as {@code extract}
     * options.
     *
     * @param allowPartialMatching if partial matching of long options shall be enabled
     */
    public DefaultParser(final boolean allowPartialMatching) {
        this.allowPartialMatching = allowPartialMatching;
        this.stripLeadingAndTrailingQuotes = null;
        this.deprecatedHandler = CommandLine.Builder.DEPRECATED_HANDLER;
    }

    /**
     * Creates a new DefaultParser instance with the specified partial matching and quote
     * stripping policy.
     *
     * @param allowPartialMatching if partial matching of long options shall be enabled
     * @param stripLeadingAndTrailingQuotes if balanced outer double quoutes should be stripped
     */
    private DefaultParser(final boolean allowPartialMatching, final Boolean stripLeadingAndTrailingQuotes, final Consumer<Option> deprecatedHandler) {
        this.allowPartialMatching = allowPartialMatching;
        this.stripLeadingAndTrailingQuotes = stripLeadingAndTrailingQuotes;
        this.deprecatedHandler = deprecatedHandler;
    }

    /**
     * Throws a {@link MissingArgumentException} if the current option didn't receive the number of arguments expected.
     */
    private void checkRequiredArgs() throws ParseException {
        if (currentOption != null && currentOption.requiresArg()) {
            if (isJavaProperty(currentOption.getKey()) && currentOption.getValuesList().size() == 1) {
                return;
            }
            throw new MissingArgumentException(currentOption);
        }
    }

    /**
     * Throws a {@link MissingOptionException} if all of the required options are not present.
     *
     * @throws MissingOptionException if any of the required Options are not present.
     */
    protected void checkRequiredOptions() throws MissingOptionException {
        // if there are required options that have not been processed
        if (!expectedOpts.isEmpty()) {
            throw new MissingOptionException(expectedOpts);
        }
    }

    /**
     * Searches for a prefix that is the long name of an option (-Xmx512m)
     *
     * @param token
     */
    private String getLongPrefix(final String token) {
        final String t = Util.stripLeadingHyphens(token);
        int i;
        String opt = null;
        for (i = t.length() - 2; i > 1; i--) {
            final String prefix = t.substring(0, i);
            if (options.hasLongOption(prefix)) {
                opt = prefix;
                break;
            }
        }
        return opt;
    }

    /**
     * Gets a list of matching option strings for the given token, depending on the selected partial matching policy.
     *
     * @param token the token (may contain leading dashes)
     * @return the list of matching option strings or an empty list if no matching option could be found
     */
    private List<String> getMatchingLongOptions(final String token) {
        if (allowPartialMatching) {
            return options.getMatchingOptions(token);
        }
        final List<String> matches = new ArrayList<>(1);
        if (options.hasLongOption(token)) {
            matches.add(options.getOption(token).getLongOpt());
        }
        return matches;
    }

    /**
     * Breaks {@code token} into its constituent parts using the following algorithm.
     *
     * <ul>
     * <li>ignore the first character ("<b>-</b>")</li>
     * <li>for each remaining character check if an {@link Option} exists with that id.</li>
     * <li>if an {@link Option} does exist then add that character prepended with "<b>-</b>" to the list of processed
     * tokens.</li>
     * <li>if the {@link Option} can have an argument value and there are remaining characters in the token then add the
     * remaining characters as a token to the list of processed tokens.</li>
     * <li>if an {@link Option} does <b>NOT</b> exist <b>AND</b> {@code stopAtNonOption} <b>IS</b> set then add the
     * special token "<b>--</b>" followed by the remaining characters and also the remaining tokens directly to the
     * processed tokens list.</li>
     * <li>if an {@link Option} does <b>NOT</b> exist <b>AND</b> {@code stopAtNonOption} <b>IS NOT</b> set then add
     * that character prepended with "<b>-</b>".</li>
     * </ul>
     *
     * @param token The current token to be <b>burst</b> at the first non-Option encountered.
     * @throws ParseException if there are any problems encountered while parsing the command line token.
     */
    protected void handleConcatenatedOptions(final String token) throws ParseException {
        for (int i = 1; i < token.length(); i++) {
            final String ch = String.valueOf(token.charAt(i));
            if (!options.hasOption(ch)) {
                handleUnknownToken(stopAtNonOption && i > 1 ? token.substring(i) : token);
                break;
            }
            handleOption(options.getOption(ch));
            if (currentOption != null && token.length() != i + 1) {
                // add the trail as an argument of the option
                currentOption.processValue(stripLeadingAndTrailingQuotesDefaultOff(token.substring(i + 1)));
                break;
            }
        }
    }

    /**
     * Handles the following tokens:
     *
     * --L --L=V --L V --l
     *
     * @param token the command line token to handle
     */
    private void handleLongOption(final String token) throws ParseException {
        if (indexOfEqual(token) == -1) {
            handleLongOptionWithoutEqual(token);
        } else {
            handleLongOptionWithEqual(token);
        }
    }

    /**
     * Handles the following tokens:
     *
     * --L=V -L=V --l=V -l=V
     *
     * @param token the command line token to handle
     */
    private void handleLongOptionWithEqual(final String token) throws ParseException {
        final int pos = indexOfEqual(token);
        final String value = token.substring(pos + 1);
        final String opt = token.substring(0, pos);
        final List<String> matchingOpts = getMatchingLongOptions(opt);
        if (matchingOpts.isEmpty()) {
            handleUnknownToken(currentToken);
        } else if (matchingOpts.size() > 1 && !options.hasLongOption(opt)) {
            throw new AmbiguousOptionException(opt, matchingOpts);
        } else {
            final String key = options.hasLongOption(opt) ? opt : matchingOpts.get(0);
            final Option option = options.getOption(key);
            if (option.acceptsArg()) {
                handleOption(option);
                currentOption.processValue(stripLeadingAndTrailingQuotesDefaultOff(value));
                currentOption = null;
            } else {
                handleUnknownToken(currentToken);
            }
        }
    }

    /**
     * Handles the following tokens:
     *
     * --L -L --l -l
     *
     * @param token the command line token to handle
     */
    private void handleLongOptionWithoutEqual(final String token) throws ParseException {
        final List<String> matchingOpts = getMatchingLongOptions(token);
        if (matchingOpts.isEmpty()) {
            handleUnknownToken(currentToken);
        } else if (matchingOpts.size() > 1 && !options.hasLongOption(token)) {
            throw new AmbiguousOptionException(token, matchingOpts);
        } else {
            final String key = options.hasLongOption(token) ? token : matchingOpts.get(0);
            handleOption(options.getOption(key));
        }
    }

    private void handleOption(final Option option) throws ParseException {
        // check the previous option before handling the next one
        checkRequiredArgs();
        final Option copy = (Option) option.clone();
        updateRequiredOptions(copy);
        cmd.addOption(copy);
        currentOption = copy.hasArg() ? copy : null;
    }

    /**
     * Sets the values of Options using the values in {@code properties}.
     *
     * @param properties The value properties to be processed.
     */
    private void handleProperties(final Properties properties) throws ParseException {
        if (properties == null) {
            return;
        }
        for (final Enumeration<?> e = properties.propertyNames(); e.hasMoreElements();) {
            final String option = e.nextElement().toString();
            final Option opt = options.getOption(option);
            if (opt == null) {
                throw new UnrecognizedOptionException("Default option wasn't defined", option);
            }
            // if the option is part of a group, check if another option of the group has been selected
            final OptionGroup group = options.getOptionGroup(opt);
            final boolean selected = group != null && group.isSelected();
            if (!cmd.hasOption(option) && !selected) {
                // get the value from the properties
                final String value = properties.getProperty(option);

                if (opt.hasArg()) {
                    if (Util.isEmpty(opt.getValues())) {
                        opt.processValue(stripLeadingAndTrailingQuotesDefaultOff(value));
                    }
                } else if (!("yes".equalsIgnoreCase(value) || "true".equalsIgnoreCase(value) || "1".equalsIgnoreCase(value))) {
                    // if the value is not yes, true or 1 then don't add the option to the CommandLine
                    continue;
                }
                handleOption(opt);
                currentOption = null;
            }
        }
    }

    /**
     * Handles the following tokens:
     *
     * -S -SV -S V -S=V -S1S2 -S1S2 V -SV1=V2
     *
     * -L -LV -L V -L=V -l
     *
     * @param hyphenToken the command line token to handle
     */
    private void handleShortAndLongOption(final String hyphenToken) throws ParseException {
        final String token = Util.stripLeadingHyphens(hyphenToken);
        final int pos = indexOfEqual(token);
        if (token.length() == 1) {
            // -S
            if (options.hasShortOption(token)) {
                handleOption(options.getOption(token));
            } else {
                handleUnknownToken(hyphenToken);
            }
        } else if (pos == -1) {
            // no equal sign found (-xxx)
            if (options.hasShortOption(token)) {
                handleOption(options.getOption(token));
            } else if (!getMatchingLongOptions(token).isEmpty()) {
                // -L or -l
                handleLongOptionWithoutEqual(hyphenToken);
            } else {
                // look for a long prefix (-Xmx512m)
                final String opt = getLongPrefix(token);

                if (opt != null && options.getOption(opt).acceptsArg()) {
                    handleOption(options.getOption(opt));
                    currentOption.processValue(stripLeadingAndTrailingQuotesDefaultOff(token.substring(opt.length())));
                    currentOption = null;
                } else if (isJavaProperty(token)) {
                    // -SV1 (-Dflag)
                    handleOption(options.getOption(token.substring(0, 1)));
                    currentOption.processValue(stripLeadingAndTrailingQuotesDefaultOff(token.substring(1)));
                    currentOption = null;
                } else {
                    // -S1S2S3 or -S1S2V
                    handleConcatenatedOptions(hyphenToken);
                }
            }
        } else {
            // equal sign found (-xxx=yyy)
            final String opt = token.substring(0, pos);
            final String value = token.substring(pos + 1);

            if (opt.length() == 1) {
                // -S=V
                final Option option = options.getOption(opt);
                if (option != null && option.acceptsArg()) {
                    handleOption(option);
                    currentOption.processValue(value);
                    currentOption = null;
                } else {
                    handleUnknownToken(hyphenToken);
                }
            } else if (isJavaProperty(opt)) {
                // -SV1=V2 (-Dkey=value)
                handleOption(options.getOption(opt.substring(0, 1)));
                currentOption.processValue(opt.substring(1));
                currentOption.processValue(value);
                currentOption = null;
            } else {
                // -L=V or -l=V
                handleLongOptionWithEqual(hyphenToken);
            }
        }
    }

    /**
     * Handles any command line token.
     *
     * @param token the command line token to handle
     * @throws ParseException
     */
    private void handleToken(final String token) throws ParseException {
        if (token != null) {
            currentToken = token;
            if (skipParsing) {
                cmd.addArg(token);
            } else if ("--".equals(token)) {
                skipParsing = true;
            } else if (currentOption != null && currentOption.acceptsArg() && isArgument(token)) {
                currentOption.processValue(stripLeadingAndTrailingQuotesDefaultOn(token));
            } else if (token.startsWith("--")) {
                handleLongOption(token);
            } else if (token.startsWith("-") && !"-".equals(token)) {
                handleShortAndLongOption(token);
            } else {
                handleUnknownToken(token);
            }
            if (currentOption != null && !currentOption.acceptsArg()) {
                currentOption = null;
            }
        }
    }

    /**
     * Handles an unknown token. If the token starts with a dash an UnrecognizedOptionException is thrown. Otherwise the
     * token is added to the arguments of the command line. If the stopAtNonOption flag is set, this stops the parsing and
     * the remaining tokens are added as-is in the arguments of the command line.
     *
     * @param token the command line token to handle
     */
    private void handleUnknownToken(final String token) throws ParseException {
        if (token.startsWith("-") && token.length() > 1 && !stopAtNonOption) {
            throw new UnrecognizedOptionException("Unrecognized option: " + token, token);
        }
        cmd.addArg(token);
        if (stopAtNonOption) {
            skipParsing = true;
        }
    }

    /**
     * Tests if the token is a valid argument.
     *
     * @param token
     */
    private boolean isArgument(final String token) {
        return !isOption(token) || isNegativeNumber(token);
    }

    /**
     * Tests if the specified token is a Java-like property (-Dkey=value).
     */
    private boolean isJavaProperty(final String token) {
        final String opt = token.isEmpty() ? null : token.substring(0, 1);
        final Option option = options.getOption(opt);
        return option != null && (option.getArgs() >= 2 || option.getArgs() == Option.UNLIMITED_VALUES);
    }

    /**
     * Tests if the token looks like a long option.
     *
     * @param token
     */
    private boolean isLongOption(final String token) {
        if (token == null || !token.startsWith("-") || token.length() == 1) {
            return false;
        }
        final int pos = indexOfEqual(token);
        final String t = pos == -1 ? token : token.substring(0, pos);
        if (!getMatchingLongOptions(t).isEmpty()) {
            // long or partial long options (--L, -L, --L=V, -L=V, --l, --l=V)
            return true;
        }
        if (getLongPrefix(token) != null && !token.startsWith("--")) {
            // -LV
            return true;
        }
        return false;
    }

    /**
     * Tests if the token is a negative number.
     *
     * @param token
     */
    private boolean isNegativeNumber(final String token) {
        try {
            Double.parseDouble(token);
            return true;
        } catch (final NumberFormatException e) {
            return false;
        }
    }

    /**
     * Tests if the token looks like an option.
     *
     * @param token
     */
    private boolean isOption(final String token) {
        return isLongOption(token) || isShortOption(token);
    }

    /**
     * Tests if the token looks like a short option.
     *
     * @param token
     */
    private boolean isShortOption(final String token) {
        // short options (-S, -SV, -S=V, -SV1=V2, -S1S2)
        if (token == null || !token.startsWith("-") || token.length() == 1) {
            return false;
        }
        // remove leading "-" and "=value"
        final int pos = indexOfEqual(token);
        final String optName = pos == -1 ? token.substring(1) : token.substring(1, pos);
        if (options.hasShortOption(optName)) {
            return true;
        }
        // check for several concatenated short options
        return !optName.isEmpty() && options.hasShortOption(String.valueOf(optName.charAt(0)));
    }

    @Override
    public CommandLine parse(final Options options, final String[] arguments) throws ParseException {
        return parse(options, arguments, null);
    }

    @Override
    public CommandLine parse(final Options options, final String[] arguments, final boolean stopAtNonOption) throws ParseException {
        return parse(options, arguments, null, stopAtNonOption);
    }

    /**
     * Parses the arguments according to the specified options and properties.
     *
     * @param options the specified Options
     * @param arguments the command line arguments
     * @param properties command line option name-value pairs
     * @return the list of atomic option and value tokens
     *
     * @throws ParseException if there are any problems encountered while parsing the command line tokens.
     */
    public CommandLine parse(final Options options, final String[] arguments, final Properties properties) throws ParseException {
        return parse(options, arguments, properties, false);
    }

    /**
     * Parses the arguments according to the specified options and properties.
     *
     * @param options the specified Options
     * @param arguments the command line arguments
     * @param properties command line option name-value pairs
     * @param stopAtNonOption if {@code true} an unrecognized argument stops the parsing and the remaining arguments
     *        are added to the {@link CommandLine}s args list. If {@code false} an unrecognized argument triggers a
     *        ParseException.
     *
     * @return the list of atomic option and value tokens
     * @throws ParseException if there are any problems encountered while parsing the command line tokens.
     */
    public CommandLine parse(final Options options, final String[] arguments, final Properties properties, final boolean stopAtNonOption)
        throws ParseException {
        this.options = options;
        this.stopAtNonOption = stopAtNonOption;
        skipParsing = false;
        currentOption = null;
        expectedOpts = new ArrayList<>(options.getRequiredOptions());
        // clear the data from the groups
        for (final OptionGroup group : options.getOptionGroups()) {
            group.setSelected(null);
        }
        cmd = CommandLine.builder().setDeprecatedHandler(deprecatedHandler).build();
        if (arguments != null) {
            for (final String argument : arguments) {
                handleToken(argument);
            }
        }
        // check the arguments of the last option
        checkRequiredArgs();
        // add the default options
        handleProperties(properties);
        checkRequiredOptions();
        return cmd;
    }

    /**
     * Strips balanced leading and trailing quotes if the stripLeadingAndTrailingQuotes is set
     * If stripLeadingAndTrailingQuotes is null, then do not strip
     *
     * @param token a string
     * @return token with the quotes stripped (if set)
     */
    private String stripLeadingAndTrailingQuotesDefaultOff(final String token) {
        if (stripLeadingAndTrailingQuotes != null && stripLeadingAndTrailingQuotes) {
            return Util.stripLeadingAndTrailingQuotes(token);
        }
        return token;
    }

    /**
     * Strips balanced leading and trailing quotes if the stripLeadingAndTrailingQuotes is set
     * If stripLeadingAndTrailingQuotes is null, then do not strip
     *
     * @param token a string
     * @return token with the quotes stripped (if set)
     */
    private String stripLeadingAndTrailingQuotesDefaultOn(final String token) {
        if (stripLeadingAndTrailingQuotes == null || stripLeadingAndTrailingQuotes) {
            return Util.stripLeadingAndTrailingQuotes(token);
        }
        return token;
    }

    /**
     * Removes the option or its group from the list of expected elements.
     *
     * @param option
     */
    private void updateRequiredOptions(final Option option) throws AlreadySelectedException {
        if (option.isRequired()) {
            expectedOpts.remove(option.getKey());
        }

        // if the option is in an OptionGroup make that option the selected option of the group
        if (options.getOptionGroup(option) != null) {
            final OptionGroup group = options.getOptionGroup(option);

            if (group.isRequired()) {
                expectedOpts.remove(group);
            }

            group.setSelected(option);
        }
    }
}
```

### FILE: src/main/java/org/apache/commons/cli/Parser.java

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

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Enumeration;
import java.util.List;
import java.util.ListIterator;
import java.util.Properties;

/**
 * {@code Parser} creates {@link CommandLine}s.
 *
 * @deprecated since 1.3, the two-pass parsing with the flatten method is not enough flexible to handle complex cases
 */
@Deprecated
public abstract class Parser implements CommandLineParser {
    /** CommandLine instance */
    protected CommandLine cmd;

    /** Current Options */
    private Options options;

    /** List of required options strings */
    private List requiredOptions;

    /**
     * Throws a {@link MissingOptionException} if all of the required options are not present.
     *
     * @throws MissingOptionException if any of the required Options are not present.
     */
    protected void checkRequiredOptions() throws MissingOptionException {
        // if there are required options that have not been processed
        if (!getRequiredOptions().isEmpty()) {
            throw new MissingOptionException(getRequiredOptions());
        }
    }

    /**
     * Subclasses must implement this method to reduce the {@code arguments} that have been passed to the parse method.
     *
     * @param opts The Options to parse the arguments by.
     * @param arguments The arguments that have to be flattened.
     * @param stopAtNonOption specifies whether to stop flattening when a non option has been encountered
     * @return a String array of the flattened arguments
     * @throws ParseException if there are any problems encountered while parsing the command line tokens.
     */
    protected abstract String[] flatten(Options opts, String[] arguments, boolean stopAtNonOption) throws ParseException;

    /**
     * Gets the options.
     *
     * @return the options.
     */
    protected Options getOptions() {
        return options;
    }

    /**
     * Gets the required options.
     *
     * @return the required options.
     */
    protected List getRequiredOptions() {
        return requiredOptions;
    }

    /**
     * Parses the specified {@code arguments} based on the specified {@link Options}.
     *
     * @param options the {@code Options}
     * @param arguments the {@code arguments}
     * @return the {@code CommandLine}
     * @throws ParseException if there are any problems encountered while parsing the command line tokens.
     */
    @Override
    public CommandLine parse(final Options options, final String[] arguments) throws ParseException {
        return parse(options, arguments, null, false);
    }

    /**
     * Parses the specified {@code arguments} based on the specified {@link Options}.
     *
     * @param options the {@code Options}
     * @param arguments the {@code arguments}
     * @param stopAtNonOption if {@code true} an unrecognized argument stops the parsing and the remaining arguments
     *        are added to the {@link CommandLine}s args list. If {@code false} an unrecognized argument triggers a
     *        ParseException.
     * @return the {@code CommandLine}
     * @throws ParseException if an error occurs when parsing the arguments.
     */
    @Override
    public CommandLine parse(final Options options, final String[] arguments, final boolean stopAtNonOption) throws ParseException {
        return parse(options, arguments, null, stopAtNonOption);
    }

    /**
     * Parse the arguments according to the specified options and properties.
     *
     * @param options the specified Options
     * @param arguments the command line arguments
     * @param properties command line option name-value pairs
     * @return the list of atomic option and value tokens
     * @throws ParseException if there are any problems encountered while parsing the command line tokens.
     * @since 1.1
     */
    public CommandLine parse(final Options options, final String[] arguments, final Properties properties) throws ParseException {
        return parse(options, arguments, properties, false);
    }

    /**
     * Parse the arguments according to the specified options and properties.
     *
     * @param options the specified Options
     * @param arguments the command line arguments
     * @param properties command line option name-value pairs
     * @param stopAtNonOption if {@code true} an unrecognized argument stops the parsing and the remaining arguments
     *        are added to the {@link CommandLine}s args list. If {@code false} an unrecognized argument triggers a
     *        ParseException.
     * @return the list of atomic option and value tokens
     * @throws ParseException if there are any problems encountered while parsing the command line tokens.
     * @since 1.1
     */
    public CommandLine parse(final Options options, final String[] arguments, final Properties properties, final boolean stopAtNonOption)
            throws ParseException {
        // clear out the data in options in case it's been used before (CLI-71)
        for (final Option opt : options.helpOptions()) {
            opt.clearValues();
        }
        // clear the data from the groups
        for (final OptionGroup group : options.getOptionGroups()) {
            group.setSelected(null);
        }
        // initialize members
        setOptions(options);
        cmd = CommandLine.builder().build();
        boolean eatTheRest = false;
        final List<String> tokenList = Arrays.asList(flatten(getOptions(), arguments == null ? new String[0] : arguments, stopAtNonOption));
        final ListIterator<String> iterator = tokenList.listIterator();
        // process each flattened token
        while (iterator.hasNext()) {
            final String token = iterator.next();
            if (token != null) {
                // the value is the double-dash
                if ("--".equals(token)) {
                    eatTheRest = true;
                } else if ("-".equals(token)) {
                    // the value is a single dash
                    if (stopAtNonOption) {
                        eatTheRest = true;
                    } else {
                        cmd.addArg(token);
                    }
                } else if (token.startsWith("-")) {
                    // the value is an option
                    if (stopAtNonOption && !getOptions().hasOption(token)) {
                        eatTheRest = true;
                        cmd.addArg(token);
                    } else {
                        processOption(token, iterator);
                    }
                } else {
                    // the value is an argument
                    cmd.addArg(token);
                    if (stopAtNonOption) {
                        eatTheRest = true;
                    }
                }
                // eat the remaining tokens
                if (eatTheRest) {
                    while (iterator.hasNext()) {
                        final String str = iterator.next();
                        // ensure only one double-dash is added
                        if (!"--".equals(str)) {
                            cmd.addArg(str);
                        }
                    }
                }
            }
        }
        processProperties(properties);
        checkRequiredOptions();
        return cmd;
    }

    /**
     * Process the argument values for the specified Option {@code opt} using the values retrieved from the specified
     * iterator {@code iter}.
     *
     * @param opt The current Option
     * @param iter The iterator over the flattened command line Options.
     * @throws ParseException if an argument value is required and it is has not been found.
     */
    public void processArgs(final Option opt, final ListIterator<String> iter) throws ParseException {
        // loop until an option is found
        while (iter.hasNext()) {
            final String str = iter.next();
            // found an Option, not an argument
            if (getOptions().hasOption(str) && str.startsWith("-")) {
                iter.previous();
                break;
            }
            // found a value
            try {
                opt.processValue(Util.stripLeadingAndTrailingQuotes(str));
            } catch (final RuntimeException exp) {
                iter.previous();
                break;
            }
        }
        if (opt.getValues() == null && !opt.hasOptionalArg()) {
            throw new MissingArgumentException(opt);
        }
    }

    /**
     * Process the Option specified by {@code arg} using the values retrieved from the specified iterator
     * {@code iter}.
     *
     * @param arg The String value representing an Option
     * @param iter The iterator over the flattened command line arguments.
     * @throws ParseException if {@code arg} does not represent an Option
     */
    protected void processOption(final String arg, final ListIterator<String> iter) throws ParseException {
        final boolean hasOption = getOptions().hasOption(arg);
        // if there is no option throw an UnrecognizedOptionException
        if (!hasOption) {
            throw new UnrecognizedOptionException("Unrecognized option: " + arg, arg);
        }
        // get the option represented by arg
        final Option opt = (Option) getOptions().getOption(arg).clone();
        // update the required options and groups
        updateRequiredOptions(opt);
        // if the option takes an argument value
        if (opt.hasArg()) {
            processArgs(opt, iter);
        }
        // set the option on the command line
        cmd.addOption(opt);
    }

    /**
     * Sets the values of Options using the values in {@code properties}.
     *
     * @param properties The value properties to be processed.
     * @throws ParseException if there are any problems encountered while processing the properties.
     */
    protected void processProperties(final Properties properties) throws ParseException {
        if (properties == null) {
            return;
        }
        for (final Enumeration<?> e = properties.propertyNames(); e.hasMoreElements();) {
            final String option = e.nextElement().toString();
            final Option opt = options.getOption(option);
            if (opt == null) {
                throw new UnrecognizedOptionException("Default option wasn't defined", option);
            }
            // if the option is part of a group, check if another option of the group has been selected
            final OptionGroup group = options.getOptionGroup(opt);
            final boolean selected = group != null && group.isSelected();
            if (!cmd.hasOption(option) && !selected) {
                // get the value from the properties instance
                final String value = properties.getProperty(option);
                if (opt.hasArg()) {
                    if (Util.isEmpty(opt.getValues())) {
                        try {
                            opt.processValue(value);
                        } catch (final RuntimeException exp) { // NOPMD
                            // if we cannot add the value don't worry about it
                        }
                    }
                } else if (!("yes".equalsIgnoreCase(value) || "true".equalsIgnoreCase(value) || "1".equalsIgnoreCase(value))) {
                    // if the value is not yes, true or 1 then don't add the
                    // option to the CommandLine
                    continue;
                }
                cmd.addOption(opt);
                updateRequiredOptions(opt);
            }
        }
    }

    /**
     * Sets the options.
     *
     * @param options the options.
     */
    protected void setOptions(final Options options) {
        this.options = options;
        this.requiredOptions = new ArrayList<>(options.getRequiredOptions());
    }

    /**
     * Removes the option or its group from the list of expected elements.
     *
     * @param opt
     */
    private void updateRequiredOptions(final Option opt) throws ParseException {
        // if the option is a required option remove the option from
        // the requiredOptions list
        if (opt.isRequired()) {
            getRequiredOptions().remove(opt.getKey());
        }
        // if the option is in an OptionGroup make that option the selected
        // option of the group
        if (getOptions().getOptionGroup(opt) != null) {
            final OptionGroup group = getOptions().getOptionGroup(opt);
            if (group.isRequired()) {
                getRequiredOptions().remove(group);
            }
            group.setSelected(opt);
        }
    }

}
```

### FILE: src/main/java/org/apache/commons/cli/MissingOptionException.java

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

import java.util.Iterator;
import java.util.List;

/**
 * Thrown when a required option has not been provided.
 */
public class MissingOptionException extends ParseException {
    /** This exception {@code serialVersionUID}. */
    private static final long serialVersionUID = 8161889051578563249L;

    /**
     * Build the exception message from the specified list of options.
     *
     * @param missingOptions the list of missing options and groups
     */
    private static String createMessage(final List<?> missingOptions) {
        final StringBuilder buf = new StringBuilder("Missing required option");
        buf.append(missingOptions.size() == 1 ? "" : "s");
        buf.append(": ");

        final Iterator<?> it = missingOptions.iterator();
        while (it.hasNext()) {
            buf.append(it.next());
            if (it.hasNext()) {
                buf.append(", ");
            }
        }

        return buf.toString();
    }

    /** The list of missing options and groups */
    private List missingOptions;

    /**
     * Constructs a new {@code MissingSelectedException} with the specified list of missing options.
     *
     * @param missingOptions the list of missing options and groups
     * @since 1.2
     */
    public MissingOptionException(final List missingOptions) {
        this(createMessage(missingOptions));
        this.missingOptions = missingOptions;
    }

    /**
     * Constructs a new {@code MissingSelectedException} with the specified detail message.
     *
     * @param message the detail message
     */
    public MissingOptionException(final String message) {
        super(message);
    }

    /**
     * Gets the list of options or option groups missing in the command line parsed.
     *
     * @return the missing options, consisting of String instances for simple options, and OptionGroup instances for
     *         required option groups.
     * @since 1.2
     */
    public List getMissingOptions() {
        return missingOptions;
    }
}
```

