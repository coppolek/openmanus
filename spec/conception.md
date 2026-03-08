# Conception: Agent IA Spécialisé en Marketing Digital

Ce document décrit l'architecture et les spécifications d'un agent IA spécialisé dans le marketing digital, conçu sur le framework OpenExpertManus.
Ce projet combine plusieurs de nos compétences de base : recherche et analyse SEO (SERP, "People Also Ask"), interactions LinkedIn ciblées et automatisées, génération d'insights sous forme de graphiques, ainsi qu'une persistance sur la machine locale.

## 1. Objectif du Projet
Créer un assistant digital autonome capable de mener à bien des campagnes SEO, d'automatiser des interactions sur LinkedIn, d'analyser les données marketing, et d'archiver correctement les rapports.

Cet agent sera composé de sous-agents ou de capacités modulaires implémentées en tant que `Tools` (outils) dans l'écosystème OpenExpertManus.

## 2. Architecture & Composants

Voici la répartition selon les domaines d'action :

### A. Domaine : SEO
- **Action (Tool / Agent)**: `SERPAnalyzer`
- **Rôle**: Effectuer des analyses poussées des pages de résultats des moteurs de recherche (SERP).
- **Technologie recommandée**:
  - Utilise l'outil existant `GoogleSearch` pour les requêtes basiques.
  - Utilise `Playwright` (idéalement via un outil de scraping dédié) pour extraire spécifiquement le bloc "People Also Ask" (PAA) et les métadonnées de la page de résultat.

### B. Domaine : LinkedIn
- **Action (Tool / Agent)**: `LinkedInBrowser`
- **Rôle**: Interagir de manière autonome mais sécurisée sur le réseau social LinkedIn (navigation, likes, ou extraction ciblée de profils de prospects potentiels).
- **Technologie recommandée**:
  - Création d'une extension basée sur `BrowserUseTool` (disponible via anthropic-computer-use ou browser-use intégrés).
  - Ce navigateur contrôlé permettra de s'adapter dynamiquement à l'interface LinkedIn et de réaliser les actions humaines simulées.

### C. Domaine : Contenu & Analyse
- **Action (Tool / Agent)**: `DataAnalysisAgent`
- **Rôle**: Interpréter les données extraites (performances SEO, etc.) et produire des analyses visuelles claires.
- **Technologie recommandée**:
  - Utilisation de l'Agent d'analyse de données (DataAnalysis Agent) mentionné dans la documentation d'OpenManus.
  - Implémentation via l'exécution de code Python (génération de graphiques) au sein des environnements isolés du framework.

### D. Domaine : Système & Persistance
- **Action (Tool / Agent)**: `FileSaver`
- **Rôle**: Sauvegarder les rapports SEO terminés pour un usage ultérieur.
- **Technologie recommandée**:
  - Développer un `Tool` natif (`file_saver.py`) avec des accès en écriture sur le système de fichiers pour enregistrer directement les rapports en `.txt` ou `.md` sur la machine.

## 3. Workflow Global (Exemple d'exécution)
1. **Initialisation** : L'utilisateur lance une requête : "Fais-moi un rapport SEO sur mot-clé X, trouve 5 profils LinkedIn pertinents et génère un graphique des performances".
2. **Recherche SEO** : L'agent appelle `SERPAnalyzer` pour récupérer les concurrents et "People Also Ask".
3. **Prospection LinkedIn** : Il utilise `LinkedInBrowser` pour chercher les profils ciblés.
4. **Analyse de Données** : Il transmet les informations au `DataAnalysisAgent` pour générer les visuels.
5. **Sauvegarde** : L'agent utilise `FileSaver` pour enregistrer l'étude complète dans le workspace local.

## 4. Prochaines Étapes pour l'Implémentation
1. **Création du dossier `spec/`** (Fait).
2. **Création des Tools Python** (`app/tool/...`).
3. **Création d'un agent personnalisé** pour orchestrer ces 4 outils spécifiques.
