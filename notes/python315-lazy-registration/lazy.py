import registry
lazy import plugin
assert registry.HANDLERS == {}
print("lazy: registry empty before first use")
assert plugin.READY is True
assert sorted(registry.HANDLERS) == ["echo"]
assert registry.HANDLERS["echo"]("hello") == "HELLO"
print("lazy: registered after first use")
