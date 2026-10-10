"""Provenance of generated hats: BASE -> EXTRACTED / RECOMBINED PARTS -> FINAL.  Pure Python.

record(...) hooks a loaded generate module (current code, or an archived copy of an
older commit, so QC hats already in game can be replayed) and keeps, per written hat:
  type     recolor | restyle | attachment | structural combination
  subtype  how, in one phrase (hue-rotate of a proven colourway, transferred band, ...)
  base     pixels of the host BEFORE any part was added (the recoloured/restyled hat)
  final    pixels exactly as written to hat.png
  parts    every source-derived part: its source hat, and for an attachment the
           extracted pixels + source base mask per view (exactly what decorate placed)
  diff     final-vs-base changed pixel count (an attachment must change pixels; a
           recolour must change none)
tools/provenance_sheet.py draws the proof sheet from these records.
"""
import copy

VIEWS = ['front', 'right', 'left', 'back']


def gen_type(row):
    """(type, subtype) from a roll-log row."""
    if row['tier'] == 'restyled': return 'restyle', 'shape of one author, shading ramp of another'
    if row['tier'] == 'combined': return 'structural combination', 'crown of one hat on the brim of another'
    if row.get('decoration'):
        d = row['decoration']
        kind = 'band transfer' if 'band' in d['label'] else 'ornament transfer'
        return 'attachment', kind + (' (NOVELTY roll)' if d.get('novelty') else '')
    if row.get('pattern'): return 'attachment', 'surface pattern transfer (' + row['pattern'] + ')'
    if row.get('addon'): return 'recolor', "recolour + the author's own add-on variant"
    mode = (row.get('colour') or {}).get('mode', '')
    if row['tier'] == 'uncommon': return 'recolor', "recolour of the author's own pattern variant"
    return 'recolor', {'fs-multiply-masked': 'Fashion Sense multiply tint of a greyscale hat',
                       'hue-rotate-proven-colourway': "hue rotation of the author's proven colourway"}.get(mode, mode)


def _part_of_dec(gen, label, from_key=None):
    decs = gen.load_approved()
    hit = [d for d in decs if (from_key and d['from'] == from_key)] or [d for d in decs if d['label'] == label]
    if not hit: return None
    d = hit[0]
    return {'role': 'attachment', 'label': d['label'], 'kind': d['kind'], 'from': d['from'], 'fromName': d.get('fromName'),
            'sourceBase': d.get('base'), 'author': d.get('author'),
            'extracted': {v: {'pixels': d['views'][v]['pixels'], 'baseMask': d['views'][v]['baseMask']} for v in VIEWS}}


def parts_of(gen, row, cons):
    """Source-derived parts behind one roll-log row."""
    col = row.get('colour') or {}
    out = []
    if row['tier'] == 'restyled':
        out.append({'role': 'shape', 'from': col.get('shapeFrom')})
        out.append({'role': 'shading ramp', 'from': col.get('rampFrom'), 'author': row['author']})
    elif row['tier'] == 'combined':
        out += [{'role': 'crown', 'from': col.get('crown')}, {'role': 'brim', 'from': col.get('brim')},
                {'role': 'style (outline/ramp)', 'from': col.get('style')}]
    else:
        out.append({'role': 'host', 'from': cons, 'colourway': col.get('from'), 'colour': col})
    if row.get('decoration'):
        p = _part_of_dec(gen, row['decoration']['label'], row['decoration'].get('from'))
        if p: out.append(p)
    if row.get('pattern'): out.append({'role': 'surface pattern', 'label': row['pattern']})
    if row.get('addon'): out.append({'role': "author's add-on", 'from': row['addon']})
    return out


def record(gen):
    """Hook generate module `gen`; returns dict name -> {'base', 'final', ...}.
    BASE is the hat pixels right before the first part is added (decorate / pattern)."""
    rec, cur = {}, {}
    dec0, pat0, write0 = gen.decorate, gen.patterns.apply, gen.write_hat

    def decorate(px, *a, **k):
        cur['base'] = copy.deepcopy(px)              # host as rendered for THIS try
        return dec0(px, *a, **k)

    def apply(p, px, *a, **k):
        cur['base'] = copy.deepcopy(px)
        return pat0(p, px, *a, **k)

    def write_hat(pack, name, c, px):
        rec[name] = {'name': name, 'frame': list(c['frame']), 'construction': c['id'],
                     'base': cur.pop('base', None) or copy.deepcopy(px), 'final': copy.deepcopy(px)}
        return write0(pack, name, c, px)

    gen.decorate, gen.patterns.apply, gen.write_hat = decorate, apply, write_hat
    return rec


def finish(gen, rec, row):
    """Add type / parts / diff to one captured record from its roll-log row."""
    r = rec[row['name']]
    r['type'], r['subtype'] = gen_type(row)
    r['author'] = row['author']
    r['parts'] = parts_of(gen, row, row['construction'])
    b, f = r['base'], r['final']
    pad = len(f) - len(b)                            # rows grown above the frame for a tall part
    r['padRows'] = pad
    r['diff'] = sum(1 for y in range(len(f)) for x in range(len(f[0]))
                    if tuple(f[y][x]) != (tuple(b[y - pad][x]) if y >= pad else (0, 0, 0, 0)))
    return r
