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

def GetProjectData(url, with_history=False):
    """Parse the Readme URL to collect remote data."""
    if url.find("//gitlab.com/") > 0:
        return get_gitlab_project(url, with_history)

    elif url.find("//huggingface.co/") > 0:
        return get_huggingface_project(url, with_history)

    elif url.find("//github.com/") > 0 or url.find("//gist.github.com/") > 0:
        return get_github_project(url, with_history)

    elif url.find("//codeberg.org/") > 0:
        return get_codeberg_project(url, with_history)

    elif url.endswith(".git"):
        return FetchGitProject(url, with_history)

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


def get_gitlab_project(url, with_history):
    apiurl = url
    apiurl = re.sub(r"(?i)-?/blob/[a-z]+/README.*", "", apiurl)
    apiurl = re.sub(r"https?://gitlab\.com/", "", apiurl).strip("/")
    if apiurl == url:
        return {}
    return FetchGitlabProject(apiurl, with_history)


def get_github_project(url, with_history):
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
    return FetchGithubProject(apiurl, with_history)


def get_codeberg_project(url, with_history):
    apiurl = url
    apiurl = re.sub(r"(?i)/src/branch/[a-z]+/README.*", "", apiurl)
    apiurl = re.sub(r"https?://codeberg\.org/", "", apiurl).strip("/")
    if apiurl.endswith(".git"):
        apiurl = apiurl[:-4]
    if apiurl == url:
        return {}
    return FetchCodebergProject(apiurl, with_history)


def get_huggingface_project(url, with_history):
    """Prepare a HuggingFace URL for the API."""
    apiurl = re.sub(r"https?://huggingface\.co/", "", url).strip("/")
    if apiurl == url:
        return {}
    return FetchHuggingFaceProject(apiurl, with_history)

