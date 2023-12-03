"""Boxout module for GitHub projects."""

# Does not work reliably due to rate limits
# see https://github.com/dribdat/dribdat/issues/265


import pystache

TEMPLATE_GITHUB = r"""
<div class="widget widget-github">
{{#issues}}
<div id="issues-list" data-github="{{repo}}" class="list-group list-data">
    <i>Loading ...</i></div>
{{/issues}}
<div data-theme="default" data-width="400" data-height="160"
     data-github="{{repo}}" class="github-card"></div>
<script src="//cdn.jsdelivr.net/github-cards/latest/widget.js"></script>
</div>
"""


def box_repo(url='dribdat/dribdat'):
    """Create a OneBox for GitHub repositories with optional issue list."""
    project_repo = url.replace('https://github.com/', '')
    if not project_repo:
        return url
    has_issues = project_repo.endswith('/issues')
    project_repo = project_repo.replace('/issues', '')
    project_repo = project_repo.strip()
    return pystache.render(TEMPLATE_GITHUB, {
        'repo': project_repo, 'issues': has_issues})
