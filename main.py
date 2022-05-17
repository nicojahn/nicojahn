# -*- coding: utf-8 -*-
"""This python code generates a README.md from the templated README.md (incl.

GitHub stats of a user).
"""
import datetime
import re
from functools import reduce
from operator import add
from zoneinfo import ZoneInfo

import requests

from data import DT_DATE
from data import dynamic_information
from data import GITHUB_USER_NAME
from data import MAX_RECENT_ACTIVITY
from data import MAX_REPOS_LISTED


def get_first_n_recent_projects(all_repositories):
    """Returns at most 'MAX_REPOS_LISTED' which where modified in the last
    'MAX_RECENT_ACTIVITY' days."""
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


def get_single_most_recent_project(all_repositories):
    """Return first repo in list, where you are a maintainer."""
    # Fixing the bug of no activity
    projects = []
    for repo in all_repositories:
        # Is None, if it is not your project
        if not repo[1] is None:
            projects = [repo[1]]
            break
    return projects


def get_github_activity():
    """This functions updates a dictionary with prepared text snippets, based
    on the GitHub activity."""
    # some misc functions
    latest_change_in_days = lambda latest_change_str: (
        DT_DATE
        - datetime.datetime.strptime(latest_change_str, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=ZoneInfo("UTC")
        )
    ).days

    # when repository is not not the profile itself it returns a string else None (filtered later)
    make_string = (
        lambda response: (
            f"repository [{response['full_name']}]({response['html_url']}) which was updated "
            + f"{latest_change_in_days(response['updated_at'])} days ago"
            + f"{' and is mainly written in '+response['language'] if response['language'] is not None else ''}"
        )
        if response["full_name"] != f"{GITHUB_USER_NAME}/{GITHUB_USER_NAME}"
        else None
    )

    # the actual request to the GitHub API
    # default response timezone:
    #  https://developer.github.com/v3/#defaulting-to-utc-without-other-timezone-information
    req = requests.get(f"https://api.github.com/users/{GITHUB_USER_NAME}/repos").json()

    # the reformatting and selection of repositories
    #  (matching criteria of latest changes and maximum amount)
    # getting a list of tuples of (days,string)
    all_repositories = sorted(
        [
            [latest_change_in_days(response["updated_at"]), make_string(response)]
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

    def __init__(self, **kwargs):
        """Expects the dictionary with the mandatory key 'filename'.

        Everything else is done dynamically.
        """
        self.information = kwargs
        self.keys = self.information.keys()
        self.filename = self.information["filename"]
        self.content = None

    def read_file_content(self):
        """Just reads the 'filename' file and returns it by list."""
        with open(self.filename, "r", encoding="utf-8") as input_file:
            self.content = input_file.readlines()
        return self

    def write_file_content(self):
        """Writes the strings in the 'self.content' list to file 'filename'."""
        with open(self.filename, "w", encoding="utf-8") as output_file:
            output_file.write("".join(self.content))
        return self

    @property
    def open_seq(self):
        return "<!-- "

    @property
    def close_seq(self):
        return " -->"

    @staticmethod
    def _is_true(i, j):
        return i and j

    @staticmethod
    def _equals(i, j):
        return i == j

    @staticmethod
    def _is_none(i):
        return UpdateREADME._equals(i, None)

    @staticmethod
    def _is_not_none(i):
        return UpdateREADME._equals(i, not None)

    def _process_lines(self, line):
        if not self.open_seq in line:
            return line

        # Get pairs of 2 tokens each
        line_split = line.split(self.open_seq)
        sliding_window_size = 2
        tuples = [
            line_split[i : i + sliding_window_size]
            for i, _ in enumerate(line_split[: 1 - sliding_window_size])
        ]

        for tup in tuples:
            # find applicable key/value pairs in the original line
            key, value = None, None
            for elem in tup:
                if not self.close_seq in elem:
                    break
                key_value = list(elem.split(self.close_seq))
                # even though the number of variables is fixed,
                #  i prefer map-reduce over hardcoded indices
                if len(key_value) == 2 and reduce(
                    self._is_true, map(self._is_none, [key, value])
                ):
                    key, value = key_value
                elif reduce(self._equals, map(self._is_not_none, [key, value])):
                    # if the sliding window does contain 2 different tags, remove it
                    if reduce(
                        self._equals,
                        map(
                            lambda x: not self._equals(*x),
                            zip([key, value], key_value),
                        ),
                    ):
                        key, value = None, None
                        break

            # replace the content
            if reduce(self._equals, map(self._is_not_none, [key, value])):
                for k in self.keys:
                    if self._equals(k, key):
                        tag = self.open_seq + key + self.close_seq
                        # an example of regex beeing used
                        #  (no wildcard necessary, 'value' is escaped)
                        span = re.search(tag + re.escape(value) + tag, line).span()
                        # tuple arithmetics
                        remove = tuple(map(add, span, (len(tag), -len(tag))))
                        line = (
                            line[: remove[0]]
                            + self.information[key]
                            + line[remove[1] :]
                        )
        return line

    def update_content(self):
        self.content = list(map(self._process_lines, self.content))
        return self


def main():
    dynamic_information["projects"] = get_github_activity()
    (
        UpdateREADME(**dynamic_information)
        .read_file_content()
        .update_content()
        .write_file_content()
    )


if __name__ == "__main__":
    main()
