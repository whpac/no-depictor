from typing import Iterable, TypeVar
import signal


class InterruptHandler:

    @property
    def interrupted(self) -> bool:
        return self._interrupted
    

    def __enter__(self):
        self._interrupted = False
        self._released = False
        self._original_handler = signal.getsignal(signal.SIGINT)

        def handler(signum, frame):
            self.release()
            self._interrupted = True

        signal.signal(signal.SIGINT, handler)
        return self


    def __exit__(self, type, value, tb):
        self.release()


    def release(self):
        if self._released:
            return
        signal.signal(signal.SIGINT, self._original_handler)
        self._released = True


    def forceInterrupt(self):
        if self._released:
            return
        self._interrupted = True


T = TypeVar('T')
def interruptible(iterable: Iterable[T], ih: InterruptHandler) -> Iterable[T]:
    '''
    A helper function that facilitates an interruptible iteration over an iterable.
    Before returning the next item, it checks if the iteration has been interrupted.
    If it has, it stops yielding items.
    This is useful for long-running operations where you want to allow the user to
    interrupt the process gracefully.

    :param iterable: The iterable to iterate over.
    :param ih: An instance of InterruptHandler to check for interruptions.
    :return: An iterable that yields items from the original iterable until interrupted.
    '''
    for item in iterable:
        if ih.interrupted:
            break
        yield item
