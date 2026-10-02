import sys
import registry
sys.set_lazy_imports_filter(lambda importer, name, fromlist: name != "plugin")
lazy import plugin
assert sorted(registry.HANDLERS) == ["echo"]
assert registry.HANDLERS["echo"]("hello") == "HELLO"
print("filter: plugin stays eager")
