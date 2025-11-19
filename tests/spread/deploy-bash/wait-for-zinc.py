# /// script
# dependencies = [
#   "jubilant"
# ]
# ///

import jubilant

jubilant.Juju().wait(lambda s: jubilant.all_active(s, "zinc-k8s"), timeout=600)
