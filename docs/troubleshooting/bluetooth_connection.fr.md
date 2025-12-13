# Problèmes de connexion Bluetooth

## Appareil non trouvé

- Assurez-vous que l'appareil est allumé.
- Assurez-vous que l'appareil n'est pas connecté à un autre téléphone ou ordinateur. L'appareil ne peut gérer qu'une seule connexion BLE à la fois.
- Essayez de vous rapprocher de l'appareil.

## Délai de connexion dépassé

Si vous rencontrez des délais d'attente lors de la connexion :

- Redémarrez le service Bluetooth sur votre ordinateur.
- Redémarrez l'appareil LED.

## Erreur `pypixelcolor.lib.transport.send_plan` avec `bleak` 2.0.x

Nous enquêtons sur des problèmes avec la nouvelle version de `bleak` 2.0.x qui peuvent causer des problèmes de connexion sur certains systèmes.
Voir [issue #58](https://github.com/lucagoc/pypixelcolor/issues/58) pour plus de détails.

```txt
Failed to enable response notifications: [org.freedesktop.DBus.Error.UnknownObject] Method "AcquireNotify" with signature "a{sv}" on interface "org.bluez.GattCharacteristic1" doesn't exist
```

Si vous rencontrez des problèmes de connexion persistants, envisagez de rétrograder vers `bleak` 1.1.1 comme solution temporaire :

```bash
pip uninstall bleak
pip install bleak==1.1.1
```
