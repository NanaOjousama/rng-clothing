"""Witch-hat forge: a design (parameters) -> 4 native 20x20 views, built ON the pixel grid.
Pure Python.  AI-ORIGINAL lane (CLAUDE.md 2b): the design parameters come from an AI brief;
this file only renders them.  Nothing here is taken from any source sprite.

Why (out/benchmark.json): shrinking an illustration to 16 px collapses a tapering cone into a
1-3 px stalk on a 1-row brim, with patchy k-means colour and no consistent light.  Good hats
are chunky volumes with form shading, deliberate ramps and coloured outlines.  So the sprite
is ray-cast here, one ray per native pixel centre (no supersampling, no smoothing):

  geometry  brim  = elliptic slab (radius R, thickness T) with edge droop/curl
            crown = solid of revolution, radius r(h) = r0 * (1 - h/H)^taper, axis bent by
                    bend * (h/H)^2 toward a yaw (the tip leans), tip may slump (fold)
            band  = crown heights [0, band_h); buckle / charm = small decals on the band or
                    crown, in 3D, so they only show from the side that faces them
  camera    orthographic, elevation ELEV (Stardew looks slightly down: the brim top shows);
            front/right/left/back = yaw 0/90/-90/180 of the SAME model -> views agree
  light     one direction (top-left-front); lambert + ambient, quantised to ramp steps;
            brim top under the crown gets one step of occlusion
  colour    each material = a hue-shifted OKLCh ramp (shadows cooler, highlights warmer)
  outline   silhouette edge -> darkest step of that material's ramp (coloured, not black);
            inner contour where a nearer part overlaps a farther one
usage: python3 -I forge.py designs.json out_dir  (designs = list of dicts, see DEFAULT)"""
import json, math, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'pack_study', 'gen'))
import png
from colour import to_lch, from_lch

# Structure measured from the vanilla Witch Hat CONTROL (out/control_rows.txt), never its pixels:
# narrow near-cylindrical crown ~5-6 px, blunt crooked tip, big deep-oval brim ~16 x 7 rows.
# The control's tip leans to the wearer's side AND backward (front: right, back: left, both sides: toward the
# back of the head): a lean with a blunt end, little fold.  bend_yaw stays +-135 (backward diagonal).
DEFAULT = dict(name='default', R=7.6, T=1.0, droop=0.3, curl=0.0, r0=3.0, H=10.5, taper=0.5, bend=2.6, bend_yaw=-135,
               crook=0.9, tip_r=1.0, flare=0.15, selout=True, spec=True, wave=0.0, lobes=5, wave_phase=0.0, rim=None,
               slump=0.0, band_lo=0.8, band_h=2.6, base=(92, 52, 150), band=(40, 30, 60), accent=(235, 190, 70), buckle='square',
               charms=[], stars=0, ramp_steps=5, tip_pom=None, pom_r=1.3, outline_mode='coloured')
ELEV = math.radians(36)                 # deep brim oval, as in the control (16 wide x ~7 rows)
LIGHT_CAM = (-0.55, 0.75, 0.45)      # from the viewer's top-left-front, in EVERY view (Stardew convention)
VIEW_YAW = {'front': 0, 'right': 90, 'left': -90, 'back': 180}


def norm(v):
    l = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / l for c in v)


LIGHT_CAM = norm(LIGHT_CAM)


def ramp(rgb, n):
    """Hue-shifted ramp, darkest first.  Shadows rotate toward blue-violet and lose chroma;
    highlights rotate toward warm and gain lightness.  OKLab L spread 0.22..0.86 scaled to base."""
    L, C, H = to_lch(rgb)
    out = []
    for i in range(n):
        t = i / (n - 1)                                   # 0 dark .. 1 light
        Li = 0.16 + (L - 0.16) * (t / 0.6) if t <= 0.6 else L + (min(0.88, L + 0.18) - L) * ((t - 0.6) / 0.4)
        Ci = C * (0.8 + 0.15 * t) if C > 0.02 else C
        target = 285.0 if t < 0.6 else 85.0                # cool shadows, warm lights
        k = (0.6 - t) / 0.6 * 0.18 if t < 0.6 else (t - 0.6) / 0.4 * 0.12
        dh = ((target - H + 180) % 360) - 180
        out.append(tuple(from_lch(max(0.05, min(0.95, Li)), Ci, (H + dh * k) % 360)))
    return out


class Hat:
    def __init__(self, d, view_right=None):
        self.d = {**DEFAULT, **d}
        g = self.d; self.H, self.r0, self.R, self.T = g['H'], g['r0'], g['R'], g['T']
        by = math.radians(g['bend_yaw']); self.bdir = (math.sin(by), math.cos(by))   # (x, z) lean direction
        if view_right is not None:
            # Stardew convention, as in the control: in every view the crown leans fully SIDEWAYS on
            # screen, toward the side the 3D lean points to; the toward/away part is dropped, so the
            # crown keeps its height and hook in all 4 views instead of foreshortening in two.
            lat = self.bdir[0] * view_right[0] + self.bdir[1] * view_right[2]
            sgn = 1.0 if lat >= 0 else -1.0
            self.bdir = (view_right[0] * sgn, view_right[2] * sgn)
        # crown axis as a polyline: arc length s in [0, H]; the axis tilts by bend (gentle lean) and
        # crook (tip bending over: angle grows ~ t^3, up to crook radians at the tip)
        N = 48; self.pts = [(0.0, 0.0, 0.0)]; x = y = z = 0.0
        lean = math.atan2(g['bend'], self.H)
        for i in range(1, N + 1):
            t = i / N; ang = lean * 2 * t + g['crook'] * t ** 3
            ds = self.H / N
            x += math.sin(ang) * ds * self.bdir[0]; z += math.sin(ang) * ds * self.bdir[1]; y += math.cos(ang) * ds
            self.pts.append((x, y, z))
        self.N = N
        # bounds for quick rejection
        self.bx = (min(p[0] for p in self.pts) - self.r0 - 1, max(p[0] for p in self.pts) + self.r0 + 1)
        self.bz = (min(p[2] for p in self.pts) - self.r0 - 1, max(p[2] for p in self.pts) + self.r0 + 1)
        self.by = (-self.T - 3, max(p[1] for p in self.pts) + 2.5)
        self.segs = []
        for i in range(N):
            a, b = self.pts[i], self.pts[i + 1]; ab = tuple(b[k] - a[k] for k in range(3))
            self.segs.append((a, ab, sum(c * c for c in ab), max(self.radius(i / N), self.radius((i + 1) / N))))

    def radius(self, t):
        g = self.d
        r = max(g['tip_r'], self.r0 * (1 - t) ** g['taper'])      # blunt tip: the control's tip folds, it is never a needle
        return r * (1 + g['flare'] * max(0.0, 0.25 - t) * 4)       # flare: wider just above the band

    def axis(self, h):
        """axis point (x, z) and radius at arc fraction h/H (used for decals and occlusion)."""
        t = max(0.0, min(1.0, h / self.H)); i = min(self.N - 1, int(t * self.N)); u = t * self.N - i
        a, b = self.pts[i], self.pts[i + 1]
        return a[0] + (b[0] - a[0]) * u, a[2] + (b[2] - a[2]) * u, self.radius(t)

    def axis_y(self, h):
        t = max(0.0, min(1.0, h / self.H)); i = min(self.N - 1, int(t * self.N)); u = t * self.N - i
        return self.pts[i][1] + (self.pts[i + 1][1] - self.pts[i][1]) * u

    def brim_y(self, rr):
        g = self.d; u = min(1.0, rr / self.R)
        return -g['droop'] * u * u + g['curl'] * u ** 4       # top surface height at radius rr

    def Rat(self, x, z):
        g = self.d; a = math.atan2(x, z)
        return self.R * (1 + g['wave'] * math.sin(g['lobes'] * a + g['wave_phase']))

    def hit(self, x, y, z):
        """part id at a 3D point or None.  y up, brim top at y=0 (centre)."""
        g = self.d; rr = math.hypot(x, z); Rl = self.Rat(x, z)
        if rr <= Rl:
            top = self.brim_y(rr)
            if top - self.T <= y <= top: return 'rim' if (g['rim'] and rr > Rl - 1.1) else 'brim'
        if g['tip_pom'] and math.dist((x, y, z), self.pts[-1]) <= g['pom_r']: return 'pom'
        if y >= -0.2 and self.bx[0] <= x <= self.bx[1] and self.bz[0] <= z <= self.bz[1] and y <= self.by[1]:
            t = self.near(x, y, z)
            if t is not None: return 'band' if g['band_lo'] <= y < g['band_h'] else 'crown'   # band raised above the brim's front edge so it reads from the front
        return None

    def near(self, x, y, z):
        """axis parameter t if (x,y,z) lies inside the swept crown, else None."""
        for i, (a, ab, L2, rmax) in enumerate(self.segs):
            ap0, ap1, ap2 = x - a[0], y - a[1], z - a[2]
            if abs(ap1) > rmax + 1.5 and abs(ap1 - ab[1]) > rmax + 1.5 and (ap1 < -rmax - 1.5 or ap1 > ab[1] + rmax + 1.5): continue
            u = (ap0 * ab[0] + ap1 * ab[1] + ap2 * ab[2]) / L2; u = 0.0 if u < 0 else 1.0 if u > 1 else u
            d2 = (ap0 - ab[0] * u) ** 2 + (ap1 - ab[1] * u) ** 2 + (ap2 - ab[2] * u) ** 2
            t = (i + u) / self.N; r = self.radius(t)
            if d2 <= r * r: return t                       # first (lowest) segment that contains the point
        return None

    def normal(self, part, x, y, z):
        if part == 'pom':
            return norm(tuple((x, y, z)[k] - self.pts[-1][k] for k in range(3)))
        if part in ('brim', 'rim'):
            rr = math.hypot(x, z) or 1e-6
            top = self.brim_y(rr)
            if y > top - 0.5:                                    # top surface (tilted by droop)
                slope = 2 * self.d['droop'] * rr / (self.R * self.R)
                return norm((x / rr * slope, 1.0, z / rr * slope))
            return norm((x / rr, -0.4, z / rr))                  # rim / underside
        t = self.near(x, y, z) or 0.0
        i = min(self.N - 1, int(t * self.N)); a, b = self.pts[i], self.pts[i + 1]
        ab = norm(tuple(b[k] - a[k] for k in range(3)))
        q = tuple(a[k] + (b[k] - a[k]) * (t * self.N - i) for k in range(3))
        rv = (x - q[0], y - q[1], z - q[2]); dot = sum(rv[k] * ab[k] for k in range(3))
        rad = norm(tuple(rv[k] - dot * ab[k] for k in range(3)))
        slope = self.r0 / self.H * self.d['taper']
        return norm(tuple(rad[k] + ab[k] * slope for k in range(3)))


def render(design, view):
    yaw = math.radians(VIEW_YAW[view]); cy, sy = math.cos(yaw), math.sin(yaw)
    hat = Hat(design, view_right=(cy, 0.0, -sy)); g = hat.d
    ce, se = math.cos(ELEV), math.sin(ELEV)
    # camera basis in world: right, up, forward(into scene)
    right = (cy, 0.0, -sy)
    fwd = (sy * ce, -se, cy * ce)          # looking down by ELEV
    fwd = (-fwd[0], fwd[1], -fwd[2])       # toward the hat from the viewer side (+z is the hat front)
    up = (-sy * se * -1, ce, cy * se * -1)
    up = norm((fwd[1] * right[2] - fwd[2] * right[1], fwd[2] * right[0] - fwd[0] * right[2], fwd[0] * right[1] - fwd[1] * right[0]))
    if up[1] < 0: up = tuple(-c for c in up)
    light = norm(tuple(right[i] * LIGHT_CAM[0] + up[i] * LIGHT_CAM[1] - fwd[i] * LIGHT_CAM[2] for i in range(3)))
    W = 20; cxp, cyp = 9.5, 10.0           # screen pixel of the brim-top centre (control: brim oval centred on row ~9)
    part = [[None] * W for _ in range(W)]; depth = [[1e9] * W for _ in range(W)]; shade = [[0.0] * W for _ in range(W)]
    for py in range(W):
        for px in range(W):
            sx, sy_ = px + 0.5 - cxp - 0.5, -(py + 0.5 - cyp)
            o = tuple(right[i] * sx + up[i] * sy_ - fwd[i] * 30 for i in range(3))
            t = 18.0
            while t < 44:
                p = tuple(o[i] + fwd[i] * t for i in range(3))
                h = hat.hit(*p)
                if h:
                    n = hat.normal(h, *p)
                    nv = n                                                    # world normal; light fixed in world
                    lam = max(0.0, sum(nv[i] * light[i] for i in range(3)))
                    s = 0.42 + 0.68 * lam
                    if h in ('brim', 'rim'): s = 0.40 + 0.42 * lam          # brim stays in the crown's value range (control)
                    if h in ('brim', 'rim'):
                        ax, az, r = hat.axis(0)
                        if math.hypot(p[0] - ax, p[2] - az) < r + 1.6 and p[1] > hat.brim_y(math.hypot(p[0], p[2])) - 0.5:
                            s *= 0.72                                         # occlusion under the crown
                    if h == 'crown' and g.get('wrinkles'):
                        ph = p[1] / hat.H
                        for w0 in g['wrinkles']:                               # a fold = thin dark ring, leaning with the bend
                            if abs(ph - w0 + 0.06 * (p[0] * hat.bdir[0] + p[2] * hat.bdir[1])) < 0.045: s *= 0.62
                    part[py][px], depth[py][px], shade[py][px] = h, t, s
                    break
                t += 0.06
    cam = dict(right=right, up=up, fwd=fwd, cxp=cxp, cyp=cyp)
    return part, depth, shade, hat, cam


def project(cam, p):
    """world point -> (px, py) screen pixel."""
    sx = sum(cam['right'][i] * p[i] for i in range(3)); sy = sum(cam['up'][i] * p[i] for i in range(3))
    return int(math.floor(sx + cam['cxp'] + 0.5)), int(math.floor(cam['cyp'] - sy))


def facing(cam, n):
    return -sum(cam['fwd'][i] * n[i] for i in range(3)) > 0.25


def colourise(design, view, decals=True):
    part, depth, shade, hat, cam = render(design, view); g = hat.d; n = g['ramp_steps']
    ramps = {'crown': ramp(g['base'], n), 'brim': ramp(g.get('brim_col') or g['base'], n), 'band': ramp(g['band'], max(3, n - 1)),
             'accent': ramp(g['accent'], 3), 'rim': ramp(g['rim'] or g['band'], max(3, n - 1)),
             'pom': ramp(g['tip_pom'] or g['accent'], 4)}
    W = 20; px = [[(0, 0, 0, 0)] * W for _ in range(W)]
    for y in range(W):
        for x in range(W):
            p = part[y][x]
            if not p: continue
            r = ramps[p]; k = max(1, min(len(r) - 1, int(shade[y][x] * (len(r) - 1) + 0.5)))   # step 0 reserved for outline
            px[y][x] = r[k] + (255,)
    # outlines: silhouette edge and depth-jump contours take the darkest step of their own ramp
    for y in range(W):
        for x in range(W):
            p = part[y][x]
            if not p: continue
            nb = [(y + dy, x + dx) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            edge = any(not (0 <= a < W and 0 <= b < W) or part[a][b] is None for a, b in nb)
            contour = any(0 <= a < W and 0 <= b < W and part[a][b] and depth[a][b] < depth[y][x] - 1.5 for a, b in nb)
            if edge or contour:
                lit = g['selout'] and edge and not contour and shade[y][x] > 0.82 and p not in ('brim', 'rim')
                px[y][x] = ramps[p][1 if lit else 0] + (255,)
    if g['spec']:
        # one highlight pixel: the brightest crown pixel that is not on the outline
        best = None
        for y in range(W):
            for x in range(W):
                if part[y][x] == 'crown' and px[y][x][:3] not in (ramps['crown'][0], ramps['crown'][1]):
                    if best is None or shade[y][x] > shade[best[0]][best[1]]: best = (y, x)
        if best and shade[best[0]][best[1]] > 0.8: px[best[0]][best[1]] = ramps['crown'][-1] + (255,)
    if decals:
        acc = ramps['accent']
        def put(x, y, c):
            if 0 <= x < W and 0 <= y < W and part[y][x]: px[y][x] = c + (255,)
        if g['buckle']:
            # buckle = point on the band surface facing +z (hat front); drawn only when it faces the camera
            yb_ = (g['band_lo'] + g['band_h']) / 2; ax, az, r = hat.axis(yb_); p3 = (ax, yb_, az + r); n3 = (0, 0, 1)
            if facing(cam, n3):
                bx, by = project(cam, p3)
                if g['buckle'] == 'square':
                    for dx in (0, 1): put(bx - 1 + dx, by, acc[2])
                    put(bx, by, acc[1])
                else:
                    put(bx, by, acc[2])
        for ch in g['charms']:
            # charm = shape stamp at (height fraction, angle around the crown; 0 = front)
            hf, ang, shape = ch['h'], math.radians(ch.get('angle', 0)), ch.get('shape', 'star')
            ax, az, r = hat.axis(hf * hat.H); y3 = hat.axis_y(hf * hat.H)
            n3 = (math.sin(ang), 0, math.cos(ang)); p3 = (ax + r * n3[0], y3, az + r * n3[2])
            if not facing(cam, n3): continue
            cx_, cy_ = project(cam, p3)
            stamp = {'star': [(0, -1, 2), (-1, 0, 2), (0, 0, 2), (1, 0, 2), (0, 1, 1)],
                     'moon': [(0, -1, 2), (-1, 0, 2), (-1, 1, 1), (0, 1, 2)],
                     'dot': [(0, 0, 2)], 'patch': [(0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 0)]}[shape]
            for dx, dy, k in stamp: put(cx_ + dx, cy_ + dy, acc[k])
    return px


def strip(design):
    views = [colourise(design, v) for v in ('front', 'right', 'left', 'back')]
    return [sum((views[v][y] for v in range(4)), []) for y in range(20)]


def save_sheet(path, strips, s=6, game=4):
    rowh = 20 * s + 8; W = 4 * (20 * s + 6) + 16 + 4 * (20 * game + 4)
    out = [[(160, 160, 160, 255)] * W for _ in range(rowh * len(strips))]
    for r, st in enumerate(strips):
        for v in range(4):
            for y in range(20):
                for x in range(20):
                    p = st[y][v * 20 + x]
                    for dy in range(s):
                        for dx in range(s):
                            out[r * rowh + y * s + dy][v * (20 * s + 6) + x * s + dx] = p if p[3] else (200, 200, 200, 255) if ((x + y) % 2) else (185, 185, 185, 255)
                    X0 = 4 * (20 * s + 6) + 16 + v * (20 * game + 4)
                    for dy in range(game):
                        for dx in range(game):
                            out[r * rowh + y * game + dy][X0 + x * game + dx] = p if p[3] else (96, 128, 72, 255)
    png.write(path, W, len(out), out)


if __name__ == '__main__':
    designs = json.load(open(sys.argv[1])); od = sys.argv[2]; os.makedirs(od, exist_ok=True)
    strips = [strip(d) for d in designs]
    save_sheet(os.path.join(od, 'forge_sheet.png'), strips)
    json.dump([{'design': d, 'strip': [[list(p) for p in row] for row in st]} for d, st in zip(designs, strips)],
              open(os.path.join(od, 'forge_strips.json'), 'w'))
    print(len(strips), 'designs ->', od)
