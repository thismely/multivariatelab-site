"""Verify the exact public release before unpacking it for GitHub Pages."""
import hashlib
import json
import re
import zipfile
from pathlib import Path


def verify(root=Path('.')):
    root = Path(root)
    manifest = json.loads((root / 'snapshot_manifest.json').read_text())
    archive_path = root / 'snapshot.zip'
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == manifest['snapshot_sha256']
    assert not manifest['real_classroom_data_included'] and not manifest['teacher_token_included']
    with zipfile.ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == set(manifest['file_sha256'])
        for name, digest in manifest['file_sha256'].items():
            path = Path(name)
            assert not path.is_absolute() and '..' not in path.parts
            assert not set(path.parts) & {'teacher_private', 'private', 'classroom', '.git', '.env'}
            raw = archive.read(name)
            assert hashlib.sha256(raw).hexdigest() == digest
            if path.suffix == '.ipynb':
                notebook = json.loads(raw)
                assert all(not c.get('outputs') and c.get('execution_count') is None
                           for c in notebook['cells'] if c['cell_type'] == 'code')
        tasks = archive.read('coursework/tasks/index.html').decode()
        assert re.findall(r'data-task-id="(T\d{3})"', tasks) == [f'T{i:03}' for i in range(1, 71)]
        destination = root / 'public'
        if destination.exists():
            raise FileExistsError('public already exists; do not overlay an unverified deployment')
        archive.extractall(destination)
    print('Public snapshot integrity and original70 tasks PASS; no real-data directory or teacher Token')


if __name__ == '__main__':
    verify()
