import requests
import json
from pathlib import Path
import os
from urllib.parse import urlparse

# links = [
#   "https://drive.google.com/open?id=168eU8anxBh3arp8Ds21jyrIjpH8Bl2v_&usp=drive_fs",
#   "https://superplay.monday.com/boards/5239196091/pulses/18147479438/posts/4566449384",
#   "https://superplay.monday.com/boards/5239196091/pulses/18147479560/posts/4566449807",
#   "https://drive.google.com/open?id=12myejlO1hw4Io52OMNuBTRhkG4Z4_5be&usp=drive_fs"
#   "https://superplay.monday.com/boards/5239196091/pulses/18142450180/posts/4566993252"
# ]

# super = [url for url in links if url.startswith("https://superplay.monday.com/")]
# google = [url for url in links if url.startswith("https://drive.google.com/")]

# print(super)
# print(google)

# url = "https://superplay.monday.com/boards/10072840854/pulses/10072841002"
# response = True if (urlparse(url if '://' in url else f'https://{url}').hostname or '').lower() == 'superplay.monday.com' else False
# print(response)

import inspect

def stack_trace():
    f = inspect.currentframe().f_back
    return {
        "func": f.f_code.co_name,
        "file": os.path.basename(f.f_code.co_filename),
        "line": f.f_lineno,
    }
def jonatan():
  print(stack_trace())

jonatan()