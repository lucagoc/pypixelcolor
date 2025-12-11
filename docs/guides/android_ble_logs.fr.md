# Obtenir les journaux BLE d'un appareil Android

## Prérequis

- Un appareil Android avec des capacités Bluetooth
- [adb](https://developer.android.com/tools/releases/platform-tools) (Android Debug Bridge) installé sur votre ordinateur
- Un câble USB pour connecter l'appareil Android à votre ordinateur (ou Wifi pour une configuration sans fil)
- [Wireshark](https://www.wireshark.org/) si vous souhaitez analyser les journaux

## Guide étape par étape

Avant de commencer à capturer les journaux BLE, vous devez préparer votre appareil Android.

### Activer le débogage USB sur votre appareil Android

- Allez dans **Paramètres** > **À propos du téléphone**.
- Appuyez sur **Numéro de build** 7 fois pour activer les options pour les développeurs.
- Revenez à **Paramètres** > **Options pour les développeurs** et activez le **Débogage USB**.

*Les étapes peuvent varier légèrement selon votre version d'Android et le fabricant de l'appareil.*

### Activer le journal de surveillance HCI Bluetooth sur votre appareil Android

Allez dans **Paramètres** > **Options pour les développeurs**.
Faites défiler vers le bas et réglez **Journal de surveillance HCI Bluetooth** sur **Activé**.
Redémarrez le service Bluetooth en désactivant puis en réactivant le Bluetooth.

Vous pouvez maintenant effectuer des actions sur votre appareil Android qui généreront des journaux BLE.

### Capturer les journaux BLE

Lorsque vous avez terminé, suivez ces étapes pour récupérer les journaux :

1. **Connectez votre appareil Android** à votre ordinateur à l'aide d'un câble USB ou assurez-vous d'avoir une configuration ADB sans fil.
2. **Ouvrez un terminal** ou une invite de commande sur votre ordinateur.
3. **Vérifiez si votre appareil est connecté** en exécutant :

   ```bash
   adb devices
   ```

   Vous devriez voir votre appareil listé.

   *Si vous voyez "unauthorized", assurez-vous d'accepter l'invite de débogage USB sur votre appareil Android.*
4. **Générez un rapport de bogue** depuis votre appareil en exécutant :

   ```bash
   adb bugreport 
   ```

   Cette commande créera un fichier zip contenant divers journaux, y compris le journal de surveillance HCI Bluetooth.
   Le fichier zip sera enregistré dans le répertoire courant avec un nom comme `bugreport-<nom_appareil>-<horodatage>.zip`.
5. **Extrayez le journal** du rapport de bogue en décompressant `FS/data/misc/bluetooth/logs/btsnoop_hci_<date>_<heure>.log`.
    Si vous n'avez qu'un fichier nommé `btsnooz_hci.log`, les données envoyées aux appareils BLE ont été filtrées de la journalisation, assurez-vous de régler le journal de surveillance HCI Bluetooth sur **Activé** et redémarrez votre appareil.

6. **Analysez le fichier journal** :
   - Vous pouvez ouvrir le fichier `btsnoop_hci.log` dans Wireshark pour l'analyse.
   - Dans Wireshark, allez dans **Fichier** > **Ouvrir** et sélectionnez le fichier `btsnoop_hci.log`.
   - Astuce : utilisez le filtre `(btatt.opcode.method == 0x12)` pour ne voir que les demandes d'écriture envoyées aux appareils BLE.
