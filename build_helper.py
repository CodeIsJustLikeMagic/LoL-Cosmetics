# Source - https://stackoverflow.com/a/78992623
# Posted by Polv, modified by community. See post 'Timeline' for change history
# Retrieved 2026-09-14, License - CC BY-SA 4.0

import PyInstaller.__main__
from pathlib import Path

icon_path = Path("assets/icon.ico").resolve()
assert icon_path.exists(), f"Icon file missing at {icon_path}"

pyi_args = [
    "main.py",
    "--name", "Cosmetics",
    "--noconsole",
    f"--icon={icon_path.as_posix()}"
]


def add_folder(folder_name: str):
    folder = Path(folder_name)
    assert folder.exists(), f"Folder {folder_name} does not exist"
    
    # Format: "source_path;destination_path" on Windows ("source_path:destination_path" on Linux/macOS)
    # Passing the base folder path includes all files and subdirectories recursively
    pyi_args.extend(("--add-data", f"{folder.as_posix()};{folder_name}"))

add_folder("assets")
add_folder("config")

PyInstaller.__main__.run(pyi_args)
