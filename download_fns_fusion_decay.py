from urllib.parse import urlparse
from urllib.request import urlopen, Request

import tarfile
from zipfile import ZipFile
import os

BLOCK_SIZE = 16384

here = os.path.abspath(os.path.dirname(__file__))

# download zip file
conderc_url = 'https://nds.iaea.org/conderc/fusion/files/fns.zip'
local_path = os.path.join(here, 'fns.zip')
p = Request(conderc_url, headers={'User-Agent': 'Mozilla/5.0'})
with urlopen(p) as response:
    if os.path.exists(local_path):
        print('File already exists, skipping download')
    else:
        with open(local_path, 'wb') as f:
            while True:
                chunk = response.read(BLOCK_SIZE)
                if not chunk:
                    break
                f.write(chunk)
        assert(os.path.exists(local_path)), 'Something wrong with download'
        print('completed download') 

# unzip
zipped_fld = os.path.join(here, 'fns')
if os.path.exists(zipped_fld):
    print('Extracted folder already exists. Exiting.')
    exit()
with ZipFile(local_path, 'r') as f:
    f.extractall(here)
    print('Unzipped')
