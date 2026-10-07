# Histoire IA : histoires TikTok multi-voix

Ce dépôt transforme un script d'histoire (`histoire.json`) en vidéos TikTok verticales :
- **une voix par personnage**, avec synthèse vocale Piper hors ligne et des réglages de hauteur, de débit et d'effets ;
- **une ambiance sonore dramatique** discrète ;
- **des sous-titres incrustés**, avec le nom de chaque personnage dans sa couleur ;
- **un calage automatique** de chaque partie entre 1:02 et 1:05.

## Histoires disponibles

| Histoire | Script | Vidéos |
|---|---|---|
| Le Comte de Monte-Cristo (2 parties) | [script.md](histoires/monte-cristo/script.md) | `sortie/monte-cristo/partie1.mp4`, `partie2.mp4` |

Chaque partie est aussi disponible en `.mp3` (audio seul) et en `.srt` (sous-titres à importer dans CapCut).

## Générer

```bash
./outils/installer.sh
python3 outils/generer.py histoires/monte-cristo/histoire.json
# ou bien, audio et sous-titres seulement :
python3 outils/generer.py histoires/monte-cristo/histoire.json --sans-video
```

## Créer une nouvelle histoire

Copie `histoires/monte-cristo/histoire.json` dans un nouveau dossier, puis modifie :
- `personnages` : `voix` vaut `gilles` (homme) ou `siwis` (femme). `hauteur` est en demi-tons, `vitesse` est un facteur où 1.1 donne une voix plus lente. `effet` vaut `null`, `salle`, `cachot` ou `comte`. `couleur` est en hexadécimal RGB.
- `parties` : un titre, un texte de fin et la liste des répliques `[personnage, texte]`.

Le script ajuste les pauses et le tempo pour atteindre la durée cible. Il affiche `HORS CIBLE` si le texte est trop long ou trop court.

Voix : Piper `fr-gilles-low` (CC0) et `fr-siwis-medium` (CC-BY 4.0, SIWIS, Université d'Édimbourg).
