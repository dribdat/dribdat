# USAGE

This document explains the basic functions of _} dribdat {_, an open source platform for data-driven team collaboration, such as *Hackathons*.

For more background and references, see [ABOUT](ABOUT.md) and [README](README.md).

## How does it look?

} dribdat { works as a website and project board for running exciting, productive events, and allows organizers and participants to collect their project details in one place, displaying the challenges and projects in Web dashboards, and plugging in community tools such as [Discourse](https://www.discourse.org/), [Slack](http://slack.com), or [Let's Chat](http://sdelements.github.io/lets-chat/) - or using the [remote API](#api) for additional interfaces such as [chatbots](https://github.com/schoolofdata-ch/dridbot) to enhance the hackathon.

Logged-in users can submit challenges, ideas and projects by linking their document or repository, or entering details directly into a form. You can change or customize these [instructions](dribdat/templates/quickstart.html) as you see fit.

![](dribdat/static/img/screenshot_start.png)

Data on projects can be entered into the application directly using [Markdown](https://www.markdowntutorial.com/) formatting, or aggregated simply by putting in a URL to a public project hosted on one of these supported platforms:

- [GitHub](https://github.com) (README / README.md)
- [GitLab](https://gitlab.com) (README.md)
- [BitBucket](https://bitbucket.org)
- [Etherpad Lite](http://etherpad.org)
- [Google Docs](https://support.google.com/docs/answer/183965?co=GENIE.Platform%3DDesktop&hl=en) (Publish to Web)
- [DokuWiki](http://make.opendata.ch/wiki/project:home)

The image below explains the various parts of a typical challenge or project page.

![](dribdat/static/img/project_page_overview.png)

# The backend

The administrative interface shown below allows defining details of the event and managing project data.

![](dribdat/static/img/screenshot_admin_projects.png)

The look and feel of the project view can be customized with CSS, and shows challenges and projects, with a rating of how completely they are documented. In the `Events` screen there are links to a *Print* view for a summary of all projects on one page, and the ability to *Embed* results into another website.

![](dribdat/static/img/screenshot_makezurich.jpg)

And, as we're really into making the most of those time constraints, the homepage and dashboard feature a big animated countdown clock.

![](dribdat/static/img/screenshot_countdown.png)

Tick tock!
