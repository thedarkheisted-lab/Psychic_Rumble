def my_logger(orig_func):
    import logging
    import time
    import inspect
    from functools import wraps
    logging.basicConfig(filename = f"{orig_func.__name__}.log", level = logging.INFO)
    
    @wraps(orig_func)
    
    def wrapper(*args, **kwargs):
        #import time
        t1 = time.time()
        #result = orig_func(*args,**kwargs)
        #t2 = time.time()-t1
        #print(f"{orig_func.__name__} ran with arguments: {args} and {kwargs} in time {t2}")
        #logging.info(f"{orig_func.__name__} ran with arguments: {args} and {kwargs} in time {t2}")
        result = orig_func(*args, **kwargs)
        t2 = time.time() - t1
        try:
            signature = inspect.signature(orig_func)
            bound = signature.bind_partial(*args, **kwargs)
            arg_labels = ", ".join(bound.arguments.keys())
        except (TypeError, ValueError):
            arg_labels = ", ".join(f"arg{idx}" for idx in range(1, len(args) + 1))
        if kwargs:
            value_display = kwargs
        else:
            value_display = args
        message = (
            f"{orig_func.__name__} ran with values: {value_display} for arguments "
            f"{{{arg_labels}}} in time {t2}"
        )
        print(message)
        logging.info(message)
        return result
    
    return wrapper









    