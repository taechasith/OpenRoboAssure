# Third-party notices

## Runtime dependency

`PyBullet` 3.2.7 is used as the secondary simulator under the Zlib licence.
Its source notice is retained by the upstream package; OpenRoboAssure does not
vendor or modify its source.

## Imported robot model assets

The unmodified `franka_emika_panda` and `universal_robots_ur5e` directories
from `google-deepmind/mujoco_menagerie` commit
`71f066ad0be9cd271f7ed58c030243ef157af9f4` are redistributed under
`assets/imported/mujoco_menagerie/`.

- `franka_emika_panda`: Apache-2.0; its upstream `LICENSE` file is retained.
- `universal_robots_ur5e`: BSD-3-Clause; its upstream `LICENSE` file is retained.

See `assets/manifest.yaml` for exact source subdirectories and entrypoint
checksums.

## Development-only exception

`pathspec` 1.1.1 is a transitive dependency of the required `mypy` development
tool. It is licensed under MPL-2.0 and is approved only as a development-only
exception. Its full MPL-2.0 notice is preserved at
[`third_party_licenses/pathspec-MPL-2.0.txt`](third_party_licenses/pathspec-MPL-2.0.txt).
OpenRoboAssure does not copy or modify MPL-covered files. See
`dependencies/license_exceptions.yaml`.

`PyOpenGL` is a MuJoCo runtime dependency with verified PyPI BSD metadata. It
is a package-specific exception, not a general approval for ambiguous BSD
metadata; preserve its upstream notice if redistribution becomes necessary.
