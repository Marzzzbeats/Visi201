def outer():
    x = 10
    def inner():
        return x
    x = 20
    return inner()

print(outer())