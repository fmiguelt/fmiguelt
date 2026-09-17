# fmiguelt.github.io

Landing page at <https://fmiguelt.github.io> listing every GitHub Pages site in
this account.

`index.html` is generated — don't edit it by hand. `build_index.py` asks the
GitHub API for repos with Pages enabled, checks each site actually responds,
and reads the page `<title>` plus the repo description for the card text.

The `Build index` workflow regenerates it on every push, daily at 05:17 UTC, and
on demand via *Run workflow*. Publish Pages on a new repo and it shows up here
within a day, with no changes to this repo.

To preview locally:

```sh
python3 build_index.py && open index.html
```

Repos skipped: this one, and the `fmiguelt` profile README repo (`SKIP` in the
script).
