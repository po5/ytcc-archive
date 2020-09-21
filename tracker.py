from typing import Optional, List
from enum import Enum, auto
import requests

# TODO: Implement backoff for 500 response codes

# https://github.com/ArchiveTeam/tencent-weibo-grab/blob/9bae5f9747e014db9227821a9c11557267967023/pipeline.py
VERSION = "20200921.01"

TRACKER_ID = "ext-yt-communitycontribs"
TRACKER_HOST = "trackerproxy.meo.ws"

BACKFEED_HOST = "blackbird-amqp.meo.ws:23038"

BACKFEED_ENDPOINT = f"http://{BACKFEED_HOST}/{TRACKER_ID}-kj57sxhhzcn2kqjp/"
TRACKER_ENDPOINT = f"http://{TRACKER_HOST}/{TRACKER_ID}"


class ItemType(Enum):
    Video = auto()
    Channel = auto()
    MixPlaylist = auto()
    Playlist = auto()


def add_item_to_tracker(item_type: ItemType, item_id: str) -> bool:
    """Feed items into the tracker through backfeed (item names will be deduplicated):
    # curl -d 'ITEMNAME' -so/dev/null $amqp_endpoint

    # Response codes:
    # 200 - Item added to tracker
    # 409 - Item is already in tracker
    # 404 - Project backfeed channel not found
    # 400 - Item name has a bad format
    """
    type_name = item_type.name.lower()
    item_name = f"{type_name}:{item_id}"

    req = requests.post(BACKFEED_ENDPOINT, data=item_name)

    code = req.status_code

    if code == 200:
        print(f"[INFO] Item ID \'{item_name}\' added to tracker successfully")
        return True
    elif code == 409:
        print(f"[INFO] Item ID \'{item_name}\' has already been added to tracker")
        return True
    elif code == 404:
        print(f"[ERROR] Unable to add item ID \'{item_name}\' to tracker. Project backfeed channel not found: {BACKFEED_ENDPOINT}")
    elif code == 400:
        print(f"[ERROR] Item ID \'{item_name}\' has a bad format")
    else:
        print(f"[ERROR] Unknown response code adding item \'{item_name}\' to tracker: {code}")

    return False


def request_item_from_tracker() -> Optional[str]:

    data = {
        # TODO: Ask Fusl what this should be
        # https://www.archiveteam.org/index.php?title=Dev/Seesaw
        # ^ says it would be filled in by the Seesaw library
        "downloader": "Fusl",
        "api_version": "2",
        "version": VERSION
    }

    req = requests.post(f"{TRACKER_ENDPOINT}/request", json=data)

    code = req.status_code

    if code == 200:
        data = req.json()

        if "item_name" in data:
            item_name = data["item_name"]
            print(f"[INFO] Received an item from tracker: {item_name}")

            return item_name
        else:
            print(f"[ERROR] Received item is missing the \'item_name\' key: {data}")

    else:
        print(f"[ERROR] Unable to get an item from tracker. Status: {code}")


def request_upload_target() -> Optional[str]:
    req = requests.get(
        # "https://httpbin.org/get",
        f"{TRACKER_ENDPOINT}/upload",
    )

    code = req.status_code

    if code == 200:
        data = req.json()

        if "upload_target" in data:
            upload_target = data["upload_target"]
            print(f"[INFO] Received an upload target from tracker: {upload_target}")
            return upload_target
        else:
            print(f"[ERROR] Response is missing the \'upload_target\' key: {data}")

    else:
        print(f"[ERROR] Unable to get an upload target from tracker. Status: {code}")


def request_all_upload_targets() -> Optional[List[str]]:
    req = requests.get(
        # "https://httpbin.org/get",
        f"{TRACKER_ENDPOINT}/upload",
    )

    code = req.status_code

    if code == 200:
        data = req.json()
        print(f"[INFO] Received all upload targets from tracker: {data}")
        return data
    else:
        print(f"[ERROR] Unable to get all upload targets from tracker. Status: {code}")


# `item_name` includes type prefix (video:id, playlist:id, etc)
def mark_item_as_done(item_name: str, item_size_bytes: int) -> bool:

    data = {
        # TODO: Ask Fusl what this should be
        # https://www.archiveteam.org/index.php?title=Dev/Seesaw
        # ^ says it would be filled in by the Seesaw library
        "downloader": "Fusl",
        "version": VERSION,
        "item": item_name,
        "bytes": {
            "data": item_size_bytes
        }
    }

    req = requests.post(f"{TRACKER_ENDPOINT}/done", json=data)

    code = req.status_code

    if code == 200:
        print(f"[INFO] Marked item \'{item_name}\' as done")
        return True
    elif code > 399 and code < 500:
        print(f"[ERROR] Unable to mark item as done. Status: {code}")
    elif code > 499 and code < 600:
        # TODO: retry here
        pass
    else:
        print(f"[ERROR] Unknown response code while marking item \'{item_name}\' as done: {code}")

    return False


if __name__ == "__main__":
    # print(add_item_to_tracker(ItemType.Channel, "test6"))
    # print(request_item_from_tracker())
    # print(request_upload_target())
    # print(request_all_upload_targets())
    # print(mark_item_as_done("test4", 200))