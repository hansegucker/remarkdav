from threading import Thread
from uuid import uuid4

import click
import dateparser
from webdav3.exceptions import WebDavException

from remarkdav.utils import clean_path, last_part_of_path, simple_path


def parse_file_info(info: dict) -> dict:
    info["created"] = dateparser.parse(info["created"]) if info["created"] else None
    info["modified"] = dateparser.parse(info["modified"]) if info["modified"] else None

    return info


class CrawlRegistry:
    def __init__(self):
        self.paths = []
        self.threads = []
        self.stack = []
        self.errors = 0
        self.error_paths = {}
        self.unresolved_errors = 0

    def add(self, path):
        self.paths.append(path)

    def lock(self, uid: str):
        self.threads.append(uid)

    def unlock(self, uid: str):
        self.threads.remove(uid)


class CrawlThread(Thread):
    def __init__(self, client, registry: CrawlRegistry, base_path: str):
        super().__init__()
        self.base_path = base_path
        self.client = client
        self.registry = registry
        self.lock = str(uuid4())

    def run(self):
        # Add lock
        self.registry.lock(self.lock)

        # Clean base path
        base_path = clean_path(self.base_path)

        # Get sub dirs
        try:
            sub_paths = self.client.list(base_path, get_info=True)
        except WebDavException as e:
            click.secho(f"Check of {base_path} failed with {e}.", fg="red")
            self.registry.unlock(self.lock)

            if base_path in self.registry.error_paths:
                if self.registry.error_paths[base_path] >= 2:
                    click.secho(f"Check of {base_path} failed – last try.", fg="red")
                    self.registry.unresolved_errors += 1
                    return
                self.registry.error_paths[base_path] += 1
            else:
                self.registry.error_paths[base_path] = 1
                self.registry.errors += 1

            # Add new crawl thread for failed path listing
            new_thread = CrawlThread(self.client, self.registry, base_path)
            self.registry.stack.append(new_thread)
            return

        for sub_path in sub_paths:
            sub_path = parse_file_info(sub_path)

            # Skip top directory in sub dir list
            if simple_path(sub_path["path"]) == last_part_of_path(base_path):
                continue

            if sub_path not in self.registry.paths:
                # Add path to registry
                self.registry.add(sub_path)

                # Start new thread for sub dirs
                new_thread = CrawlThread(self.client, self.registry, sub_path["path"])
                self.registry.stack.append(new_thread)

        # Remove lock
        self.registry.unlock(self.lock)
