# -*- coding: utf-8 -*-
"""Configuration data and constants for README generation.

This module contains all the configuration parameters, user information,
and dynamic data used to generate the README.md file with current GitHub
activity and profile information.
"""
import datetime
from typing import Dict, Optional, Union
from zoneinfo import ZoneInfo

# GitHub configuration constants
GITHUB_USER_NAME: str = "nicojahn"
TZ: str = "Europe/Berlin"
MAX_RECENT_ACTIVITY: int = 14  # days
MAX_REPOS_LISTED: int = 5  # number of repositories
DT_DATE: datetime.datetime = datetime.datetime.now(ZoneInfo(TZ))

# Dynamic information dictionary used for README template replacement
dynamic_information: Dict[str, Optional[Union[str, None]]] = {
    "city": "Berlin",
    "contact": (
        ":email: dev@nicojahn.com, "
        + ":octocat: [nicoja-hn](https://github.com/nicoja-hn), "
        + ":computer: [nicoja.hn](https://nicoja.hn)"
    ),
    "date": DT_DATE.strftime("%A, %d %B %Y, %Z"),
    "filename": "README.md",
    "github": f"github.com/{GITHUB_USER_NAME}",
    "name": "Nico Jahn",
    "projects": None,
}
