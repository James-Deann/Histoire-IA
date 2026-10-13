# 🥐 Projet TikTok « Pitchou »

Une série animée et drôle sur une petite viennoiserie qui ne sait pas si elle s'appelle **pain au chocolat** ou **chocolatine**.
Cible : public français. Objectif : **10 000 abonnés**, puis le programme **Creator Rewards** de TikTok.

![Photo de profil](photo-profil.png)

---

## 1. La mascotte : Pitchou

| | |
|---|---|
| **Qui** | Un pain au chocolat né ce matin à 6 h dans une petite boulangerie de Paris. |
| **Look** | Petit, tout rond, de grands yeux brillants, les joues roses, une mèche feuilletée en spirale sur la tête et deux barres de chocolat qui dépassent de chaque côté. |
| **Caractère** | Naïf, curieux, très gentil, un peu maladroit. Il découvre le monde à chaque épisode. On a envie de le protéger. |
| **Voix** | Aiguë et enfantine. |
| **Le grand mystère** | Il ne sait pas comment il s'appelle. **Ce sont les abonnés qui décident** en commentaire. C'est le fil rouge de la série et le moteur des commentaires. |
| **Tic** | Il répond toujours « pain au chocolat ! » quand on essaie de lui faire dire « chocolatine ». |

**Pourquoi on s'y attache** : les grands yeux et la petite taille déclenchent l'instinct « trop mignon ». Sa naïveté le rend drôle sans méchanceté. Surtout, le public a un **pouvoir sur sa vie** grâce aux votes et aux choix en commentaire, et c'est ce qui crée l'attachement.

### Les personnages secondaires

| Personnage | Rôle |
|---|---|
| **Chocolatine** | La cousine de Toulouse, avec son béret rouge et ses paupières mi-closes. Sûre d'elle, un peu peste, mais elle adore Pitchou au fond. Elle incarne le camp « chocolatine » du Sud-Ouest. |
| **M. Croissant** | Le vieux sage grincheux de la vitrine, avec sa moustache et son monocle. Il raconte « la guerre » entre pain au chocolat et chocolatine comme un ancien combattant. C'est la cible préférée des vannes. |

Fiche des expressions : [`fiche-personnages.png`](fiche-personnages.png) (normal, content, choc, triste, colère).

**Idées de personnages à ajouter** : Baguette (la grande sœur sportive), Éclair (le rapide qui ne finit jamais ses phrases), Macaron (l'influenceur parisien snob), la Boulangère (qu'on ne voit jamais, seulement ses mains).

---

## 2. Stratégie pour atteindre 10 000 abonnés

### Les règles de monétisation (à vérifier dans l'appli TikTok)
- Avoir **18 ans ou plus**, avec un **compte personnel** (pas un compte Business).
- **10 000 abonnés** et **100 000 vues sur les 30 derniers jours**.
- Seules les vidéos **de plus d'une minute** rapportent. Nos épisodes durent entre 1 min 05 et 1 min 30.
- Le contenu doit être **original**, ce qui est notre cas. **Active l'étiquette « Contenu généré par l'IA »** à chaque publication : c'est obligatoire et ça ne pénalise pas la portée.

### Le format qui marche
1. **Hook dans les 2 premières secondes** : une phrase choc ou une question (« Pardon ? Un pain au chocolat ?! »).
2. **Une série numérotée** (« Épisode 1, 2, 3… ») pour que les gens cherchent la suite et s'abonnent.
3. **Une fin qui appelle un commentaire** : chaque épisode termine sur un vote ou une question.
4. **Le débat pain au chocolat / chocolatine**, qui garantit des commentaires en masse. Plus il y a de commentaires, plus l'algorithme pousse la vidéo.

### Rythme de publication
- **1 vidéo par jour** pendant les 30 premiers jours (2 par jour si possible la première semaine).
- Meilleurs horaires en France : **12 h – 13 h** et **18 h – 21 h**.
- **Épingle** le commentaire « Team PAIN AU CHOCOLAT 👇 / Team CHOCOLATINE 👇 » sous chaque vidéo.
- **Réponds aux commentaires en vidéo** (« Pitchou répond à @… ») : TikTok adore ça et ça fait un épisode gratuit.

### Légende et hashtags types
> Pitchou ne sait pas comment il s'appelle 😭 Aide-le ! 🍫 #painauchocolat #chocolatine #pitchou #animation #humour #boulangerie #pourtoi

### Plan des 10 premiers épisodes

| # | Titre | Idée |
|---|---|---|
| 1 | **Pain au chocolat ou chocolatine ?** ✅ | Pitchou naît et rencontre sa cousine Chocolatine. Vote. |
| 2 | **Les résultats du vote** | Pitchou lit les commentaires (les vrais pseudos des abonnés !). Le débat est trop serré : « deuxième tour ». |
| 3 | **La guerre des viennoiseries** | M. Croissant raconte l'histoire de la guerre comme un documentaire de guerre. |
| 4 | **Pitchou part à Toulouse** | Choc culturel : on dit « poche » et pas « sac », « chocolatine »… |
| 5 | **Le premier client** | Quelqu'un veut acheter Pitchou. Panique dans la vitrine. |
| 6 | **Pitchou au micro-ondes** | Film d'horreur parodique. |
| 7 | **Le procès** | Un tribunal de viennoiseries juge « pain au chocolat contre chocolatine ». Le public est le jury. |
| 8 | **Pitchou tombe amoureux** | D'une religieuse. M. Croissant donne des conseils de drague catastrophiques. |
| 9 | **L'invasion des pains au chocolat surgelés** | Les industriels attaquent la boulangerie. |
| 10 | **Le grand nom** | Le camp gagnant baptise Pitchou. Épisode événement. |

---

## 3. Comment on travaille ensemble

Tu me dis simplement quoi faire, par exemple :
- « Fais l'épisode 2 avec les résultats du vote, voici 5 commentaires drôles : … »
- « Ajoute le personnage Baguette »
- « Pitchou doit être plus triste à la fin »

Je m'occupe ensuite du script, des voix, de l'animation et des sous-titres, puis je te livre le `.mp4` prêt à publier.

### Fabrication technique
```bash
./outils/installer.sh                                   # une seule fois (voix françaises)
pip install cairosvg
python3 outils/animer.py pitchou/episodes/ep01.json     # vidéo HD (≈ 15 min)
python3 outils/animer.py pitchou/episodes/ep01.json --apercu   # aperçu rapide (≈ 1 min)
python3 outils/fiche.py                                 # fiche des persos et photo de profil
```
Sorties dans `sortie/pitchou/` : `epNN.mp4` (1080x1920, prête pour TikTok), `epNN.srt` (sous-titres) et `epNN.wav` (son).

Un épisode est un fichier JSON (voir `episodes/ep01.json`) composé de scènes. Chaque scène indique qui est présent à l'écran et liste des répliques au format `[personnage, expression, texte]`. Un 4e élément est possible, `{"reactions": {...}}`, pour changer la tête des autres personnages pendant la réplique.

### Pour aller plus loin : version 3D « IA vidéo »
Les épisodes actuels sont en dessin animé 2D, fabriqués entièrement ici, avec des voix de synthèse hors ligne un peu robotiques. Pour monter en gamme :
- **Voix** : passe les répliques dans ElevenLabs (voix enfant pour Pitchou), puis remplace la piste son. La synchro labiale suit automatiquement l'audio.
- **Images 3D** : à générer avec Kling, Veo ou Runway à partir de `photo-profil.png` comme image de référence, avec ce prompt :
  > *Cute 3D Pixar-style animated pain au chocolat character named Pitchou, small rectangular golden flaky pastry body, two dark chocolate bars poking out of each side, huge shiny dark eyes with white highlights, rosy blushing cheeks, tiny smile, a little curled pastry swirl on top of its head, tiny stubby arms and feet, standing on a wooden bakery counter, warm morning light, Parisian boulangerie background softly blurred, vertical 9:16*
