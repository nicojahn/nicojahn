# -*- coding: utf-8 -*-
"""Just a helper file which holds most of the data."""
import datetime
from zoneinfo import ZoneInfo

GITHUB_USER_NAME = "nicojahn"
TZ = "Europe/Berlin"
MAX_RECENT_ACTIVITY = 14  # days
MAX_REPOS_LISTED = 5  # number of repositories
DT_DATE = datetime.datetime.now(ZoneInfo(TZ))

dynamic_information = {
    "city": "Berlin",
    "contact": (
        ":email: dev@nicojahn.com, "
        + ":bird: [nicojahn96](https://twitter.com/nicojahn96), "
        + ":computer: [nicojahn.com](https://nicojahn.com)"
    ),
    "date": DT_DATE.strftime("%A, %d %B %Y, %Z"),
    "filename": "README.md",
    "github": f"github.com/{GITHUB_USER_NAME}",
    "name": "Nico Jahn",
    "projects": None,
}
