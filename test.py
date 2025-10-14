import requests
import json
from pathlib import Path

links = [
  "https://drive.google.com/open?id=168eU8anxBh3arp8Ds21jyrIjpH8Bl2v_&usp=drive_fs",
  "https://superplay.monday.com/boards/5239196091/pulses/18147479438/posts/4566449384",
  "https://superplay.monday.com/boards/5239196091/pulses/18147479560/posts/4566449807",
  "https://drive.google.com/open?id=12myejlO1hw4Io52OMNuBTRhkG4Z4_5be&usp=drive_fs"
  "https://superplay.monday.com/boards/5239196091/pulses/18142450180/posts/4566993252"
]

super = [url for url in links if url.startswith("https://superplay.monday.com/")]
google = [url for url in links if url.startswith("https://drive.google.com/")]

print(super)
print(google)
