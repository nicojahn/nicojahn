import os
import datetime
from functools import reduce
from operator import add
import re
import pytz
import json
import requests

github_user_name = 'nicojahn'
timezone = 'Europe/Berlin'
max_recent_activity = 14 # days
max_repos_listed = 5 # number of repositories

dt_date = datetime.datetime.now(pytz.timezone(timezone))

dynamic_information = { 'city': 'Berlin',
                        'contact': ':email: dev@nicojahn.com, :bird: [nicojahn96](https://twitter.com/nicojahn96), :computer: [nicojahn.com](https://nicojahn.com)',
                        'date': dt_date.strftime("%A, %d %B %Y, %Z"),
                        'filename': 'README.md',
                        'github': 'github.com/%s'%github_user_name,
                        'name': 'Nico Jahn',
                        'projects' : None,
                      }

def getGitHubActivity():
    # some misc functions
    latest_change_in_days = lambda latest_change_str: (dt_date-datetime.datetime.strptime(latest_change_str,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.timezone('UTC'))).days
    # when repository is not not the profile itself it returns a string else None (filtered later)
    make_string = lambda response: f"repository [{response['full_name']}]({response['html_url']}) which was updated {latest_change_in_days(response['updated_at'])} days ago{' and is mainly written in '+response['language'] if response['language'] is not None else ''}" if response['full_name'] != f"{github_user_name}/{github_user_name}" else None

    # the actual request to the GitHub API
    # default response timezone: https://developer.github.com/v3/#defaulting-to-utc-without-other-timezone-information
    r = requests.get(f'https://api.github.com/users/{github_user_name}/repos').json()

    # the reformatting and selection of repositories (matching criteria of latest changes and maximum amount)
    # getting a list of tuples of (days,string)
    all_repositories = sorted([   [latest_change_in_days(response['updated_at']), make_string(response)]
                                for response in r
                              ],
                              key=lambda time_and_string:time_and_string[0]
                             )
    # testing the walrus-operator
    i = 0
    projects = []
    for repo in all_repositories:
        if not repo[1] is None and repo[0] < max_recent_activity: # filtering the profile repo
            if (i := i+1) <= max_repos_listed:
                projects += [repo[1]]

    # either use the n most recent projects or if no filter applies, use just the most recent
    dynamic_information['projects'] = ' as well as '.join(projects) if len(projects) else all_repositories[0]

class UpdateREADME:
    def __init__(self,*args,**kwargs):
        self.information = kwargs
        self.keys = self.information.keys()
        
    def readFileContent(self):
        assert 'filename' in self.keys
        with open(self.information['filename'], 'r') as input:
            self.content = input.readlines()
        return self

    def writeFileContent(self):
        with open(self.information['filename'], 'w') as output:
            output.write(''.join(self.content))
        return self

    def updateContent(self):
        isTrue = lambda x,y: x and y
        equals = lambda x,y: x == y
        isNone = lambda x: equals(x, None)
        isNotNone = lambda x: equals(x, not None)
        
        for idx, line in enumerate(self.content):
            line_replacement = line
            if '<!-- ' in line:
                line_split = line.split('<!-- ')
                sliding_window_size = 2
                tuples = [line_split[i:i+sliding_window_size] for i, elem in enumerate(line_split[:1-sliding_window_size])]
                for tup in tuples:
                    # find applicable key/value pairs in the original line
                    key, value = None, None
                    for elem in tup:
                        if not ' -->' in elem:
                            break
                        key_value = [e for e in elem.split(' -->')]
                        # even though the number of variables is fixed, i prefer map-reduce over hardcoded indices
                        if len(key_value) == 2 and reduce(isTrue, map(isNone, [key, value])):
                            key, value = key_value
                        elif reduce(equals, map(isNotNone, [key, value])):
                            # if the sliding window does contain 2 different tags, remove it
                            if reduce(equals, map(lambda x: not equals(*x), zip([key, value], key_value))):
                                key, value = None, None
                                break
                    
                    # replace the content
                    if reduce(equals, map(isNotNone, [key, value])):
                        for k in self.keys:
                            if k == key:
                                tag = '<!-- ' + key + ' -->'
                                # an example of regex beeing used (no wildcard necessary, 'value' is escaped)
                                span = re.search(tag + re.escape(value) + tag, line_replacement).span()
                                # tuple arithmetics
                                remove = tuple(map(add, span, (len(tag), -len(tag))))
                                line_replacement = line_replacement[:remove[0]]) + str(self.information[key]) + line_replacement[remove[1]:]
            self.content[idx] = line_replacement
        return self

getGitHubActivity()
UpdateREADME(**dynamic_information).readFileContent().updateContent().writeFileContent()
