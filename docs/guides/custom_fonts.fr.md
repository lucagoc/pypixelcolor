# Polices personnalisées

La bibliothèque est fournie avec un support intégré pour plusieurs polices (CUSONG, SIMSUN, VCR_OSD_MONO). Cependant, vous pouvez également utiliser vos propres fichiers TTF.

## Utilisation

Pour utiliser une police personnalisée avec la bibliothèque pypixelcolor, vous pouvez spécifier le chemin vers votre fichier de police TTF lors de l'envoi de texte. Voici un exemple de la façon de procéder :

```python
import pypixelcolor

if __name__ == "__main__":
    client = pypixelcolor.Client("AF:1D:E1:BD:5C:80")
    client.connect()
    client.send_text("Bonjour", font="./Minecraft.ttf")
    client.disconnect()
```

Un fichier doit être créé avec le même nom que le fichier TTF mais avec une extension `.json` (par exemple, `Minecraft.json`) dans le même répertoire que le fichier TTF, contenant les métadonnées de la police. Voici un exemple de ce à quoi le fichier JSON devrait ressembler :

```json
{
  "name": "Minecraft",
  "metrics": {
    "16": {
      "font_size": 16,
      "offset": [0, 0],
      "pixel_threshold": 70
    },
    "20": {
      "font_size": 20,
      "offset": [0, 0],
      "pixel_threshold": 70
    },
    "24": {
      "font_size": 24,
      "offset": [0, -1],
      "pixel_threshold": 80
    },
    "32": {
      "font_size": 25,
      "offset": [0, 2],
      "pixel_threshold": 85
    }
  }
}
```

### Structure du fichier JSON

- `name` : Le nom de la police.
- `metrics` : Un dictionnaire où chaque clé est une taille de hauteur de caractère (en pixels, 16, 20, 24 ou 32) et la valeur est un autre dictionnaire contenant :
  - `font_size` : La taille de la police à utiliser.
  - `offset` : Une liste de deux entiers représentant le décalage x et y pour le rendu de la police.
  - `pixel_threshold` : Une valeur entière qui détermine le seuil d'intensité des pixels pour le rendu de la police.

## Remarques

- Assurez-vous que les fichiers TTF et JSON sont dans le même répertoire.
- Les tailles de police spécifiées dans le fichier JSON doivent correspondre aux tailles que vous avez l'intention d'utiliser lors de l'envoi de texte.
- Ajustez les valeurs `offset` et `pixel_threshold` selon les besoins pour obtenir l'apparence souhaitée sur votre appareil pixel.
