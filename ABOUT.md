This document summarises the current status and makes some vision statements about possible future developments as discussed in [issue #100](https://github.com/datalets/dribdat/issues/100).

For more background and references, see the [User's Guide](USAGE.md) and [README](README.md).

# About dribdat

[![](https://blog.datalets.ch/workshops/2017/dribdat/dribdat.png)](https://github.com/datalets/dribdat/)

`} dribdat {` (originally from "Driven By Data") is an open source tool for data-driven team collaboration (such as hackathons). It provides an open source website and project board for running events, and integrates popular community platforms and open source code repositories. It is the official platform of [Opendata.ch Hackdays](https://hack.opendata.ch) and has been used to host many other events in the Swiss open data and open source community.

## Screenshots

[![Now.Makezurich.ch](https://blog.datalets.ch/workshops/2017/dribdat/nowmakezurich.jpg)](http://now.makezurich.ch/)

[![Climathon Zürich](https://blog.datalets.ch/workshops/2017/dribdat/climathon.jpg)](https://hack.opendata.ch/event/4)

[![Open Food Hackdays](https://blog.datalets.ch/workshops/2017/dribdat/foodhackdays-openreceipts.jpg)](https://hack.opendata.ch/project/74)     

Using dribdat's API, it is also possible to create a live dashboard, for example for use as Digital Signage at the event:

![](https://blog.datalets.ch/workshops/2017/dribdat/IMG_6910_800.JPG)

*Photo credit: MakeZurich 2018 by Christina Rieder CC BY-SA 4.0*

## Introduction

dribdat is an open source project board designed for splendid collaboration. On dribdat-powered sites we collect and showcase all projects from an event in one place. Designed for use at hackathons, being part of a project team is more than just a trendy way to get recruited into an IT job: they are an important venue for open collaboration, civic engagement, and technical experimentation in a social setting.

The name _dribdat_ is an amalgam of "Driven By Data" - with a tip of the hat to [Dribbble](https://dribbble.com/), a famous online community for graphic design which was one of the inspirations at the start of the project. We have organised a lot of hackathons over the years, and started this platform to streamline our own efforts. It is designed with the goal of helping teams - and their facilitators - sustain efforts over time, streamline information channels, and let everyone focus on driving their ideas forward. 

On the front page you can see the upcoming event, as well as any previous events. A short description is followed by a link to the event home page, as well as a countdown of time remaining until the start or finish (if already started) of the event. The Projects, Challenges and Resources are shown on the event home page. Here you can learn about topics, datasets, schedules, get directions and any other vital information that the organizers of the event have provided. Once the event has started, and you have formed a team, you can login and "Share project". 

### How does it work?

Once a team has formed around a Challenge, any of the team members can Post an update, and promote it to Project status. At that point you can see a log of the progress the team is making (encourage them to Post regularly to help track activities), and the latest version of their pitch and documentation. As we will discuss in more detail below, this documentation can come from almost any open Internet source and be embedded on the project page.

Users can use [Markdown](https://en.wikipedia.org/wiki/Markdown) formatting to document their project and customise its display. Projects which are published in a compatible source repository - such as [GitHub](http://github.com/), [Bitbucket](http://bitbucket.com/), or supported wikis - can be auto-synced in dribdat, so that the documentation work can take place in the README's favored by the open source community. You can also update your progress level, in addition to an automatic metric for profile completeness and activity levels, to give each project a progress score. Your team members can subscribe to the project once you have started it, link their public profile in the team roster, and make changes to the data.

At the end of the event, the teams, audience and organizers should have an excellent overview of the work that was done during the event, see the progress of the documentation at a glance, and export data for analysis using the administrative console.

For more user-facing guidance, see the [User's Guide](USAGE.md) and installation instructions in the [README](README.md).

### Schema

One starts an **Event**, to which Challenges (= Ideas) are added. These can take the form of **Projects** (at progress level 0), or **Categories**. A team is made of up of any number of **Users** who have certain organizer-defined **Roles** and have joined a **Project**. **Resources** can be added to a Project by attaching one to a **Post**.

The main models are represented here:

[![](https://mermaid.ink/img/eyJjb2RlIjoiZ3JhcGggVERcbiAgICBFdmVudCAtLS0gUHJvamVjdFxuICAgIFByb2plY3QgLS0tIFVzZXJcbiAgICBQcm9qZWN0IC0tLSBDYXRlZ29yeVxuICAgIFByb2plY3QgLS0tIFByb2dyZXNzXG4gICAgQWN0aXZpdGllcyAtLS0gVXNlciAmIFByb2plY3QgJiBSZXNvdXJjZVxuICAgIFVzZXIgLS0tIFJvbGUiLCJtZXJtYWlkIjp7InRoZW1lIjoiZGVmYXVsdCJ9LCJ1cGRhdGVFZGl0b3IiOmZhbHNlfQ)](https://mermaid-js.github.io/mermaid-live-editor/#/edit/eyJjb2RlIjoiZ3JhcGggVERcbiAgICBFdmVudCAtLS0gUHJvamVjdFxuICAgIFByb2plY3QgLS0tIFVzZXJcbiAgICBQcm9qZWN0IC0tLSBDYXRlZ29yeVxuICAgIFByb2plY3QgLS0tIFByb2dyZXNzXG4gICAgQWN0aXZpdGllcyAtLS0gVXNlciAmIFByb2plY3QgJiBSZXNvdXJjZVxuICAgIFVzZXIgLS0tIFJvbGUiLCJtZXJtYWlkIjp7InRoZW1lIjoiZGVmYXVsdCJ9LCJ1cGRhdGVFZGl0b3IiOmZhbHNlfQ)

What are the differences between a Project and a Challenge?

- A **Challenge** is a problem statement, often with some elaboration of some ideas of how to address it - at a hackathon, this typically involves links to technical tools, datasets, or information resources. In dribdat, these are published in the form of Projects (set to an initial idea/challenge stage) and/or **Categories**.
- A **Project** contains evidence of work that has been done - typically but not always in response to a specific Challenge, as often as possible with links to documentation, source code, presentation, or any other relevant artifacts.

### History

We have built this project to "scratch our own itch". In it's first two years of service, it has supported dozens of events around Switzerland, and become the official hackathon platform of [Opendata.ch](https://opendata.ch) - Swiss chapter of Open Knowledge, the [Open Network Infrastructure Association](https://opennetworkinfrastructure.org/), and others. We have interesting ideas about how to develop the project further, and a supportive community giving us the feedback and means to realize them. 

Easiest of all is to sign up for an upcoming [hackathon](http://hack.opendata.ch/), and try dribdat out as a participant. You can also visit the project's home page for instructions on how to quickly deploy it on your own server and set up your own events. 

dribdat is a responsive Web application written using the Flask framework for Python and Bootstrap. It runs on all major operating systems and databases. Take it for a spin!

### Links / contacts

- Source: [github.com/hackathons-ftw/dribdat](https://github.com/hackathons-ftw/dribdat)
- Website: [dribdat.cc](https://dribdat.cc)
- Discuss: [forum.opendata.ch](https://forum.schoolofdata.ch/search?q=dribdat)

## FAQ

The following questions were compiled as part of the projects [DINAcon nomination](https://dinacon.ch/en/dinacon-awards/nominations/), and last updated on May 5, 2021.

_&gt; How mature is the project?_

Live and production ready.

_&gt; When was the project started?_

November 2015

_&gt; Under which license is your project licensed?_

OSI/FSD-approved free software license (MIT)

_&gt; Does one need to sign a contributor agreement?_

No

_&gt; How many different contributors did contribute to the project within the last 12 months?_

5

_&gt; How many commits did your project receive within the last 12 months? Projects not having a version control system (e.g. Open Data projects or similar) can also specify changesets or similar._

393

_&gt; Was this project forked (split into different communities) in the past or is this project a fork of an other project? Please describe the situation (was it a friendly/unfriendly fork, what was the reason, what is the current state of the projects that are/were involved)._

No

_&gt; If your project is based on a (public) GitLab instance, on Github, on Bitbucket, etc. that offers a metric like "followers" or "likes", what is the metric of your project?_

38 stars, 17 forks

_&gt; Does the community meet in "real life" on a regular base (e.g. yearly, monthly, ...)? How many people do meet at such meetings?_

Yes. We meet at least twice a year at events where we use, and further develop, this platform. There is a small group of people that has directly influenced, and continues to take an interest in, the course of this project. We have several online locations to share updates (notably on [Mattermost](https://team.opendata.ch/signup_user_complete/?id=74yuxwruaby9fpoukx9bmoxday), Discord and Slack).

_&gt; Do you have other metrics that you would like to share with us, which help us to understand how successful your project is?_

Used at 50+ hackathons. The single largest installation has 750+ users.

_&gt; Does your project have a non-coder community e.g. UX designer, translator, marketing, etc.? What kind of non-coder people are involved in your project?_

Yes. Hackathon participations are not just coders, and non-technical users who would like to discover open source activities are an important prerogative for this project. 

_&gt; Does your project offer something like "easy hacks" to make it easy to get a foot into the project?_

Yes, there is a getting started page which can also be customized by the organisers. The process of running creative events like hackathons, combining our experience in code, is something we have aimed to build into all parts of the tool to make the event format accessible to an even wider public. To run your own instance of dribdat, there is an easy to use "deploy to Heroku" button on the GitHub page.

_&gt; Please provide the page where we can find more information about the easy hacks._

For deployment see the [README](README.md)

For usage notes, see [ABOUT](ABOUT.md)

For general guidelines, visit [https://forum.opendata.ch/t/make-the-most-of-hackathon-season/167](https://forum.schoolofdata.ch/t/make-the-most-of-hackathon-season/167)

_&gt; Do you have people mentoring new contributors and actively helping them to get on board of the project?_

Oleg and other people with experience in using the platform are available via various community channels to new users of dribdat. We regularly mentor new users in getting started. There is also a hosted version of the platform which we can set up to get hackathons going quickly.

_&gt; Does your project undertake specific efforts to make sure, that people regardless of ethnicity, gender, etc. can contribute and participate in the project? Does your project for example have a Code of Conduct or is it in general open and friendly to all human beings? Please explain the current situation._

The Hack Code of Conduct, which we have applied to events for the past 3 years, is now in dribdat by default to help facilitate inclusive events.

_&gt; Please describe the business case of your project._

There are hackathons happening all over the world every weekend. Countless more collaborative online "hacking" events happen every day in companies, institutions and the civil society. Each of them generates interest, activity, networking and new initiatives. While several hackathon platforms contend to "lead the market", we are one of a handful of open source alternatives, most notably [HackDash](https://github.com/impronunciable/hackdash/) and [Sparkboard](https://github.com/sparkboard/sparkboard) - which operate in a SaaS model.

Please visit our [OpenCollective](https://opencollective.com/dribdat), where we are currently focusing our fundraising and transparent budgeting.

_&gt; How relevant is your project in regard to a commercial use?_

Currently we accept sponsoring and distribute it within the project, but do not charge a licensing fee of any kind. There is a strong, recurrent interest from companies in using dashboards similar to this one for tracking internal activities above and beyond hackathon-type events. Several commercial models come to mind: the original motivation for the project came out of a hackathon sponsored by Swisscom, a company that champions innovation culture. We are inspired us to pursue an organic and grassroots business model that benefits a wide variety of "start-up" initiatives.

_&gt; This project is important to the world because...._

Hackathons have become a useful instrument to see critically beyond the veil of pragmatic utility in Information Technologies, and have been embraced by the most disruptive companies and organisations around the world as a vehicle for positive change. By imbuing a software project with the ethics and values of hackathons, we can scale these experiments from our local community to many other corners of the world and many domains of creative collaboration.

_&gt; If this project stops its development and ceases to exist, this would be the impact..._

We wouldn't have our own platform to hack the meta-side of hackathons, and that would be a shame. We could go back to using wikis and repo organisations, with all the constraints and loss of user friendliness that entails.

_&gt; Do you have any usage metrics you can provide which show how succesful your project is? (downloads, visits on website, registered users, etc.)_

In addition to the low thousands of user accounts and hundreds of projects across the different installations (these are visible to administrators in the dashboard), many dribdat instances have "open analytics": scroll down to the bottom of the page (for example, on hack.opendata.ch) and click Analytics.
