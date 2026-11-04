#!/usr/bin/env python3
import hashlib,json,sys,zipfile,struct
from pathlib import Path
p=Path(sys.argv[1]); assert p.is_file()
with zipfile.ZipFile(p) as z:
 names=z.namelist();assert names[0]=='meta.json' and len(names)==len(set(names)) and z.testzip() is None
 assert [n for n in names if n.lower().endswith('.json')]==['meta.json']
 m=json.loads(z.read('meta.json'));assert m['packageVersion']=='EXP19-MESA26.2.6' and m['minApi']==30
 assert m['libraryName']=='libvulkan_freedreno.so'
 lib=z.read('libvulkan_freedreno.so')
 assert lib[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<HH',lib,16)==(3,183)
 assert m['driverVersion'].encode() in lib
 assert z.read('SHA256SUMS.txt').decode().strip()==hashlib.sha256(lib).hexdigest()+'  libvulkan_freedreno.so'
 assert len(lib)>1000000
 print('PASS: ZIP CRC, ADPKG layout, ELF ARM64, release version, SHA256, minApi')
