# -*- coding: utf-8 -*-
"""Utilities for aggregating data."""

import re
from dribdat.apifetch import (
    FetchWebGitHub,
    FetchWebGitHubGist,
    FetchGithubProject,
    FetchGithubIssue,
    FetchGitlabProject,
    FetchCodebergProject,
    FetchDribdatProject,
    FetchDataProject,
    FetchWebProject,
    FetchGitProject,
    FetchHuggingFaceProject,
)

def GetProjectData(url):
    """Parse the Readme URL to collect remote data."""
    if url.find("//gitlab.com/") > 0:
        return get_gitlab_project(url)

    elif url.find("//huggingface.co/") > 0:
        return get_huggingface_project(url)

    elif url.find("//github.com/") > 0 or url.find("//gist.github.com/") > 0:
        return get_github_project(url)

    elif url.find("//codeberg.org/") > 0:
        return get_codeberg_project(url)

    elif url.endswith(".git"):
        return FetchGitProject(url)

    # The fun begins
    elif url.find(".json") > 0:  # not /datapackage
        return FetchDataProject(url)

    # TODO: replace with <meta generator dribdat>
    elif url.find("/project/") > 0:
        try_dribdat = FetchDribdatProject(url)
        if try_dribdat != {}:
            return try_dribdat

    # Now we're really rock'n'rollin'
    return FetchWebProject(url)


def get_gitlab_project(url):
    apiurl = url
    apiurl = re.sub(r"(?i)-?/blob/[a-z]+/README.*", "", apiurl)
    apiurl = re.sub(r"https?://gitlab\.com/", "", apiurl).strip("/")
    if apiurl == url:
        return {}
    return FetchGitlabProject(apiurl)


def get_github_project(url):
    apiurl = url
    if apiurl.startswith("https://gist.github.com/"):
        # GitHub Gist
        return FetchWebGitHubGist(url)
    apiurl = re.sub(r"(?i)/blob/[a-z]+/README.*", "", apiurl)
    apiurl = re.sub(r"https?://github\.com/", "", apiurl).strip("/")
    if apiurl.endswith(".git"):
        apiurl = apiurl[:-4]
    if apiurl == url:
        return {}
    if apiurl.endswith(".md"):
        # GitHub Markdown
        return FetchWebGitHub(url)
    if "/issues/" in apiurl:
        iuarr = apiurl.split("/issues/")
        if len(iuarr) == 2:
            return FetchGithubIssue(iuarr[0], int(iuarr[1]))
    return FetchGithubProject(apiurl)


def get_codeberg_project(url):
    apiurl = url
    apiurl = re.sub(r"(?i)/src/branch/[a-z]+/README.*", "", apiurl)
    apiurl = re.sub(r"https?://codeberg\.org/", "", apiurl).strip("/")
    if apiurl.endswith(".git"):
        apiurl = apiurl[:-4]
    if apiurl == url:
        return {}
    return FetchCodebergProject(apiurl)


def get_huggingface_project(url):
    """Prepare a HuggingFace URL for the API."""
    apiurl = re.sub(r"https?://huggingface\.co/", "", url).strip("/")
    if apiurl == url:
        return {}
    return FetchHuggingFaceProject(apiurl)

