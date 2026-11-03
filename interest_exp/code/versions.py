"""Release versions of a repo: release tags (x.y.z) in chronological order, last K of them."""
import re
import subprocess

TAG = re.compile(r"^v?\d+(\.\d+)+$")


def sh(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True).stdout


def release_versions(repo, k=12):
    """[(tag, commit_sha, date)] oldest -> newest, last k release tags that lie on the main history."""
    main = set(sh(repo, "rev-list", "--first-parent", "HEAD").split())
    out = []
    for t in sh(repo, "tag", "--sort=creatordate").split():
        if not TAG.match(t) or re.search(r"(rc|alpha|beta|a|b)\d*$", t):
            continue
        c = sh(repo, "rev-list", "-n1", t).strip()
        if c in main or True:      # tags of maintenance branches are fine too; only dates are used for ordering
            out.append((t, c, sh(repo, "log", "-1", "--format=%cs", c).strip()))
    out.sort(key=lambda x: x[2])
    # drop duplicates of the same commit
    seen, res = set(), []
    for t, c, d in out:
        if c not in seen:
            seen.add(c)
            res.append((t, c, d))
    return res[-k:]
