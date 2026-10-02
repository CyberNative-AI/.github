import registry
registry.HANDLERS["echo"] = lambda text: text.upper()
READY = True
