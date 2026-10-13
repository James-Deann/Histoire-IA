#!/usr/bin/env python3
"""Génère la fiche des personnages et la photo de profil TikTok de Pitchou.

Usage : python3 outils/fiche.py   ->  pitchou/fiche-personnages.png, pitchou/photo-profil.png
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import personnages  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent
POLICE = str(RACINE / "polices" / "LilitaOne-Regular.ttf")
EXPRESSIONS = ["normal", "content", "choc", "triste", "colere"]
LIGNES = [("pitchou", "Pitchou"), ("chocolatine", "Chocolatine"), ("croissant", "M. Croissant")]


def texte(d, xy, s, taille, couleur, contour=(60, 30, 10)):
    f = ImageFont.truetype(POLICE, taille)
    d.text(xy, s, font=f, fill=couleur, anchor="mm", stroke_width=max(2, taille // 12), stroke_fill=contour)


def fiche():
    c, entete, marge = 300, 150, 230
    img = Image.new("RGBA", (marge + c * len(EXPRESSIONS), entete + c * len(LIGNES)), (255, 241, 220, 255))
    d = ImageDraw.Draw(img)
    texte(d, (img.width // 2, 60), "La bande de Pitchou", 70, (255, 194, 77))
    for i, e in enumerate(EXPRESSIONS):
        texte(d, (marge + c * i + c // 2, entete - 25), e.replace("colere", "colère"), 34, (255, 255, 255))
    for r, (nom, titre) in enumerate(LIGNES):
        y = entete + c * r
        texte(d, (marge // 2, y + c // 2), titre, 38, (255, 255, 255))
        for i, e in enumerate(EXPRESSIONS):
            spr = personnages.image(nom, c, expression=e, bras_haut=e in ("content", "choc"))
            img.alpha_composite(spr, (marge + c * i, y))
    img.convert("RGB").save(RACINE / "pitchou" / "fiche-personnages.png")


def profil():
    t = 1000
    img = Image.new("RGBA", (t, t), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, t, t), fill=(255, 214, 160, 255))
    d.ellipse((60, 60, t - 60, t - 60), fill=(255, 236, 205, 255))
    spr = personnages.image("pitchou", 980, expression="normal", bras_haut=True)
    img.alpha_composite(spr, (10, 70))
    img.save(RACINE / "pitchou" / "photo-profil.png")


if __name__ == "__main__":
    fiche()
    profil()
    print("OK")
