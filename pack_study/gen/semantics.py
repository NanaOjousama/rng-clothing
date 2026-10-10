"""Semantic attachment classes: a taste filter ON TOP of geometric seating.  Pure Python.

decorate.place / band.place / pattern.apply answer "does it fit?".  This answers
"does it belong?": a leaf sprig seats on a ball cap, but a sprig on a ball cap is
a joke.  Every approved part has a profile in data/attachment_profiles.json:
  class      surface | structural | ornament | headpiece
  transfer   broad | family-limited | novelty-only | headpiece-only
  prefer / allow / reject / novelty   host families
  placement  the anchor the part keeps on its host (checked against the source)

HOST FAMILY comes from positive evidence only: the author's names and the vanilla
name of the source (same rule as band.eligible).  Shape-family membership is not
evidence (CLAUDE.md s3).  Opaque ids (Coii female_N, Seyph hats_N, ...) give no
family -> 'unknown'; data/host_labels.json labels them by eye (high/medium only).
"""
import json, os, re
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ALLOW_W = 0.4          # weight of an 'allow' host vs a 'prefer' host
NOVELTY_RATE = 0.08    # share of decorated hats rolled as an intentional novelty

# name patterns -> host family; a hat can be in several.  Applied to normalised names
# (underscores -> spaces, CamelCase split) so "28_BlueFish_0" reads "Blue Fish".
FAMILIES = [
    ('straw',    r'straw|sun ?hat|boater|sombrero|sakkat|panama|beekeeper'),
    ('floral',   r'flower|floral|garland|dais(y|ies)|wreath|laurel|tulip|\brose\b|orchid|forager|living hat'),
    ('cottage',  r'bonnet|headscarf|kerchief|maid cap|beret|\btam\b|chapeau|paperboy|pageboy|bucket|fishing hat|wester|hat of girl|chef'),
    ('western',  r'cowboy|cowgal|cowpoke'),
    ('formal',   r'top ?hat|bowler|fedora|governor|flat topped|sherlock|watson|detective|\bgent\b|magician|turban|\bfez\b|qi.s hat'),
    ('cavalier', r'tricorn|pirate|swashbuckler|musketeer'),
    ('cap',      r'\bcaps?\b|ballcap|snapback|trucker'),
    ('knit',     r'beanie|knit|针织|trapper|santa'),
    ('fantasy',  r'witch|wizard|\bmage\b|arcane|magic|gnome|jester|leprechaun|junimo|mushroom|deviruchi|kitsune|succubus|incubus|horns?\b|elf|fairy|angel|bat wings|plague|soul|paralysis'),
    ('regal',    r'crown|tiara|diadem|coronet'),
    ('helmet',   r'helmet|\bhelm\b|hard hat'),
    ('party',    r'party|paper hat|cone hat|\bcake\b|propeller'),
    ('animal',   r'\bcats?\b|bunny|rabbit|\bfrog\b|tiger|panda|raccoon|teddy|shark|squid|dinosaur|chicken|bluebird|\bfish\b|blobfish|mouse|\bbao\b|drooping'),
    ('hair',     r'headband|barrette|\bclips?\b|\bbows?\b|ribbon|\bhair\b|bells?\b|veil|earmuffs|goggles|sunglasses|tropiclip|\bband\b|headphones'),
    ('mask',     r'mask|eye patch'),
    ('hood',     r'\bhood'),
]
NOT_FAMILY = {                          # name words that look like a family but are not
    'cap': r'gnome|mushroom|maid cap',
    'regal': r'flower crown|flower dance crown|laurel wreath crown',
    'mask': r'on head',
    'hair': r'old straw hat w/ ribbon|sun hat \(ribbon\)|boater hat \(|beret \(white ribbon\)|cap&headphones',
}
_RX = [(f, re.compile(p, re.I)) for f, p in FAMILIES]
_NOT = {f: re.compile(p, re.I) for f, p in NOT_FAMILY.items()}
_PROF = _LABELS = None


def norm(n):
    n = re.sub(r'([a-z])([A-Z])', r'\1 \2', n)
    return re.sub(r'[_]+', ' ', n)


def host_families(names, cons_id=None):
    """Set of host families for a construction's names (author + vanilla); 'unknown'
    when none.  A hand label in data/host_labels.json wins."""
    global _LABELS
    if _LABELS is None:
        p = os.path.join(HERE, 'data', 'host_labels.json')
        raw = json.load(open(p)).get('labels', {}) if os.path.exists(p) else {}
        # visual labels: only high/medium confidence with a family count; low / [] stay unknown
        _LABELS = {k: set(v['families']) for k, v in raw.items()
                   if v['families'] and v.get('confidence') in ('high', 'medium')}
    if cons_id in _LABELS: return _LABELS[cons_id]
    out = set()
    for n in filter(None, names):
        n = norm(n)
        for f, rx in _RX:
            if rx.search(n) and not (f in _NOT and _NOT[f].search(n)): out.add(f)
    return out or {'unknown'}


def profiles():
    global _PROF
    if _PROF is None:
        _PROF = json.load(open(os.path.join(HERE, 'data', 'attachment_profiles.json')))['profiles']
    return _PROF


def key_of(dec):
    """Approval key of a decoration record (decorate.load_approved) or 'pattern:<label>'."""
    if 'from' in dec: return dec['from'].rsplit('__', 1)[0]
    return 'pattern:' + dec['label']


def verdict(prof, fams):
    """('prefer'|'allow'|'novelty'|'unknown'|'reject', weight) for one part on one host.
    'unknown' = the host's names give no family; weight = the profile's unknownHost.
    'novelty' = named host outside prefer/allow and not rejected: only in a novelty roll."""
    if prof['transfer'] == 'headpiece-only': return 'reject', 0.0
    if fams & set(prof.get('reject', [])): return 'reject', 0.0     # a horned headband is fantasy AND hair: hair wins
    if fams & set(prof.get('prefer', [])): return 'prefer', 1.0
    if fams & set(prof.get('allow', [])): return 'allow', ALLOW_W
    if fams == {'unknown'}: return 'unknown', prof.get('unknownHost', 0)   # no name evidence either way
    return 'novelty', 0.0


def weight(dec, fams, novelty=False):
    """Selection weight of an approved part on a host; 0 = filtered out.
    In a novelty roll, off-family named hosts (and a novelty-only part's own novelty
    hosts) get weight 1; rejects stay 0 and in-family placements are not novelties."""
    prof = profiles().get(key_of(dec))
    if prof is None: return 0.0                       # no profile -> not yet judged -> not used
    v, w = verdict(prof, fams)
    if not novelty: return w
    if v != 'novelty': return 0.0
    nov = prof.get('novelty')
    return 1.0 if nov is None or fams & set(nov) else 0.0
