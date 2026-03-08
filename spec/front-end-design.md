# Conception de l'Interface Front-End (Agent Marketing Digital)

Ce document décrit l'architecture et les choix techniques pour développer l'interface utilisateur de notre agent d'intelligence artificielle spécialisé en marketing digital (basé sur le framework OpenExpertManus détaillé dans `spec/conception.md`).

---

## 1. Stack Technologique Standard (Clean Architecture)

L'application Front-End respectera strictement la stack standard définie pour les nouveaux projets :

- **Framework** : Next.js (App Router, TypeScript).
- **Styling** : Tailwind CSS (Mobile-first, Utility-first) avec `clsx` et `tailwind-merge`.
- **Composants UI** : shadcn/ui.
- **Formulaires** : combination Zod (validation), react-hook-form (gestion state), shadcn Form (UI).
- **Gestion d'État (State Management)** :
  - **Server State** : TanStack Query (v5+) (`useQuery`, `useMutation`).
  - **Client State** : Zustand (fichiers dans `@/store/`).

---

## 2. Bibliothèques et Outils Adaptés au Projet

L'agent Marketing Digital a des besoins spécifiques (rendu de rapports SEO, affichage d'analyses de données, affichage des logs de navigation LinkedIn, etc.). Voici les bibliothèques recommandées en plus de la stack standard :

### A. Rendu des Contenus (Rapports FileSaver & Contenu IA)
- **`react-markdown`** & **`remark-gfm`** : L'agent génère des rapports Markdown (tableaux, listes SEO). Ces librairies permettent un rendu propre des fichiers statiques sauvegardés par `FileSaver`.
- **`highlight.js`** ou **`prismjs`** : Pour la coloration syntaxique si du code (ex: requêtes JSON LinkedIn) est généré dans les rapports.

### B. Visualisation de Données (DataAnalysisAgent)
- **`recharts`** : Si l'agent d'analyse de données (DataAnalysisAgent) renvoie des jeux de données JSON bruts, `recharts` permet de générer des graphiques performants et responsives (camemberts, courbes SEO, etc.).

### C. Chat UI & Interfaces Conversationnelles
- **`ai` et `@ai-sdk/react` (Vercel AI SDK)** : C'est l'outil indispensable (https://ai-sdk.dev/) pour construire une interface de Chat fluide.
  - Gère nativement le streaming des réponses LLM (via le hook `useAssistant` ou `useChat`).
  - Permet d'intégrer des UI génératives (React Server Components) : par exemple, le `DataAnalysisAgent` peut renvoyer directement un composant React (un graphique `recharts`) dans le flux de discussion au lieu d'une simple image.
  - Gère automatiquement les états de chargement des appels d'outils (Tool Calling), parfait pour afficher un "loader" spécifique quand le `SERPAnalyzer` ou le `LinkedInBrowser` sont en cours d'exécution.

### D. Temps Réel (Monitoring des Agents)
- **SSE (Server-Sent Events) ou WebSockets** : Pour afficher en temps réel l'avancement des sous-agents (ex: "SERPAnalyzer en cours...", "LinkedInBrowser visite 5 profils"). Complémentaire au Vercel AI SDK si l'agent Python backend n'est pas conçu pour streamer directement de l'OpenAI-compatible.

### D. Icônes
- **`lucide-react`** : Inclus par défaut avec shadcn/ui (icones pour le SEO, graphes, navigateur, sauvegardes).

---

## 3. Structure Fonctionnelle de l'Interface (App Router)

### Pages (`app/`)
* **`/` (Dashboard Pincipal)** : Vue globale des performances, des campagnes en cours et raccourcis vers la génération d'un rapport SEO rapide.
* **`/campaigns/new`** : Interface de création de tâche détaillée pour l'agent (ex: "Fais-moi un rapport SEO sur mot-clé X, trouve 5 profils LinkedIn pertinents et génère un graphique des performances").
  - *Composant clé* : `<CampaignForm />` utilisant Zod pour valider les paramètres (Mots-clés, URLs cibles, Instructions LinkedIn).
* **`/campaigns/[id]`** : Interface de suivi temps réel et résultat final d'un run métier :
  - Historique des actions (`SERPAnalyzer` -> `LinkedInBrowser` -> `DataAnalysisAgent`).
  - Affichage direct du rapport final.
* **`/saved-reports`** : Vue "explorateur de fichiers" qui expose les fichiers `.txt` et `.md` stockés localement par l'outil `FileSaver`.

### Architecture des Composants (`components/`)
Suivant la convention, les composants seront structurés :

* **`components/ui/`** : Composants shadcn bruts (Boutons, Inputs, Cards).
* **`components/features/campaigns/`** : Composants liés à l'exécution de l'agent :
  - `CampaignProgress.tsx` : Barre ou Timeline d'avancement des agents.
  - `ChatPromptInput.tsx` : Interface type chat asynchrone ("Prompt").
* **`components/features/reports/`** :
  - `MarkdownViewer.tsx` : Rendu des rapports SEO (`react-markdown`).
  - `PerformanceChart.tsx` : Rendu des graphes de `DataAnalysisAgent` (`recharts`).

---

## 4. Intégration Next.js / Python Backend (FastAPI recommandé)

Actuellement, `OpenExpertManus` est un projet Python (CLI/Agent). Pour le rendre accessible au front-end, une couche d'abstraction (type Architecture Hexagonale avec contrôleur REST) est à produire en Python (par exemple via FastAPI) :

* **`POST /api/v1/campaigns`** : Payload validé via Zod côté client, envoie le *prompt métier* à l'agent (SERP + LinkedIn + Graphiques).
* **`GET /api/v1/campaigns/{id}/stream`** : End point SSE (Server-Sent Events) pour faire un stream des "Pensées" (`thought`) et "Actions" (`tool calls`) de l'agent OpenManus en temps réel.
* **`GET /api/v1/reports`** : Liste les rapports gérés par `FileSaver` dans le workspace pour les afficher dans `/saved-reports`.
