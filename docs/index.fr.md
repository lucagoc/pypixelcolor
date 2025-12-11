# pypixelcolor

![pypixelcolor logo](assets/pngs/banner.png)

**pypixelcolor** (aussi connu sous le nom de `iPixel-CLI`) est une bibliothèque Python et un outil en ligne de commande (CLI) pour contrôler les appareils à matrice LED iPixel Color via Bluetooth Low Energy (BLE). Il vous permet d'envoyer des commandes à l'appareil pour manipuler l'affichage LED, récupérer des informations sur l'appareil, et plus encore.

## Fonctionnalités

- 📝 **Envoyer du texte** : Affichez des messages personnalisés avec diverses polices et animations.
- 🖼️ **Envoyer des images** : Affichez des images et des GIFs sur la matrice.
- ⚙️ **Contrôler les paramètres** : Ajustez la luminosité, l'orientation et l'alimentation.
- 🕒 **Modes** : Basculez entre les modes Horloge, Rythme et Fun.
- 🐍 **Scriptable** : Support complet de la bibliothèque Python pour l'automatisation.
- 🖥️ **CLI** : Interface en ligne de commande facile à utiliser.

## Installation

Vous pouvez installer `pypixelcolor` via pip :

```bash
pip install pypixelcolor
```

## Démarrage rapide

### Interface en ligne de commande (CLI)

Scanner les appareils :

```bash
pypixelcolor --scan
```

Envoyer du texte à un appareil :

```bash
pypixelcolor -a <ADRESSE_MAC> -c send_text "Bonjour le monde"
```

[En savoir plus sur la CLI](getting_started/cli.md){ .md-button .md-button--primary }

### Bibliothèque Python

```python
import pypixelcolor

client = pypixelcolor.Client("XX:XX:XX:XX:XX:XX")
client.connect()
client.send_text("Bonjour le monde")
client.disconnect()
```

[En savoir plus sur la bibliothèque](getting_started/library.md){ .md-button .md-button--primary }
