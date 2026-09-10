"""Show or hide the GitHub profile README without discarding its contents."""
from pathlib import Path
import sys


def set_visibility(mode, directory=Path('.')):
    if mode not in ('on', 'off'):
        raise ValueError('Visibility must be on or off.')
    visible = directory / 'README.md'
    hidden = directory / 'PROFILE.md'
    if visible.exists() and hidden.exists():
        raise RuntimeError('Both README.md and PROFILE.md exist; refusing to overwrite either file.')
    source, target = (hidden, visible) if mode == 'on' else (visible, hidden)
    if source.exists():
        source.rename(target)
        return True
    if target.exists():
        return False
    raise RuntimeError('No saved profile file was found.')


if __name__ == '__main__':
    mode = sys.argv[1]
    changed = set_visibility(mode)
    print(f'Profile visibility: {mode}. ' + ('Saved file renamed; content preserved.' if changed else 'Already set; no changes needed.'))
