
Run pre-commit install to install pre-commit into your git hooks. pre-commit will now run on every commit. Every time you clone a project using pre-commit running pre-commit install should always be the first thing you do.

If you want to manually run all pre-commit hooks on a repository, run pre-commit run --all-files. To run individual hooks use pre-commit run <hook_id>.

The first time pre-commit runs on a file it will automatically download, install, and run the hook. Note that running a hook for the first time may be slow.


> Installer ci renovate

> FIX pylama in ci max_lengt_line

> FINIR markdowns documentation

> MAYBE ajouter un linter de markdown

TODO in his own file

### User Interface Usage

argparse is a full command-line argument parser tool

> logging

TODO in his own file

# Logging

le fichier d'ouput des log, par default sortie standard
filename avec la date
logging.basicConfig(level=logging.DEBUG, filename="logfile", filemode="w+", format="%(asctime)-15s %(levelname)-8s %(message)s")
add ce fichier dans le gitignore

> FIX mongoDB

> FEAT tests
<https://stackoverflow.com/questions/3942820/how-to-do-unit-testing-of-functions-writing-files-using-pythons-unittest>
<https://github.com/mongomock/mongomock>

> FEAT edit

> FEAT edit thumbnail

> FEAT publish

> FEAT pydoc

> FIX release

> FIX publish
faire une action et la rendre manuelle
<https://dev.to/this-is-learning/manually-trigger-a-github-action-with-workflowdispatch-3mga>

> FEAT ci test Run unit tests and collect coverage
