# twitch_compyle 


## Keywords 

APIs, Twitch, Youtube, clips, video editing...

## Requierements

1. Python at least 3.10
   
2. Poetry any stable version like 1.2.2 (requires Python 3.7 and above). <br>
https://python-poetry.org/docs/#installation

3. ImageMagick <br>
https://imagemagick.org/script/download.php 

> Once you have installed it, ImageMagick will be automatically detected by MoviePy, except for some developpers like windows users, thus make sure to check _"install legacy utilities"_ in the installation wizard. You may also set the variable _IMAGEMAGICK_BINARY_ from the moviepy/config_defaults.py file

> MoviePy depends on the Python modules Numpy, imageio, Decorator, and tqdm, which will be automatically installed during MoviePy’s installation but MoviePy also need additional common libraries like PIL, FFMPEG for specific usage...

## Getting started

### Installation

1. Clone the repository

```sh 
git clone https://github.com/amaurylrd/twitch_compyle.git
cd twitch_compyle
```

2. Checkout the branch

### Setup

To setup this project, install the dependencies using poetry like so:

```sh 
poetry lock
poetry install
```
### Run

To run the project, run the following command in a poetry shell:

```sh 
python sources/main.py
```

## Continous Integration

### Code Formatting

> Keep it clean, keep it clear

In poetry shell you can run linters that are implemented as poetry dependecies like pylama, black...

```py
black compyle/<path_to_directory_or_file>
pylama compyle/<path_to_directory_or_file>
```

## Contributing

Development of `twitch_compyle` happens at https://github.com/amaurylrd/twitch_compyle/tree/main.
<br><br>
&rarr; For contributing to this project please contact us via GitHub or by mail <br>

1. Create a new **fork** of the project
2. Create your feature branch
```sh
git checkout -b feature/AwesomeFeature
```
3. Add then **commit** your changes
```sh
git add *
git commit -m "add some awesome feature"
```
4. **Push** to the branch
```sh
git push origin feature/AwesomeFeature
```
5. Open a **pull request**

&rarr; If you have any suggestions, bug reports please report them to the issue tracker at https://github.com/amaurylrd/twitch_compyle/issues

## Contact 
  
Tho we like postcards, we prefer emails : [@adesvall](https://github.com/adesvall), [@amaurylrd](https://github.com/amaurylrd), [@BOOOYAA](https://github.com/BOOOYAA)

## License

See the [LICENSE](/LICENSE) file for licensing information

<br>

And don't forget to give the project a star! :star: