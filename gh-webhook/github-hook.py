#!/usr/bin/python3
# -*- python-indent-offset: 4 -*-

import sys
import json
from pathlib import Path

update_dir = Path("/var/www/hip.zijistark.com/hiphub")

tracked_repos = {
    'Aasmul/SWMH-BETA': ['master', 'Timeline_Extension+Bookmark_BETA'],
    'escalonn/sed2': ['dev', 'timeline'],
    'EMFTeam/EMF': ['alpha', 'timeline'],
    'EMFTeam/MiniSWMH': ['master', 'timeline'],
    'EMFTeam/HIP-tools': ['master'],
    'zijistark/ck2utils': ['dev'],
    'sifsilver/CPRplus': ['dev'],
    'ArkoG/ARKOpack': ['master'],
    'escalonn/ArumbaKS': ['master'],
    'Leybrook/LTM': ['master', 'dev']
}


def main():
    print("Content-Type: text/plain")
    print()
    sys.stdout.flush()
    
    payload = json.load(sys.stdin);

    if "head_commit" not in payload or "after" not in payload or "before" not in payload \
        or "ref" not in payload or "repository" not in payload:
        print("Thanks, but that's not interesting to me!")
        return 0

    repo = payload["repository"]

    if "name" not in repo or "full_name" not in repo:
        print("Expected to find repository/{name,full_name} in payload, discarding.")
        return 0

    name = repo["name"]
    full_name = repo["full_name"]

    if full_name not in tracked_repos:
        print("Repository not being actively tracked.")
        return 0

    branches = tracked_repos[full_name]
    ref_parts = payload["ref"].split('/')

    if len(ref_parts) != 3 or not (ref_parts[0] == 'refs' and ref_parts[1] == 'heads' and ref_parts[2] in branches):
        print("Branch not being actively tracked or weird ref.")
        return 0

    branch = ref_parts[2]
    filename = Path("{}:{}".format(name, branch))

    with (update_dir / filename).open("w") as f:
        print(payload["after"], file=f)

    print("Thanks for the update!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
