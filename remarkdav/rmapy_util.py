from rmapy.api import Client
from rmapy.folder import Folder


def create_folders(rmapy: Client, *folders):
    # Get all existing folders
    r_collection = rmapy.get_meta_items()
    r_folders = {f.ID: f for f in r_collection if isinstance(f, Folder)}

    # Create folder structure
    current_folder = None
    current_parent = ""
    for folder in folders:
        # Search for folder
        folder_found = False
        for r_id, r_folder in r_folders.items():
            if r_folder.VissibleName == folder and r_folder.Parent == current_parent:
                current_folder = r_folder
                current_parent = r_id
                folder_found = True
                break

        # Not found: create
        if not folder_found:
            current_folder = Folder(folder, Parent=current_parent)
            rmapy.create_folder(current_folder)
            current_parent = current_folder.ID

    return current_folder
