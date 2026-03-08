# Inventaire des Outils (Tools) Disponibles

Suite à l'analyse du dossier `app/tool/` du framework OpenExpertManus, voici la cartographie des outils **déjà existants** qui répondent parfaitement aux besoins de notre Agent IA de Marketing Digital décrits dans `spec/conception.md` :

---

## 1. Domaine : SEO (Action : SERPAnalyzer)
*Besoin : Extraire les requêtes Google, lire le contenu des résultats et les "People Also Ask".*

**Outils disponibles dans le projet :**
- **`app/tool/web_search.py`** : Fournit la classe `WebSearch` qui interroge directement Google, Bing, ou DuckDuckGo. Ce tool gère le scraping intelligent du contenu (`fetch_content=True`) pour lire le texte de la page sans le bruit HTML.
- **`app/tool/crawl4ai.py`** : Fournit des fonctionnalités de web crawling avancées avec extraction asynchrone pour analyser en profondeur les sites concurrents liés au SEO.

## 2. Domaine : LinkedIn (Action : LinkedInBrowser)
*Besoin : Naviguer sur LinkedIn, liker ou extraire des profils prospects.*

**Outils disponibles dans le projet :**
- **`app/tool/browser_use_tool.py`** : C'est le module de contrôle de navigateur par excellence (basé sur Playwright et l'AI). Il permet à l'agent de prendre le contrôle d'un navigateur headless pour se connecter à LinkedIn, cliquer sur des boutons précis, scroller et extraire l'information des profils exactement comme le ferait un humain.

## 3. Domaine : Contenu / Data (Action : DataAnalysisAgent)
*Besoin : Générer des graphiques de performance.*

**Outils disponibles dans le projet :**
- **`app/tool/chart_visualization/`** (dossier) : Ce répertoire contient l'agent spécialisé en data visualisation. Il est capable de prendre des données métier (ex: l'évolution du rang SEO ou des vues LinkedIn) et de générer automatiquement des visualisations sous forme de graphiques.
- **`app/tool/python_execute.py`** : Si des graphiques personnalisés (via matplotlib ou seaborn) ou un post-traitement des données sont nécessaires, ce tool permet à l'agent d'exécuter du code Python directement de façon sécurisée.

## 4. Domaine : Système (Action : FileSaver)
*Besoin : Sauvegarder les rapports SEO en .txt ou .md sur la machine locale.*

**Outils disponibles dans le projet :**
- **`app/tool/file_operators.py`** : Contient la classe `LocalFileOperator` avec la méthode `write_file`. Ce tool donne à l'agent la capacité native de créer, écrire et archiver des fichiers texte ou markdown (`.txt`, `.md`) directement dans le répertoire de travail de l'utilisateur.

---

### Conclusion
La bonne nouvelle est que **la quasi-totalité des briques techniques de base sont déjà développées et fonctionnelles** dans `app/tool/`.

L'effort de développement consistera principalement à :
1. Configurer finement les prompts de l'Agent pour qu'il chaîne ces outils logiquement.
2. S'assurer que les connexions requises (comme les cookies ou credentials LinkedIn pour le `browser_use_tool.py`) sont bien passées à l'environnement.
