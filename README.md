Jira Upgrade Baseline Toolkit

Toolkit Python destiné à préparer, documenter et contrôler une montée de version Jira Data Center.

Le projet collecte une baseline technique depuis Jira via un endpoint ScriptRunner, analyse la préparation de l'instance par rapport à une version Jira cible, contrôle les plateformes supportées et la compatibilité des applications, puis génère un rapport Excel exploitable avant et après l'upgrade.

Fonctionnalités principales

Collecte d'une baseline Jira Data Center via ScriptRunner.

Inventaire Jira, Java/JVM, OS, base de données, architecture et applications.

Analyse de readiness avant upgrade.

Contrôle des Supported Platforms pour la version Jira cible.

Analyse de compatibilité des applications Atlassian Marketplace.

Distinction entre applications Marketplace et composants Atlassian bundlés.

Recherche d'une version passerelle compatible source/cible lorsqu'elle existe.

Identification d'une version compatible uniquement avec la cible si aucune passerelle n'existe.

Génération de rapports Excel PRE, POST et COMPARE.

Comparaison de la baseline avant et après upgrade.

Architecture fonctionnelle

Jira Data Center
      |
      v
Endpoint ScriptRunner upgradeBaseline
      |
      v
Baseline JSON
      |
      +--> Baseline Analyzer
      |
      +--> Readiness Analyzer
      |       |
      |       +--> Supported Platforms
      |
      +--> App Compatibility
              |
              +--> Atlassian Marketplace API
              +--> Apps Atlassian bundlées
      |
      v
Rapport Excel PRE / POST / COMPARE

Prérequis

Python 3.11 ou supérieur recommandé.

Jira Data Center accessible depuis la machine exécutant le toolkit.

ScriptRunner installé sur l'instance Jira source.

Endpoint ScriptRunner upgradeBaseline déployé.

Compte/token permettant d'appeler l'endpoint Jira.

Accès Internet pour les contrôles Marketplace et les sources Atlassian externes.

Installation

Cloner le dépôt puis créer un environnement virtuel :

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copier ensuite le modèle de configuration :

Copy-Item .env.example .env

Le fichier .env contient les paramètres propres à l'environnement et ne doit jamais être versionné.

Configuration

Exemple :

JIRA_URL=http://jira.example.com
JIRA_PAT=CHANGE_ME

INSTANCE_NAME=JIRA01

TARGET_JIRA_FAMILY=11.3
TARGET_JIRA_VERSION=11.3.11

BASELINE_ENDPOINT=/rest/scriptrunner/latest/custom/upgradeBaseline

REQUEST_TIMEOUT=30
MAX_RETRIES=4
VERIFY_SSL=true

OUTPUT_DIR=output

JIRA_EMAIL=CHANGE_ME
JIRA_API_TOKEN=CHANGE_ME

Variables importantes

Variable

Description

JIRA_URL

URL de l'instance Jira à analyser.

JIRA_PAT

Token utilisé pour l'appel Jira lorsque ce mode d'authentification est utilisé.

INSTANCE_NAME

Nom logique utilisé dans les fichiers générés.

TARGET_JIRA_FAMILY

Famille Jira cible, par exemple 11.3.

TARGET_JIRA_VERSION

Version Jira cible exacte, par exemple 11.3.11.

BASELINE_ENDPOINT

Endpoint ScriptRunner utilisé pour la collecte.

REQUEST_TIMEOUT

Timeout HTTP en secondes.

MAX_RETRIES

Nombre maximum de retries HTTP.

VERIFY_SSL

Active/désactive la vérification SSL.

OUTPUT_DIR

Répertoire des fichiers générés.

JIRA_EMAIL

Identifiant Atlassian utilisé lorsque requis par l'API Marketplace.

JIRA_API_TOKEN

Token Atlassian utilisé lorsque requis par l'API Marketplace.

Utilisation

Baseline PRE

À exécuter avant l'upgrade :

python main.py --mode pre

Le toolkit collecte l'état source, calcule le readiness et génère les fichiers JSON/Excel de référence.

Baseline POST

À exécuter après l'upgrade :

python main.py --mode post

Comparaison PRE / POST

python main.py --mode compare

Le comparateur utilise les dernières baselines PRE et POST disponibles pour l'instance concernée.

Rapport Excel

Selon le mode et les données disponibles, le rapport peut contenir notamment :

Summary : synthèse de l'instance et de la cible.

Baseline : données techniques collectées.

Findings : constats issus de l'analyse de baseline.

Readiness : contrôles de préparation à l'upgrade.

Supported Platforms : matrice technique liée à la version Jira cible.

App Compatibility : stratégie de compatibilité des applications.

PRE_POST : comparaison avant/après lorsque le mode COMPARE est utilisé.

Le guide utilisateur détaille la signification des colonnes, des statuts et les informations à compléter manuellement.

Statuts Readiness

Statut

Signification

PASS

Contrôle effectué et conforme.

WARNING

Contrôle effectué avec point d'attention ou action requise.

FAIL

Prérequis non respecté ou blocage identifié.

NOT_ASSESSED

Information disponible mais contrôle non encore effectué.

UNKNOWN

Information non obtenue ou non déterminable.

INFO

Information descriptive, sans validation associée.

N/A

Contrôle non applicable.

Compatibilité des applications

Le toolkit distingue deux catégories principales.

Applications Marketplace

Le moteur analyse notamment :

la version actuellement installée ;

sa compatibilité avec Jira source ;

sa compatibilité avec Jira cible ;

la dernière version compatible avec la source ;

l'existence éventuelle d'une version passerelle compatible source et cible ;

une version compatible uniquement avec Jira cible si aucune passerelle n'existe.

Les stratégies possibles incluent notamment KEEP, PRE_UPGRADE_BRIDGE, PRE_UPGRADE_BRIDGE_THEN_POST, DISABLE_THEN_POST_UPGRADE, MANUAL_REVIEW et NO_TARGET_VERSION.

Composants Atlassian bundlés

Les composants connus comme Automation for Jira, Authentication / SSO Data Center ou Jira Cloud Migration Assistant ne suivent pas la logique de version passerelle Marketplace. Ils sont traités comme composants Atlassian fournis/bundlés avec Jira cible, avec validation fonctionnelle après upgrade lorsque nécessaire.

Sécurité

Ne jamais versionner :

.env ;

tokens/API keys ;

mots de passe ;

exports contenant des données client ;

fichiers générés dans output/ ;

logs d'exécution contenant des informations sensibles.

Le fichier .gitignore protège les principaux artefacts locaux et secrets.

Documentation

La documentation fonctionnelle détaillée est maintenue séparément :

Documentation d'architecture JiraUpgradeBaselineToolkit.

Guide utilisateur JiraUpgradeBaselineToolkit.

Les versions Word sont destinées à l'import dans Confluence.

Version

Version en préparation : v0.4

Principaux apports de cette version :

matrice Supported Platforms ;

analyse App Compatibility ;

gestion des versions bridge / target-only ;

traitement spécifique des applications Atlassian bundlées ;

enrichissement du rapport Excel et de la documentation.