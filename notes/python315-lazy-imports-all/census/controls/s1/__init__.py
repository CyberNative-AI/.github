registry = []
from . import plugin_a
if len(registry) != 1:
    raise RuntimeError("plugin not registered")
