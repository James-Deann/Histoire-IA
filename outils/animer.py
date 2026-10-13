#!/usr/bin/env python3
"""Génère un épisode animé de la série Pitchou (personnages dessinés, voix, lip-sync, musique).

Usage :
    python3 outils/animer.py pitchou/episodes/ep01.json [--apercu]

Sorties (dans sortie/pitchou/) :
    epNN.mp4  vidéo verticale 1080x1920, 30 i/s, sous-titres incrustés
    epNN.srt  sous-titres (pour CapCut ou les sous-titres TikTok)
    epNN.wav  bande son finale

--apercu rend une vidéo en 540x960 à 15 i/s, plus rapide.
"""
import argparse
import io
import json
import math
import random
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import cairosvg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import personnages  # noqa: E402
from generer import synthese, morceaux, ts_srt, ts_ass, ass_couleur  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent
SR = 44100
L, H = 1080, 1920
SOL = 1400            # hauteur du comptoir où se posent les personnages
PAUSE, PAUSE_SCENE = 0.22, 0.6
DEBUT, FIN = 0.5, 2.2
# Taille de rendu de chaque personnage selon le nombre de personnages à l'écran.
TAILLES = {1: 1000, 2: 690, 3: 500}
ECHELLE = {"pitchou": 0.88, "chocolatine": 1.0, "croissant": 0.92}


# ---------------------------------------------------------------- décor

def decor():
    rayures = "".join(f'<rect x="{x}" y="0" width="45" height="{H}" fill="#FFE3BE"/>' for x in range(0, L, 90))
    store = "".join(
        f'<path d="M{x} 0 H{x + 90} V150 A45 45 0 0 1 {x} 150 Z" fill="{"#E8574A" if i % 2 == 0 else "#FFF5E8"}"/>'
        for i, x in enumerate(range(0, L, 90)))
    def etagere(y):
        pains = []
        for i, x in enumerate(range(60, L, 170)):
            if i % 2 == 0:  # baguette
                pains.append(f'<rect x="{x}" y="{y - 48}" width="150" height="40" rx="20" fill="#D9963F"/>'
                             f'<path d="M{x + 30} {y - 38} l18 20 M{x + 70} {y - 38} l18 20 M{x + 110} {y - 38} l18 20" '
                             f'stroke="#B8752B" stroke-width="6" stroke-linecap="round"/>')
            else:  # brioche
                pains.append(f'<circle cx="{x + 75}" cy="{y - 42}" r="40" fill="#E2A04C"/>'
                             f'<circle cx="{x + 75}" cy="{y - 82}" r="20" fill="#E8AE5C"/>')
        return (f'<g opacity=".55">{"".join(pains)}</g>'
                f'<rect x="0" y="{y}" width="{L}" height="26" fill="#A8693A"/>'
                f'<rect x="0" y="{y + 26}" width="{L}" height="10" fill="#7E4A26" opacity=".6"/>')
    planches = "".join(f'<rect x="0" y="{y}" width="{L}" height="4" fill="#8E5527" opacity=".45"/>'
                       for y in range(SOL + 120, H, 110))
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L} {H}" width="{L}" height="{H}">'
         '<defs><linearGradient id="mur" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFF1DC"/>'
         '<stop offset="1" stop-color="#FFD6A0"/></linearGradient>'
         '<radialGradient id="lum" cx=".2" cy=".15" r=".7"><stop offset="0" stop-color="#fff" stop-opacity=".7"/>'
         '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
         '<linearGradient id="bois" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#C98446"/>'
         '<stop offset="1" stop-color="#9C5E2E"/></linearGradient></defs>'
         f'<rect width="{L}" height="{H}" fill="url(#mur)"/>{rayures}'
         f'{etagere(820)}{etagere(1110)}'
         f'<rect width="{L}" height="{H}" fill="url(#lum)"/>{store}'
         f'<rect x="0" y="{SOL}" width="{L}" height="{H - SOL}" fill="url(#bois)"/>'
         f'<rect x="0" y="{SOL - 18}" width="{L}" height="34" rx="6" fill="#E3A465"/>{planches}</svg>')
    png = cairosvg.svg2png(bytestring=s.encode(), output_width=L, output_height=H)
    img = Image.open(io.BytesIO(png)).convert("RGB")
    # Étagères légèrement floues pour garder l'attention sur les personnages.
    haut = img.crop((0, 160, L, SOL - 20)).filter(ImageFilter.GaussianBlur(3))
    img.paste(haut, (0, 160))
    return img


# ---------------------------------------------------------------- sons

def pluck(freq, dur, rng):
    """Corde pincée (Karplus-Strong) : son doux type ukulélé."""
    n = int(SR * dur)
    p = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, p)
    out = np.empty(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.996
    return out


def musique(total, seed=3):
    """Petite boucle guillerette I–V–vi–IV, 112 bpm."""
    rng = np.random.default_rng(seed)
    noire = 60 / 112
    note = lambda m: 440 * 2 ** ((m - 69) / 12)
    accords = [(60, 64, 67), (55, 59, 62), (57, 60, 64), (53, 57, 60)]  # do, sol, la m, fa
    mesure = int(SR * noire * 4)
    boucle = np.zeros(mesure * 4 + SR)
    cache = {}
    for a, acc in enumerate(accords):
        base = a * mesure
        motif = [acc[0], acc[1], acc[2], acc[1] + 12, acc[2], acc[1], acc[0] + 12, acc[2]]
        for k, m in enumerate(motif):
            if m not in cache:
                cache[m] = pluck(note(m), 0.9, rng)
            d = base + int(k * SR * noire / 2)
            boucle[d:d + len(cache[m])] += cache[m] * (0.55 if k % 2 else 0.75)
        basse = acc[0] - 24
        t = np.arange(int(SR * noire * 1.8)) / SR
        b = np.sin(2 * np.pi * note(basse) * t) * np.exp(-t * 2.5)
        for k in (0, 2):
            d = base + int(k * SR * noire)
            boucle[d:d + len(b)] += 0.6 * b
    boucle = boucle[:mesure * 4]
    reps = int(math.ceil(total * SR / len(boucle)))
    m = np.tile(boucle, reps)[:int(total * SR)]
    m /= np.max(np.abs(m)) + 1e-9
    fondu = int(SR * 1.5)
    m[-fondu:] *= np.linspace(1, 0, fondu)
    return m


def sfx(nom):
    if nom == "pop":
        t = np.arange(int(SR * 0.09)) / SR
        f = 500 + 9000 * t
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 40)
    if nom == "boing":
        t = np.arange(int(SR * 0.45)) / SR
        f = 320 * np.exp(-t * 2) * (1 + 0.25 * np.sin(2 * np.pi * 14 * t))
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6)
    if nom == "tada":
        t = np.arange(int(SR * 0.7)) / SR
        return sum(np.sin(2 * np.pi * f * t) for f in (523, 659, 784, 1047)) / 4 * np.exp(-t * 4)
    raise ValueError(nom)


def lire_wav(p):
    with wave.open(str(p)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
        if w.getnchannels() == 2:
            a = a.reshape(-1, 2).mean(axis=1)
        assert w.getframerate() == SR
    return a


def ecrire_wav(p, a):
    a = np.clip(a, -1, 1)
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- montage

def construire(ep, tmp):
    """Synthétise les voix et calcule la chronologie de l'épisode."""
    persos = ep["personnages"]
    pistes, chrono, t = [], [], DEBUT
    for s, scene in enumerate(ep["scenes"]):
        if s > 0:
            t += PAUSE_SCENE - PAUSE
        debut_scene = t
        for i, rep in enumerate(scene["repliques"]):
            pid, expr, texte = rep[:3]
            opts = rep[3] if len(rep) > 3 else {}
            dest = tmp / f"s{s:02}_{i:02}.wav"
            synthese(persos[pid], texte, dest, tmp)
            a = lire_wav(dest)
            chrono.append({"scene": s, "perso": pid, "expr": expr, "texte": texte, "debut": t,
                           "fin": t + len(a) / SR, "opts": opts})
            pistes.append((t, a))
            t += len(a) / SR + PAUSE
        scene["_debut"] = debut_scene
    total = t - PAUSE + FIN
    voix = np.zeros(int(total * SR) + SR)
    for d, a in pistes:
        i = int(d * SR)
        voix[i:i + len(a)] += a
    voix = voix[:int(total * SR)]
    return voix, chrono, total


def bande_son(voix, chrono, scenes, total):
    son = voix * 0.95
    son += 0.07 * musique(total)[:len(son)]
    def poser(t, nom, vol):
        e = sfx(nom) * vol
        i = int(t * SR)
        son[i:i + len(e)] += e[:len(son) - i]
    for s, sc in enumerate(scenes):
        if s > 0:
            poser(sc["_debut"] - 0.25, "pop", 0.35)
    for c in chrono:
        if c["expr"] == "choc":
            poser(c["debut"] - 0.12, "boing", 0.3)
        if c["opts"].get("son"):
            poser(c["debut"] - 0.1, c["opts"]["son"], 0.35)
    poser(total - FIN, "tada", 0.3)
    return son / max(1.0, np.max(np.abs(son)) / 0.97)


def enveloppe(voix, fps, total):
    n = int(total * fps)
    pas = SR // fps
    env = np.array([np.sqrt(np.mean(voix[i * pas:(i + 1) * pas] ** 2)) if (i + 1) * pas <= len(voix) else 0
                    for i in range(n)])
    return env / (np.percentile(env[env > 0], 95) + 1e-9) if np.any(env > 0) else env


def sous_titres(ep, chrono, total, base):
    persos = ep["personnages"]
    srt, evts = [], []
    for c in chrono:
        bouts = morceaux(c["texte"], max_mots=5)
        poids = [len(b) + 6 for b in bouts]
        t = c["debut"]
        p = persos[c["perso"]]
        for b, w in zip(bouts, poids):
            d = (c["fin"] - c["debut"]) * w / sum(poids)
            srt.append((t, t + d, f"{p['nom']} : {b}"))
            fin = t + d + (PAUSE if b == bouts[-1] else 0)
            nom = "" if c["perso"] == "narrateur" else f"{{\\fs50\\c{ass_couleur(p['couleur'])}}}{p['nom'].upper()}\\N"
            style = "Narration" if c["perso"] == "narrateur" else "Texte"
            evts.append(f"Dialogue: 1,{ts_ass(t)},{ts_ass(fin)},{style},,0,0,0,,"
                        f"{{\\fscx70\\fscy70\\t(0,90,\\fscx100\\fscy100)}}{nom}{{\\fs84\\c&H00FFFFFF&}}{b}")
            t += d
    base.with_suffix(".srt").write_text(
        "\n".join(f"{i}\n{ts_srt(a)} --> {ts_srt(b)}\n{txt}\n" for i, (a, b, txt) in enumerate(srt, 1)),
        encoding="utf-8")
    entete = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {L}", f"PlayResY: {H}", "WrapStyle: 0", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding",
        "Style: Texte,Lilita One,84,&H00FFFFFF,&H00FFFFFF,&H00301A0B,&H64000000,0,0,0,0,100,100,1,0,1,7,3,5,70,70,0,1",
        "Style: Narration,Lilita One,84,&H00FFFFFF,&H00FFFFFF,&H00703010,&H64000000,0,0,0,0,100,100,1,0,1,7,3,5,70,70,0,1",
        "Style: Titre,Lilita One,78,&H00FFFFFF,&H00FFFFFF,&H002A3FD8,&H64000000,0,0,0,0,100,100,1,-2,1,8,4,8,50,50,215,1",
        "Style: Fin,Lilita One,76,&H0061C8FF,&H00FFFFFF,&H00301A0B,&H64000000,0,0,0,0,100,100,1,0,1,7,3,5,60,60,0,1",
        "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        f"Dialogue: 0,{ts_ass(0)},{ts_ass(total)},Titre,,0,0,0,,{{\\fad(400,0)}}{ep['titre']}",
    ]
    evts = [e.replace("0,0,0,,{\\fscx70", "0,0,0,,{\\pos(540,620)\\fscx70", 1) for e in evts]
    entete.append(f"Dialogue: 2,{ts_ass(total - FIN + 0.2)},{ts_ass(total)},Fin,,0,0,0,,"
                  f"{{\\pos(540,620)\\fad(200,0)\\fscx70\\fscy70\\t(0,120,\\fscx100\\fscy100)}}{ep['fin']}")
    base.with_suffix(".ass").write_text("\n".join(entete + evts) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- image par image

_ombres = {}


def ombre(w):
    """Ombre douce posée sur le comptoir sous un personnage."""
    if w not in _ombres:
        o = Image.new("RGBA", (w + 40, 70), (0, 0, 0, 0))
        ImageDraw.Draw(o).ellipse((20, 20, w + 20, 50), fill=(90, 45, 15, 90))
        _ombres[w] = o.filter(ImageFilter.GaussianBlur(8))
    return _ombres[w]


def rendre(ep, chrono, env, total, fps, echelle, sortie_video, audio, ass):
    fond = decor()
    rng = random.Random(7)
    lw, lh = int(L * echelle), int(H * echelle)
    # Clignements : instants aléatoires par personnage.
    clins = {p: sorted(rng.uniform(0, total) for _ in range(int(total / 3.2))) for p in ep["personnages"]}
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{lw}x{lh}",
         "-r", str(fps), "-i", "-", "-i", str(audio),
         "-vf", f"ass={ass}:fontsdir={RACINE / 'polices'}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
         str(sortie_video)], stdin=subprocess.PIPE)
    scenes = ep["scenes"]
    n = int(total * fps)
    expr_courante, scene_courante = {}, None
    for f in range(n):
        t = f / fps
        s = max(i for i, sc in enumerate(scenes) if sc["_debut"] - 0.25 <= t or i == 0)
        sc = scenes[s]
        actifs = [c for c in chrono if c["debut"] - 0.05 <= t <= c["fin"] + PAUSE and c["scene"] == s]
        parle = actifs[0] if actifs else None
        # Expressions : celle de la réplique en cours pour qui parle, les réactions pour les autres.
        if s != scene_courante:
            expr_courante = {p: sc.get("expressions", {}).get(p, "normal") for p in sc["presents"]}
            scene_courante = s
        if parle:
            if parle["perso"] in expr_courante:
                expr_courante[parle["perso"]] = parle["expr"]
            for p, e in parle["opts"].get("reactions", {}).items():
                expr_courante[p] = e
        img = fond.copy()
        presents = sc["presents"]
        taille = TAILLES[len(presents)]
        largeur = L / len(presents)
        zoom, cx_zoom, secousse = 1.0, L / 2, (0, 0)
        for k, p in enumerate(presents):
            cx = largeur * (k + 0.5)
            ta = int(taille * ECHELLE[p])
            parle_moi = parle is not None and parle["perso"] == p and parle["debut"] <= t <= parle["fin"]
            a = env[f] if parle_moi and f < len(env) else 0.0
            bouche = parle_moi and a > 0.18 and (f % 2 == 0 or a > 0.55)
            ferme = any(c <= t < c + 0.13 for c in clins[p])
            e = expr_courante.get(p, "normal")
            spr = personnages.image(p, ta, expression=e, yeux_fermes=ferme, bouche_ouverte=bouche,
                                    bras_haut=e in ("content", "choc") and (parle_moi or e == "choc"))
            # Respiration, rebond quand il parle, apparition en « pop » au début de la scène.
            ph = k * 1.7
            sy = 1 + 0.018 * math.sin(2 * math.pi * 0.55 * t + ph)
            dy = 0.0
            if parle_moi:
                sy += 0.035 * min(1.0, a) * math.sin(2 * math.pi * 3.2 * t)
                dy = -abs(math.sin(2 * math.pi * 1.6 * t)) * 16 * min(1.0, a + 0.3)
            age = t - sc["_debut"] + 0.25
            pop = 1.0
            if age < 0.35:
                x = max(0.0, age / 0.35)
                pop = 0.4 + 0.6 * (1 - (1 - x) ** 3) + 0.12 * math.sin(math.pi * x)
            w, h = max(1, int(ta * pop / sy ** 0.5)), max(1, int(ta * pop * sy))
            spr2 = spr.resize((w, h), Image.BILINEAR)
            # Les pieds (y≈500/600 du dessin) restent posés sur le comptoir.
            px, py = int(cx - w / 2), int(SOL + 12 - h * 500 / 600 + dy)
            o = ombre(int(w * 0.62) // 8 * 8)
            img.paste(o, (int(cx - o.width / 2), SOL + 10 - o.height // 2), o)
            img.paste(spr2, (px, py), spr2)
            if parle_moi:
                cx_zoom = cx
                if e == "choc" and t - parle["debut"] < 0.35:
                    secousse = (rng.randint(-14, 14), rng.randint(-10, 10))
        # Léger zoom lent vers celui qui parle (garde l'image vivante).
        if parle:
            prog = min(1.0, (t - parle["debut"]) / max(0.5, parle["fin"] - parle["debut"]))
            zoom = 1.0 + 0.05 * (0.5 - 0.5 * math.cos(math.pi * prog))
        if zoom > 1.001 or secousse != (0, 0):
            cw, ch = L / zoom, H / zoom
            x0 = min(max(0, cx_zoom - cw / 2), L - cw) + secousse[0]
            y0 = (H - ch) * 0.62 + secousse[1]
            img = img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch)))
        img = img.resize((lw, lh), Image.BILINEAR) if img.size != (lw, lh) else img
        ff.stdin.write(img.tobytes())
        if f % (fps * 10) == 0:
            print(f"  image {f}/{n}", flush=True)
    ff.stdin.close()
    if ff.wait():
        raise SystemExit("ffmpeg a échoué")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--apercu", action="store_true")
    args = ap.parse_args()
    chemin = Path(args.episode)
    ep = json.loads(chemin.read_text(encoding="utf-8"))
    dossier = RACINE / "sortie" / "pitchou"
    dossier.mkdir(parents=True, exist_ok=True)
    base = dossier / chemin.stem
    fps, echelle = (15, 0.5) if args.apercu else (30, 1.0)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        print("Voix…", flush=True)
        voix, chrono, total = construire(ep, tmp)
        son = bande_son(voix, chrono, ep["scenes"], total)
        ecrire_wav(base.with_suffix(".wav"), son)
        sous_titres(ep, chrono, total, base)
        print(f"Durée : {int(total // 60)}:{total % 60:05.2f}"
              f"{'' if total >= 61 else '  ATTENTION : moins d une minute, rallonger le texte'}", flush=True)
        print("Images…", flush=True)
        rendre(ep, chrono, enveloppe(voix, fps, total), total, fps, echelle,
               base.with_suffix(".mp4"), base.with_suffix(".wav"), base.with_suffix(".ass"))
    print(f"OK -> {base.with_suffix('.mp4')}")


if __name__ == "__main__":
    main()
