"""Dessins vectoriels (SVG) des personnages de la série Pitchou.

Chaque personnage se dessine dans un carré de 600x600 avec :
    expression     normal | content | choc | triste | colere
    yeux_fermes    clignement
    bouche_ouverte pour le lip-sync
    bras_haut      bras levés (joie, surprise)
"""
import io

import cairosvg
from PIL import Image

CONTOUR = "#7A3F12"
CHOCO = "#4B230E"

# Couleurs de pâte : (haut, bas, reflet, plis)
PATES = {
    "pitchou": ("#F2B257", "#C97A2C", "#FFE2A6", "#A85E22"),
    "chocolatine": ("#F6BD5C", "#D3862F", "#FFE7B0", "#AF6324"),
    "croissant": ("#EDA94C", "#BF6E25", "#FFDB9A", "#9C5520"),
}


def _defs(nom):
    haut, bas, _, _ = PATES[nom]
    return (f'<defs><linearGradient id="pate" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{haut}"/><stop offset="1" stop-color="{bas}"/></linearGradient>'
            f'<radialGradient id="joue"><stop offset="0" stop-color="#FF7F86" stop-opacity=".75"/>'
            f'<stop offset="1" stop-color="#FF7F86" stop-opacity="0"/></radialGradient></defs>')


def _oeil(x, y, expression, ferme, cils=False, mi_clos=False, cote=1, echelle=1.0):
    """Un oeil centré en (x, y). cote = -1 pour l'oeil gauche, 1 pour le droit."""
    s = [f'<g transform="translate({x},{y}) scale({echelle})">']
    trait = 'stroke="#2A1405" stroke-width="7" stroke-linecap="round" fill="none"'
    if ferme:
        s.append(f'<path d="M-27 2 Q0 18 27 2" {trait}/>')
    elif expression == "content":
        s.append(f'<path d="M-27 10 Q0 -24 27 10" {trait}/>')
    elif expression == "choc":
        s.append('<ellipse rx="35" ry="43" fill="#fff" stroke="#2A1405" stroke-width="6"/>'
                 '<circle r="13" fill="#2A1405"/><circle cx="-4" cy="-5" r="4" fill="#fff"/>')
    else:
        ry = 31 if expression == "colere" else 39
        s.append(f'<clipPath id="oeil{cote}"><ellipse rx="31" ry="{ry}"/></clipPath>'
                 f'<ellipse rx="31" ry="{ry}" fill="#2A1405"/>'
                 f'<circle cx="-10" cy="-14" r="12" fill="#fff"/>'
                 f'<circle cx="11" cy="13" r="5.5" fill="#fff" opacity=".9"/>')
        if mi_clos:
            s.append(f'<path d="M-36 -2 Q0 -12 36 -2 L36 -48 L-36 -48 Z" fill="#D98A3A" clip-path="url(#oeil{cote})"/>'
                     f'<path d="M-33 -4 Q0 -14 33 -4" {trait}/>')
    if cils and not ferme and expression != "content":
        haut = -10 if mi_clos else -36
        s.append(f'<path d="M{cote * 24} {haut} l{cote * 14} -12 M{cote * 30} {haut + 8} l{cote * 16} -6" '
                 f'stroke="#2A1405" stroke-width="5" stroke-linecap="round"/>')
    if expression == "triste":
        s.append(f'<path d="M{-cote * 26} -66 L{cote * 26} -52" {trait}/>')
    elif expression == "colere":
        s.append(f'<path d="M{-cote * 26} -42 L{cote * 30} -62" stroke="#2A1405" stroke-width="9" '
                 f'stroke-linecap="round"/>')
    s.append("</g>")
    return "".join(s)


def _bouche(x, y, expression, ouverte):
    t = f'transform="translate({x},{y})"'
    trait = 'stroke="#2A1405" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"'
    if expression == "choc":
        r = (17, 23) if ouverte else (10, 12)
        return f'<ellipse {t} rx="{r[0]}" ry="{r[1]}" fill="#5A1E10" {trait}/>'
    if expression == "triste":
        if ouverte:
            return (f'<g {t}><path d="M-18 14 Q0 -12 18 14 Z" fill="#5A1E10" {trait}/></g>')
        return f'<path {t} d="M-17 10 Q0 -5 17 10" fill="none" {trait}/>'
    if expression == "colere":
        h = 22 if ouverte else 10
        return (f'<g {t}><rect x="-22" y="-4" width="44" height="{h}" rx="6" fill="#5A1E10" {trait}/>'
                f'<path d="M-18 1 H18" stroke="#fff" stroke-width="5"/></g>')
    if ouverte or expression == "content":
        p = 30 if ouverte else 18
        return (f'<g {t}><path d="M-26 -6 Q0 -9 26 -6 Q22 {p} 0 {p + 2} Q-22 {p} -26 -6 Z" fill="#5A1E10" {trait}/>'
                f'<ellipse cy="{p - 8}" rx="12" ry="{6 if p > 20 else 4}" fill="#F27C7C"/></g>')
    return f'<path {t} d="M-19 -2 Q-9 10 0 2 Q9 10 19 -2" fill="none" {trait}/>'


def _visage(cx, cy, expression, ferme, ouverte, ecart=62, joues=104, **kw):
    s = [f'<ellipse cx="{cx - joues}" cy="{cy + 42}" rx="34" ry="20" fill="url(#joue)"/>',
         f'<ellipse cx="{cx + joues}" cy="{cy + 42}" rx="34" ry="20" fill="url(#joue)"/>',
         _oeil(cx - ecart, cy - 8, expression, ferme, cote=-1, **kw),
         _oeil(cx + ecart, cy - 8, expression, ferme, cote=1, **kw),
         _bouche(cx, cy + 50, expression, ouverte)]
    if expression == "triste" and not ferme:
        s.append(f'<path d="M{cx + ecart + 18} {cy + 22} q10 16 0 24 q-10 -8 0 -24 Z" fill="#7FC8FF" '
                 f'stroke="#3E8FD0" stroke-width="3"/>')
    return "".join(s)


def _bras(nom, haut):
    _, bas, _, _ = PATES[nom]
    if haut:
        poses = [(118, 300, -35), (482, 300, 35)]
        return "".join(f'<ellipse cx="{x}" cy="{y - 40}" rx="20" ry="40" transform="rotate({a} {x} {y})" '
                       f'fill="{bas}" stroke="{CONTOUR}" stroke-width="6"/>' for x, y, a in poses)
    poses = [(112, 430, 28), (488, 430, -28)]
    return "".join(f'<ellipse cx="{x}" cy="{y + 22}" rx="20" ry="36" transform="rotate({a} {x} {y})" '
                   f'fill="{bas}" stroke="{CONTOUR}" stroke-width="6"/>' for x, y, a in poses)


def _pieds(xs, y):
    return "".join(f'<ellipse cx="{x}" cy="{y}" rx="40" ry="19" fill="#A85A1C" stroke="{CONTOUR}" '
                   f'stroke-width="6"/>' for x in xs)


def _pain_au_chocolat(nom, expression, ferme, ouverte, bras_haut):
    _, _, reflet, plis = PATES[nom]
    s = [_defs(nom), _pieds((228, 372), 492)]
    if not bras_haut:
        s.append(_bras(nom, False))
    corps = ("M108 305 C108 218 172 196 300 196 C428 196 492 218 492 305 L492 418 "
             "C492 470 452 482 300 482 C148 482 108 470 108 418 Z")
    s.append(f'<path d="{corps}" fill="url(#pate)" stroke="{CONTOUR}" stroke-width="7"/>')
    s.append(f'<ellipse cx="236" cy="236" rx="96" ry="22" fill="{reflet}" opacity=".65" transform="rotate(-4 236 236)"/>')
    s.append(f'<ellipse cx="380" cy="228" rx="30" ry="9" fill="{reflet}" opacity=".5"/>')
    pli = f'stroke="{plis}" stroke-width="6" stroke-linecap="round" fill="none" opacity=".6"'
    s.append(f'<path d="M126 268 C220 252 380 252 474 268" {pli}/>')
    s.append(f'<path d="M124 448 C220 462 380 462 476 448" {pli}/>')
    # Les deux barres de chocolat qui dépassent de chaque côté.
    for x in (86, 474):
        for y in (304, 372):
            s.append(f'<rect x="{x}" y="{y}" width="40" height="28" rx="11" fill="{CHOCO}" stroke="#2E1407" stroke-width="5"/>'
                     f'<rect x="{x + 9}" y="{y + 6}" width="16" height="6" rx="3" fill="#7A4524"/>')
    if bras_haut:
        s.append(_bras(nom, True))
    if nom == "pitchou":
        # La petite mèche feuilletée sur la tête.
        s.append(f'<path d="M300 199 C284 160 330 140 342 168 C350 188 322 194 318 178" fill="none" '
                 f'stroke="{CONTOUR}" stroke-width="8" stroke-linecap="round"/>')
        s.append(_visage(300, 345, expression, ferme, ouverte, echelle=1.15))
    else:
        # Béret rouge du Sud-Ouest, penché.
        s.append('<g transform="rotate(14 360 196)"><ellipse cx="360" cy="196" rx="96" ry="30" fill="#D7263D" '
                 'stroke="#7E1020" stroke-width="6"/><ellipse cx="350" cy="186" rx="60" ry="12" fill="#F05165" opacity=".7"/>'
                 '<path d="M360 167 q4 -18 16 -20" stroke="#7E1020" stroke-width="7" stroke-linecap="round" fill="none"/></g>')
        s.append(_visage(300, 348, expression, ferme, ouverte, cils=True, mi_clos=(expression == "normal")))
    return s


def _croissant(expression, ferme, ouverte, bras_haut):
    _, _, reflet, plis = PATES["croissant"]
    s = [_defs("croissant"), _pieds((240, 360), 480)]
    if not bras_haut:
        s.append(_bras("croissant", False))
    # Segments du croissant, des pointes vers le centre.
    segments = [(92, 438, 50, 46, -42), (508, 438, 50, 46, 42),
                (176, 392, 84, 80, -22), (424, 392, 84, 80, 22), (300, 340, 128, 122, 0)]
    for x, y, rx, ry, a in segments:
        s.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" transform="rotate({a} {x} {y})" '
                 f'fill="url(#pate)" stroke="{CONTOUR}" stroke-width="7"/>')
        s.append(f'<ellipse cx="{x - rx * .2}" cy="{y - ry * .62}" rx="{rx * .5}" ry="{ry * .14}" '
                 f'transform="rotate({a} {x} {y})" fill="{reflet}" opacity=".6"/>')
    s.append(f'<path d="M210 262 C260 236 340 236 390 262" stroke="{plis}" stroke-width="6" fill="none" '
             f'stroke-linecap="round" opacity=".6"/>')
    if bras_haut:
        s.append(_bras("croissant", True))
    s.append(_visage(300, 330, expression, ferme, ouverte, ecart=56, joues=88))
    # Moustache grise et monocle.
    s.append('<path d="M300 366 C280 350 240 352 232 376 C252 368 276 378 300 374 C324 378 348 368 368 376 '
             'C360 352 320 350 300 366 Z" fill="#E9E1D8" stroke="#8C8279" stroke-width="5" stroke-linejoin="round"/>')
    if not ferme and expression not in ("content",):
        s.append('<circle cx="356" cy="322" r="44" fill="#BFE6FF" fill-opacity=".18" stroke="#D9A31A" stroke-width="6"/>'
                 '<path d="M398 336 Q430 400 412 460" stroke="#D9A31A" stroke-width="3" fill="none"/>')
    return s


def svg(nom, expression="normal", yeux_fermes=False, bouche_ouverte=False, bras_haut=False):
    if nom == "croissant":
        corps = _croissant(expression, yeux_fermes, bouche_ouverte, bras_haut)
    else:
        corps = _pain_au_chocolat(nom, expression, yeux_fermes, bouche_ouverte, bras_haut)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
            + "".join(corps) + "</svg>")


_cache = {}


def image(nom, taille, **etat):
    """Rendu PNG (PIL, RGBA) d'un personnage, mis en cache."""
    cle = (nom, taille, tuple(sorted(etat.items())))
    if cle not in _cache:
        png = cairosvg.svg2png(bytestring=svg(nom, **etat).encode(), output_width=taille, output_height=taille)
        _cache[cle] = Image.open(io.BytesIO(png)).convert("RGBA")
    return _cache[cle]
