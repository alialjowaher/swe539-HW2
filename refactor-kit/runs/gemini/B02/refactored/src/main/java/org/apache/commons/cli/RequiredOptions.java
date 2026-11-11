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
import java.util.List;

/**
 * Tracks the required options and option groups that are still expected during command-line parsing.
 */
final class RequiredOptions {

    /** The list of required option keys and required OptionGroup instances still expected. */
    private final List<Object> expectedOpts;

    /**
     * Constructs a new tracker initialized with the required options from {@code options}.
     *
     * @param options the Options being parsed
     */
    RequiredOptions(final Options options) {
        this.expectedOpts = new ArrayList<>(options.getRequiredOptions());
    }

    /**
     * Throws a {@link MissingOptionException} if any required options or option groups have not been seen.
     *
     * @throws MissingOptionException if any required options are still missing
     */
    void checkAllPresent() throws MissingOptionException {
        if (!expectedOpts.isEmpty()) {
            throw new MissingOptionException(expectedOpts);
        }
    }

    /**
     * Gets the live mutable list of still-expected options and groups for subclass compatibility.
     *
     * @return the list of still-expected required options and groups
     */
    List<Object> getExpectedOptions() {
        return expectedOpts;
    }

    /**
     * Records that {@code option} (and its enclosing {@code group}, if any) has been seen during parsing.
     *
     * @param option the option that was matched
     * @param group the OptionGroup containing {@code option}, or {@code null} if none
     * @throws AlreadySelectedException if another option in {@code group} was already selected
     */
    void markSeen(final Option option, final OptionGroup group) throws AlreadySelectedException {
        if (option.isRequired()) {
            expectedOpts.remove(option.getKey());
        }
        if (group != null) {
            if (group.isRequired()) {
                expectedOpts.remove(group);
            }
            group.setSelected(option);
        }
    }
}
