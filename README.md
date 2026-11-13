# Réseaux de Petri — Apprendre

Jeu pédagogique Windows pour apprendre les réseaux de Petri (places, transitions, arcs pondérés, marquage, franchissement, arcs inhibiteurs, priorités).

## Contenu

- **40 niveaux** : 10 Facile, 10 Moyen, 10 Difficile, 10 Expert
- **Éditeur complet** : ajouter / supprimer / déplacer places & transitions, arcs, inhibiteurs, jetons, poids, priorités
- **Résoudre** : validation structurelle puis **animation automatique** des jetons
- Progression sauvegardée localement (niveaux validés)

## Lancer depuis Godot

1. Installez [Godot 4.3](https://godotengine.org/download) (ou utilisez `tools/godot/Godot_v4.3-stable_win64.exe` fourni dans ce dépôt si présent).
2. Ouvrez le dossier `godot_project/` dans Godot.
3. Appuyez sur **F5** (scène principale : menu).

## Générer le `.exe`

1. Dans Godot : **Éditeur → Gérer les modèles d’export…** et installez les templates **4.3.stable**.
2. **Projet → Exporter…** → preset **Windows Desktop**.
3. Exportez vers `build/PetriNetLearn.exe` (défini dans `export_presets.cfg`).

Ou en ligne de commande (Godot + templates déjà installés) :

```powershell
New-Item -ItemType Directory -Force -Path build | Out-Null
.\tools\godot\Godot_v4.3-stable_win64_console.exe --path .\godot_project --headless --export-release "Windows Desktop" .\build\PetriNetLearn.exe
```

## Régénérer les niveaux

```powershell
py -3 tools\generate_levels.py
py -3 tools\validate_levels.py
```

## Structure

| Dossier | Rôle |
|---------|------|
| `godot_project/core/` | Moteur RdP, simulateur, validateur |
| `godot_project/ui/` | Menus, éditeur canvas, animation |
| `godot_project/data/levels/` | 40 niveaux JSON |
| `cours_petri2.pdf` | Cours de référence |
