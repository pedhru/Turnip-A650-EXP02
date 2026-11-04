#!/usr/bin/env python3
"""Package one Mesa Android driver; validate its real ARM64 ELF and HAL export."""
from pathlib import Path
import hashlib,json,re,shutil,struct,subprocess,sys,tempfile,zipfile
recipe=Path(__file__).resolve().parent
binary,strip,output=map(Path,sys.argv[1:4]);strip=strip.absolute()
meta=json.loads((recipe/'meta-template.txt').read_text())
assert meta['libraryName']=='libvulkan_freedreno.so' and meta['minApi']==30
with tempfile.TemporaryDirectory() as d:
 lib=Path(d)/meta['libraryName'];shutil.copy2(binary,lib)
 subprocess.run([str(strip),'--strip-debug',str(lib)],check=True)
 data=lib.read_bytes()
 assert data[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<HH',data,16)==(3,183)
 readelf=strip.with_name('llvm-readelf')
 r=subprocess.run([str(readelf),'-d','--dyn-syms',str(lib)],text=True,capture_output=True,check=True)
 assert any('GLOBAL DEFAULT' in l and ' UND ' not in l and l.rstrip().endswith(' HMI') for l in r.stdout.splitlines())
 needed=set(re.findall(r'\(NEEDED\).*?\[([^\]]+)\]',r.stdout))
 allowed={'libhardware.so','liblog.so','libnativewindow.so','libsync.so','libm.so','libz.so','libdl.so','libc.so','libandroid.so'}
 assert needed and needed<=allowed,needed
 assert meta['driverVersion'].encode() in data
 assert len(data)>1000000, 'Unexpectedly small driver ELF'
 assert b'libvulkan_freedreno' not in data[:4], 'Corrupt ELF'
 manifest={'binary_sha256':hashlib.sha256(data).hexdigest(),'binary_bytes':len(data),
           'elf':'ELF64 little-endian ET_DYN AArch64','export':'HMI','needed':sorted(needed),
           'gpu_execution_tested':False,'cts_tested':False,'fps_measured':False}
 output.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  def write(name,contents):
   info=zipfile.ZipInfo(name,date_time=(2020,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
   z.writestr(info,contents,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
  write('meta.json',(json.dumps(meta,ensure_ascii=False,indent=2)+'\n').encode())
  write(meta['libraryName'],data)
  write('LEIA-ME.txt',(recipe/'driver-readme.txt').read_bytes())
  write('SHA256SUMS.txt',(manifest['binary_sha256']+'  '+meta['libraryName']+'\n').encode())
  write('SOURCE/elf-validation.txt',(json.dumps(manifest,indent=2)+'\n').encode())
  for p in sorted(recipe.iterdir()):
   if p.is_file() and p.suffix in {'.txt','.py','.sh','.patch'} and p.name!='elf-validation.txt':
    write('SOURCE/'+p.name,p.read_bytes())
  for directory in ['licenses','.github']:
   for p in sorted((recipe/directory).rglob('*')):
    if p.is_file():write('SOURCE/'+p.relative_to(recipe).as_posix(),p.read_bytes())
 with zipfile.ZipFile(output) as z:
  assert z.namelist()[0]=='meta.json'
  assert [n for n in z.namelist() if '.json' in n.lower()]==['meta.json']
  assert len(z.namelist())==len(set(z.namelist())) and z.testzip() is None
 print('PASS: metadata first; one JSON filename; ARM64 shared ELF; HMI; system dependencies only.')
 print('Dependencies:',', '.join(sorted(needed)))
 print('Driver SHA256:',manifest['binary_sha256'])
 print('ZIP:',output.resolve())
 print('ZIP SHA256:',hashlib.sha256(output.read_bytes()).hexdigest())
