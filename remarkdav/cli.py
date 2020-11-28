import time

import click
from webdav3.client import Client

from remarkdav.config import settings
from remarkdav.crawl import CrawlRegistry, CrawlThread


@click.group()
def cli():
    pass


@cli.command()
# @click.option("--count", default=1, help="Number of greetings.")
@click.option(
    "--password", prompt="Password", help="The password of your webdav login.", hide_input=True
)
def sync(password):
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
            "webdav_password": password,
        }
        client = Client(options)

        # Start crawler
        registry = CrawlRegistry()
        crawl_thread = CrawlThread(client, registry, "ilias/ref_20086")
        crawl_thread.run()
        while len(registry.threads) > 0:
            time.sleep(0.5)
            click.echo(f"Load paths: {len(registry.paths)} directories or files detected.")

        all_paths = registry.paths
        print(all_paths)
        print(f"{len(all_paths)} paths were found")


if __name__ == "__main__":
    cli()
