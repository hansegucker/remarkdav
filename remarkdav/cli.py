import os
import shutil
import tempfile
import time
from threading import Thread
from uuid import uuid4

import click
import dateparser
from tabulate import tabulate
from webdav3.client import Client

from remarkdav.config import settings
from remarkdav.crawl import CrawlRegistry, CrawlThread
from remarkdav.sync_db import File
from remarkdav.utils import has_extension, get_filename, make_unique_filename


@click.group()
def cli():
    pass


RELEVANT_FILE_ENDINGS = ["pdf"]


class DownloadThread(Thread):
    def __init__(self, client, path, source):
        super().__init__()
        self.client = client
        self.path = path
        self.source = source

    def run(self):
        filename = self.path["filename"]
        click.echo(f"Download {filename}")
        self.client.download_sync(
            remote_path=self.path["path"], local_path=self.path["download_filename"]
        )
        click.echo(f"Download of {filename} finished.")

        file, _ = File.get_or_create(path=self.path["path"], source=self.source)
        file.downloaded = True
        file.synced = False
        file.modified = self.path["modified"]
        file.upload_path = self.path["upload_path"]
        file.save()


@cli.command()
def sync():
    """Run synchronisation for all mappings."""
    mappings = settings.get("mappings", [])

    if len(mappings) < 1:
        click.secho("No valid mappings configured.", fg="red")
        return

    for mapping in mappings:
        click.echo(f"Run synchronisation for config {mapping}")
        options = {
            "webdav_hostname": mapping["webdav"]["hostname"],
            "webdav_login": mapping["webdav"]["login"],
            "webdav_password": mapping["webdav"]["password"],
        }
        client = Client(options)

        # Start crawler
        registry = CrawlRegistry()
        DOWNLOAD_PATH = "/webdav.php/ilias/ref_20086/"
        crawl_thread = CrawlThread(client, registry, DOWNLOAD_PATH)
        crawl_thread.run()
        while len(registry.threads) > 0:
            time.sleep(0.5)
            click.echo(f"Load paths: {len(registry.paths)} directories or files detected.")

        all_paths = registry.paths

        # Print found paths
        print(tabulate(all_paths))
        print(f"{len(all_paths)} paths were found")

        # Filter paths
        my_paths = filter(
            lambda path: has_extension(path["path"], RELEVANT_FILE_ENDINGS), all_paths
        )

        # Make temp directory for downloads
        temp_directory = tempfile.mkdtemp()
        threads = []
        for path in my_paths:
            filename = get_filename(path["path"])
            path["filename"] = filename
            path["download_filename"] = os.path.join(temp_directory, make_unique_filename(filename))
            path["upload_path"] = path["path"].replace(DOWNLOAD_PATH, "")

            sync_this_file = False

            # Check whether this file has already been synced
            qs = File.select().where(
                File.path == path["path"], File.source == mapping["id"], File.uploaded == False
            )
            if qs.count() >= 1:
                # Get object and modification timestamp
                file_object = qs[0]
                modified = dateparser.parse(file_object.modified)

                # If downloaded file is newer than synced file, resync this file
                if path["modified"] > modified:
                    sync_this_file = True
                    click.echo(f"Sync {filename} because its newer")
                    file_object.downloaded = False
                    file_object.uploaded = False
                    file_object.save()
            else:
                click.echo(f"Sync {filename} because it was added")
                sync_this_file = True

            if sync_this_file:
                # Start download thread
                thread = DownloadThread(client, path, mapping["id"])
                thread.start()
                threads.append(thread)

        # Wait until all files are downloaded
        for thread in threads:
            thread.join()

        # Get all files to upload
        qs = File.select().where(
            File.source == mapping["id"], File.downloaded == True, File.uploaded == False
        )

        for file in qs:
            # UPLOAD HERE TO REMARKABLE
            click.echo(f"Upload file {file.path} to ReMarkable Cloud")
            file.uploaded = True
            file.save()

        # Clean up temp directory
        shutil.rmtree(temp_directory)


if __name__ == "__main__":
    cli()
