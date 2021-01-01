import os
import shutil
import tempfile
import time
from threading import Thread
from uuid import uuid4

import click
import dateparser
from rmapy.api import Client as RMClient
from rmapy.document import Document, ZipDocument
from rmapy.exceptions import AuthError
from tabulate import tabulate
from webdav3.client import Client

from remarkdav.config import settings
from remarkdav.crawl import CrawlRegistry, CrawlThread
from remarkdav.pdf import create_sync_status_pdf
from remarkdav.rmapy_util import create_folders
from remarkdav.sync_db import File
from remarkdav.utils import get_filename, has_extension


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
            remote_path=self.path["path"], local_path=self.path["download_path"]
        )
        click.echo(f"Download of {filename} finished.")

        file, _ = File.get_or_create(path=self.path["path"], source=self.source)
        file.downloaded = True
        file.synced = False
        file.modified = self.path["modified"]
        file.upload_path = self.path["upload_path"]
        file.local_path = self.path["download_path"]
        file.save()


@cli.command()
def sync():
    """Run synchronisation for all mappings."""
    # Authenticate against reMarkable API
    rmapy = RMClient()

    try:
        try:
            rmapy.renew_token()
            click.secho("Successful connected to reMarkable API", fg="green")
        except AuthError:
            code = click.prompt("Please enter reMarkable one-time code")
            res = rmapy.register_device(code)
            if res:
                click.secho("Successful connected to reMarkable API", fg="green")
    except AuthError as e:
        click.secho(f"Connection error while connecting to reMarkable API: {e}", fg="red")

    mappings = settings.get("mappings", [])

    if len(mappings) < 1:
        click.secho("No valid mappings configured.", fg="red")
        return

    for mapping in mappings:
        mapping_id = mapping["id"]
        click.echo(f"Run synchronisation for config {mapping_id}")
        options = {
            "webdav_hostname": mapping["webdav"]["hostname"],
            "webdav_login": mapping["webdav"]["login"],
            "webdav_password": mapping["webdav"]["password"],
        }
        client = Client(options)

        # Start crawler
        registry = CrawlRegistry()
        crawl_thread = CrawlThread(client, registry, mapping["webdav"]["base_path"])
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

            # Make unique dir
            uid = str(uuid4())
            os.mkdir(os.path.join(temp_directory, uid))

            # Set download and upload paths
            path["download_path"] = os.path.join(temp_directory, uid, filename)
            path["upload_path"] = path["path"].replace(mapping["webdav"]["base_path"], "")

            sync_this_file = False

            # Check whether this file has already been synced
            qs = File.select().where(
                File.path == path["path"],
                File.source == mapping["id"],
                File.uploaded == True,  # noqa
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
            File.source == mapping["id"], File.downloaded == True, File.uploaded == False  # noqa
        )

        for file in qs:
            click.echo(f"Upload file {file.upload_path} to reMarkable Cloud")

            # Get necessary folders and the filename
            path_split = file.upload_path.split("/")
            folders = [mapping["base_folder"]] + path_split[:-1]
            filename = path_split[-1]

            upload_folder = create_folders(rmapy, *folders)

            # Upload new document to cloud
            doc = ZipDocument(doc=os.path.abspath(file.local_path))
            doc.metadata["VissibleName"] = filename.split(".")[0]
            rmapy.upload(doc, upload_folder)

            # Save sync status
            file.uploaded = True
            file.save()

            click.secho("  Upload finished.", fg="green")

        # Create sync status
        sync_doc_name = "Sync status"
        sync_status_filename = create_sync_status_pdf(mapping)

        # Create folder
        sync_status_folder = create_folders(rmapy, mapping["base_folder"])

        # Get all existing documents
        r_collection = rmapy.get_meta_items()

        for meta_item in r_collection:
            if (
                isinstance(meta_item, Document)
                and meta_item.VissibleName == sync_doc_name
                and meta_item.Parent == sync_status_folder.ID
            ):
                # Delete old file
                rmapy.delete(meta_item)
                break

        # Upload new document to cloud
        doc = ZipDocument(doc=sync_status_filename)
        doc.metadata["VissibleName"] = sync_doc_name
        rmapy.upload(doc, sync_status_folder)

        # Clean up temp directory
        shutil.rmtree(temp_directory)


if __name__ == "__main__":
    cli()
