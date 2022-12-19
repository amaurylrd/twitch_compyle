🎉🎉 Thank you so much for taking the time to contribute. Any contributions you make are **greatly appreciated** 🎉🎉

## Contributing

Development of `twitch_compyle` happens at https://github.com/amaurylrd/twitch_compyle/tree/main.
<br><br>
&rarr; For contributing to this project please contact us via GitHub or by mail <br>

1. Create a new **fork** of the project
2. Create your feature **branch**
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


## Continous Integration

### Code Formatting

> Keep it clean, keep it clear

In poetry shell you can run linters that are implemented as poetry dependecies like pylama, black...

```sh
black compyle/<path_to_directory_or_file>
pylama compyle/<path_to_directory_or_file>
```

TODO git squash, 

```sh
git commit --amend
git push --force
```
```sh
git rebase -i <hash_of_commit> or git rebase -i HEAD~4
git push origin HEAD:<name_of_remote_branch> --force
```
Make sure the topmost, first commit says “pick” and change the rest below from “pick” to “squash”. This will squash each commit into the previous commit, which will continue until every commit is squashed into the first commit.
in git editor


changelog https://github.com/othneildrew/Best-README-Template/blob/master/CHANGELOG.md