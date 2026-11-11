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
import java.util.List;

/** Tracks required options and option groups during parsing. */
final class RequiredOptions implements Serializable {
    private static final long serialVersionUID = 1L;

    private final List<Object> options;

    /** Creates an empty required-options tracker. */
    RequiredOptions() {
        options = new ArrayList<>();
    }

    /** Creates a tracker initialized with the supplied required elements. */
    RequiredOptions(final Collection<?> requiredOptions) {
        options = new ArrayList<>(requiredOptions);
    }

    /** Adds a required option key, preserving the original replacement order. */
    void addOption(final String key) {
        if (options.contains(key)) {
            options.remove(options.indexOf(key));
        }
        options.add(key);
    }

    /** Adds a required option group. */
    void addGroup(final OptionGroup group) {
        options.add(group);
    }

    /** Marks an option and its group as present. */
    void markSeen(final Option option, final OptionGroup group) throws AlreadySelectedException {
        if (option.isRequired()) {
            options.remove(option.getKey());
        }
        if (group != null) {
            if (group.isRequired()) {
                options.remove(group);
            }
            group.setSelected(option);
        }
    }

    /** Throws if required options remain. */
    void checkAllPresent() throws MissingOptionException {
        if (!options.isEmpty()) {
            throw new MissingOptionException(options);
        }
    }

    /** Gets the mutable tracked elements. */
    List<Object> getOptions() {
        return options;
    }
}
