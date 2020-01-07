This document summarises the current status and makes some vision statements about possible future developments as discussed in [issue #100](https://github.com/datalets/dribdat/issues/100).

For more background and references, see the [User's Guide](USAGE.md) and [README](README.md).

# About Dribdat

[![](https://blog.datalets.ch/workshops/2017/dribdat/dribdat.png)](https://github.com/datalets/dribdat/)

Dribdat (originally from "Driven By Data") is an open source tool for data-driven team collaboration, such as Hackathons. It provides an open source website and project board for running events, and integrates popular community platforms and open source code repositories. It is the official platform of [Opendata.ch hackathons](https://hack.opendata.ch) and has been used to host many other events in the Swiss open data and open source community.

## Screenshots

[![Now.Makezurich.ch](https://blog.datalets.ch/workshops/2017/dribdat/nowmakezurich.jpg)](http://now.makezurich.ch/)

[![Climathon Zürich](https://blog.datalets.ch/workshops/2017/dribdat/climathon.jpg)](https://hack.opendata.ch/event/4)

[![Open Food Hackdays](https://blog.datalets.ch/workshops/2017/dribdat/foodhackdays-openreceipts.jpg)](https://hack.opendata.ch/project/74)     

Using dribdat's API, it is also possible to create a live dashboard, for example for use as Digital Signage at the event:

![](https://blog.datalets.ch/workshops/2017/dribdat/IMG_6910_800.JPG)

*Photo credit: MakeZurich 2018 by Christina Rieder CC BY-SA 4.0*

## Summary

Dribdat is an open source project board designed for splendid collaboration. On Dribdat-powered sites we collect and showcase all projects from a hackathon event in one place. Hackathons are more than just a trendy way to get recruited into an IT job: they are an important venue for open collaboration, civic engagement, and technical experimentation in a social setting.

The name is an amalgam of "Driven By Data" - with a tip of the hat to [Dribbble](https://dribbble.com/), a famous online community for graphic design which was one of the inspirations at the start of the project. We have organised a lot of hackathons over the years, and started this platform to streamline our own efforts. It is designed with the goal of helping hackathon teams - and their facilitators - sustain efforts over time, streamline information channels, and let everyone focus on driving their ideas forward. 

On the front page you can see the upcoming event, as well as any previous events. A short description is followed by a link to the event home page, as well as a countdown of time remaining until the start or finish (if already started) of the hackathon. The Projects, Challenges and Resources are shown on the event home page. Here you can learn about topics, datasets, schedules, get directions and any other vital information that the organizers of the event have provided. Once the event has started, and you have formed a team, you can login and "Share project". 

Users can use [Markdown](https://en.wikipedia.org/wiki/Markdown) formatting to document their project and customise its display. Projects which are published in a compatible source repository - such as [GitHub](http://github.com/), [Bitbucket](http://bitbucket.com/), or supported wikis - can be auto-synced in Dribdat, so that the documentation work can take place in the README's favored by the open source community. You can also update your progress level, in addition to an automatic metric for profile completeness and activity levels, to give each project a progress score. Your team members can subscribe to the project once you have started it: their public profile will then be linked to it, and they will also be able to make changes to the project data.

We have built this project to "scratch our own itch". In it's first two years of service, it has supported dozens of events around Switzerland, and become the official hackathon platform of Opendata.ch and the Open Network Infrastructure Association. We have lots of interesting ideas about how to develop the project further, and need some support and feedback to realize them. 

Easiest of all is to sign up for an upcoming [hackathon](http://hack.opendata.ch/), and try Dribdat out as a participant. You can also visit the project's home page for instructions on how to quickly deploy it on your own server and set up your own events. 

Dribdat is a Web application written using the Flask framework for Python and Bootstrap. It runs on all major operating systems and databases. Looking forward to your contribution!

### Links / contacts

- Source: [github.com/datalets/dribdat](https://github.com/datalets/dribdat)
- Website: [datalets.ch/dribdat](https://datalets.ch/dribdat)
- Discuss:  [forum.schoolofdata.ch](https://forum.schoolofdata.ch/search?q=dribdat)

## FAQ

The following questions were asked at the [DINAcon](https://dinacon.ch/dinacon-awards/) 2017 nomination submissions.

_&gt; How mature is the project?_

Live and production ready.

_&gt; When was the project started?_

November 2015

_&gt; Under which license is your project licensed?_

OSI/FSD-approved free software license (MIT)

_&gt; Does one need to sign a contributor agreement?_

No

_&gt; How many different contributors did contribute to the project within the last 12 months?_

1

_&gt; How many commits did your project receive within the last 12 months? Projects not having a version control system (e.g. Open Data projects or similar) can also specify changesets or similar._

268

_&gt; Was this project forked (splitted into different communities) in the past or is this project a fork of an other project? Please describe the situation (was it a friendly/unfriendly fork, what was the reason, what is the current state of the projects that are/were involved)._

No

_&gt; If your project is based on a (public) GitLab instance, on Github, on Bitbucket, etc. that offers a metric like "followers" or "likes", what is the metric of your project?_

9 stars, 4 forks

_&gt; Does the community meet in "real life" on a regular base (e.g. yearly, monthly, ...)? How many people do meet at such meetings?_

Yes. We meet at least twice a year at hackathons where we use, and further develop, this platform. I can think of at least 5 people who have directly influenced, and continue to take an interest in, the course of this project.

_&gt; Do you have other metrics that you would like to share with us, which help us to understand how successful your project is?_

Used at 10+ hackathons. The single largest installation has 150+ users.

_&gt; Does your project have a non-coder community e.g. UX designer, translator, marketing, etc.? What kind of non-coder people are involved in your project?_

Yes. Hackathon participations are not just coders, and non-technical users who would like to discover open source activities are an important prerogative for this project. 

_&gt; Does your project offer something like "easy hacks" to make it easy to get a foot into the project?_

Yes, there is a getting started page which can also be customized by the hackathon organisers. The process of running hackathons itself, combining our experience in code, is something we have aimed to build into all parts of the tool to make the event format accessible to an even wider public. To run your own instance of Dribdat, there is an easy to use "deploy to Heroku" button on the GitHub page.

_&gt; Please provide the page where we can find more information about the easy hacks._

For deployment see [https://github.com/datalets/dribdat](https://github.com/datalets/dribdat)

For usage notes, see [https://hack.opendata.ch/about/](https://hack.opendata.ch/about/)

For general guidelines, visit [https://forum.schoolofdata.ch/t/make-the-most-of-hackathon-season/167](https://forum.schoolofdata.ch/t/make-the-most-of-hackathon-season/167)

_&gt; Do you have people mentoring new contributors and actively helping them to get on board of the project?_

Oleg and other people at Opendata.ch with experience in using the platform are available via various community channels to new users of Dribdat. We regularly mentor new users in getting started. There is also a hosted version of the platform which we can set up to get hackathons going quickly.

_&gt; Does your project undertake specific efforts to make sure, that people regardless of ethnicity, gender, etc. can contribute and participate in the project? Does your project for example have a Code of Conduct or is it in general open and friendly to all human beings? Please explain the current situation._

No. But I think that would be a terrific idea, and have recently discussed this with colleagues. In fact, I think a Code of Conduct should be built into Dribdat to help facilitate inclusive events.

_&gt; Please describe the business case of your project. _

There are hackathons happening all over the world every weekend. Each of them generates interest, activity, networking and new initiatives. There is still no "market leading" open source hackathon platform board. Several services similar to Dribdat, most notably HackDash and Sparkboard, operate in a SaaS model. There is also strong, recurrent interest from companies in using dashboards similar to this one for tracking internal activities above and beyond hackathon-type events. Several business models come to mind leveraging the experience of deploying Dribdat. Indeed, the original motivation for the project came out of a hackathon sponsored by Swisscom, a champion of innovation culture.

_&gt; How relevant is your project in regard to a commercial use?_

We accept sponsoring and distribute it within the project

_&gt; This project is important to the world because...._

Hackathons are becoming a critical instrument to seeing beyond the veil of pragmatic utility in Information Technologies, and have been embraced by the most disruptive companies and organisations around the world as a vehicle for positive change. By imbuing a software project with the ethics and values of hackathons, we can scale these experiments from our local community to many other corners of the world.

_&gt; If this project stops its development and ceases to exist, this would be the impact..._

We wouldn't have our own platform to hack the meta-side of hackathons, and that would be a shame. We would probably go back to using wikis and repo organisations, with all the constraints and loss of user friendliness that entails.

_&gt; Do you have any usage metrics you can provide which show how succesful your project is? (downloads, visits on website, registered users, etc.)_

There are about 200 user accounts and over 250 projects across the different installations known to me.
