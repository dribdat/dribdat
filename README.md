# dribdat

![Github Actions build](https://github.com/dribdat/dribdat/workflows/build/badge.svg)
[![codecov](https://codecov.io/gh/dribdat/dribdat/branch/main/graph/badge.svg?token=Ccd1vTxRXg)](https://codecov.io/gh/dribdat/dribdat)
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Floleg%2Fdribdat.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Floleg%2Fdribdat?ref=badge_shield)

### Tools for time-limited, team-based, open-by-default collaboration

`dribdat` is an open source web platform for team collaboration online and offline. Originally designed to promote and support open data expeditions and [awesome hackathons](https://github.com/dribdat/awesome-hackathon). It is akin to a Swiss Army Knife for event organizers: a website, guidelines, countdown clock, challenge board, project log, progress tracker, integrations with popular chat platforms, code repositories and open data APIs. The philosophy of this project, in a nutshell, is: **live and let live** (no tech religion, use whatever design / dev / doc tools you want as long as they are accessible to your team), **commit sustainably** (aggregate outputs in standard web of data formats for optimal search and archiving), **create in safe spaces** (embedded code of conduct, works offline, minimal privacy footprint).

For more background and references, see the [User Handbook](https://docs.dribdat.cc/usage/). If you need help or advice in setting up your event, or would like to contribute to the project: please get in touch via [GitHub Issues](https://github.com/dribdat/dribdat/issues) or [website](https://dribdat.cc). 

![Screenshot of dribdat](dribdat/static/img/screenshot_sandbox.png)

Follow and support the project's development on [OpenCollective](https://opencollective.com/dribdat/updates).

<a href="https://opencollective.com/dribdat/donate" target="_blank"><img src="https://opencollective.com/dribdat/donate/button@2x.png?color=blue" width=300 /></a>

# Quickstart

This project can be deployed to any server capable of serving Python applications, and is set up for fast deployment using [Docker](https://github.com/dribdat/dribdat/blob/main/docs/DEPLOY.md#with-docker). The first user that registers becomes an admin, so don't delay! 

If you would like to run dribdat on any other cloud or local machine, there are additional instructions in the [Deployment guide](https://docs.dribdat.cc/deploy/). Information on contributing and extending dribdat can be found in the [Developer guide](https://docs.dribdat.cc/contribute/), which includes API documentation and more.

See also **[backboard](https://github.com/dribdat/backboard)**, a sample responsive web application, and our **[dridbot](https://github.com/dribdat/dridbot)** chat client, which both demonstrate reuse of the dribdat API.

If you need support with your deployment, please reach out through Issues or the contact form on our website: [dribdat.cc](https://dribdat.cc)

# Credits

This project is currently mantained by [@loleg](https://github.com/loleg). See [Contributors](https://github.com/dataletsch/dribdat/graphs/contributors) for a full list of people who have helped us with the code, and [Forks](https://github.com/dataletsch/dribdat/network/members) to find other users of this project.

Special thanks to the [Open Data](https://opendata.ch), [Open Networking](https://opennetworkinfrastructure.org/) and [Open Source](https://dinacon.ch) communities in Switzerland for the many trials and feedbacks. We are also grateful to F. Wieser and M.-C. Gasser at [Swisscom](http://swisscom.com) for conceptual inputs and financial support at an early stage of this project.

This code is originally based on Steven Loria's [cookiecutter-flask](https://github.com/sloria/cookiecutter-flask). A more modern version of which is [cookiecutter-flask-restful](https://github.com/karec/cookiecutter-flask-restful).

Additional and :heart:-felt thanks for testing and feedback to:

- [Alexandre Cotting](https://github.com/Cotting)
- [Anthony Ritz](https://github.com/RitzAnthony)
- [Chris Mutel](https://github.com/cmutel)
- [Fabien Schwob](https://github.com/jibaku)
- [Jonathan Sobel](https://github.com/JonathanSOBEL)
- [Thomas Amberg](https://github.com/tamberg)
- [@jonhesso](https://github.com/jonHESSO)
- [@khashashin](https://github.com/khashashin)
- [@philshem](https://github.com/philshem)

.. and all the hackathon contributors!

## License

This project is open source under the [MIT License](LICENSE).

Due to the use of the [boto3](https://github.com/boto/boto3/) library for S3 support, there is a dependency on OpenSSL via awscrt. If you use these features, please note that the product includes cryptographic software written by Eric Young (eay@cryptsoft.com) and Tim Hudson (tjh@cryptsoft.com).
