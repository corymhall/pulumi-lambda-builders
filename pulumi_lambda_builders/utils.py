import os
from typing import Optional


def find_up(filename: str, dir: str) -> Optional[str]:
    print(f"dir: {dir}")
    if os.path.exists(os.path.join(dir, filename)):
        return os.path.join(dir, filename)
    if dir == get_root_directory(dir):
        return None
    return find_up(filename, os.path.dirname(dir))


def get_root_directory(path: str) -> str:
    # Split the drive and path
    drive, _ = os.path.splitdrive(path)

    # For Unix-like systems, the root is simply '/'
    if path.startswith("/"):
        return "/"

    # For Windows, return the drive as the root
    return drive
