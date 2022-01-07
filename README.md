# dribdat

![Github Actions build](https://github.com/dribdat/dribdat/workflows/build/badge.svg)
[![codecov](https://codecov.io/gh/dribdat/dribdat/branch/main/graph/badge.svg?token=Ccd1vTxRXg)](https://codecov.io/gh/dribdat/dribdat)
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Floleg%2Fdribdat.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Floleg%2Fdribdat?ref=badge_shield)
[![Mattermost](https://img.shields.io/badge/Mattermost-chat-blue.svg)](https://team.opendata.ch/signup_user_complete/?id=74yuxwruaby9fpoukx9bmoxday)
<object type="image/svg+xml" data="https://opencollective.com/dribdat/tiers/backer.svg?avatarHeight=36&width=600"></object>

### Tools for time-limited, team-based, data-driven, open collaboration

`dribdat` is an open source web platform for data-driven team collaboration. Designed for hackathons, it is a Swiss Army Knife of everything you need for your event: a website, countdown clock and challenge board, project log and progress tracker, integrations with popular chat platforms and code repositories, open data support and APIs.

For more background and references, see the [Usage Guide](docs/USAGE.md) and [About Page](docs/ABOUT.md). If you need help or advice in setting up your event, or would like to contribute to the project: please get in touch via [GitHub Issues](https://github.com/dribdat/dribdat/issues) or [website](https://dribdat.cc).

![](dribdat/static/img/screenshot_sandbox.png)

_Screenshot of a dribdat event page._

# Quickstart

This project can be deployed to any server capable of serving Python applications, and is set up for fast deployment using [Docker](https://github.com/dribdat/dribdat/blob/main/docs/DEPLOY.md#with-docker) or to the [Heroku](http://heroku.com) cloud:

[![Deploy with Heroku](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy)

The first user that registers becomes an admin, so don't delay! If you would like to run dribdat on any other cloud or local machine, there are additional instructions in the [Deployment guide](docs/DEPLOY.md).

Information on contributing and extending dribdat, as well as running it on your local machine, can be found in the [Developer guide](docs/CONTRIBUTE.md) which includes API documentation and more. See also [dridbot](https://github.com/dribdat/dridbot), our chatbot project.

If you need support with your deployment, please reach out through our website https://dribdat.cc

# Credits

See [Contributors](https://github.com/dataletsch/dribdat/graphs/contributors) for a list of people who have made changes to the code, and [Forks](https://github.com/dataletsch/dribdat/network/members) to find other users of this project.

This project is currently mantained by [@loleg](https://github.com/loleg) and [@gonzalocasas](https://github.com/gonzalocasas). You can chat with us on Mattermost, linked to the badge at the top of this README.

Special thanks to the [Open Data](https://opendata.ch), [Open Networking](https://opennetworkinfrastructure.org/) and [Open Source](https://dinacon.ch) communities in Switzerland for the many trials and feedbacks. We are also grateful to F. Wieser and M.-C. Gasser at [Swisscom](http://swisscom.com) for conceptual inputs and financial support at an early stage of this project. This code is originally based on Steven Loria's [flask-cookiecutter](https://github.com/sloria/cookiecutter-flask), which we of course encourage you to use in YOUR next project!

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


## License

This project is open source under the [MIT License](LICENSE).

Due to the use of the [boto3](https://github.com/boto/boto3/) library for S3 support, there is a dependency on OpenSSL via awscrt. If you use these features, please note that the product includes cryptographic software written by Eric Young (eay@cryptsoft.com) and Tim Hudson (tjh@cryptsoft.com).
