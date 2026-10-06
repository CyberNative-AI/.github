def add_tag(tag, tags=[]):
    tags.append(tag)
    return tags


if __name__ == "__main__":
    first = add_tag("first")
    second = add_tag("second")
    print(first, second, first is second)
