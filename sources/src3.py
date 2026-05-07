def outer():
    x = 10
    def middle():
        def inner():
            return x
        return
    x = 20
    return