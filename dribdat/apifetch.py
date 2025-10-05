# -*- coding: utf-8 -*-
"""Collecting data from third party API repositories."""

from flask import current_app
from pyquery import PyQuery as pq  # noqa: N813
from base64 import b64decode
from bleach.sanitizer import ALLOWED_ATTRIBUTES
from urllib.parse import quote_plus
import huggingface_hub
import shutil
import requests
import bleach
from .apievents import (
    fetch_commits,
    fetch_commits_gitlab,
    fetch_commits_github,
    fetch_commits_codeberg,
)
from .git import (
    clone_repo,
    get_git_log,
    get_file_content,
)
from .utils import (
    sanitize_url,
    load_presets,
    load_yaml_presets,
    fix_relative_links,
    markdownit,
)
from future.standard_library import install_aliases

install_aliases()

# In seconds, how long to wait for API response
REQUEST_TIMEOUT = 10


def FetchStageConfig(url, top_element="stages", by_col="name"):
    """Download a remote YAML stages configuration."""
    if not url.startswith("http:") and not url.startswith("https:"):
        if current_app:
            current_app.logger.info("Loading stages from file")
        return load_yaml_presets(top_element, by_col, url)
    if current_app:
        current_app.logger.info("Loading stages from URL")
    data = requests.get(url, timeout=REQUEST_TIMEOUT)
    if data.text.find("stages:") < 0:
        if current_app:
            current_app.logger.debug("No stage data: %s", data.text)
        return {}
    blob = data.text
    return load_presets(blob, top_element, by_col)


def FetchCodebergProject(project_url):
    """Download data from Codeberg, a large Forgejo site."""
    # Docs: https://codeberg.org/api/swagger
    site_root = "https://codeberg.org"
    url_q = quote_plus(project_url, "/")
    api_repos = site_root + "/api/v1/repos/%s" % url_q
    api_content = api_repos + "/contents"
    # Collect basic data
    current_app.logger.info("Fetching Codeberg: %s", url_q)
    data = requests.get(api_repos, timeout=REQUEST_TIMEOUT)
    if data.text.find("{") < 0:
        current_app.logger.debug("No data: %s", data.text)
        return {}
    json = data.json()
    if "name" not in json:
        current_app.logger.debug("Invalid data: %s", data.text)
        return {}
    # Collect the README
    data = requests.get(api_content, timeout=REQUEST_TIMEOUT)
    readme = ""
    if not data.text.find("{") < 0:
        readmeurl = None
        for repo_file in data.json():
            if "readme" in repo_file["name"].lower():
                readmeurl = repo_file["download_url"]
                readmedata = requests.get(readmeurl, timeout=REQUEST_TIMEOUT)
                readme = readmedata.text
                break
        if readmeurl is None:
            current_app.logger.info("Could not find README: %s", url_q)
    issuesurl = ""
    if json["has_issues"]:
        issuesurl = json["html_url"] + "/issues"
    return {
        "type": "Codeberg",
        "name": json["name"],
        "summary": json["description"],
        "description": readme,
        "source_url": json["html_url"],
        "image_url": json["avatar_url"] or json["owner"]["avatar_url"],
        "contact_url": issuesurl,
        "commits": fetch_commits_codeberg(project_url),
    }


def FetchGitProject(url):
    """Download from an arbitrary Git URL."""
    current_app.logger.info("Fetching from Git repo: %s", url)
    repo_path = clone_repo(url)
    if not repo_path:
        current_app.logger.warning("Could not clone")
        return {}

    # TODO: list files to look for README
    content = get_file_content(repo_path, "README.md")
    if not content:
        content = get_file_content(repo_path, "README")

    # Clone the repo to get commit history
    commits = get_git_log(repo_path)
    shutil.rmtree(repo_path)

    # Parse the repo name from URL
    repo_name = url.split("/")[-1].replace(".git", "")

    return {
        "type": "Git",
        "name": repo_name,
        "summary": "",  # No summary field in repo
        "description": content,
        "source_url": url,
        "image_url": "",
        "contact_url": "", 
        "commits": commits,
    }


def FetchHuggingFaceProject(project_url):
    """Download data from Hugging Face."""
    current_app.logger.info("Fetching Hugging Face: %s", project_url)
    try:
        api = huggingface_hub.HfApi()
        repo_info = api.repo_info(repo_id=project_url)
        repo_files = api.list_repo_files(repo_id=project_url)
    except huggingface_hub.utils.RepositoryNotFoundError:
        current_app.logger.debug("Repository not found: %s", project_url)
        return {}

    readme_filename = None
    for filename in repo_files:
        if 'readme' in filename.lower():
            readme_filename = filename
            break

    readme = ""
    if readme_filename:
        readme_url = huggingface_hub.hf_hub_url(project_url, readme_filename)
        try:
            readme = requests.get(readme_url, timeout=REQUEST_TIMEOUT).text
        except requests.exceptions.RequestException as e:
            current_app.logger.warning("Could not fetch README: %s", e)

    # Clone the repo to get commit history
    # TODO: check if this is possible in API
    clone_url = "https://huggingface.co/" + project_url + ".git"
    repo_path = clone_repo(clone_url)
    if repo_path:
        commits = get_git_log(repo_path)
        shutil.rmtree(repo_path)
    else:
        commits = []

    return {
        "type": "Hugging Face",
        "name": repo_info.id,
        "summary": "",  # No summary field in repo_info
        "description": readme,
        "source_url": "https://huggingface.co/" + project_url,
        "image_url": "",
        "contact_url": "https://huggingface.co/" + project_url + "/discussions",
        "commits": commits,
    }


def FetchGitlabProject(project_url):
    """Download data from GitLab."""
    WEB_BASE = "https://gitlab.com"
    API_BASE = WEB_BASE + "/api/v4/projects/%s"
    current_app.logger.info("Fetching GitLab: %s" % project_url)
    # Collect basic data
    url_q = quote_plus(project_url)
    data = requests.get(API_BASE % url_q, timeout=REQUEST_TIMEOUT)
    if data.text.find("{") < 0:
        current_app.logger.debug("No data: %s", data.text)
        return {}
    json = data.json()
    if "name" not in json:
        current_app.logger.debug("Invalid data: %s", data.text)
        return {}
    # Collect the README
    readmeurl = json["readme_url"] + "?inline=false"
    readmeurl = readmeurl.replace("-/blob/", "-/raw/")
    readmedata = requests.get(readmeurl, timeout=REQUEST_TIMEOUT)
    readme = readmedata.text or ""
    return {
        "type": "GitLab",
        "name": json["name"],
        "summary": json["description"],
        "description": readme,
        "source_url": json["web_url"],
        "image_url": json["avatar_url"],
        "contact_url": json["web_url"] + "/issues",
        "commits": fetch_commits_gitlab(json["id"]),
    }


def FetchGitlabAvatar(email):
    """Download a user avatar from GitLab."""
    apiurl = "https://gitlab.com/api/v4/avatar?email=%s&size=80"
    data = requests.get(apiurl % email, timeout=REQUEST_TIMEOUT)
    if data.text.find("{") < 0:
        current_app.logger.debug("No data: %s", data.text)
        return None
    json = data.json()
    if "avatar_url" not in json:
        return None
    return json["avatar_url"]


def FetchGithubProject(project_url):
    """Download data from GitHub."""
    API_BASE = "https://api.github.com/repos/%s"
    current_app.logger.info("Fetching GitHub: %s", project_url)
    data = requests.get(API_BASE % project_url, timeout=REQUEST_TIMEOUT)
    if data.text.find("{") < 0:
        current_app.logger.debug("No data: %s", data.text)
        return {}
    json = data.json()
    if "name" not in json or "full_name" not in json:
        current_app.logger.debug("Invalid data: %s", data.text)
        return {}
    repo_full_name = json["full_name"]
    default_branch = json["default_branch"] or "main"
    readmeurl = "%s/readme" % (API_BASE % project_url)
    readmedata = requests.get(readmeurl, timeout=REQUEST_TIMEOUT)
    readme = ""
    if readmedata.text.find("{") < 0:
        current_app.logger.debug("No readme: %s", data.text)
    else:
        readme = readmedata.json()
    if "content" not in readme:
        readme = ""
    else:
        # Convert from base64
        readme = b64decode(readme["content"]).decode("utf-8")  # type: ignore
        # Fix relative links in text
        imgroot = "https://raw.githubusercontent.com"
        readme = fix_relative_links(readme, imgroot, repo_full_name, default_branch)
    return {
        "type": "GitHub",
        "name": json["name"],
        "summary": json["description"],
        "description": readme,
        "webpage_url": json["homepage"],
        "source_url": json["html_url"],
        "image_url": json["owner"]["avatar_url"],
        "contact_url": json["html_url"] + "/issues",
        "download_url": json["html_url"] + "/releases",
        "commits": fetch_commits_github(json["clone_url"]),
    }


def FetchGithubIssue(project_url, issue_id):
    """Download an issue from GitHub."""
    project_data = FetchGithubProject(project_url)
    current_app.logger.info("Fetching GitHub Issue: %s", issue_id)
    API_BASE = "https://api.github.com/repos/%s/issues/%d"
    data = requests.get(API_BASE % (project_url, issue_id), timeout=REQUEST_TIMEOUT)
    if data.text.find("{") < 0:
        current_app.logger.debug("No data: %s", data.text)
        return {}
    json = data.json()
    if "title" not in json or "body" not in json:
        current_app.logger.debug("Invalid data: %s", data.text)
        return {}
    project_data["hashtag"] = "#%d" % issue_id
    project_data["summary"] = project_data["name"]
    project_data["name"] = json["title"][:77]
    project_data["description"] = json["body"]
    return project_data


def FetchDataProject(datapackage_url):
    """Try to load a Data Package formatted JSON file."""
    # TODO: use frictionlessdata library!
    project_url = datapackage_url.replace("datapackage.json", "")
    project_url = sanitize_url(project_url) + "datapackage.json"
    data = requests.get(project_url, timeout=REQUEST_TIMEOUT)
    # TODO: treat dribdat events as special
    current_app.logger.info("Fetching Data Package: %s", project_url)
    if data.text.find("{") < 0:
        current_app.logger.debug("No data at: %s", project_url)
        return {}
    json = data.json()
    contact_url = ""
    if "name" not in json or "title" not in json:
        current_app.logger.debug("Invalid format at: %s", project_url)
        return {}
    try:
        text_content = parse_data_package(json)
    except KeyError:
        text_content = "(Could not parse Data Package contents)"
    if "homepage" in json:
        contact_url = json["homepage"] or ""
    elif (
        "maintainers" in json
        and len(json["maintainers"]) > 0
        and "web" in json["maintainers"][0]
    ):
        contact_url = json["maintainers"][0]["web"]
    return {
        "type": "Data Package",
        "name": json["name"],
        "summary": json["title"],
        "description": text_content,
        "source_url": project_url,
        "logo_icon": "box-open",
        "contact_url": contact_url,
    }


def parse_data_package(json):
    """Extract contents of a Data Package."""
    text_content = ""
    if "description" in json:
        text_content = json["description"] + "\n\n"
    if "resources" in json:
        text_content = text_content + "\n### Resources\n\n"
        for r in json["resources"]:
            rn = r["name"]
            if "path" in r:
                rn = "[%s](%s)" % (rn, r["path"])
            text_content = text_content + "- " + rn + "\n"
    if "sources" in json:
        text_content = text_content + "\n### Sources\n\n"
        for r in json["sources"]:
            rn = r["title"]
            if "path" in r:
                rn = "[%s](%s)" % (rn, r["path"])
            text_content = text_content + "- " + rn + "\n"
    if text_content == "":
        raise KeyError("No content")
    return text_content


def FetchDribdatProject(dribdat_url):
    """Try to load a Dribdat project from a remote page."""
    project_url = dribdat_url.replace("/project/", "/api/project/")
    project_url = sanitize_url(project_url) + "?full=1"
    data = requests.get(project_url, timeout=REQUEST_TIMEOUT)
    # TODO: treat dribdat events as special
    current_app.logger.info("Fetching Dribdat site: %s", project_url)
    if data.text.find("{") < 0:
        current_app.logger.debug("No data at: %s", project_url)
        return {}
    json = data.json()
    if "project" not in json or "event" not in json:
        current_app.logger.debug("Invalid format at: %s", project_url)
        return {}
    projectdata = json["project"]
    projectdata["type"] = "Dribdat"
    projectdata["description"] = projectdata["longtext"]
    return projectdata


# Basis: https://github.com/mozilla/bleach/blob/master/bleach/sanitizer.py#L16
ALLOWED_HTML_TAGS = [
    "acronym",
    "a",
    "blockquote",
    "li",
    "abbr",
    "strong",
    "b",
    "i",
    "ul",
    "ol",
    "code",
    "em",
    "img",
    "font",
    "center",
    "sub",
    "sup",
    "pre",
    "table",
    "tr",
    "thead",
    "tbody",
    "td",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "p",
    "u",
]
ALLOWED_HTML_ATTR = ALLOWED_ATTRIBUTES
ALLOWED_HTML_ATTR["h1"] = ["id"]
ALLOWED_HTML_ATTR["h2"] = ["id"]
ALLOWED_HTML_ATTR["h3"] = ["id"]
ALLOWED_HTML_ATTR["h4"] = ["id"]
ALLOWED_HTML_ATTR["h5"] = ["id"]
ALLOWED_HTML_ATTR["a"] = ["href", "title", "class", "name"]
ALLOWED_HTML_ATTR["img"] = ["src", "width", "height", "alt", "class"]
ALLOWED_HTML_ATTR["font"] = ["color"]


def RequestRemoteContent(project_url):
    try:
        # TODO: the admin should be able to whitelist a range of allowed
        # online resources controlling the domains from which we can
        # fetch remote content.
        project_url = sanitize_url(project_url)
        current_app.logger.info("Fetching: %s", project_url)
        data = requests.get(project_url, timeout=REQUEST_TIMEOUT)
        return data.text or None
    except requests.exceptions.RequestException:
        current_app.logger.warning("Could not connect to %s" % project_url)
        return None


def FetchWebProject(project_url):
    """Parse a remote Document, wiki or website URL."""

    datatext = RequestRemoteContent(project_url)
    if datatext is None:
        return {}

    # Google Document
    if project_url.startswith("https://docs.google.com/document"):
        return FetchWebGoogleDoc(datatext, project_url)
    # Instructables
    elif project_url.startswith("https://www.instructables.com/"):
        return FetchWebInstructables(datatext, project_url)
    # Pretalx
    elif datatext.find('<meta name="generator" content="pretalx"') > 0:
        return FetchWebPretalx(datatext, project_url)
    # DokuWiki
    elif datatext.find('<meta name="generator" content="DokuWiki"') > 0:
        return FetchWebDokuWiki(datatext, project_url)
    # Etherpad
    elif datatext.find("pad.importExport.exportetherpad") > 0:
        return FetchWebEtherpad(datatext, project_url)
    # CodiMD / HackMD
    elif datatext.find('<div id="doc" ') > 0:
        return FetchWebCodiMD(datatext, project_url)
    
    return {}


def FetchWebGoogleDoc(text, url):
    """Help extract data from a Google doc."""
    doc = pq(text)
    doc("style").remove()
    ptitle = doc("div#title") or doc("div#header")
    if len(ptitle) < 1:
        return {}
    content = doc("div#contents")
    if len(content) < 1:
        return {}
    content = str(content.html()).strip()
    if not content or len(content) < 1:
        return {}
    html_content = bleach.clean(
        content,
        strip=True,
        tags=frozenset(ALLOWED_HTML_TAGS),
        attributes=ALLOWED_HTML_ATTR,
    )
    obj = {}
    # {
    #     'type': 'Google', ...
    #     'name': name,
    #     'summary': summary,
    #     'description': html_content,
    #     'image_url': image_url
    #     'source_url': project_url,
    # }
    obj["type"] = "Google Docs"
    obj["name"] = ptitle.text()
    obj["description"] = html_content
    obj["source_url"] = url
    obj["logo_icon"] = "paperclip"
    return obj


def FetchWebCodiMD(text, url):
    """Help extract data from CodiMD."""
    doc = pq(text)
    ptitle = doc("title")
    if len(ptitle) < 1:
        return {}
    content = str(doc("div#doc").html())
    if len(content) < 1:
        return {}
    obj = {}
    obj["type"] = "Markdown"
    obj["name"] = ptitle.text()
    obj["description"] = markdownit(content)
    obj["source_url"] = url
    obj["logo_icon"] = "outdent"
    return obj


def FetchWebDokuWiki(text, url):
    """Help extract data from DokuWiki."""
    doc = pq(text)
    ptitle = doc(".pageId")
    if len(ptitle) < 1:
        return {}
    title = str(ptitle.text()).replace("project:", "")
    if len(ptitle) < 1:
        return {}
    content = doc("#dokuwiki__content")
    if len(content) < 1:
        content = doc("div.dw-content")
        if len(content) < 1:
            return {}
    html_content = bleach.clean(
        str(content.html()).strip(),
        strip=True,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTR,
    )
    obj = {}
    obj["type"] = "DokuWiki"
    obj["name"] = title
    obj["description"] = html_content
    obj["source_url"] = url
    obj["logo_icon"] = "list-ul"
    return obj


def FetchWebEtherpad(text, url):
    """Help extract data from Etherpad Lite."""
    ptitle = url.split("/")[-1]
    if len(ptitle) < 1:
        return {}
    text_content = requests.get("%s/export/txt" % url, timeout=REQUEST_TIMEOUT).text
    obj = {}
    obj["type"] = "Etherpad"
    obj["name"] = ptitle.replace("_", " ")
    obj["description"] = text_content
    obj["source_url"] = url
    obj["logo_icon"] = "pen"
    return obj


def FetchWebInstructables(text, url):
    """Help extract data from Instructables."""
    doc = pq(text)
    ptitle = doc(".header-title")
    content = doc(".main-content")
    if len(content) < 1 or len(ptitle) < 1:
        return {}
    html_content = ParseInstructablesPage(content)
    obj = {}
    obj["type"] = "Instructables"
    obj["name"] = ptitle.text()
    obj["description"] = html_content
    obj["source_url"] = url
    obj["logo_icon"] = "wrench"
    return obj


def FetchWebGitHub(url):
    """Grab a Markdown source from a GitHub link."""
    if not url.endswith(".md") or "/blob/" not in url:
        return {}
    filename = url.split("/")[-1].replace(".md", "")
    rawurl = url.replace("/blob/", "/raw/").replace("https://github.com/", "")
    rawdata = requests.get("https://github.com/" + rawurl, timeout=REQUEST_TIMEOUT)
    text_content = rawdata.text or ""
    return {
        "type": "Markdown",
        "name": filename,
        "description": text_content,
        "source_url": url,
        "logo_icon": "outdent",
    }


def FetchWebGitHubGist(url):
    """Grab a Markdown source from a GitHub Gist link."""
    rawurl = url.replace("https://gist.github.com/", "") + "/raw"
    rawdata = requests.get(
        "https://gist.githubusercontent.com/" + rawurl, timeout=REQUEST_TIMEOUT
    )
    text_content = rawdata.text or ""
    return {
        "type": "Markdown",
        "name": "Gist",
        "description": text_content,
        "source_url": url,
        "logo_icon": "outdent",
    }


def ParseInstructablesPage(content):
    """Create an HTML summary of content."""
    html_content = ""
    for step in content.find(".step"):
        step_title = pq(step).find(".step-title")
        if step_title is not None:
            html_content += "<h3>%s</h3>" % step_title.text()
        # Grab photos
        for img in pq(step).find("noscript"):
            img_html = str(pq(img).html())
            if "{{ file" not in img_html:
                html_content += img_html
        # Iterate through body
        step_content = pq(step).find(".step-body")
        if step_content is None:
            continue
        for elem in pq(step_content).children():
            elem_tag, p = ParseInstructablesElement(elem)
            if elem_tag is None:
                continue
            html_content += "<%s>%s</%s>" % (elem_tag, p, elem_tag)
    return html_content


def ParseInstructablesElement(elem):
    """Check and return minimal contents."""
    if elem.tag == "pre":
        if elem.text is None:
            return None, None
        return "pre", elem.text
    else:
        p = pq(elem).html()
        if p is None:
            return None, None
        p = bleach.clean(
            str(p).strip(),
            strip=True,
            tags=ALLOWED_HTML_TAGS,
            attributes=ALLOWED_HTML_ATTR,
        )
        return elem.tag, p


def FetchWebPretalx(text, url):
    """Grab Pretalx data from a talk."""
    if "/talk/" not in url:
        return {}
    doc = pq(text)
    apiurl = doc('link[@rel="alternate"]').attr("href")
    rawdata = requests.get(str(apiurl) + "?format=json", timeout=REQUEST_TIMEOUT)
    if rawdata.text.find("{") < 0:
        return {}
    jsondata = rawdata.json()
    return {
        "type": "Pretalx",
        "name": jsondata["title"],
        "summary": jsondata["abstract"][:2000],
        "description": jsondata["description"],
        "source_url": url,
        "logo_icon": "window-maximize",
    }
