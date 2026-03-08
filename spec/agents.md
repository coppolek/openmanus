# Inventaire des Agents Disponibles

Suite à l'analyse du dossier `app/agent/` du framework OpenExpertManus, voici la liste des agents existants et comment ils s'intègrent à notre projet d'Agent de Marketing Digital défini dans `spec/conception.md` :

---

## 1. Agent LinkedIn (Action : Navigation et Extraction)
*Besoin : Interagir de manière autonome sur LinkedIn.*

**Agent disponible : `BrowserAgent` (`app/agent/browser.py`)**
- **Description** : Un agent spécialisé dans le pilotage de navigateur web.
- **Outils injectés** : Il utilise `BrowserUseTool` pour naviguer, cliquer, scroller et extraire l'information.
- **Adéquation projet** : **Parfaite**. Cet agent est prêt à l'emploi pour gérer la partie LinkedIn. Il suffit de lui fournir un prompt système orienté "Prospection LinkedIn" pour qu'il exécute les tâches demandées.

## 2. Agent Contenu & Analyse (Action : Génération de graphiques)
*Besoin : Interpréter les données d'analyse (SEO, LinkedIn) et produire des graphiques.*

**Agent disponible : `DataAnalysis` (`app/agent/data_analysis.py`)**
- **Description** : Un agent analytique conçu pour résoudre des tâches complexes d'analyse de données.
- **Outils injectés** : Il possède `NormalPythonExecute`, `VisualizationPrepare` et `DataVisualization`.
- **Adéquation projet** : **Parfaite**. Cet agent dispose de toute la logique nécessaire pour parser des JSON de résultats SEO ou LinkedIn et tracer des courbes d'évolution.

## 3. L'Orchestrateur Global (`run_flow.py` et `app/flow/`)
*Besoin : Comprendre la requête initiale de l'utilisateur, et déléguer aux sous-agents ou utiliser les outils directs.*

Dans OpenExpertManus, l'orchestration multi-agents ne se fait pas par un "Super Agent" monolithique, mais via un système de **Flow** (Flux de travail).

**Comment ça marche concrètement (basé sur `run_flow.py` et `app/flow/planning.py`) :**

1. **Initialisation des Agents (`run_flow.py`)** : Le script instancie un dictionnaire contenant les agents disponibles (ex: `Manus` par défaut, et `DataAnalysis` s'il est activé dans la configuration).
2. **Création du Flow (`FlowFactory`)** : La requête utilisateur est passée à la `FlowFactory`, qui instancie un `PlanningFlow`.
3. **Phase de Planification (`PlanningFlow._create_initial_plan`)** : Le `PlanningFlow` utilise un LLM de haut niveau pour décomposer la requête de l'utilisateur en un *Plan d'Action* (une liste d'étapes séquentielles). Le LLM reçoit en prompt la liste des agents disponibles et leurs capacités.
4. **Exécution (Routing)** : La boucle principale (`PlanningFlow.execute`) lit le plan étape par étape. Pour chaque étape, la méthode `get_executor` attribue la tâche à l'Agent le plus pertinent (le `DataAnalysis` agent, ou l'agent principal `Manus`) en fonction de la consigne (ex: "chercher sur internet" -> Manus, "Créer un graphique" -> DataAnalysis).

**Adéquation projet** : **Parfaite**.
Pour notre "Agent Marketing Digital", il suffira de :
1. Instancier notre `MarketingAgent` (ou `Manus` configuré) et le `DataAnalysis` dans `run_flow.py`.
2. Donner les *outils SEO et d'écriture de fichier* (FileSaver) à notre agent principal.
3. Laisser la puissance du `PlanningFlow` décomposer automatiquement la requête (ex: *"Fais un rapport SEO et un graphe"*) et router les étapes au bon agent dynamiquement.

## 4. Agent SEO (SERP & PAA) - *À créer ou intégrer*
*Besoin : Effectuer les requêtes SEO, analyser la SERP.*

**Statut :** Il n'y a pas d'agent spécifiquement nommé "SEOAgent" dans `app/agent/`.
- **Solution** : L'intelligence métier SEO n'a pas forcément besoin d'un *Agent* complet avec sa propre boucle de pensée si l'outil est déjà performant. Nous utiliserons l'Agent Orchestrateur (`MarketingAgent` ou `Manus`) en lui injectant simplement le **tool** `web_search.py` (ou `crawl4ai.py`). L'orchestrateur s'occupera lui-même de formuler la requête Google et d'en analyser le texte retourné.

---

### Résumé des développements pour les Agents
L'architecture multi-agents d'OpenExpertManus est très bien pensée. Pour notre projet, l'effort principal sera de :
1. **Créer un fichier `app/agent/marketing.py`** (ou équivalent) pour définir l'agent principal (Orchestrateur Marketing).
2. Lui injecter les outils SEO (`web_search`), le composant de sauvegarde (`file_operators`), et lui apprendre à déléguer l'analyse visuelle au `DataAnalysis` agent, et le scraping profond au `BrowserAgent`.
