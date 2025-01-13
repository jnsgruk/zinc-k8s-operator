# Copyright 2022 Jon Seager
# See LICENSE file for licensing details.

"""The `parca` machine charm has been deprecated.

This library has been transferred to the `parca-k8s` charm.
If you are using this library, please replace it with the new one:

    charmcraft fetch-lib charms.parca_k8s.v0.parca_scrape
"""

# The unique Charmhub library identifier, never change it
LIBID = "7b30b495435746acb645ca414898621f"

# Increment this major API version when introducing breaking changes
LIBAPI = 0

# Increment this PATCH version before using `charmcraft publish-lib` or reset
# to 0 if you are raising the major API version
LIBPATCH = 6

raise ImportError(
    "This library has been migrated to the `parca-k8s` charm. "
    "Delete it and replace it with the equivalent `charms.parca_k8s.v0.parca_scrape`."
)