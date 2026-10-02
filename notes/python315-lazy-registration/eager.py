import registry
import plugin
assert sorted(registry.HANDLERS) == ["echo"]
assert registry.HANDLERS["echo"]("hello") == "HELLO"
print("eager: registered before use")
