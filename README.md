# Preview images for PR #911 (#887)

Generated artifacts only -- nothing here is source, and this branch is
deliberately NOT part of the PR. It exists so the pull request body can show
what the feature looks like without committing binaries into the tree, which
this repo's maintainer has asked not to happen for regenerable files.

Regenerate any of them with:

    python3 py_router/make_movie.py <workdir> --panels xray+iso \
        --iso-max-renders 12 --iso-zoom 1.4 --size 720 -o two_panel.gif
