# Conception de l'AgentMarketing

Ce document décrit la spécification technique pour la création et l'intégration du nouvel agent dédié au marketing digital : l'**AgentMarketing**.

---

## 1. Objectif Backend : Création de l'AgentMarketing

Dans le framework OpenExpertManus (dossier `app/agent/`), nous allons créer un nouvel agent spécialisé dont le rôle est d'orchestrer les tâches marketing SEO, la prospection et la sauvegarde locale.

### Fichier : `app/agent/marketing.py`

*   **Classe** : `AgentMarketing(ToolCallAgent)`
*   **Description** : "Un agent expert en marketing digital capable d'effectuer des recherches SEO, de collecter des données concurrentielles et de sauvegarder des rapports (FileSaver)."
*   **Outils (Tools) Injectés :**
    *   `WebSearch` (depuis `app/tool/web_search.py`) : Pour lire la SERP et les PAA (People Also Ask).
    *   `Crawl4AI` (depuis `app/tool/crawl4ai.py`) : Pour extraire le contenu profond d'un site web concurrent.
    *   `LocalFileOperator` (depuis `app/tool/file_operators.py`) : Le fameux rôle "FileSaver" pour écrire les rapports `.md` ou `.txt`.
    *   `Terminate` : Pour signaler la fin de la réflexion.
*   **Prompt Système (`system_prompt`) :**
    Ce prompt devra expliquer à l'agent comment :
    1.  Recevoir un mot-clé ou un objectif.
    2.  Requêter les moteurs de recherche pour extraire l'intention et la concurrence.
    3.  Formater proprement la réponse en Markdown (Rapport SEO).
    4.  Utiliser `LocalFileOperator` pour sauvegarder ce rapport dans le dossier souhaité.

### Fichier : `run_flow.py` (Mise à jour)
Il faudra modifier l'orchestrateur initial pour y ajouter notre agent :
```python
agents = {
    "manus": Manus(),
    "marketing": AgentMarketing(), # <-- Nouvel agent ajouté au dictionnaire
}
if config.run_flow_config.use_data_analysis_agent:
    agents["data_analysis"] = DataAnalysis()
```

---

## 2. Intégration Frontend : Interface Utilisateur

Dans l'application Next.js (décrite dans `spec/front-end-design.md`), l'utilisateur doit avoir explicitement le contrôle sur le choix de l'agent avant de lancer sa requête, afin d'optimiser les prompts et les outils utilisés.

### A. Sélecteur d'Agent (Composant UI)
Dans la page de création de campagne (`/campaigns/new`) ou le Dashboard, intégrer un composant **`<AgentSelector />`** (par exemple, un `Select` de shadcn/ui) proposant :
*   **Agent Marketing** : (Recommandé pour le SEO, la stratégie de contenu, et la veille concurrentielle).
*   **Agent Data Analyst** : (Recommandé pour la visualisation des datas).
*   **Agent Général (Manus)** : (Pour des tâches transversales ou non spécifiques).

### B. Formulaire de Prompt Dynamique
En sélectionnant l'**AgentMarketing**, le formulaire s'adapte et propose des champs orientés métier :
*   **Champ `Mot-clé / Sujet Ciblé`** (Input).
*   **Section `Objectifs`** (Checkbox / Multi-Select) :
    *   [ ] Extraire les "People Also Ask" (PAA)
    *   [ ] Auditer la concurrence SERP
    *   [ ] Chercher des prospects LinkedIn
    *   [ ] Sauvegarder le rapport final (.md)

### C. Le Payload vers l'API
Lorsque l'utilisateur soumet ses objectifs, le Front-end génère un "Super Prompt" orienté pour `run_flow.py`.

*Exemple de structure envoyée au Backend :*
```json
{
  "selected_agent": "marketing",
  "prompt": "Analyse la SERP pour 'Logiciel CRM SaaS'. Retourne-moi les principales questions 'People Also Ask'. Enfin, sauvegarde ce rapport détaillé au format Markdown sur le disque local."
}
```

### D. Traitement côté Backend FastAPI (Couche API)
L'API REST devra recevoir ce composant `selected_agent` pour forcer `FlowFactory` à n'utiliser **que** l'AgentMarketing (ou à lui donner la priorité absolue dans la fonction `get_executor` de `PlanningFlow`).
