def register(handlers):
    handlers["echo"] = lambda text: text.upper()
