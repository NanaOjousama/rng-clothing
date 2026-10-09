"""Lenient JSON loader for SMAPI/Fashion Sense files (comments, trailing commas, BOM)."""
import json, re

def _strip(s):
    out, i, n, q = [], 0, len(s), None
    while i < n:
        c = s[i]
        if q:
            out.append(c)
            if c == '\\' and i + 1 < n:
                out.append(s[i + 1]); i += 2; continue
            if c == q: q = None
            i += 1; continue
        if c == '"': q = c; out.append(c); i += 1; continue
        if s.startswith('//', i):
            j = s.find('\n', i); i = n if j < 0 else j; continue
        if s.startswith('/*', i):
            j = s.find('*/', i + 2); i = n if j < 0 else j + 2; continue
        out.append(c); i += 1
    return re.sub(r',(\s*[}\]])', r'\1', ''.join(out))

def load(path):
    raw = open(path, 'rb').read().decode('utf-8-sig', errors='replace')
    try:
        return json.loads(raw)
    except Exception:
        return json.loads(_strip(raw))
