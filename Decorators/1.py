#Decorators

def outer_function(msg):
    def inner_function():
        print(msg)

    return inner_function

    
hi_func = outer_function("Hi")
bye_func = outer_function("Bye")

hi_func()
bye_func() 