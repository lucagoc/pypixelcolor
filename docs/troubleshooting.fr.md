# Dépannage

Voici quelques problèmes courants et leurs solutions lors de l'utilisation de `pypixelcolor`.

## Problèmes de connexion Bluetooth

### Appareil introuvable

- Assurez-vous que l'appareil est allumé.
- Assurez-vous que l'appareil n'est pas connecté à un autre téléphone ou ordinateur. L'appareil ne peut gérer qu'une seule connexion BLE à la fois.
- Essayez de vous rapprocher de l'appareil.

### Délai d'attente de connexion (Timeout)

Si vous rencontrez des délais d'attente lors de la connexion :

- Redémarrez le service Bluetooth sur votre ordinateur.
- Éteignez et rallumez l'appareil LED.

## Spécificités Linux

Sous Linux, vous devrez peut-être vous assurer que votre utilisateur dispose des autorisations correctes pour accéder à l'adaptateur Bluetooth.

1. Assurez-vous que `bluez` est installé.
2. Ajoutez votre utilisateur au groupe `bluetooth` (s'il existe) ou consultez la documentation de votre distribution pour les autorisations BLE.

```bash
sudo usermod -aG bluetooth $USER
```

Vous devrez peut-être vous déconnecter et vous reconnecter pour que les modifications prennent effet.
