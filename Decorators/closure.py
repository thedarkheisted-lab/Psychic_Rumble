import logging
logging.basicConfig(filename = 'example.log', level = logging.INFO)

def logger(func):
    def log_func(*args):
        logging.info(f'Running "{func.__name__}" with arguments {args}')
        print(func(*args))

    return log_func

def add(x, y):
    return x+y

def subtract(x, y):
    return x-y

add_logger = logger(add)
sub_logger = logger(subtract)

add_logger(3,5)
add_logger(6,7)

sub_logger(7,4)
sub_logger(9,5)
