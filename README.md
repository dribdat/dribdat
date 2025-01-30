![Github Actions build status](https://github.com/dribdat/dribdat/workflows/build/badge.svg)
[![codecov status](https://codecov.io/gh/dribdat/dribdat/branch/main/graph/badge.svg?token=Ccd1vTxRXg)](https://codecov.io/gh/dribdat/dribdat)
[![FOSSA status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Floleg%2Fdribdat.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Floleg%2Fdribdat?ref=badge_shield)

# Dribdat

**An open source hackathon management application that playfully assists your team in crowdsourcing technical designs. See [Tour de Hack](https://dribdat.cc/tour) for more examples, and our [User handbook](https://dribdat.cc/usage) for screenshots.**

🏳️‍🌈 We aim to include people of all backgrounds in using and developing this tool - no matter your age, gender, race, ability, or sexual identity. See our [Contributor Covenant Code of Conduct](code_of_conduct.md), and visit the [HackIntegration Hackfinder](https://hackintegration.ch/hackfinder) to discover events connected to our ongoing research & development in this area.

🏔️ We keep an active mirror on [Codeberg](https://codeberg.org/dribdat) 

🩵 Please support the project on [OpenCollective](https://opencollective.com/dribdat/updates) 

<a href="https://opencollective.com/dribdat/donate" target="_blank"><img src="https://opencollective.com/dribdat/donate/button@2x.png?color=blue" width=300 /></a>

# Purpose

Created in light of the [Hacker ethic](https://en.wikipedia.org/wiki/Hacker_ethic), the philosophy of `d}}BD{t` is (in a nutshell):

- **Commit sustainably**: aggregate results in standard web data formats for search and archiving.
- **Go live and let live**: efficiently deploy designs, dev envs, docs accessible to your entire team.
- **Co-create in safe spaces**: with content and tools promoting safer conduct and increased privacy.

Designed to bootstrap your [awesome hackathon](https://github.com/dribdat/awesome-hackathon), Dribdat's toolset can be used as a versatile toolbox for civic tech sprints. To get started, [install](#Quickstart) the software, or try it yourself at the next [community event](https://schoolofdata.ch). 

For more background and references, see the [User Handbook](https://docs.dribdat.cc/usage), or read the [Whitepaper](https://dribdat.cc/whitepaper). If you need help or advice in setting up your site, or would like to contribute to the project: please get in touch via [Discussions](https://github.com/orgs/dribdat/discussions) or [GitHub Issues](https://github.com/dribdat/dribdat/issues).

# Quickstart

The Dribdat project can be deployed to any server capable of serving [Python](https://python.org) applications, and is set up for fast deployment using [Ansible or Docker](https://dribdat.cc/deploy). The first user that registers becomes an admin, so don't delay!

If you would like to run dribdat on any other cloud or local machine, there are additional instructions in the [Deployment guide](https://docs.dribdat.cc/deploy). Information on contributing and extending the code can be found in the [Contributors guide](https://docs.dribdat.cc/contribute), which includes API documentation, and other details.

See also **[backboard](https://github.com/dribdat/backboard)**: a responsive, modern alternative frontend, and our **[dridbot](https://github.com/dribdat/dridbot)** chat client. Both demonstrate reuse of the dribdat API.

If you need support with your deployment, please reach out through [Discussions](https://github.com/orgs/dribdat/discussions).

# Credits

This application was based on [cookiecutter-flask](https://github.com/sloria/cookiecutter-flask) by [Steven Loria](https://github.com/sloria), a more modern version of which is [cookiecutter-flask-restful](https://github.com/karec/cookiecutter-flask-restful). [Cookiecutter](https://cookiecutter.readthedocs.io/en/stable/README.html#available-templates) could also be a good bootstrap for your own hackathon projects!

Currently mantained by [@loleg](https://github.com/loleg) and [Contributors](https://github.com/dribdat/dribdat/graphs/contributors) and [Forks](https://github.com/dribdat/dribdat/network/members) to find other users of this project ♡ Sincere thanks to the [Open Data](https://opendata.ch), [Open Networking](https://opennetworkinfrastructure.org/) and [Open Source](https://dinacon.ch) communities in 🇨🇭 Switzerland for the many trials and feedbacks through over three hundred events.

Additional and ♥-felt thanks for your contributions to: F. Wieser and M.-C. Gasser at [Swisscom](http://swisscom.com) for support at an early stage of this project, to [Alexandre Cotting](https://github.com/Cotting), [Anthony Ritz](https://github.com/RitzAnthony), [Chris Mutel](https://github.com/cmutel), [Fabien Schwob](https://github.com/jibaku), [Gonzalo Casas](https://github.com/gonzalocasas), [Janik von Rotz](https://janikvonrotz.ch/), [Jonathan Schnyder](https://github.com/jonHESSO), [Jonathan Sobel](https://github.com/JonathanSOBEL), [Philip Shemella](https://github.com/philshem), [Thomas Amberg](https://github.com/tamberg), [Yusuf Khasbulatov](https://github.com/khashashin) .. and all participants and organizers sending in bugs and requests! 🤗 This humongous badge of honor is for you:

![](dribdat/static/img/logo/logo13.png)

## License

This project is open source under the [MIT License](LICENSE).

The [Contributor Covenant Code of Conduct](code_of_conduct.md) applies to interactions with the maintainers and support community of the project.

Due to the use of the [boto3](https://github.com/boto/boto3/) library for optional S3 upload support, there is a dependency on OpenSSL via awscrt. If you use these features, please note that the product includes cryptographic software written by Eric Young (eay@cryptsoft.com) and Tim Hudson (tjh@cryptsoft.com).
