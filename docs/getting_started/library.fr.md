# Utiliser pypixelcolor comme une bibliothèque Python

## Utilisation de base

Vous pouvez également utiliser `pypixelcolor` comme une bibliothèque Python dans vos propres scripts.

```python
import pypixelcolor

# Créer une instance de l'appareil PixelColor
device = pypixelcolor.Client("30:E1:AF:BD:5F:D0")

# Se connecter à l'appareil
device.connect()

# Envoyer un message texte à l'appareil
device.send_text("Bonjour depuis Python !", animation=1, speed=100)

# Se déconnecter de l'appareil
device.disconnect()
```

## Appareils multiples

Vous pouvez vous connecter à plusieurs appareils en créant plusieurs instances de `Client` :

```python
import pypixelcolor

devices = [
    pypixelcolor.Client("30:E1:AF:BD:5F:D0"), 
    pypixelcolor.Client("30:E1:AF:BD:20:A9")
]

for device in devices:
    device.connect()

for device in devices:
    device.send_text("Bonjour depuis Python !", animation=1, speed=100)

for device in devices:
    device.disconnect()
```

### Utilisation asynchrone

Vous pouvez envoyer des commandes à plusieurs appareils iPixel Color simultanément en utilisant la programmation asynchrone avec la bibliothèque `asyncio`. Voici un exemple de la façon de procéder :

```python
import asyncio
import pypixelcolor

async def main():
    addresses = [
        "30:E1:AF:BD:5F:D0",
        "30:E1:AF:BD:20:A9",
    ]

    # Créer des clients et se connecter séquentiellement (sûr pour les backends courants)
    devices = []
    for addr in addresses:
        client = pypixelcolor.AsyncClient(addr)
        await client.connect()
        devices.append(client)

    if not devices:
        return

    # Lancer les envois simultanément sur tous les appareils connectés
    tasks = [asyncio.create_task(d.send_image("./python.png")) for d in devices]
    await asyncio.gather(*tasks)

    # Tout déconnecter
    for d in devices:
        await d.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

!!! warning "Précaution"
    Les opérations lourdes en données (comme l'envoi d'images) ne sont pas stables lorsqu'elles sont effectuées simultanément sur plusieurs appareils en raison des limitations potentielles du backend Bluetooth.
