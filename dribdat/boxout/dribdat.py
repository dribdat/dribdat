"""Boxout module for Dribdat projects."""

import pystache

TEMPLATE_PROJECT = r"""
<div class="onebox honeycomb">
    <a href="{{link}}"
       class="hexagon
        {{#is_challenge}}challenge{{/is_challenge}}
        {{^is_challenge}}project stage-{{progress}}{{/is_challenge}}">
        <div class="hexagontent">
    {{#image_url}}
    <div class="hexaicon" style="background-image:url('{{image_url}}')"></div>
    {{/image_url}}
        </div>
    </a>
    <a href="{{link}}" class="title">{{name}}</a>
    <div class="event-detail">
        <span>{{event_name}}</span>
        <i class="phase">{{phase}}</i>
    </div>
    <p>{{summary}}</p>
</div>
"""


def box_project(url):
    """Create a OneBox for local projects."""
    project_id = url.split('/')[-1]
    if not project_id:
        return None
    from ..user.models import Project
    project = Project.query.filter_by(id=int(project_id)).first()
    if not project:
        return None
    pd = project.data
    # project.url returns a relative path
    pd['link'] = url
    return pystache.render(TEMPLATE_PROJECT, pd)
