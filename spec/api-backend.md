# Conception de l'API Backend (FastAPI) pour le Front-end

Ce document définit la spécification technique de la couche API REST qui exposera les capacités de l'agent OpenExpertManus (actuellement en CLI) au Front-end Next.js.

Conformément à l'Architecture Hexagonale (cf. `@MEMORY[user_global]`), nous séparons l'entrée (Interfaces/Entrypoints) de la logique métier (Use Cases / Flow).

---

## 1. Choix Technologique

*   **Framework** : FastAPI (Python 3.12+).
*   **Validation et Typage** : Pydantic v2 (natif à FastAPI).
*   **Asynchronisme** : `async def` natif (FastAPI gère nativement les appels asynchrones d'OpenExpertManus comme `run_flow()`).
*   **Temps réel (Streaming)** : SSE (Server-Sent Events) via `StreamingResponse` pour envoyer le "Thought stream" (les pensées et actions de l'agent) directement au Vercel AI SDK du Front-end.

---

## 2. Structure des Dossiers du Backend API

L'API sera intégrée au projet existant sans casser le fonctionnement CLI actuel (fichiers `app/api/`).

```text
OpenExpertManus/
├── app/
│   ├── api/                  # [NOUVEAU] Entrypoints / Rest Controllers
│   │   ├── main.py           # Point d'entrée de l'application FastAPI
│   │   ├── routes/           # Séparation logique des endpoints
│   │   │   ├── campaign.py   # Gestion de la création et du run des agents
│   │   │   └── reports.py    # Endpoint pour récupérer les logs et rapports
│   │   └── schemas/          # Modèles Pydantic pour (Request/Response validation)
│   ├── agent/                # Domaine Métier (existant + AgentMarketing)
│   ├── flow/                 # Orchestrateur (existant)
│   └── tool/                 # Infrastucture (existant)
```

---

## 3. Définition des Endpoints (Routes REST)

### A. Lancer une campagne (Agent Run)

**`POST /api/v1/campaigns`**
*   **Rôle** : Reçoit les configurations du Front-end, instancie le *Flow* avec l'Agent ciblé (ex: `AgentMarketing`) et initie une connexion persistante.
*   **Payload (Request) validé par Pydantic :**
    ```json
    {
      "selected_agent": "marketing",
      "prompt": "Analyse la SERP pour 'Logiciel CRM SaaS'.",
      "tools_override": ["web_search", "file_saver"] // Optionnel : forcer l'usage de certains outils
    }
    ```
*   **Réponse (Response) :**
    ```json
    {
      "campaign_id": "uuid-1234-5678",
      "status": "initialized",
      "stream_url": "/api/v1/campaigns/uuid-1234-5678/stream"
    }
    ```

### B. Suivre l'exécution en temps réel (SSE Stream)

**`GET /api/v1/campaigns/{campaign_id}/stream`**
*   **Rôle** : C'est ici que toute la magie opère. Au lieu d'attendre 2 minutes que l'agent finisse, cet endpoint utilise `StreamingResponse` pour renvoyer des événements SSE. Ces évènements peuvent être consommés par le Hook `useChat` de Vercel AI SDK côté React.
*   **Format de retour (Content-Type: text/event-stream) :**
    ```text
    event: thought
    data: {"message": "Je vais commencer par lancer une recherche SERP..."}

    event: tool_call
    data: {"tool": "web_search", "params": {"query": "Logiciel CRM SaaS"}}

    event: tool_result
    data: {"tool": "web_search", "status": "success"}

    event: text
    data: "La recherche est terminée, voici le rapport Markdown..."
    ```
    *Note technique* : Il faudra surcharger ou "hooker" le logger d'OpenManus (`app/logger.py` ou le système de `Message`) pour qu'il pousse ses messages dans une file d'attente asynchrone (Queue) lue par cet endpoint.

### C. Récupérer les rapports générés (FileSaver Viewer)

**`GET /api/v1/reports`**
*   **Rôle** : Lister les fichiers Markdown générés par les agents et stockés localement (pratique pour l'interface de `/saved-reports` du front).
*   **Réponse (Response) :**
    ```json
    {
      "reports": [
        {"id": "doc-1", "filename": "rapport-seo-crm.md", "created_at": "2026-03-08T10:00:00Z"},
        {"id": "doc-2", "filename": "prospects-linkedin.csv", "created_at": "2026-03-08T10:05:00Z"}
      ]
    }
    ```

**`GET /api/v1/reports/{file_id}`**
*   **Rôle** : Retourne le contenu brut (Markdown) ou pré-processé d'un document généré, pour le rendre dans le `<MarkdownViewer />` du front-end.

---

## 4. Stratégie d'Implémentation et Clean Architecture

1.  **Domain & Use Cases Intacts** : Les agents (Domain) et l'orchestrateur (Use Cases via `app/flow`) ne doivent pas avoir conscience qu'ils tournent sous FastAPI ou en CLI.
2.  **L'Adaptateur (Adapter) SSE** : Le principal défi technique backend sera un "Listener" asynchrone qui écoute les étapes de l'agent (`agent.think()`) et les encode au format *OpenAI compatibles* ou en structure SSE personnalisée pour que le Front-end puisse les afficher en *Streaming*.
3.  **Commandes** : On rajoutera un fichier racine `run_api.py` qui exécutera le serveur uvicorn : `uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload`.
