from threading import Thread
from uuid import uuid4

from remarkdav.utils import clean_path, last_part_of_path, simple_path


class CrawlRegistry:
    def __init__(self):
        self.paths = []
        self.threads = []

    def add(self, path):
        self.paths.append(path)

    def lock(self, uid: str):
        self.threads.append(uid)

    def unlock(self, uid: str):
        self.threads.remove(uid)


class CrawlThread(Thread):
    def __init__(self, client, registry: CrawlRegistry, base_path: str):
        super().__init__()
        self.client = client
        self.registry = registry
        self.lock = str(uuid4())
        self.registry.lock(self.lock)
        self.base_path = base_path

    def run(self):
        # Clean base path
        base_path = clean_path(self.base_path)

        # Get sub dirs
        sub_paths = self.client.list(base_path)

        for sub_path in sub_paths:
            # Skip top directory in sub dir list
            if simple_path(sub_path) == last_part_of_path(base_path):
                continue

            # Build full path
            full_path = base_path + sub_path

            # Add path to registry
            self.registry.add(full_path)

            # Start new thread for sub dirs
            new_thread = CrawlThread(self.client, self.registry, full_path)
            new_thread.start()

        self.registry.unlock(self.lock)
