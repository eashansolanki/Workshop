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
excluded={'__pycache__','.pytest_cache','.venv','.browsers','dist','build','.git'}
lines=['Workshop knowledge map','Updated: 2026-10-10; version 0.3.1','','Stack: existing Python/MCP/Playwright with Node/npm; no frontend or Mac application.','Changes: added GitHub-ready README, source/build guides and contribution guide; release builder is included in scripts/ and emits dist/ artifacts. Removed unrelated document capability and workflow references. Renamed all package, module, integration, skill hub, installer paths and branding to Workshop. Replaced GUI launcher with a self-contained shell installer. Payload is compressed and checksummed; official uv installs private managed Python, dependency wheels and Chromium. Node uses official checksummed prebuilt macOS/Linux archives. Each integration is verified before config merge. Existing settings are backed up; one Bionic hub includes eight references. User-owned host settings were not modified during development. Mac bundle, launcher and builder were deleted at user request.','','Function/component/loop inventory:']
for file in sorted(root.rglob('*.py')):
    tree=ast.parse(file.read_text(),filename=str(file))
    for node in sorted(ast.walk(tree),key=lambda n:getattr(n,'lineno',0)):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            lines.append(f'{file.relative_to(root)}:{node.lineno} {type(node).__name__} {node.name}')
        elif isinstance(node,(ast.For,ast.AsyncFor,ast.While,ast.ListComp,ast.SetComp,ast.DictComp,ast.GeneratorExp,ast.Lambda)):
            lines.append(f'{file.relative_to(root)}:{node.lineno} {type(node).__name__}')
for number,line in enumerate((root/'installer/install.template.sh').read_text().splitlines(),1):
    if line.startswith('cleanup()') or line.startswith('for argument'):
        lines.append(f'installer/install.template.sh:{number} function/loop {line}')
(root/'knowledge.txt').write_text('\n'.join(lines)+'\n')
buffer=io.BytesIO()
with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
    for file in sorted(root.rglob('*')):
        if file.is_file() and file.name!='install.sh' and file.suffix!='.pyc' and not any(part in excluded or part.endswith('.egg-info') for part in file.parts):
            assert not file.is_symlink()
            archive.add(file,arcname=str(Path(root.name)/file.relative_to(root)),recursive=False)
payload=buffer.getvalue()
encoded=base64.encodebytes(payload).decode()
text=(root/'installer/install.template.sh').read_text().replace('@@PAYLOAD@@',encoded.rstrip()).replace('@@SHA256@@',hashlib.sha256(payload).hexdigest())
for file in [root/'install.sh',output/'install.sh']:
    file.write_text(text)
    file.chmod(0o755)
with zipfile.ZipFile(output/'workshop.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for file in sorted(root.rglob('*')):
        if file.is_file() and file.suffix!='.pyc' and not any(part in excluded or part.endswith('.egg-info') for part in file.parts):
            archive.write(file,Path(root.name)/file.relative_to(root))
shutil.copyfile(root/'README.md',output/'SETUP.md')
shutil.copyfile(root/'TEST-REPORT.md',output/'TEST-REPORT.md')
assert not list(output.rglob('*.app'))
print('Built self-contained install.sh; no Mac app remains.')
