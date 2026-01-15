# -*- coding: utf-8 -*-
"""Just a helper file which holds most of the data."""
import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

# Configuration constants
GITHUB_USER_NAME: str = "nicojahn"
TZ: str = "Europe/Berlin"
MAX_RECENT_ACTIVITY: int = 14  # days
MAX_REPOS_LISTED: int = 5  # number of repositories
DT_DATE: datetime.datetime = datetime.datetime.now(ZoneInfo(TZ))

# Dynamic information dictionary for template replacement
dynamic_information: Dict[str, Optional[Any]] = {
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
