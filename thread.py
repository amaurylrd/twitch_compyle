import threading

lock = threading.Lock()


def func(list: list):
    pass

    elem = 0


threads = []

from multiprocessing.pool import ThreadPool

# pool = ThreadPool(processes=10)


def task(clip, subclips: list):
    lock.acquire()
    subclips.append(clip)
    lock.release()


clips = range(1, 11)
subclips = []
threads = []

for clip in clips:
    # async_result = pool.apply_async(task, (subclips,))
    # value = result.get()

    thread = threading.Thread(
        target=task,
        args=(
            clip,
            subclips,
        ),
    )
    thread.start()
    threads.append(thread)

for thread in threads:
    if thread.is_alive():
        thread.join()

print(subclips)
# pool.terminate()
