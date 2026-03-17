# LinkedApiDoc - Changelog

## [1.2.1] - 2026-03-17
### Fixed
- Correction des paramètres manquants pour **93 endpoints** (parameters = {}).
- Extraction automatique des signatures de méthodes depuis les fichiers `.cs` des contrôleurs.
- Mise à jour des descriptions pour inclure les paramètres manquants.
- Script Python `fix-empty-parameters-v3.py` pour automatisation complète.

## [1.2.0] - 2026-03-17
### Added
- Remplissage automatique des descriptions des endpoints (basé sur le nom des contrôleurs et des routes).
- Route `POST /api/update-descriptions` protégée par authentification admin.
- Script `update-descriptions.js` pour mise à jour en masse des descriptions.

## [1.1.0] - 2026-03-17
### Added
- Filtrage automatique (sans "ApplyFilter").
- Recherche instantanée dans le champ "Route".
- Gestion des versions.

## [1.0.0] - 2026-03-16
### Added
- Interface de base.
- Dark mode.
