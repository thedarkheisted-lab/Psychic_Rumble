class decorator_class(object):
    def __init__(self, original_function):
        self.original_function = original_function

    def __call__(self,*args, **kwargs):
        print(f"call method executed before {self.original_function.__name__}")
        return self.original_function(*args, **kwargs)

