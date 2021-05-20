import datetime
import inspect
import time


class RetryWrapper:
    """Generic class for retrying method calls on an object"""

    def __init__(self, object, exception=Exception, timeout=10):
        self.object = object
        self.exception = exception
        self.timeout = timeout

    def __getattribute__(self, name, *args, **kwargs):
        object = super().__getattribute__("object")
        exception = super().__getattribute__("exception")
        timeout = super().__getattribute__("timeout")

        if not hasattr(object, name):
            raise AttributeError(f"No {name} on {type(object)}")
        else:
            attr = getattr(object, name)

            if not inspect.ismethod(attr):
                return attr

            def wrapped(*args, **kwargs):
                deadline = datetime.datetime.now() + datetime.timedelta(seconds=timeout)

                while True:
                    try:
                        result = attr(*args, **kwargs)

                        return result
                    except exception as e:
                        if datetime.datetime.now() >= deadline:
                            raise e
                        time.sleep(1)

            return wrapped
