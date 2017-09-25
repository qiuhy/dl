import time
from functools import wraps

TIMEOUT_TRIES = 4
TIMEOUT_DELAY = 3


def retry(ExceptionToCheck=Exception, tries=TIMEOUT_TRIES, delay=TIMEOUT_DELAY, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """

    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    msg = "{}{} {}, Retrying in {} seconds...".format(f.__name__, args, e, mdelay)
                    logobj = logger
                    if logobj is None and len(args) > 0:
                        if hasattr(args[0], 'logger'):
                            logobj = getattr(args[0], 'logger')

                    if logobj:
                        logobj.debug(msg)
                    # else:
                    #     print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry
