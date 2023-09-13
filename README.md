<!-- markdownlint-disable MD029 MD041 MD042 MD045 -->

v0.0.1 [![License][license-bullet]][license-url] [![][status-bullet]][status-url] [![][status-bullet]][t]

[status-bullet]: https://github.com/amaurylrd/twitch_compyle/actions/workflows/.github-ci.yaml/badge.svg?branch=main
[status-url]: .github/workflows/.github-ci.yaml

[license-bullet]: https://img.shields.io/badge/License-Apache_2.0-blue.svg
[license-url]: https://opensource.org/licenses/Apache-2.0

[t]: https://github.com/amaurylrd/twitch_compyle/actions/workflows/.github-ci.yaml
# $${Com \color{red} py \color{black} le}$$

## Keywords

APIs, Twitch, Youtube, MoviePy, OpenCV, MongoDB...

![](.github/docs/media/twitch-youtube-logo-banner.jpg)

## Requirements

1. Python, at least 3.10

2. Poetry, any stable version since 1.2 but idealy requires 1.3 or above <br>
<https://python-poetry.org/docs/#installation>

1. ImageMagick <br>
<https://imagemagick.org/script/download.php>

:warning: Once you have installed it, ImageMagick should be automatically detected by MoviePy, except for some developers under specific OS:

- for **windows users**, you may also set the variable _IMAGEMAGICK_BINARY_ from the moviepy config file. To avoid doing so, make sure to check _"install legacy utilities"_ in the installation wizard.

- for **ubuntu users (≥ 19.04)**, you may have installed from [apt://imagemagick]() (or via the apt install command line), then you need to disable this line ``<policy domain="path" rights="none" pattern="@*"/>`` from the security policy file located at ``/etc/ImageMagick/policy.xml``.

> MoviePy additionally depends on the Python modules Numpy, imageio, Decorator, and tqdm, which will be automatically installed during MoviePy’s installation but it also needs extra common libraries like PIL, FFMPEG for specific usecases...

## Getting started

### Installation

1. **Clone** the repository

```sh
git clone https://github.com/amaurylrd/twitch_compyle.git
cd twitch_compyle/
```

2. **Checkout** the main branch

### Setup

To setup this project, install the dependencies using poetry like so:

```sh
poetry lock
poetry install --sync
```

Secondly refer to the [configuration guide](.github/docs/CONFIGURATION.md) for a documentated overview on how to configure the ``.env`` file.

### Run

To run the project and list the possible sub-commands, run the following command in a poetry shell:

```sh
python sources/main.py -h
```

## Getting addicted

### 🚧 Contribution

If you are interested in the project, check the [development manual](.github/docs/CONTRIBUTING.md).
Please review this guide for further information on how to get started on the project for developers and contributors.

### 📫 Contact

Tho we like postcards, we prefer emails : [@adesvall](https://github.com/adesvall), [@amaurylrd](https://github.com/amaurylrd) (owner), [@thomasabreudias](https://github.com/ThomasAbreuDias)

## License

See the [LICENSE](/LICENSE) file for licensing information

<br>

And don't forget to give the project a star! :star:
