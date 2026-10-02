import registry
lazy import explicit_plugin
assert registry.HANDLERS == {}
explicit_plugin.register(registry.HANDLERS)
assert sorted(registry.HANDLERS) == ["echo"]
assert registry.HANDLERS["echo"]("hello") == "HELLO"
print("explicit: registered at initialization")
