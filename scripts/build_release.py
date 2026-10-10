import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import shutil
import tarfile
import zipfile

root=Path(__file__).resolve().parents[1]
output=root/'dist'
output.mkdir(exist_ok=True)
excluded={'__pycache__','.pytest_cache','.venv','.browsers','dist','build','.git','tests'}
buffer=io.BytesIO()
with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
    for file in sorted(root.rglob('*')):
        if file.is_file() and file.name not in {'install.sh','installupdate.sh','knowledge.txt','knowledge.tx','TEST-REPORT.md'} and file.suffix!='.pyc' and not any(part in excluded or part.endswith('.egg-info') for part in file.parts):
            assert not file.is_symlink()
            archive.add(file,arcname=str(Path("workshop")/file.relative_to(root)),recursive=False)
payload=buffer.getvalue()
encoded=base64.encodebytes(payload).decode()
for name, updating in (("install.sh", "0"), ("installupdate.sh", "1")):
    text=(root/'installer/install.template.sh').read_text().replace('@@UPDATE@@',updating).replace('@@PAYLOAD@@',encoded.rstrip()).replace('@@SHA256@@',hashlib.sha256(payload).hexdigest())
    for file in [root/name,output/name]:
        file.write_text(text)
        file.chmod(0o755)
with zipfile.ZipFile(output/'workshop.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for file in sorted(root.rglob('*')):
        if file.is_file() and file.name not in {'knowledge.txt','knowledge.tx','TEST-REPORT.md'} and file.suffix!='.pyc' and not any(part in excluded or part.endswith('.egg-info') for part in file.parts):
            archive.write(file,Path("workshop")/file.relative_to(root))
shutil.copyfile(root/'README.md',output/'SETUP.md')
assert not list(output.rglob('*.app'))
print('Built self-contained install.sh; no Mac app remains.')
