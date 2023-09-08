<!-- markdownlint-disable MD029 MD041 -->
🎉🎉 Thank you so much for taking the time to contribute. Any contributions you make are **greatly appreciated** 🎉🎉

## Contributing

Development of `twitch_compyle` happens at <https://github.com/amaurylrd/twitch_compyle/tree/main>.
<br><br>
&rarr; One way of contributing to this project is to contact us via GitHub or by mail <br>
&rarr; Another way is to make a merge request:

1. Create a new **fork** of the project
2. Create your feature **branch**

```sh
git checkout -b feat/AwesomeFeature
```

3. Add then **commit** your changes

```sh
git add *
git commit -m "feat(moviepy): add some awesome new feature"
```

4. **Push** to the branch

```sh
git push origin feat/AwesomeFeature
```

5. Open a **pull request**

&rarr; If you have any suggestions, bug reports please report them to the issue tracker at <https://github.com/amaurylrd/twitch_compyle/issues>


### Contributing Policy

#### Code Formatting

In poetry shell you can run specific linters that are implemented as poetry dependencies like pylama and black:

```sh
pylama compyle/
black compyle/
```

https://github.com/zeke/semantic-release-with-github-actions
https://github.com/angular/angular.js/blob/master/DEVELOPERS.md#commits

You are also strongly encouraged to keep the git trace as clean as possible with for example consice commits that are expected to start with one in feature, bugfix, update, release, or anything that gives a short and comprehensible hint on the content, even for small additions.

You can also make use of the provided git commands, such as **squashing** (with ``git rebase``) or **amending** (with ``git commit --amend --no-edit``).

To make an audit of the code before submitting a commit, you can run the [pre-commit hooks](../../.pre-commit-config.yaml). To invoke those checks on every commit run:

```sh
pre-commit install
```

If you want to run the checks on-demand (outside of git hooks), run:

```sh
pre-commit run --all-files --verbose
```

#### Continuous Integration

-> pipeline travis TODO
