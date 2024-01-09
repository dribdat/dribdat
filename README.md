![Github Actions build status](https://github.com/dribdat/dribdat/workflows/build/badge.svg)
[![codecov status](https://codecov.io/gh/dribdat/dribdat/branch/main/graph/badge.svg?token=Ccd1vTxRXg)](https://codecov.io/gh/dribdat/dribdat)
[![FOSSA status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Floleg%2Fdribdat.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Floleg%2Fdribdat?ref=badge_shield)

## Tools for time-limited, team-based, open-by-default collaboration

`dribdat` is an open source web application that assists teams working playfully on projects with data. Designed to support [awesome hackathons](https://github.com/dribdat/awesome-hackathon) and promote [data expeditions](https://schoolofdata.ch), it is a 🇨🇭 Swiss Army Knife for Civic Tech: your events, guidelines, count-downs, challenge board, project log, progress tracker, integrating with prototyping tools, group chat, code repositories, open data APIs, and more!

![Dribdat Logo](dribdat/static/img/logo12_128x128.png)

The philosophy of this project, in a nutshell, is: **live and let live** (no tech religion, use whatever design / dev / doc tools you want as long as they are accessible to your team), **commit sustainably** (aggregate outputs in standard web of data formats for optimal search and archiving), **create in safe spaces** (embedded code of conduct, works offline, minimal privacy footprint). 

[Install](https://dribdat.cc/deploy) the software, read our [Whitepaper](https://dribdat.cc/whitepaper), or try dribdat yourself at a [community](https://forum.opendata.ch/c/expeditions/hackathons/16/l/latest) hackathon.

![Screenshot of a Dribdat instance](https://dribdat.cc/images/glamhack.jpg)
<br><small><i>A screenshot of an event page in Dribdat.</i></small>

For more background and references, see the [User Handbook](https://docs.dribdat.cc/usage). If you need help or advice in setting up your event, or would like to contribute to the project: please get in touch via [Discussions](https://github.com/orgs/dribdat/discussions) or [GitHub Issues](https://github.com/dribdat/dribdat/issues). You can follow and support the project on [OpenCollective](https://opencollective.com/dribdat/updates) or [Codeberg](https://codeberg.org/dribdat)

<a href="https://opencollective.com/dribdat/donate" target="_blank"><img src="https://opencollective.com/dribdat/donate/button@2x.png?color=blue" width=300 /></a>

_If you use Dribdat, please add yourself to the [Tour de Hack](https://meta.dribdat.cc/event/5)! It only takes a minute, and knowing this helps keep the 🔥 alive._

# Quickstart

The dribdat project can be deployed to any server capable of serving [Python](https://python.org) applications, and is set up for fast deployment using [Ansible or Docker](https://dribdat.cc/deploy). The first user that registers becomes an admin, so don't delay! 

If you would like to run dribdat on any other cloud or local machine, there are additional instructions in the [Deployment guide](https://docs.dribdat.cc/deploy). Information on contributing and extending the code can be found in the [Contributors guide](https://docs.dribdat.cc/contribute), which includes API documentation, and other details.

See also **[backboard](https://github.com/dribdat/backboard)**: a responsive, modern alternative frontend, and our **[dridbot](https://github.com/dribdat/dridbot)** chat client. Both demonstrate reuse of the dribdat API.

If you need support with your deployment, please reach out through [Discussions](https://github.com/orgs/dribdat/discussions).

# Credits

This project is currently mantained by [@loleg](https://github.com/loleg). See [Contributors](https://github.com/dataletsch/dribdat/graphs/contributors) and [Forks](https://github.com/dataletsch/dribdat/network/members) to find other users of this project.

Special thanks to the [Open Data](https://hack.opendata.ch), [Open Networking](https://now.makezurich.ch/) and [Open Source](https://hacknight.dinacon.ch) communities in Switzerland for the many trials and feedbacks through over one hundred events.

This project is inspired by the work of many wonderful hackathonistas to the [East](https://meta.dribdat.cc/project/42), [West](https://meta.dribdat.cc/project/7), [North](https://meta.dribdat.cc/project/10), and [South](https://meta.dribdat.cc/project/41) of here. We are grateful to F. Wieser and M.-C. Gasser at [Swisscom](http://swisscom.com) for conceptual inputs and financial support at an early stage of this project. This application was based on Steven Loria's [cookiecutter-flask](https://github.com/sloria/cookiecutter-flask), a more modern version of which is [cookiecutter-flask-restful](https://github.com/karec/cookiecutter-flask-restful) - and could be a good basis for your own hackathon projects. 

Additional and ♥-felt thanks for your contributions to: [Alexandre Cotting](https://github.com/Cotting), [Anthony Ritz](https://github.com/RitzAnthony), [Chris Mutel](https://github.com/cmutel), [Fabien Schwob](https://github.com/jibaku), [Gonzalo Casas](https://github.com/gonzalocasas), [Jonathan Schnyder](https://github.com/jonHESSO), [Jonathan Sobel](https://github.com/JonathanSOBEL), [Philip Shemella](https://github.com/philshem), [Thomas Amberg](https://github.com/tamberg), [Yusuf Khasbulatov](https://github.com/khashashin) .. and all the participants and organizers sending in bugs and requests! 🤗

## License

This project is open source under the [MIT License](LICENSE).

Due to the use of the [boto3](https://github.com/boto/boto3/) library for S3 support, there is a dependency on OpenSSL via awscrt. If you use these features, please note that the product includes cryptographic software written by Eric Young (eay@cryptsoft.com) and Tim Hudson (tjh@cryptsoft.com).
