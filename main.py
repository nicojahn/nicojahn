# -*- coding: utf-8 -*-
"""This python code generates a README.md from the templated README.md (incl.

GitHub stats of a user).
"""
import datetime
import re
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import requests

from data import DT_DATE
from data import dynamic_information
from data import GITHUB_USER_NAME
from data import MAX_RECENT_ACTIVITY
from data import MAX_REPOS_LISTED


def get_first_n_recent_projects(all_repositories: List[List[Any]]) -> List[str]:
    """Returns at most 'MAX_REPOS_LISTED' which where modified in the last
    'MAX_RECENT_ACTIVITY' days.

    Args:
        all_repositories: List of [days_since_update, repository_string] pairs

    Returns:
        List of repository description strings
    """
    # Testing the walrus-operator
    i = 0
    projects = []
    for repo in all_repositories:
        if (
            not repo[1] is None and repo[0] < MAX_RECENT_ACTIVITY
        ):  # Filtering the profile repo
            if (i := i + 1) <= MAX_REPOS_LISTED:
                projects += [repo[1]]
    return projects


def get_single_most_recent_project(all_repositories: List[List[Any]]) -> List[str]:
    """Return first repo in list, where you are a maintainer.

    Args:
        all_repositories: List of [days_since_update, repository_string] pairs

    Returns:
        List containing the most recent repository description string
    """
    # Fixing the bug of no activity
    projects = []
    for repo in all_repositories:
        # Is None, if it is not your project
        if not repo[1] is None:
            projects = [repo[1]]
            break
    return projects


def _calculate_days_since_update(latest_change_str: str) -> int:
    """Calculate days since the latest repository update.

    Args:
        latest_change_str: ISO format timestamp string

    Returns:
        Number of days since the update
    """
    return (
        DT_DATE
        - datetime.datetime.strptime(latest_change_str, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=ZoneInfo("UTC")
        )
    ).days


def _format_repository_string(response: Dict[str, Any]) -> Optional[str]:
    """Format repository information into a display string.

    Args:
        response: GitHub API response dictionary for a repository

    Returns:
        Formatted repository string or None if it's the profile repository
    """
    # When repository is not the profile itself it returns a string else None (filtered later)
    if response["full_name"] != f"{GITHUB_USER_NAME}/{GITHUB_USER_NAME}":
        days_ago = _calculate_days_since_update(response["updated_at"])
        language_part = (
            f" and is mainly written in {response['language']}"
            if response["language"] is not None
            else ""
        )
        return (
            f"repository [{response['full_name']}]({response['html_url']}) which was updated "
            + f"{days_ago} days ago{language_part}"
        )
    return None


def get_github_activity() -> str:
    """This functions updates a dictionary with prepared text snippets, based
    on the GitHub activity.

    Returns:
        Formatted string describing recent GitHub activity
    """
    # the actual request to the GitHub API
    # default response timezone:
    #  https://developer.github.com/v3/#defaulting-to-utc-without-other-timezone-information
    req = requests.get(
        f"https://api.github.com/users/{GITHUB_USER_NAME}/repos", timeout=10
    ).json()

    # the reformatting and selection of repositories
    #  (matching criteria of latest changes and maximum amount)
    # getting a list of tuples of (days,string)
    all_repositories = sorted(
        [
            [
                _calculate_days_since_update(response["updated_at"]),
                _format_repository_string(response),
            ]
            for response in req
        ],
        key=lambda time_and_string: time_and_string[0],
    )

    projects = get_first_n_recent_projects(all_repositories)
    if len(projects) == 0:
        projects = get_single_most_recent_project(all_repositories)

    # either use the n most recent projects or if no filter applies, use just the most recent
    return " as well as ".join(projects)


class UpdateREADME:
    """This class is reading the README template, fill in the gaps and writes
    it again onto disk."""

    def __init__(self, **kwargs: Any) -> None:
        """Expects the dictionary with the mandatory key 'filename'.

        Everything else is done dynamically.

        Args:
            **kwargs: Dictionary containing 'filename' and other template variables
        """
        self.information = kwargs
        self.keys = self.information.keys()
        self.filename: str = self.information["filename"]
        self.content: Optional[List[str]] = None

    def read_file_content(self) -> "UpdateREADME":
        """Just reads the 'filename' file and returns it by list.

        Returns:
            Self for method chaining
        """
        with open(self.filename, "r", encoding="utf-8") as input_file:
            self.content = input_file.readlines()
        return self

    def write_file_content(self) -> "UpdateREADME":
        """Writes the strings in the 'self.content' list to file 'filename'.

        Returns:
            Self for method chaining
        """
        with open(self.filename, "w", encoding="utf-8") as output_file:
            output_file.write("".join(self.content))
        return self

    @property
    def open_seq(self) -> str:
        """Return the opening sequence for template tags.

        Returns:
            Opening tag sequence
        """
        return "<!-- "

    @property
    def close_seq(self) -> str:
        """Return the closing sequence for template tags.

        Returns:
            Closing tag sequence
        """
        return " -->"

    @staticmethod
    def _is_true(i: Any, j: Any) -> bool:
        """Check if both values are truthy.

        Args:
            i: First value
            j: Second value

        Returns:
            True if both values are truthy
        """
        return bool(i and j)

    @staticmethod
    def _equals(i: Any, j: Any) -> bool:
        """Check if two values are equal.

        Args:
            i: First value
            j: Second value

        Returns:
            True if values are equal
        """
        return i == j

    @staticmethod
    def _is_none(i: Any) -> bool:
        """Check if value is None.

        Args:
            i: Value to check

        Returns:
            True if value is None
        """
        return i is None

    @staticmethod
    def _is_not_none(i: Any) -> bool:
        """Check if value is not None.

        Args:
            i: Value to check

        Returns:
            True if value is not None
        """
        return i is not None

    def _extract_tag_pairs(self, line: str) -> List[Tuple[str, str]]:
        """Extract key-value pairs from template tags in a line.

        Args:
            line: Line to process

        Returns:
            List of (key, value) tuples found in the line
        """
        if self.open_seq not in line:
            return []

        # Get pairs of 2 tokens each (sliding window)
        line_split = line.split(self.open_seq)
        sliding_window_size = 2
        tuples = [
            line_split[i : i + sliding_window_size]
            for i, _ in enumerate(line_split[: 1 - sliding_window_size])
        ]

        tag_pairs = []
        for tup in tuples:
            # find applicable key/value pairs in the original line
            key, value = None, None
            for elem in tup:
                if self.close_seq not in elem:
                    break
                key_value = elem.split(self.close_seq)

                # Check if we have exactly 2 parts and no previous key/value set
                if len(key_value) == 2 and key is None and value is None:
                    key, value = key_value
                elif key is not None and value is not None:
                    # if the sliding window contains 2 different tags, reset
                    # This checks if current key_value differs from stored key, value
                    if key_value[0] != key or len(key_value) != 2:
                        key, value = None, None
                        break

            # Store valid key-value pairs where both key and value are not None
            if key is not None and value is not None:
                tag_pairs.append((key, value))

        return tag_pairs

    def _replace_tag_content(self, line: str, key: str, value: str) -> str:
        """Replace tag content in a line with the corresponding information.

        Args:
            line: Line containing the tag
            key: Tag key to replace
            value: Current tag value

        Returns:
            Line with tag content replaced
        """
        if key in self.keys:
            tag = self.open_seq + key + self.close_seq
            # Find the tag pattern with the current value
            pattern = tag + re.escape(value) + tag
            match = re.search(pattern, line)
            if match:
                span = match.span()
                # Calculate positions to remove (excluding outer tags)
                start_pos = span[0] + len(tag)
                end_pos = span[1] - len(tag)
                # Replace the content between tags
                line = line[:start_pos] + self.information[key] + line[end_pos:]
        return line

    def _process_lines(self, line: str) -> str:
        """Process a single line, replacing template tags with actual content.

        This method finds template tag pairs in the format:
        <!-- key -->value<!-- key -->
        and replaces 'value' with the corresponding content from self.information.

        Args:
            line: Single line from the template file

        Returns:
            Processed line with template tags replaced
        """
        if self.open_seq not in line:
            return line

        # Extract all valid tag pairs from the line
        tag_pairs = self._extract_tag_pairs(line)

        # Replace content for each valid tag pair
        for key, value in tag_pairs:
            line = self._replace_tag_content(line, key, value)

        return line

    def update_content(self) -> "UpdateREADME":
        """Update all content by processing each line.

        Returns:
            Self for method chaining
        """
        if self.content is not None:
            self.content = [self._process_lines(line) for line in self.content]
        return self


def main() -> None:
    """Main function to update README with GitHub activity information.

    Fetches GitHub activity data and processes the README template to
    generate the final README.md file.
    """
    dynamic_information["projects"] = get_github_activity()
    (
        UpdateREADME(**dynamic_information)
        .read_file_content()
        .update_content()
        .write_file_content()
    )


if __name__ == "__main__":
    main()
