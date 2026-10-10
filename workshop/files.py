"""Workspace-only optimistic edits, with actionable stale/ambiguous-match errors."""
import hashlib
import os
import re
import stat
import uuid
from . import core

LIMIT = 1_000_000


def snapshot(relative):
    target = core.path(relative)
    data = target.read_bytes()
    if len(data) > LIMIT:
        raise ValueError('Text editing supports files up to 1 MB')
    return {'path': str(target), 'content': data.decode('utf-8'),
            'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def edit(relative, expected_sha256, replacement, search=None):
    """Exact version required; safe full-file edits avoid fragile copied search snippets."""
    target = core.path(relative)
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
        raise ValueError('Read read_file_snapshot first and supply its sha256')
    # Parent directory descriptors prevent a symlink swap redirecting the commit.
    if os.name != 'posix':
        raise PermissionError('Atomic protected edits currently require POSIX directory descriptors')
    root = core.workspace()
    parts = target.relative_to(root).parts
    parent = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    temporary = None
    try:
        for component in parts[:-1]:
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent); parent = child
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
        with os.fdopen(fd, 'rb') as stream:
            before_stat = os.fstat(stream.fileno())
            if not stat.S_ISREG(before_stat.st_mode) or before_stat.st_size > LIMIT:
                raise ValueError('Edit target must be a regular UTF-8 file up to 1 MB')
            data = stream.read(LIMIT + 1)
        actual_hash = hashlib.sha256(data).hexdigest()
        if actual_hash != expected_sha256:
            raise ValueError('File changed since it was read. Read read_file_snapshot again and reapply the intended change; nothing was edited.')
        content = data.decode('utf-8')
        if search is None:
            updated = replacement
        else:
            if not search:
                raise ValueError('Search must be nonempty; omit search for a version-checked full-file edit')
            windows = '\r\n' in content and '\n' not in content.replace('\r\n', '')
            needle = search
            if content.count(needle) == 0 and windows:
                needle = search.replace('\r\n', '\n').replace('\n', '\r\n')
            matches = sum(1 for _ in re.finditer("(?=" + re.escape(needle) + ")", content))
            if matches != 1:
                raise ValueError(f'Search matched {matches} locations. Read read_file_snapshot again and use a unique complete snippet, or omit search and provide the complete edited content. Nothing was edited.')
            value = replacement.replace('\r\n', '\n').replace('\n', '\r\n') if windows else replacement
            updated = content.replace(needle, value, 1)
        encoded = updated.encode('utf-8')
        if len(encoded) > LIMIT:
            raise ValueError('Edited text exceeds 1 MB')
        if encoded == data:
            return {'path': str(target), 'sha256': actual_hash, 'changed': False}
        temporary = '.workshop-edit-' + uuid.uuid4().hex
        out = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        with os.fdopen(out, 'wb') as stream:
            stream.write(encoded)
            os.fchmod(stream.fileno(), stat.S_IMODE(before_stat.st_mode))
            stream.flush(); os.fsync(stream.fileno())
        # Recheck concurrent changes immediately before replacing the local entry.
        current = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
        with os.fdopen(current, 'rb') as stream:
            current_stat = os.fstat(stream.fileno())
            current_data = stream.read(LIMIT + 1)
        if (current_stat.st_dev, current_stat.st_ino) != (before_stat.st_dev, before_stat.st_ino) or current_data != data:
            raise ValueError('File changed during editing; nothing was replaced. Read it again.')
        os.replace(temporary, parts[-1], src_dir_fd=parent, dst_dir_fd=parent)
        temporary = None
        return {'path': str(target), 'sha256': hashlib.sha256(encoded).hexdigest(), 'changed': True}
    finally:
        if temporary is not None:
            os.unlink(temporary, dir_fd=parent)
        os.close(parent)
