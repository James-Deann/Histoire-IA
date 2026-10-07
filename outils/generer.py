#!/usr/bin/env python3
"""Génère l'audio multi-voix, les sous-titres et la vidéo TikTok d'une histoire.

Usage :
    python3 outils/generer.py histoires/monte-cristo/histoire.json [--sans-video]

Sorties (dans sortie/<nom-histoire>/) :
    partieN.mp3  audio final (voix + ambiance)
    partieN.srt  sous-titres (à importer dans CapCut / TikTok si besoin)
    partieN.ass  sous-titres stylés (couleur par personnage)
    partieN.mp4  vidéo verticale 1080x1920 avec sous-titres incrustés
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig

RACINE = Path(__file__).resolve().parent.parent
VOIX = {
    "gilles": RACINE / "voix" / "fr-gilles-low.onnx",
    "siwis": RACINE / "voix" / "fr-siwis-medium.onnx",
}
EFFETS = {
    None: "",
    "salle": "aecho=0.8:0.6:40|70:0.12|0.08",
    "cachot": "aecho=0.8:0.7:90|160:0.28|0.18",
    "comte": "equalizer=f=120:t=q:w=1:g=4,aecho=0.8:0.6:60|120:0.22|0.12",
}
SR = 44100
PAUSE_MIN, PAUSE_MAX = 0.25, 0.9
DEBUT, FIN = 0.4, 1.2  # silence avant la première réplique / après la dernière


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duree(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout
    return float(out)


_voix_cache = {}


def synthese(perso, texte, dest, tmp):
    if perso["voix"] not in _voix_cache:
        _voix_cache[perso["voix"]] = PiperVoice.load(str(VOIX[perso["voix"]]))
    brut = tmp / (dest.stem + "_brut.wav")
    with wave.open(str(brut), "wb") as w:
        _voix_cache[perso["voix"]].synthesize_wav(
            texte, w, syn_config=SynthesisConfig(length_scale=perso["vitesse"], noise_scale=0.6, noise_w_scale=0.8)
        )
    filtres = [f"aresample={SR}"]
    if perso["hauteur"]:
        filtres.append(f"rubberband=pitch={2 ** (perso['hauteur'] / 12):.4f}:formant=preserved")
    if EFFETS[perso["effet"]]:
        filtres.append(EFFETS[perso["effet"]])
    filtres += ["silenceremove=start_periods=1:start_threshold=-50dB", "areverse",
                "silenceremove=start_periods=1:start_threshold=-50dB", "areverse",
                "loudnorm=I=-16:TP=-1.5:LRA=7", f"aresample={SR}"]
    run(["ffmpeg", "-y", "-i", str(brut), "-af", ",".join(filtres), "-ac", "1", str(dest)])


def morceaux(texte, max_mots=7):
    """Découpe une réplique en sous-titres courts, de préférence sur la ponctuation."""
    phrases = re.split(r"(?<=[.!?…:])\s+", texte)
    res = []
    for p in phrases:
        mots = p.split()
        while len(mots) > max_mots:
            coupe = max_mots
            for i in range(max_mots, 2, -1):
                if mots[i - 1].endswith(","):
                    coupe = i
                    break
            res.append(" ".join(mots[:coupe]))
            mots = mots[coupe:]
        if mots:
            res.append(" ".join(mots))
    return res


def ts_srt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def ts_ass(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02}:{cs // 100 % 60:02}.{cs % 100:02}"


def ass_couleur(hexrgb):
    return f"&H00{hexrgb[4:6]}{hexrgb[2:4]}{hexrgb[0:2]}&"


def sous_titres(titre_histoire, partie, persos, segments, total, base):
    srt, evts = [], []
    for (pid, texte), (debut, fin) in zip(partie["repliques"], segments):
        bouts = morceaux(texte)
        poids = [len(b) + 8 for b in bouts]
        t = debut
        for b, p in zip(bouts, poids):
            d = (fin - debut) * p / sum(poids)
            srt.append((t, t + d, f"{persos[pid]['nom']} : {b}"))
            nom = persos[pid]["nom"].upper()
            col = ass_couleur(persos[pid]["couleur"])
            evts.append(f"Dialogue: 1,{ts_ass(t)},{ts_ass(t + d)},Texte,,0,0,0,,"
                        f"{{\\fs46\\c{col}}}{nom}\\N{{\\fs74\\c&H00FFFFFF&}}{b}")
            t += d
    base.with_suffix(".srt").write_text(
        "\n".join(f"{i}\n{ts_srt(a)} --> {ts_srt(b)}\n{txt}\n" for i, (a, b, txt) in enumerate(srt, 1)),
        encoding="utf-8")
    entete = [
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 0", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding",
        "Style: Texte,DejaVu Sans,74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,1,0,0,0,100,100,0,0,1,5,2,5,80,80,0,1",
        "Style: Titre,DejaVu Serif,68,&H0060C8F0,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,2,0,1,4,3,8,60,60,230,1",
        "Style: Sous,DejaVu Serif,54,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,1,0,0,100,100,1,0,1,3,2,8,60,60,330,1",
        "Style: Fin,DejaVu Serif,64,&H0060C8F0,&H00FFFFFF,&H00000000,&H00000000,1,1,0,0,100,100,1,0,1,4,2,2,60,60,300,1",
        "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        f"Dialogue: 0,{ts_ass(0)},{ts_ass(total)},Titre,,0,0,0,,{{\\fad(600,0)}}{titre_histoire}",
        f"Dialogue: 0,{ts_ass(0)},{ts_ass(total)},Sous,,0,0,0,,{{\\fad(900,0)}}{partie['titre']}",
        f"Dialogue: 0,{ts_ass(max(0, total - 3.5))},{ts_ass(total)},Fin,,0,0,0,,{{\\fad(500,0)}}{partie['fin']}",
    ]
    base.with_suffix(".ass").write_text("\n".join(entete + evts) + "\n", encoding="utf-8")


def generer_partie(n, titre_histoire, partie, persos, cible, dossier, video):
    base = dossier / f"partie{n}"
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        clips = []
        for i, (pid, texte) in enumerate(partie["repliques"]):
            dest = tmp / f"r{i:02}.wav"
            synthese(persos[pid], texte, dest, tmp)
            clips.append((dest, duree(dest)))

        # Ajuste les pauses puis, si besoin, le tempo global pour tomber dans la durée cible.
        parole = sum(d for _, d in clips)
        nb_pauses = len(clips) - 1
        vise = sum(cible) / 2
        pause = min(PAUSE_MAX, max(PAUSE_MIN, (vise - DEBUT - FIN - parole) / nb_pauses))
        brut_total = DEBUT + parole + pause * nb_pauses + FIN
        tempo = 1.0
        if not cible[0] <= brut_total <= cible[1]:
            tempo = min(1.12, max(0.9, (DEBUT + parole + pause * nb_pauses + FIN) / vise))

        # Concatène avec silences, en appliquant le tempo (sans changer la hauteur).
        liste, segments, t = [], [], DEBUT / tempo
        silence = lambda s, nom: run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono",
                                      "-t", f"{s:.3f}", str(tmp / nom)]) or tmp / nom
        liste.append(silence(DEBUT / tempo, "debut.wav"))
        for i, (clip, d) in enumerate(clips):
            if tempo != 1.0:
                ajuste = tmp / f"t{i:02}.wav"
                run(["ffmpeg", "-y", "-i", str(clip), "-af", f"atempo={tempo:.4f}", str(ajuste)])
                clip, d = ajuste, duree(ajuste)
            liste.append(clip)
            segments.append((t, t + d))
            t += d
            if i < nb_pauses:
                liste.append(silence(pause / tempo, f"p{i:02}.wav"))
                t += pause / tempo
        liste.append(silence(FIN, "fin.wav"))
        total = t + FIN
        (tmp / "liste.txt").write_text("".join(f"file '{p}'\n" for p in liste))
        voix = tmp / "voix.wav"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "liste.txt"), "-c", "copy", str(voix)])
        total = duree(voix)

        # Ambiance dramatique : nappe grave synthétisée, très discrète.
        nappe = ("0.5*sin(2*PI*55*t)*(0.6+0.4*sin(2*PI*0.08*t))"
                 "+0.35*sin(2*PI*82.4*t)*(0.6+0.4*sin(2*PI*0.05*t+1))"
                 "+0.25*sin(2*PI*110*t)*(0.5+0.5*sin(2*PI*0.11*t+2))"
                 "+0.15*sin(2*PI*164.8*t)*(0.5+0.5*sin(2*PI*0.07*t+3))")
        run(["ffmpeg", "-y", "-i", str(voix),
             "-f", "lavfi", "-i", f"aevalsrc='{nappe}':s={SR}:d={total:.3f}",
             "-f", "lavfi", "-i", f"anoisesrc=c=brown:r={SR}:a=0.4:d={total:.3f}",
             "-filter_complex",
             f"[1:a]volume=0.05,afade=t=in:d=2,afade=t=out:st={total - 2:.3f}:d=2[m];"
             f"[2:a]lowpass=f=300,volume=0.08,afade=t=in:d=2,afade=t=out:st={total - 2:.3f}:d=2[b];"
             "[0:a][m][b]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.95[out]",
             "-map", "[out]", "-ac", "2", "-b:a", "192k", str(base.with_suffix(".mp3"))])

        sous_titres(titre_histoire, partie, persos, segments, total, base)

        if video:
            run(["ffmpeg", "-y",
                 "-f", "lavfi", "-i",
                 f"gradients=s=1080x1920:r=30:d={total:.3f}:speed=0.004:n=3:"
                 "c0=0x05070f:c1=0x0b1a33:c2=0x1d0d14:type=radial",
                 "-i", str(base.with_suffix(".mp3")),
                 "-vf", f"noise=alls=6:allf=t,vignette=PI/4,ass={base.with_suffix('.ass')}",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
                 "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(base.with_suffix(".mp4"))])
    return total, pause, tempo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("histoire")
    ap.add_argument("--sans-video", action="store_true")
    args = ap.parse_args()
    chemin = Path(args.histoire)
    data = json.loads(chemin.read_text(encoding="utf-8"))
    dossier = RACINE / "sortie" / chemin.parent.name
    dossier.mkdir(parents=True, exist_ok=True)
    for n, partie in enumerate(data["parties"], 1):
        # La synthèse varie un peu d'un essai à l'autre : on relance si la durée sort de la cible.
        for _ in range(3):
            total, pause, tempo = generer_partie(n, data["titre"], partie, data["personnages"], data["duree_cible"],
                                                 dossier, not args.sans_video)
            ok = data["duree_cible"][0] <= total <= data["duree_cible"][1]
            if ok:
                break
        print(f"Partie {n} : {int(total // 60)}:{total % 60:05.2f} "
              f"(pause {pause:.2f}s, tempo x{tempo:.3f}) {'OK' if ok else 'HORS CIBLE'}")
        if not ok:
            print("  -> raccourcir/allonger le texte de cette partie", file=sys.stderr)


if __name__ == "__main__":
    main()
