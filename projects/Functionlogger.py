def my_logger(orig_func):
    import logging
    logging.basicConfig(filename = f"{orig_func.__name__}.log", level = logging.INFO)

    def wrapper(*args, **kwargs):
        import time
        t1 = time.time()
        result = orig_func(*args,**kwargs)
        t2 = time.time()-t1
        print(f"{orig_func.__name__} ran with arguments: {args} and {kwargs} in time {t2}")
        logging.info(f"{orig_func.__name__} ran with arguments: {args} and {kwargs} in time {t2}")

        return result
    
    return wrapper









    