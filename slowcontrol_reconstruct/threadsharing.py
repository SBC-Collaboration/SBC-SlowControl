import threading
import time

class ThreadA(threading.Thread):
    def __init__(self, shared_data, lock):
        super().__init__()
        self.shared_data = shared_data
        self.lock = lock

    def run(self):
        for i in range(5):
            data_to_send = {'ThreadA': i}
            with self.lock:
                self.shared_data.update(data_to_send)
                print(f'ThreadA sending: {data_to_send}')
            time.sleep(2)

class ThreadB(threading.Thread):
    def __init__(self, shared_data, lock):
        super().__init__()
        self.shared_data = shared_data
        self.lock = lock

    def run(self):
        for i in range(5):
            with self.lock:
                data_received = dict(self.shared_data)
                print(f'ThreadB received: {data_received}')
            time.sleep(1)

if __name__ == "__main__":
    # Create a shared dictionary and a lock
    shared_data = {}
    shared_data_lock = threading.Lock()

    # Create instances of ThreadA and ThreadB, passing the shared data and lock
    thread_a = ThreadA(shared_data, shared_data_lock)
    thread_b = ThreadB(shared_data, shared_data_lock)

    # Start both threads
    thread_a.start()
    thread_b.start()

    # Wait for both threads to finish
    thread_a.join()
    thread_b.join()
