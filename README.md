<!-- markdownlint-disable MD029 MD041 MD042 MD045 -->

[![Build Status](https://app.travis-ci.com/amaurylrd/twitch_compyle.svg?token=8zCbm6e8xiaKAE2XXKzm&branch=main)](https://app.travis-ci.com/amaurylrd/twitch_compyle)[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# twitch_compyle

## Keywords

APIs, Twitch, Youtube, MoviePy, OpenCV...

![](https://www.minuitdouze.com/wp-content/uploads/twitch-youtube-logo-banner.jpg)

## Requierements

1. Python, at least 3.8

2. Poetry, any stable version since 1.2 but idealy requires 1.3 or above <br>
<https://python-poetry.org/docs/#installation>

1. ImageMagick <br>
<https://imagemagick.org/script/download.php>

:warning: Once you have installed it, ImageMagick should be automatically detected by MoviePy, except for some developpers under specific OS:

- for **windows users**, you may also set the variable _IMAGEMAGICK_BINARY_ from the moviepy config file. To avoid doing so, make sure to check _"install legacy utilities"_ in the installation wizard.
  
- for **ubuntu users (≥ 19.04)**, you may have installed from [apt://imagemagick]() (or via the apt install command line), then you need to disable this line ``<policy domain="path" rights="none" pattern="@*"/>`` from the security policy file located at ``/etc/ImageMagick/policy.xml``.

> MoviePy additionally depends on the Python modules Numpy, imageio, Decorator, and tqdm, which will be automatically installed during MoviePy’s installation but it also needs extra common libraries like PIL, FFMPEG for specific usecases...

## Getting started

### Installation

1. **Clone** the repository

```sh
git clone https://github.com/amaurylrd/twitch_compyle.git
cd twitch_compyle
```

2. **Checkout** the main branch

### Setup

To setup this project, install the dependencies using poetry like so:

```sh
poetry lock
poetry install --sync
```

Secondly refer to the [configuration guide](/CONFIGURATION.md) for a documentated overview on how to configure the ``.env`` file.

### Run

To run the project, run the following command in a poetry shell:

```sh
python sources/main.py
```

## Getting addicted

### 🚧 Contribution

If you are intrested in the project, check the [development manual](/DEVELOPMENT.md).
Please review this guide for further information on how to get started on the project for developpers and contributors.

### 📫 Contact
  
Tho we like postcards, we prefer emails : [@adesvall](https://github.com/adesvall), [@amaurylrd](https://github.com/amaurylrd) (owner), [@thomasabreudias](https://github.com/ThomasAbreuDias)

## License

See the [LICENSE](/LICENSE) file for licensing information

<br>

And don't forget to give the project a star! :star:
