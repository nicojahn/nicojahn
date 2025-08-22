# -*- coding: utf-8 -*-
"""README.md generation from template with GitHub activity integration.

This module generates a README.md file from a templated README.md by fetching
GitHub user activity and replacing template tags with dynamic content including
repository information and profile data.
"""
import datetime
import re
from functools import reduce
from typing import Any, Dict, List, Optional, Tuple, Union
from zoneinfo import ZoneInfo

import requests

from data import DT_DATE
from data import dynamic_information
from data import GITHUB_USER_NAME
from data import MAX_RECENT_ACTIVITY
from data import MAX_REPOS_LISTED


def get_first_n_recent_projects(
    all_repositories: List[List[Union[int, Optional[str]]]],
) -> List[str]:
    """Return at most MAX_REPOS_LISTED projects modified in the last MAX_RECENT_ACTIVITY days.

    Args:
        all_repositories: List of [days_since_update, repo_description] pairs.

    Returns:
        List of repository description strings for recently active projects.
    """
    # Testing the walrus-operator
    projects: List[str] = []
    count = 0
    for repo in all_repositories:
        days_since_update = repo[0]
        repo_description = repo[1]
        if (
            isinstance(repo_description, str)
            and isinstance(days_since_update, int)
            and days_since_update < MAX_RECENT_ACTIVITY
        ):  # Filtering the profile repo
            if (count := count + 1) <= MAX_REPOS_LISTED:
                projects.append(repo_description)
    return projects


def get_single_most_recent_project(
    all_repositories: List[List[Union[int, Optional[str]]]],
) -> List[str]:
    """Return the first repository where the user is a maintainer.

    Args:
        all_repositories: List of [days_since_update, repo_description] pairs.

    Returns:
        List containing the description of the most recent maintainer project,
        or empty list if none found.
    """
    # Fixing the bug of no activity
    projects: List[str] = []
    for repo in all_repositories:
        repo_description = repo[1]
        # Is None, if it is not your project
        if isinstance(repo_description, str):
            projects = [repo_description]
            break
    return projects


def get_github_activity() -> str:
    """Update dictionary with prepared text snippets based on GitHub activity.

    Fetches repository information from GitHub API and formats it into
    a readable string describing recent projects and their activity.

    Returns:
        Formatted string describing recent repository activity.
    """

    def calculate_days_since_update(latest_change_str: str) -> int:
        """Calculate days since the last repository update."""
        return (
            DT_DATE
            - datetime.datetime.strptime(
                latest_change_str, "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=ZoneInfo("UTC"))
        ).days

    def create_repository_description(response: Dict[str, Any]) -> Optional[str]:
        """Create repository description string if not the profile repository."""
        if response["full_name"] == f"{GITHUB_USER_NAME}/{GITHUB_USER_NAME}":
            return None

        language_info = (
            f" and is mainly written in {response['language']}"
            if response["language"] is not None
            else ""
        )

        return (
            f"repository [{response['full_name']}]({response['html_url']}) "
            f"which was updated {calculate_days_since_update(response['updated_at'])} days ago"
            f"{language_info}"
        )

    # GitHub API request with timeout
    # Default response timezone:
    # https://developer.github.com/v3/#defaulting-to-utc-without-other-timezone-information
    req = requests.get(
        f"https://api.github.com/users/{GITHUB_USER_NAME}/repos", timeout=10
    ).json()

    # Reformatting and selection of repositories
    # (matching criteria of latest changes and maximum amount)
    # Getting a list of tuples of (days, string)
    all_repositories = sorted(
        [
            [
                calculate_days_since_update(response["updated_at"]),
                create_repository_description(response),
            ]
            for response in req
        ],
        key=lambda time_and_string: (
            time_and_string[0] if isinstance(time_and_string[0], int) else 0
        ),
    )

    projects = get_first_n_recent_projects(all_repositories)
    if len(projects) == 0:
        projects = get_single_most_recent_project(all_repositories)

    # Either use the n most recent projects or if no filter applies, use just the most recent
    return " as well as ".join(projects)


class UpdateREADME:
    """README template processor that reads, processes, and writes README files.

    This class handles reading a README template, replacing template tags with
    dynamic content from a provided information dictionary, and writing the
    updated content back to disk.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the UpdateREADME processor.

        Args:
            **kwargs: Dictionary containing template replacement values.
                     Must include 'filename' key specifying the target file.
        """
        self.information: Dict[str, Any] = kwargs
        self.keys: List[str] = list(self.information.keys())
        self.filename: str = self.information["filename"]
        self.content: Optional[List[str]] = None

    def read_file_content(self) -> "UpdateREADME":
        """Read the template file content into memory.

        Returns:
            Self for method chaining.
        """
        with open(self.filename, "r", encoding="utf-8") as input_file:
            self.content = input_file.readlines()
        return self

    def write_file_content(self) -> "UpdateREADME":
        """Write the processed content to the target file.

        Returns:
            Self for method chaining.
        """
        if self.content is not None:
            with open(self.filename, "w", encoding="utf-8") as output_file:
                output_file.write("".join(self.content))
        return self

    @property
    def open_seq(self) -> str:
        """Return the opening sequence for template tags."""
        return "<!-- "

    @property
    def close_seq(self) -> str:
        """Return the closing sequence for template tags."""
        return " -->"

    @staticmethod
    def _is_true(i: Any, j: Any) -> bool:
        """Check if both arguments are truthy."""
        return i and j

    @staticmethod
    def _equals(i: Any, j: Any) -> bool:
        """Check if two values are equal."""
        return i == j

    @staticmethod
    def _is_none(i: Any) -> bool:
        """Check if value is None."""
        return UpdateREADME._equals(i, None)

    @staticmethod
    def _is_not_none(i: Any) -> bool:
        """Check if value is not None."""
        return UpdateREADME._equals(i, not None)

    def _process_lines(self, line: str) -> str:
        """Process a single line to replace template tags with dynamic content.

        This method finds template tags in the format <!-- key -->value<!-- key -->
        and replaces them with corresponding values from the information dictionary.

        Args:
            line: The line of text to process.

        Returns:
            The processed line with template tags replaced.
        """
        if self.open_seq not in line:
            return line

        # Split line by opening sequence to create sliding windows
        line_split = line.split(self.open_seq)
        sliding_window_size = 2
        tuples = [
            line_split[i : i + sliding_window_size]
            for i, _ in enumerate(line_split[: 1 - sliding_window_size])
        ]

        for tup in tuples:
            key, value = self._extract_key_value_pair(tup)

            if key is not None and value is not None:
                line = self._replace_tag_in_line(line, key, value)

        return line

    def _extract_key_value_pair(
        self, tup: List[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Extract key-value pair from a tuple of line elements.

        Args:
            tup: Tuple containing potential template tag elements.

        Returns:
            Tuple of (key, value) if found, (None, None) otherwise.
        """
        key, value = None, None

        for elem in tup:
            if self.close_seq not in elem:
                break

            key_value = elem.split(self.close_seq)

            # Check if we found a valid key-value pair
            if len(key_value) == 2 and self._both_are_none(key, value):
                key, value = key_value
            elif self._both_are_not_none(key, value):
                # If sliding window contains 2 different tags, reset them
                if (
                    key is not None
                    and value is not None
                    and self._are_different_tags(key, value, key_value)
                ):
                    key, value = None, None
                    break

        return key, value

    def _replace_tag_in_line(self, line: str, key: str, value: str) -> str:
        """Replace a template tag with its corresponding value in the line.

        Args:
            line: The line containing the template tag.
            key: The template tag key.
            value: The current value in the template.

        Returns:
            The line with the template tag replaced.
        """
        for k in self.keys:
            if self._equals(k, key):
                tag = self.open_seq + key + self.close_seq
                # Replace the entire template structure: <!-- key -->value<!-- key -->
                # with just the new information value
                pattern = tag + re.escape(value) + tag
                line = re.sub(pattern, self.information[key], line)
                break

        return line

    def _both_are_none(self, key: Optional[str], value: Optional[str]) -> bool:
        """Check if both key and value are None."""
        return reduce(self._is_true, map(self._is_none, [key, value]))

    def _both_are_not_none(self, key: Optional[str], value: Optional[str]) -> bool:
        """Check if both key and value are not None."""
        return reduce(self._equals, map(self._is_not_none, [key, value]))

    def _are_different_tags(self, key: str, value: str, key_value: List[str]) -> bool:
        """Check if the current key-value pair differs from the new one."""
        return reduce(
            self._equals,
            map(
                lambda x: not self._equals(*x),
                zip([key, value], key_value),
            ),
        )

    def update_content(self) -> "UpdateREADME":
        """Process all lines in the content to replace template tags.

        Returns:
            Self for method chaining.
        """
        if self.content is not None:
            self.content = list(map(self._process_lines, self.content))
        return self


def main() -> None:
    """Main function to generate README with current GitHub activity."""
    dynamic_information["projects"] = get_github_activity()
    (
        UpdateREADME(**dynamic_information)
        .read_file_content()
        .update_content()
        .write_file_content()
    )


if __name__ == "__main__":
    main()
