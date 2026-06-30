# Contribuer

## Versioning et notes de version

### Numérotation
Format obligatoire : `MAJEUR.MINEUR.CORRECTIF` (ex. `5.1.0`).

- **MAJEUR** : refonte ou rupture de compatibilité
- **MINEUR** : nouvelle fonctionnalité
- **CORRECTIF** : correction de bug ou ajustement mineur

La version courante est portée par [`version.json`](version.json) à la racine du projet.

### Fichier `CHANGELOG.md`
- Présent à la racine, mis à jour à **chaque** modification livrée.
- Une entrée par version, avec les sections : `Ajouté`, `Modifié`, `Corrigé`,
  `Supprimé`, `Sécurité`.
- Aucun merge en production sans mise à jour du `CHANGELOG.md`.

### Branches Git
- `main` : version en production
- `develop` : version en cours
- `feature/nom-court` : nouvelles fonctionnalités
- `hotfix/nom-court` : correctifs urgents

### Tags
- Tag Git obligatoire à chaque déploiement en production (ex. `5.1.0`),
  aligné sur `version.json` et sur la convention de l'historique (sans préfixe `v`).
