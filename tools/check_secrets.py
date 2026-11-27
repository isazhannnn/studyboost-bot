"""Check tracked text files without printing matched credentials."""
import re
import subprocess
from pathlib import Path

PATTERNS = {
    'Telegram token': re.compile(r'\b\d{6,12}:[A-Za-z0-9_-]{30,}\b'),
    'GitHub token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b'),
    'Private key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'AWS access key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
}


def scan(paths):
    findings = []
    for path in paths:
        try:
            content = Path(path).read_text(encoding='utf-8')
        except (UnicodeError, OSError):
            continue
        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(content):
                findings.append((str(path), content.count('\n', 0, match.start()) + 1, name))
    return findings


if __name__ == '__main__':
    paths = subprocess.check_output(['git', 'ls-files', '-z']).decode().split('\0')
    findings = scan(filter(None, paths))
    for path, line, kind in findings:
        print(f'{path}:{line}: possible {kind}')
    raise SystemExit(bool(findings))
