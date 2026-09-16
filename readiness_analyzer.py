# ============================================================
# READINESS ANALYZER
#
# Objectif :
# Construire le tableau de préparation de l'upgrade Jira.
#
# Le fichier Excel PRE est généré une seule fois puis devient
# le document de travail vivant du projet.
#
# Les applications sont intégrées dynamiquement.
# ============================================================


import re

from compatibility_matrix import get_supported_platforms


# ============================================================
# OUTILS GENERIQUES
# ============================================================

def get_nested(
    data: dict,
    path: str
):
    """
    Récupère une valeur dans un dictionnaire imbriqué.

    Exemple :
        get_nested(baseline, "java.version")
    """

    current = data

    for part in path.split("."):

        if not isinstance(
            current,
            dict
        ):
            return None

        current = current.get(
            part
        )

        if current is None:
            return None

    return current


def first_value(
    data: dict,
    *paths
):
    """
    Retourne la première valeur non vide trouvée
    parmi plusieurs chemins possibles.

    Cela permet au Readiness de rester compatible
    avec les futurs enrichissements de la baseline.
    """

    for path in paths:

        value = get_nested(
            data,
            path
        )

        if value not in (
            None,
            "",
            [],
            {}
        ):
            return value

    return None


def display_value(
    value,
    default="Non renseigné"
):
    """
    Formate une valeur pour l'affichage Excel.
    """

    if value is None:
        return default

    if value is True:
        return "Oui"

    if value is False:
        return "Non"

    if isinstance(
        value,
        list
    ):
        return ", ".join(
            str(item)
            for item in value
        )

    return str(value)


def derive_target_family(
    target_family,
    target_version
):
    """
    Si TARGET_JIRA_FAMILY n'est pas renseigné,
    tente de dériver la famille depuis la version exacte.

    Exemple :
        11.3.2 -> 11.3
    """

    if target_family:
        return str(
            target_family
        ).strip()

    if target_version:

        parts = str(
            target_version
        ).split(".")

        if len(parts) >= 2:

            return ".".join(
                parts[:2]
            )

    return None



def extract_major_version(version):
    """
    Extrait la version majeure d'une valeur de version.

    Exemples :
        17.0.20.1 -> "17"
        21 -> "21"
        PostgreSQL 17.2 -> "17"
    """

    if version is None:
        return None

    match = re.search(
        r"(\d+)",
        str(version)
    )

    if not match:
        return None

    return match.group(1)


def matrix_status_to_readiness(
    support_status
):
    """
    Convertit le statut de la matrice de compatibilité
    en statut Readiness.
    """

    mapping = {
        "SUPPORTED": "PASS",
        "TESTED": "PASS",
        "DEPRECATED": "WARNING",
        "UNSUPPORTED": "FAIL"
    }

    return mapping.get(
        str(support_status or "").upper(),
        "NOT_ASSESSED"
    )


def get_matrix_rows(
    target_version,
    category=None,
    technology=None
):
    """
    Retourne les lignes de compatibility_matrix.py
    correspondant aux critères fournis.
    """

    if not target_version:
        return []

    rows = get_supported_platforms(
        target_version
    )

    filtered = []

    for item in rows:

        if category:
            if (
                str(
                    item.get(
                        "category",
                        ""
                    )
                ).lower()
                !=
                str(category).lower()
            ):
                continue

        if technology:
            if (
                str(
                    item.get(
                        "technology",
                        ""
                    )
                ).lower()
                !=
                str(technology).lower()
            ):
                continue

        filtered.append(
            item
        )

    return filtered


def get_java_compatibility(
    target_version,
    current_version
):
    """
    Evalue automatiquement la version Java détectée
    contre la matrice de la version Jira cible.
    """

    if not current_version:
        return {
            "status": "UNKNOWN",
            "target_expected": (
                "Version Java supportée par la cible Jira"
            ),
            "assessment_method": "AUTO",
            "action_required": (
                "Identifier la version Java utilisée par Jira"
            ),
            "message": (
                "La version Java n'a pas été détectée."
            )
        }

    if not target_version:
        return {
            "status": "NOT_ASSESSED",
            "target_expected": (
                "Version Java supportée par la cible Jira"
            ),
            "assessment_method": "EXTERNAL",
            "action_required": (
                "Définir TARGET_JIRA_VERSION avant "
                "d'évaluer Java"
            ),
            "message": (
                "La cible Jira exacte n'est pas définie."
            )
        }

    matrix_rows = get_matrix_rows(
        target_version,
        category="JAVA"
    )

    if not matrix_rows:
        return {
            "status": "NOT_ASSESSED",
            "target_expected": (
                f"Version Java supportée par Jira "
                f"{target_version}"
            ),
            "assessment_method": "EXTERNAL",
            "action_required": (
                "Compléter la matrice de compatibilité Java"
            ),
            "message": (
                "Aucune règle Java n'est disponible dans "
                "compatibility_matrix.py pour cette cible."
            )
        }

    supported_versions = []

    for item in matrix_rows:

        matrix_status = str(
            item.get(
                "status",
                ""
            )
        ).upper()

        matrix_version = str(
            item.get(
                "version",
                ""
            )
        )

        if (
            matrix_status in (
                "SUPPORTED",
                "TESTED"
            )
            and matrix_version
            not in supported_versions
        ):
            supported_versions.append(
                matrix_version
            )

    if supported_versions:
        target_expected = (
            "Java "
            + " ou ".join(
                supported_versions
            )
        )
    else:
        target_expected = (
            f"Version Java supportée par Jira "
            f"{target_version}"
        )

    current_major = extract_major_version(
        current_version
    )

    matching = []

    for item in matrix_rows:

        if (
            str(
                item.get(
                    "version",
                    ""
                )
            )
            == str(current_major)
        ):
            matching.append(
                item
            )

    if not matching:
        return {
            "status": "NOT_ASSESSED",
            "target_expected": target_expected,
            "assessment_method": "AUTO",
            "action_required": (
                "Vérifier cette version Java dans la "
                "documentation Atlassian"
            ),
            "message": (
                f"Java {current_major or current_version} "
                "n'est pas décrit explicitement dans la "
                "matrice locale."
            )
        }

    # En cas de plusieurs lignes pour une même version
    # (par exemple plusieurs distributions Java), on garde
    # le statut le plus contraignant.
    priority = {
        "UNSUPPORTED": 4,
        "DEPRECATED": 3,
        "SUPPORTED": 2,
        "TESTED": 2
    }

    selected = max(
        matching,
        key=lambda item: priority.get(
            str(
                item.get(
                    "status",
                    ""
                )
            ).upper(),
            0
        )
    )

    support_status = str(
        selected.get(
            "status",
            ""
        )
    ).upper()

    readiness_status = (
        matrix_status_to_readiness(
            support_status
        )
    )

    if readiness_status == "PASS":
        action_required = "Aucune"

    elif readiness_status == "WARNING":
        action_required = (
            "Planifier le passage à une version Java "
            "pleinement supportée"
        )

    elif readiness_status == "FAIL":
        action_required = (
            f"Installer/configurer {target_expected} "
            f"avant de démarrer Jira {target_version}"
        )

    else:
        action_required = (
            "Vérifier la compatibilité Java"
        )

    matrix_note = selected.get(
        "notes",
        ""
    )

    message = (
        f"Evaluation automatique : Java {current_major} "
        f"est {support_status} pour Jira {target_version}."
    )

    if matrix_note:
        message += (
            f" {matrix_note}"
        )

    return {
        "status": readiness_status,
        "target_expected": target_expected,
        "assessment_method": "AUTO",
        "action_required": action_required,
        "message": message
    }


def get_database_matrix_technology(
    database_name
):
    """
    Convertit le nom détecté de la base vers le nom
    utilisé dans compatibility_matrix.py.
    """

    value = str(
        database_name or ""
    ).strip().lower()

    if "postgres" in value:
        return "PostgreSQL"

    if value.startswith("mysql"):
        return "MySQL"

    if "oracle" in value:
        return "Oracle Database"

    if (
        "sql server" in value
        or "sqlserver" in value
        or "mssql" in value
    ):
        return "Microsoft SQL Server"

    if "mariadb" in value:
        return "MariaDB"

    if "percona" in value:
        return "PerconaDB"

    return None


def normalize_database_version_for_matrix(
    technology,
    raw_version
):
    """
    Transforme la version réelle de la base en version
    comparable aux entrées de compatibility_matrix.py.
    """

    if not raw_version:
        return None

    raw = str(
        raw_version
    ).strip()

    lower = raw.lower()

    if technology == "PostgreSQL":
        return extract_major_version(
            raw
        )

    if technology == "MySQL":
        match = re.search(
            r"(\d+)\.(\d+)",
            raw
        )

        if match:
            return (
                f"{match.group(1)}."
                f"{match.group(2)}"
            )

    if technology == "Oracle Database":

        if "23ai" in lower:
            return "23ai"

        if "19c" in lower:
            return "19c"

        major = extract_major_version(
            raw
        )

        if major == "23":
            return "23ai"

        if major == "19":
            return "19c"

    if technology == "Microsoft SQL Server":

        for year in (
            "2022",
            "2019",
            "2017"
        ):
            if year in raw:
                return year

        major = extract_major_version(
            raw
        )

        sql_server_major_mapping = {
            "16": "2022",
            "15": "2019",
            "14": "2017"
        }

        if major in sql_server_major_mapping:
            return sql_server_major_mapping[
                major
            ]

    if technology in (
        "MariaDB",
        "PerconaDB"
    ):
        return "Toutes"

    return raw


def get_database_compatibility(
    target_version,
    database_name,
    current_version
):
    """
    Evalue automatiquement la version de base détectée
    contre la matrice de la cible Jira.
    """

    technology = (
        get_database_matrix_technology(
            database_name
        )
    )

    if not target_version:
        return {
            "status": "NOT_ASSESSED",
            "target_expected": (
                "Version de base supportée par la cible Jira"
            ),
            "assessment_method": "EXTERNAL",
            "action_required": (
                "Définir TARGET_JIRA_VERSION avant "
                "d'évaluer la base"
            ),
            "message": (
                "La cible Jira exacte n'est pas définie."
            )
        }

    if not technology:
        return {
            "status": "NOT_ASSESSED",
            "target_expected": (
                f"Version de {database_name} supportée "
                f"par Jira {target_version}"
            ),
            "assessment_method": "EXTERNAL",
            "action_required": (
                "Vérifier manuellement la compatibilité "
                "de la base"
            ),
            "message": (
                "Le moteur détecté ne correspond pas à "
                "une technologie de la matrice locale."
            )
        }

    matrix_rows = get_matrix_rows(
        target_version,
        category="DATABASE",
        technology=technology
    )

    if not matrix_rows:
        return {
            "status": "NOT_ASSESSED",
            "target_expected": (
                f"Version de {technology} supportée "
                f"par Jira {target_version}"
            ),
            "assessment_method": "EXTERNAL",
            "action_required": (
                "Compléter la matrice de compatibilité "
                "de la base"
            ),
            "message": (
                "Aucune règle n'est disponible dans "
                "compatibility_matrix.py pour ce moteur."
            )
        }

    supported = []
    deprecated = []

    for item in matrix_rows:

        matrix_status = str(
            item.get(
                "status",
                ""
            )
        ).upper()

        matrix_version = str(
            item.get(
                "version",
                ""
            )
        )

        if matrix_status in (
            "SUPPORTED",
            "TESTED"
        ):
            if matrix_version not in supported:
                supported.append(
                    matrix_version
                )

        elif matrix_status == "DEPRECATED":
            if matrix_version not in deprecated:
                deprecated.append(
                    matrix_version
                )

    expectation_parts = []

    if supported:
        expectation_parts.append(
            f"{technology} "
            + ", ".join(supported)
            + " supporté"
        )

    if deprecated:
        expectation_parts.append(
            f"{technology} "
            + ", ".join(deprecated)
            + " déprécié"
        )

    target_expected = (
        " ; ".join(
            expectation_parts
        )
        if expectation_parts
        else
        f"Version de {technology} supportée "
        f"par Jira {target_version}"
    )

    if not current_version:
        return {
            "status": "UNKNOWN",
            "target_expected": target_expected,
            "assessment_method": "AUTO",
            "action_required": (
                f"Récupérer automatiquement la version "
                f"de {technology}"
            ),
            "message": (
                "Le moteur de base est identifié, mais sa "
                "version exacte n'est pas encore disponible."
            )
        }

    comparable_version = (
        normalize_database_version_for_matrix(
            technology,
            current_version
        )
    )

    selected = None

    for item in matrix_rows:

        if (
            str(
                item.get(
                    "version",
                    ""
                )
            ).lower()
            ==
            str(
                comparable_version
            ).lower()
        ):
            selected = item
            break

    if not selected:
        return {
            "status": "NOT_ASSESSED",
            "target_expected": target_expected,
            "assessment_method": "AUTO",
            "action_required": (
                "Vérifier cette version dans la "
                "documentation Atlassian"
            ),
            "message": (
                f"La version {current_version} de "
                f"{technology} n'est pas décrite "
                "explicitement dans la matrice locale."
            )
        }

    support_status = str(
        selected.get(
            "status",
            ""
        )
    ).upper()

    readiness_status = (
        matrix_status_to_readiness(
            support_status
        )
    )

    if readiness_status == "PASS":
        action_required = "Aucune"

    elif readiness_status == "WARNING":
        action_required = (
            f"Évaluer le passage de {technology} "
            "à une version pleinement supportée"
        )

    elif readiness_status == "FAIL":
        action_required = (
            f"Mettre à niveau {technology} vers une "
            f"version supportée avant Jira {target_version}"
        )

    else:
        action_required = (
            "Vérifier la compatibilité de la base"
        )

    matrix_note = selected.get(
        "notes",
        ""
    )

    message = (
        f"Evaluation automatique : {technology} "
        f"{comparable_version} est {support_status} "
        f"pour Jira {target_version}."
    )

    if matrix_note:
        message += (
            f" {matrix_note}"
        )

    return {
        "status": readiness_status,
        "target_expected": target_expected,
        "assessment_method": "AUTO",
        "action_required": action_required,
        "message": message
    }

def determine_responsible(
    assessment_method: str,
    domain: str,
    check: str
) -> str:
    """
    Détermine le responsable opérationnel d'une ligne Readiness.

    Assessment Method répond à la question : "comment le contrôle
    est-il réalisé ?"

    Responsable répond à la question : "qui doit traiter, renseigner
    ou valider ce contrôle ?"

    Valeurs normalisées :
        OUTIL
        PILOTE JIRA
        INFRA
        DB
        PILOTE JIRA + INFRA
        PILOTE JIRA + DB
        INFRA + DB
        PILOTE JIRA + INFRA + DB
    """

    method = str(assessment_method or "").strip().upper()
    domain_name = str(domain or "").strip().upper()
    check_name = str(check or "").strip().lower()

    # Les contrôles AUTO sont alimentés par le toolkit.
    if method == "AUTO":
        return "OUTIL"

    # Les contrôles de compatibilité des applications sont pilotés
    # côté Jira, même lorsque la source est Marketplace / éditeur.
    if domain_name == "APPLICATIONS":
        return "PILOTE JIRA"

    # Contrôles EXTERNAL : la source de vérité est externe au projet.
    if method == "EXTERNAL":
        if domain_name == "UPGRADE":
            return "PILOTE JIRA"
        if domain_name == "OS":
            return "PILOTE JIRA + INFRA"
        if domain_name == "JAVA":
            return "PILOTE JIRA + INFRA"
        if domain_name == "DATABASE":
            return "PILOTE JIRA + DB"
        return "PILOTE JIRA"

    # Contrôles MANUAL : répartition selon le domaine opérationnel.
    if method == "MANUAL":
        if domain_name == "UPGRADE":
            return "PILOTE JIRA"

        if domain_name == "JAVA":
            return "PILOTE JIRA + INFRA"

        if domain_name in {"INFRASTRUCTURE", "PROXY"}:
            return "INFRA"

        if domain_name == "FILESYSTEM":
            if "personnalis" in check_name or "modifi" in check_name:
                return "PILOTE JIRA + INFRA"
            return "INFRA"

        if domain_name in {"AUTHENTICATION", "LDAP", "MAIL"}:
            return "PILOTE JIRA + INFRA"

        if domain_name in {"AUTOMATION", "SCRIPTING", "INDEX", "TESTING", "LICENSING"}:
            return "PILOTE JIRA"

        if domain_name == "INTEGRATIONS":
            return "PILOTE JIRA + INFRA"

        if domain_name == "DATA":
            return "PILOTE JIRA + INFRA"

        if domain_name == "DATABASE":
            return "PILOTE JIRA + DB"

        if domain_name == "BACKUP":
            if "base de données" in check_name or "database" in check_name:
                return "DB"
            return "INFRA"

        if domain_name == "ROLLBACK":
            return "PILOTE JIRA + INFRA + DB"

        if domain_name == "CLONE":
            if "clone de production" in check_name:
                return "PILOTE JIRA + INFRA + DB"
            return "PILOTE JIRA + INFRA"

        if domain_name == "ACCESS":
            if "base de données" in check_name or "db" in check_name:
                return "DB"
            if "serveur" in check_name:
                return "INFRA"
            if "administrateur jira" in check_name:
                return "PILOTE JIRA"
            return "PILOTE JIRA + INFRA"

        if domain_name in {"LOGGING", "MONITORING"}:
            return "PILOTE JIRA + INFRA"

        if domain_name == "GOVERNANCE":
            return "PILOTE JIRA + INFRA + DB"

        return "PILOTE JIRA"

    return ""


def readiness_finding(
    status: str,
    domain: str,
    check: str,
    current_value,
    target_expected,
    selected_value="",
    assessment_method="",
    responsible=None,
    action_required="",
    message=""
) -> dict:
    """
    Structure standard d'une ligne Readiness.

    Current Value
        Etat constaté / information détectée.

    Target / Expected
        Condition précise attendue.

    Version / valeur retenue
        Décision projet. Elle sera généralement
        complétée manuellement dans Excel.

    Assessment Method
        AUTO
        EXTERNAL
        MANUAL

    Responsable
        Équipe qui doit traiter, renseigner ou valider le contrôle.
        Si aucune valeur explicite n'est fournie, elle est dérivée
        automatiquement du domaine et de la méthode d'évaluation.
    """

    if responsible in (None, ""):
        responsible = determine_responsible(
            assessment_method,
            domain,
            check
        )

    return {
        "status": status,
        "domain": domain,
        "check": check,
        "current_value": current_value,

        # Nouveau modèle
        "target_expected": target_expected,
        "selected_value": selected_value,
        "assessment_method": assessment_method,
        "responsible": responsible,
        "action_required": action_required,
        "message": message,

        # Compatibilité temporaire éventuelle
        # avec d'autres parties de l'ancien programme.
        "target_value": target_expected
    }


# ============================================================
# ANALYSE READINESS
# ============================================================

def analyze_readiness(
    baseline: dict,
    settings
) -> list[dict]:

    results = []

    # ========================================================
    # DONNEES PRINCIPALES
    # ========================================================

    jira = baseline.get(
        "jira",
        {}
    )

    java = baseline.get(
        "java",
        {}
    )

    database = baseline.get(
        "database",
        {}
    )

    architecture = baseline.get(
        "architecture",
        {}
    )

    third_party_apps = baseline.get(
        "thirdPartyApps",
        []
    ) or []

    important_apps = baseline.get(
        "importantAtlassianApps",
        []
    ) or []

    # ========================================================
    # SOURCE / CIBLE
    # ========================================================

    source_version = jira.get(
        "version"
    )

    configured_target_family = getattr(
        settings,
        "target_jira_family",
        None
    )

    target_version = getattr(
        settings,
        "target_jira_version",
        None
    )

    target_version = (
        str(target_version).strip()
        if target_version
        else None
    )

    target_family = derive_target_family(
        configured_target_family,
        target_version
    )

    if target_version:

        target_label = (
            f"Jira {target_version}"
        )

    elif target_family:

        target_label = (
            f"Jira {target_family}.x"
        )

    else:

        target_label = (
            "cible Jira non définie"
        )

    # ========================================================
    # JIRA - VERSION SOURCE
    # ========================================================

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if source_version
                else "UNKNOWN"
            ),
            domain="JIRA",
            check="Version source Jira",
            current_value=display_value(
                source_version
            ),
            target_expected=(
                "Version source Jira "
                "détectée automatiquement"
            ),
            assessment_method="AUTO",
            action_required=(
                "Aucune"
                if source_version
                else
                "Corriger la collecte de la version Jira"
            ),
            message=(
                "Version Jira actuellement installée "
                "sur l'instance source."
            )
        )
    )

    # ========================================================
    # JIRA - BUILD SOURCE
    # ========================================================

    application_build = jira.get(
        "applicationBuildNumber"
    )

    database_build = jira.get(
        "databaseBuildNumber"
    )

    builds_match = jira.get(
        "buildsMatch"
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if application_build
                else "UNKNOWN"
            ),
            domain="JIRA",
            check="Build source Jira",
            current_value=display_value(
                application_build
            ),
            target_expected=(
                "Build de l'instance source "
                "correctement identifié"
            ),
            assessment_method="AUTO",
            action_required=(
                "Aucune"
                if application_build
                else
                "Identifier le build Jira source"
            ),
            message=(
                "Numéro de build actuellement "
                "détecté sur Jira."
            )
        )
    )

    # ========================================================
    # JIRA - COHERENCE BUILD / DB
    # ========================================================

    build_current = (
        f"Jira: {display_value(application_build)} "
        f"/ DB: {display_value(database_build)}"
    )

    if builds_match is True:

        build_status = "PASS"
        build_action = "Aucune"
        build_message = (
            "Le build applicatif Jira correspond "
            "au build enregistré en base."
        )

    elif builds_match is False:

        build_status = "FAIL"
        build_action = (
            "Analyser l'incohérence entre "
            "le build Jira et la base"
        )
        build_message = (
            "Le build applicatif Jira et le build "
            "enregistré en base sont différents."
        )

    else:

        build_status = "UNKNOWN"
        build_action = (
            "Déterminer les builds Jira et DB"
        )
        build_message = (
            "La cohérence entre le build applicatif "
            "et le build DB n'a pas pu être déterminée."
        )

    results.append(
        readiness_finding(
            status=build_status,
            domain="JIRA",
            check="Cohérence build Jira / base",
            current_value=build_current,
            target_expected=(
                "Build Jira installé identique au "
                "build enregistré en base"
            ),
            assessment_method="AUTO",
            action_required=build_action,
            message=build_message
        )
    )

    # ========================================================
    # UPGRADE - VERSION CIBLE
    # ========================================================

    if target_version:

        target_status = "PASS"

        target_expected = (
            f"Version exacte de {target_label} définie"
        )

        selected_target = (
            target_version
        )

        target_action = "Aucune"

        target_message = (
            "La version cible exacte est définie "
            "dans TARGET_JIRA_VERSION."
        )

    else:

        target_status = "NOT_ASSESSED"

        target_expected = (
            f"Version Jira "
            f"{target_family}.x exacte définie"
            if target_family
            else
            "Version cible Jira exacte définie"
        )

        selected_target = ""

        target_action = (
            "Renseigner TARGET_JIRA_VERSION "
            "dans le fichier .env"
        )

        target_message = (
            "La famille Jira cible est connue mais "
            "la version exacte n'est pas encore retenue."
            if target_family
            else
            "La cible Jira n'est pas encore définie."
        )

    results.append(
        readiness_finding(
            status=target_status,
            domain="UPGRADE",
            check="Version cible Jira",
            current_value="Non applicable",
            target_expected=target_expected,
            selected_value=selected_target,
            assessment_method="MANUAL",
            action_required=target_action,
            message=target_message
        )
    )

    # ========================================================
    # UPGRADE - BUILD CIBLE
    #
    # Pas de build inventé ou calculé.
    # ========================================================

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="UPGRADE",
            check="Build cible Jira",
            current_value="Non déterminé",
            target_expected=(
                f"Build officiel correspondant "
                f"à {target_label}"
            ),
            selected_value="",
            assessment_method="EXTERNAL",
            action_required=(
                "Déterminer le build officiel de "
                "la version Jira cible"
                if target_version
                else
                "Définir d'abord la version Jira cible exacte"
            ),
            message=(
                "Le build cible ne doit pas être calculé "
                "ou deviné. Il devra être obtenu depuis "
                "une source Atlassian fiable."
            )
        )
    )

    # ========================================================
    # UPGRADE - CHEMIN
    # ========================================================

    upgrade_path = (
        f"{source_version or 'Source inconnue'} "
        f"→ {target_label}"
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="UPGRADE",
            check="Chemin de montée de version",
            current_value=upgrade_path,
            target_expected=(
                "Chemin de montée de version "
                "supporté par Atlassian"
            ),
            assessment_method="EXTERNAL",
            action_required=(
                "Vérifier le chemin d'upgrade "
                "dans la documentation Atlassian"
            ),
            message=(
                "Contrôle du chemin entre la version "
                "source et la version cible."
            )
        )
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="UPGRADE",
            check="Version intermédiaire",
            current_value="Non déterminée",
            target_expected=(
                "Aucune version intermédiaire requise "
                "ou version intermédiaire identifiée"
            ),
            assessment_method="EXTERNAL",
            action_required=(
                "Vérifier si une version intermédiaire "
                "est nécessaire"
            ),
            message=(
                "La nécessité d'une étape intermédiaire "
                "dépend du chemin d'upgrade supporté."
            )
        )
    )

    # ========================================================
    # JAVA
    #
    # Les informations techniques de la JVM sont collectées
    # automatiquement par l'endpoint ScriptRunner.
    # La compatibilité est évaluée automatiquement à partir
    # de compatibility_matrix.py lorsque TARGET_JIRA_VERSION
    # est défini.
    # ========================================================

    java_version = java.get(
        "version"
    )

    java_vendor = java.get(
        "vendor"
    )

    java_vm_name = java.get(
        "vmName"
    )

    java_vm_version = java.get(
        "vmVersion"
    )

    java_home = first_value(
        baseline,
        "java.javaHome",
        "java.home",
        "system.javaHome"
    )

    environment_java_home = first_value(
        baseline,
        "java.environmentJavaHome"
    )

    xms = first_value(
        baseline,
        "java.xms",
        "java.jvmMinimumMemory",
        "jvm.xms"
    )

    xmx = first_value(
        baseline,
        "java.xmx",
        "java.jvmMaximumMemory",
        "jvm.xmx"
    )

    max_heap_mb = first_value(
        baseline,
        "java.maxHeapMB"
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if java_version
                else "UNKNOWN"
            ),
            domain="JAVA",
            check="Version Java détectée",
            current_value=display_value(
                java_version
            ),
            target_expected=(
                "Version Java de l'instance "
                "source correctement identifiée"
            ),
            assessment_method="AUTO",
            action_required=(
                "Aucune"
                if java_version
                else
                "Identifier la JVM utilisée par Jira"
            ),
            message=(
                "Version Java réellement utilisée "
                "par le processus Jira."
            )
        )
    )

    java_compatibility = get_java_compatibility(
        target_version,
        java_version
    )

    results.append(
        readiness_finding(
            status=java_compatibility[
                "status"
            ],
            domain="JAVA",
            check="Compatibilité Java avec la cible",
            current_value=(
                f"Java {java_version}"
                if java_version
                else "Non renseigné"
            ),
            target_expected=java_compatibility[
                "target_expected"
            ],
            assessment_method=java_compatibility[
                "assessment_method"
            ],
            action_required=java_compatibility[
                "action_required"
            ],
            message=java_compatibility[
                "message"
            ]
        )
    )

    vm_display_parts = []

    if java_vm_name:
        vm_display_parts.append(
            str(java_vm_name)
        )

    if java_vm_version:
        vm_display_parts.append(
            str(java_vm_version)
        )

    if java_vendor:
        vm_display_parts.append(
            str(java_vendor)
        )

    vm_display = (
        " / ".join(vm_display_parts)
        if vm_display_parts
        else "Non renseigné"
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if vm_display_parts
                else "UNKNOWN"
            ),
            domain="JAVA",
            check="JVM utilisée par Jira",
            current_value=vm_display,
            target_expected=(
                "JVM utilisée par Jira identifiée"
            ),
            assessment_method="AUTO",
            action_required=(
                "Aucune"
                if vm_display_parts
                else
                "Identifier la JVM utilisée par Jira"
            ),
            message=(
                "Nom, version de VM et fournisseur "
                "détectés sur le processus Jira."
            )
        )
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if java_home
                else "UNKNOWN"
            ),
            domain="JAVA",
            check="JDK réellement utilisé par Jira",
            current_value=display_value(
                java_home
            ),
            target_expected=(
                "Chemin du JDK réellement utilisé "
                "par le processus Jira identifié"
            ),
            assessment_method="AUTO",
            action_required=(
                "Aucune"
                if java_home
                else
                "Identifier le JDK réellement utilisé par Jira"
            ),
            message=(
                "Valeur issue de la propriété système "
                "java.home du processus Jira."
            )
        )
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if environment_java_home
                else "UNKNOWN"
            ),
            domain="JAVA",
            check="JAVA_HOME environnement",
            current_value=display_value(
                environment_java_home
            ),
            target_expected=(
                "Variable JAVA_HOME identifiée"
            ),
            assessment_method="AUTO",
            action_required=(
                "Aucune"
                if environment_java_home
                else
                "Identifier la variable JAVA_HOME"
            ),
            message=(
                "Variable JAVA_HOME visible par "
                "le processus Jira."
            )
        )
    )

    if java_home and environment_java_home:

        normalized_java_home = (
            str(java_home)
            .rstrip("\\/")
            .lower()
        )

        normalized_environment_java_home = (
            str(environment_java_home)
            .rstrip("\\/")
            .lower()
        )

        java_home_match = (
            normalized_java_home
            == normalized_environment_java_home
        )

        java_home_status = (
            "PASS"
            if java_home_match
            else "WARNING"
        )

        java_home_action = (
            "Aucune"
            if java_home_match
            else
            "Vérifier pourquoi JAVA_HOME et le JDK Jira diffèrent"
        )

        java_home_message = (
            "JAVA_HOME et le JDK réellement utilisé "
            "par Jira sont cohérents."
            if java_home_match
            else
            "JAVA_HOME ne correspond pas au JDK "
            "réellement utilisé par Jira."
        )

    else:

        java_home_status = "UNKNOWN"
        java_home_action = (
            "Compléter les informations Java Home"
        )
        java_home_message = (
            "Impossible de comparer JAVA_HOME au JDK "
            "réellement utilisé par Jira."
        )

    results.append(
        readiness_finding(
            status=java_home_status,
            domain="JAVA",
            check="Cohérence JAVA_HOME / JVM Jira",
            current_value=(
                f"Jira: {display_value(java_home)} / "
                f"JAVA_HOME: {display_value(environment_java_home)}"
            ),
            target_expected=(
                "JAVA_HOME cohérent avec le JDK "
                "réellement utilisé par Jira"
            ),
            assessment_method="AUTO",
            action_required=java_home_action,
            message=java_home_message
        )
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if xms
                else "UNKNOWN"
            ),
            domain="JAVA",
            check="Mémoire JVM Xms",
            current_value=display_value(
                xms
            ),
            target_expected=(
                "Valeur Xms identifiée et validée "
                "pour l'environnement cible"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Valider le dimensionnement Xms"
            ),
            message=(
                "La valeur est collectée automatiquement ; "
                "son dimensionnement reste à valider."
            )
        )
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if xmx
                else "UNKNOWN"
            ),
            domain="JAVA",
            check="Mémoire JVM Xmx",
            current_value=display_value(
                xmx
            ),
            target_expected=(
                "Valeur Xmx identifiée et validée "
                "pour l'environnement cible"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Valider le dimensionnement Xmx"
            ),
            message=(
                "La valeur est collectée automatiquement ; "
                "son dimensionnement reste à valider."
            )
        )
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if max_heap_mb is not None
                else "UNKNOWN"
            ),
            domain="JAVA",
            check="Heap JVM maximale détectée",
            current_value=(
                f"{max_heap_mb} MB"
                if max_heap_mb is not None
                else "Non renseigné"
            ),
            target_expected=(
                "Heap JVM maximale identifiée et "
                "cohérente avec le Xmx configuré"
            ),
            assessment_method="AUTO",
            action_required=(
                "Vérifier la cohérence avec Xmx"
            ),
            message=(
                "Valeur maximale réellement exposée "
                "par la JVM au moment de la collecte."
            )
        )
    )

    # ========================================================
    # DATABASE
    # ========================================================

    database_type = database.get(
        "type"
    )

    database_product_name = first_value(
        baseline,
        "database.productName",
        "database.databaseProductName"
    )

    database_version = first_value(
        baseline,
        "database.productVersion",
        "database.version",
        "database.databaseVersion"
    )

    jdbc_driver = first_value(
        baseline,
        "database.jdbcDriver",
        "database.driverClass"
    )

    driver_version = first_value(
        baseline,
        "database.driverVersion",
        "database.jdbcDriverVersion"
    )

    database_schema = database.get(
        "schema"
    )

    database_jdbc_url = database.get(
        "jdbcUrl"
    )

    if database_product_name:

        db_name = str(
            database_product_name
        )

    elif database_type:

        database_type_lower = str(
            database_type
        ).lower()

        if database_type_lower.startswith(
            "postgres"
        ):
            db_name = "PostgreSQL"

        elif database_type_lower.startswith(
            "mysql"
        ):
            db_name = "MySQL"

        elif database_type_lower.startswith(
            "oracle"
        ):
            db_name = "Oracle"

        elif (
            "sqlserver" in database_type_lower
            or "mssql" in database_type_lower
        ):
            db_name = "Microsoft SQL Server"

        else:
            db_name = str(
                database_type
            )

    else:

        db_name = "base de données"

    database_engine_display = (
        f"{db_name} (type Jira: {database_type})"
        if database_type and db_name != database_type
        else display_value(database_type or database_product_name)
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if database_type or database_product_name
                else "UNKNOWN"
            ),
            domain="DATABASE",
            check="Moteur de base de données",
            current_value=database_engine_display,
            target_expected=(
                "Moteur de base correctement identifié"
            ),
            assessment_method="AUTO",
            action_required=(
                "Aucune"
                if database_type or database_product_name
                else
                "Identifier le moteur de base"
            ),
            message=(
                "Le type Jira postgres72 désigne PostgreSQL ; "
                "il ne représente pas la version PostgreSQL 7.2."
                if str(database_type).lower().startswith("postgres")
                else
                "Moteur de base utilisé par Jira."
            )
        )
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if database_version
                else "UNKNOWN"
            ),
            domain="DATABASE",
            check=f"Version {db_name}",
            current_value=display_value(
                database_version
            ),
            target_expected=(
                f"Version exacte de {db_name} identifiée"
            ),
            assessment_method="AUTO",
            action_required=(
                "Aucune"
                if database_version
                else
                f"Récupérer automatiquement la version de {db_name}"
            ),
            message=(
                "La version du moteur n'est pas encore "
                "présente dans la baseline actuelle."
                if not database_version
                else
                "Version exacte du moteur de base détectée."
            )
        )
    )

    database_compatibility = get_database_compatibility(
        target_version,
        db_name,
        database_version
    )

    results.append(
        readiness_finding(
            status=database_compatibility[
                "status"
            ],
            domain="DATABASE",
            check="Compatibilité base de données",
            current_value=(
                f"{db_name} {database_version}"
                if database_version
                else f"{db_name} - version non détectée"
            ),
            target_expected=database_compatibility[
                "target_expected"
            ],
            assessment_method=database_compatibility[
                "assessment_method"
            ],
            action_required=database_compatibility[
                "action_required"
            ],
            message=database_compatibility[
                "message"
            ]
        )
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if jdbc_driver
                else "UNKNOWN"
            ),
            domain="DATABASE",
            check="Driver JDBC utilisé",
            current_value=display_value(
                jdbc_driver
            ),
            target_expected=(
                "Classe du driver JDBC identifiée"
            ),
            assessment_method="AUTO",
            action_required=(
                "Aucune"
                if jdbc_driver
                else
                "Identifier le driver JDBC utilisé"
            ),
            message=(
                "Classe Java du driver JDBC configuré "
                "dans dbconfig.xml."
            )
        )
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if driver_version
                else "UNKNOWN"
            ),
            domain="DATABASE",
            check="Version du driver JDBC",
            current_value=display_value(
                driver_version
            ),
            target_expected=(
                f"Version du driver JDBC supportée "
                f"pour {target_label}"
            ),
            assessment_method=(
                "EXTERNAL"
                if driver_version
                else "AUTO"
            ),
            action_required=(
                "Vérifier la compatibilité du driver JDBC"
                if driver_version
                else
                "Récupérer automatiquement la version du driver JDBC"
            ),
            message=(
                "La classe JDBC est connue, mais sa version "
                "n'est pas encore remontée par l'endpoint."
                if not driver_version
                else
                "Version du driver JDBC détectée."
            )
        )
    )

    db_connection_parts = []

    if database_jdbc_url:
        db_connection_parts.append(
            str(database_jdbc_url)
        )

    if database_schema:
        db_connection_parts.append(
            f"schéma={database_schema}"
        )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if db_connection_parts
                else "UNKNOWN"
            ),
            domain="DATABASE",
            check="Configuration de connexion DB",
            current_value=(
                " / ".join(db_connection_parts)
                if db_connection_parts
                else "Non renseigné"
            ),
            target_expected=(
                "URL JDBC et schéma de la base identifiés"
            ),
            assessment_method="AUTO",
            action_required=(
                "Aucune"
                if db_connection_parts
                else
                "Identifier la configuration DB"
            ),
            message=(
                "Le mot de passe n'est jamais collecté "
                "dans la baseline."
            )
        )
    )

    database_build_for_connection = jira.get(
        "databaseBuildNumber"
    )

    results.append(
        readiness_finding(
            status=(
                "PASS"
                if database_build_for_connection
                else "NOT_ASSESSED"
            ),
            domain="DATABASE",
            check="Connectivité Jira vers la base",
            current_value=(
                f"Connexion opérationnelle - build DB "
                f"{database_build_for_connection}"
                if database_build_for_connection
                else "À confirmer"
            ),
            target_expected=(
                "Connexion Jira vers la base opérationnelle"
            ),
            assessment_method="AUTO",
            action_required=(
                "Aucune"
                if database_build_for_connection
                else
                "Valider la connectivité DB avant l'upgrade"
            ),
            message=(
                "Le build DB est lu par Jira, ce qui confirme "
                "une connexion active à la base au moment "
                "de la collecte."
                if database_build_for_connection
                else
                "La connectivité n'a pas pu être confirmée."
            )
        )
    )

    # ========================================================
    # ARCHITECTURE
    # ========================================================

    clustered = architecture.get(
        "clustered"
    )

    if clustered is True:

        topology = "Cluster"
        topology_status = "INFO"

    elif clustered is False:

        topology = "Single node"
        topology_status = "INFO"

    else:

        topology = "Non déterminée"
        topology_status = "UNKNOWN"

    results.append(
        readiness_finding(
            status=topology_status,
            domain="ARCHITECTURE",
            check="Topologie Jira",
            current_value=topology,
            target_expected=(
                f"Architecture connue et supportée "
                f"par {target_label}"
            ),
            assessment_method="AUTO",
            action_required=(
                "Valider l'architecture cible"
            ),
            message=(
                "Topologie actuelle de l'instance Jira."
            )
        )
    )

    shared_home = first_value(
        baseline,
        "architecture.sharedHome",
        "filesystem.sharedHome"
    )

    if clustered is False:

        shared_status = "N/A"
        shared_current = "Non applicable"
        shared_action = "Aucune"

    elif shared_home:

        shared_status = "INFO"
        shared_current = shared_home
        shared_action = (
            "Vérifier le Shared Home"
        )

    else:

        shared_status = "UNKNOWN"
        shared_current = "Non renseigné"
        shared_action = (
            "Identifier le Shared Home"
        )

    results.append(
        readiness_finding(
            status=shared_status,
            domain="ARCHITECTURE",
            check="Shared Home Data Center",
            current_value=shared_current,
            target_expected=(
                "Shared Home identifié et accessible "
                "pour une architecture cluster"
            ),
            assessment_method="AUTO",
            action_required=shared_action,
            message=(
                "Non applicable aux instances "
                "single node."
            )
        )
    )

    # ========================================================
    # JIRA - BASE URL
    # ========================================================

    base_url = jira.get(
        "baseUrl"
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if base_url
                else "UNKNOWN"
            ),
            domain="JIRA",
            check="Base URL",
            current_value=display_value(
                base_url
            ),
            target_expected=(
                "Base URL de l'environnement "
                "correctement identifiée"
            ),
            assessment_method="AUTO",
            action_required=(
                "Vérifier la Base URL"
            ),
            message=(
                "La présence d'une URL ne suffit pas "
                "à prouver que le clone est isolé."
            )
        )
    )

    # ========================================================
    # OS
    # ========================================================

    os_name = first_value(
        baseline,
        "operatingSystem.name",
        "os.name",
        "system.osName",
        "system.operatingSystem"
    )

    os_version = first_value(
        baseline,
        "operatingSystem.version",
        "os.version",
        "system.osVersion"
    )

    os_architecture = first_value(
        baseline,
        "operatingSystem.architecture",
        "os.architecture",
        "system.architecture"
    )

    if os_name and os_version:

        os_display = (
            f"{os_name} / version {os_version}"
        )

    else:

        os_display = display_value(
            os_name or os_version
        )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if os_name or os_version
                else "UNKNOWN"
            ),
            domain="OS",
            check="Système d'exploitation",
            current_value=os_display,
            target_expected=(
                "OS et version exacte identifiés"
            ),
            assessment_method="AUTO",
            action_required=(
                "Aucune"
                if os_name or os_version
                else
                "Identifier l'OS et sa version"
            ),
            message=(
                "Système d'exploitation du serveur Jira "
                "collecté automatiquement."
            )
        )
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if os_architecture
                else "UNKNOWN"
            ),
            domain="OS",
            check="Architecture système",
            current_value=display_value(
                os_architecture
            ),
            target_expected=(
                "Architecture système identifiée "
                "et adaptée à la cible"
            ),
            assessment_method="AUTO",
            action_required=(
                "Valider l'architecture système"
            ),
            message=(
                "Architecture du système d'exploitation "
                "exposée à la JVM."
            )
        )
    )

    results.append(
        readiness_finding(
            status=(
                "NOT_ASSESSED"
                if os_name or os_version
                else "UNKNOWN"
            ),
            domain="OS",
            check="Compatibilité OS avec la cible",
            current_value=os_display,
            target_expected=(
                f"OS supporté par {target_label}"
            ),
            assessment_method="EXTERNAL",
            action_required=(
                "Vérifier l'OS dans les "
                "Supported Platforms Atlassian"
            ),
            message=(
                "La plateforme est détectée automatiquement ; "
                "sa compatibilité avec Jira cible reste à valider."
            )
        )
    )

    # ========================================================
    # INFRASTRUCTURE
    # ========================================================

    hostname = first_value(
        baseline,
        "operatingSystem.hostname",
        "system.hostname"
    )

    service_user = first_value(
        baseline,
        "operatingSystem.serviceUser",
        "system.serviceUser"
    )

    cpu = first_value(
        baseline,
        "operatingSystem.processors",
        "system.cpu",
        "infrastructure.cpu",
        "system.cpuCount"
    )

    total_ram_gb = first_value(
        baseline,
        "operatingSystem.totalPhysicalMemoryGB",
        "system.totalPhysicalMemoryGB",
        "system.ram",
        "infrastructure.ram",
        "system.totalMemory"
    )

    free_ram_gb = first_value(
        baseline,
        "operatingSystem.freePhysicalMemoryGB",
        "system.freePhysicalMemoryGB"
    )

    jira_home_disk_total = first_value(
        baseline,
        "filesystem.jiraHomeDisk.totalGB",
        "disk.totalGB"
    )

    jira_home_disk_free = first_value(
        baseline,
        "filesystem.jiraHomeDisk.freeGB",
        "disk.freeGB"
    )

    jira_home_disk_usable = first_value(
        baseline,
        "filesystem.jiraHomeDisk.usableGB",
        "disk.usableGB"
    )

    jira_install_disk_total = first_value(
        baseline,
        "filesystem.jiraInstallDisk.totalGB"
    )

    jira_install_disk_usable = first_value(
        baseline,
        "filesystem.jiraInstallDisk.usableGB"
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if hostname
                else "UNKNOWN"
            ),
            domain="INFRASTRUCTURE",
            check="Nom du serveur Jira",
            current_value=display_value(
                hostname
            ),
            target_expected=(
                "Serveur hébergeant Jira identifié"
            ),
            assessment_method="AUTO",
            action_required=(
                "Aucune"
                if hostname
                else
                "Identifier le serveur Jira"
            ),
            message=(
                "Hostname du serveur exécutant le processus Jira."
            )
        )
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if service_user
                else "UNKNOWN"
            ),
            domain="INFRASTRUCTURE",
            check="Compte de service Jira",
            current_value=display_value(
                service_user
            ),
            target_expected=(
                "Compte exécutant le service Jira identifié"
            ),
            assessment_method="AUTO",
            action_required=(
                "Aucune"
                if service_user
                else
                "Identifier le compte de service Jira"
            ),
            message=(
                "Compte système utilisé par le processus Jira."
            )
        )
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if cpu is not None
                else "UNKNOWN"
            ),
            domain="INFRASTRUCTURE",
            check="CPU serveur",
            current_value=(
                f"{cpu} processeur(s) logique(s)"
                if cpu is not None
                else "Non renseigné"
            ),
            target_expected=(
                "Capacité CPU validée pour "
                "l'environnement cible"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Valider le dimensionnement CPU"
            ),
            message=(
                "Le nombre de processeurs logiques est "
                "collecté automatiquement ; le sizing "
                "reste à valider."
            )
        )
    )

    if total_ram_gb is not None:

        ram_current = (
            f"{total_ram_gb} GB total"
        )

        if free_ram_gb is not None:
            ram_current += (
                f" / {free_ram_gb} GB disponibles"
            )

    else:

        ram_current = "Non renseigné"

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if total_ram_gb is not None
                else "UNKNOWN"
            ),
            domain="INFRASTRUCTURE",
            check="Mémoire RAM serveur",
            current_value=ram_current,
            target_expected=(
                "Capacité RAM validée pour "
                "l'environnement cible"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Valider le dimensionnement RAM"
            ),
            message=(
                "La RAM physique est collectée automatiquement ; "
                "le sizing reste à valider."
            )
        )
    )

    if jira_home_disk_usable is not None:

        disk_current = (
            f"{jira_home_disk_usable} GB utilisables"
        )

        if jira_home_disk_total is not None:
            disk_current += (
                f" / {jira_home_disk_total} GB total"
            )

        if jira_home_disk_free is not None:
            disk_current += (
                f" / {jira_home_disk_free} GB libres"
            )

    else:

        disk_current = "Non renseigné"

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if jira_home_disk_usable is not None
                else "UNKNOWN"
            ),
            domain="INFRASTRUCTURE",
            check="Espace disque JIRA_HOME",
            current_value=disk_current,
            target_expected=(
                "Espace suffisant pour données, logs, "
                "index et opération d'upgrade"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Valider l'espace disque nécessaire "
                "pour l'upgrade"
            ),
            message=(
                "L'espace disque est collecté automatiquement ; "
                "la marge nécessaire dépend de la volumétrie."
            )
        )
    )

    if jira_install_disk_usable is not None:

        install_disk_current = (
            f"{jira_install_disk_usable} GB utilisables"
        )

        if jira_install_disk_total is not None:
            install_disk_current += (
                f" / {jira_install_disk_total} GB total"
            )

        results.append(
            readiness_finding(
                status="INFO",
                domain="INFRASTRUCTURE",
                check="Espace disque installation Jira",
                current_value=install_disk_current,
                target_expected=(
                    "Espace suffisant pour installer "
                    "la version Jira cible"
                ),
                assessment_method="MANUAL",
                action_required=(
                    "Valider l'espace nécessaire à "
                    "l'installation de Jira cible"
                ),
                message=(
                    "Espace disponible sur le volume hébergeant "
                    "le répertoire d'installation Jira."
                )
            )
        )

    # ========================================================
    # FILESYSTEM
    # ========================================================

    jira_home = first_value(
        baseline,
        "filesystem.jiraHome",
        "jira.jiraHome",
        "jira.home",
        "paths.jiraHome"
    )

    install_dir = first_value(
        baseline,
        "filesystem.jiraInstall",
        "jira.jiraInstall",
        "jira.installationDirectory",
        "filesystem.installationDirectory",
        "paths.installationDirectory"
    )

    jira_home_exists = first_value(
        baseline,
        "filesystem.jiraHomeDisk.exists"
    )

    jira_install_exists = first_value(
        baseline,
        "filesystem.jiraInstallDisk.exists"
    )

    results.append(
        readiness_finding(
            status=(
                "PASS"
                if jira_home and jira_home_exists is True
                else "INFO"
                if jira_home
                else "UNKNOWN"
            ),
            domain="FILESYSTEM",
            check="JIRA_HOME",
            current_value=display_value(
                jira_home
            ),
            target_expected=(
                "JIRA_HOME identifié et accessible"
            ),
            assessment_method="AUTO",
            action_required=(
                "Aucune"
                if jira_home and jira_home_exists is True
                else
                "Identifier et valider JIRA_HOME"
            ),
            message=(
                "Le chemin existe sur le serveur."
                if jira_home_exists is True
                else
                "Répertoire de données Jira détecté ; "
                "l'accessibilité reste à confirmer."
            )
        )
    )

    results.append(
        readiness_finding(
            status=(
                "PASS"
                if install_dir and jira_install_exists is True
                else "INFO"
                if install_dir
                else "UNKNOWN"
            ),
            domain="FILESYSTEM",
            check="Répertoire d'installation Jira",
            current_value=display_value(
                install_dir
            ),
            target_expected=(
                "Répertoire d'installation Jira "
                "identifié et accessible"
            ),
            assessment_method="AUTO",
            action_required=(
                "Aucune"
                if install_dir and jira_install_exists is True
                else
                "Identifier et valider le répertoire "
                "d'installation Jira"
            ),
            message=(
                "Le chemin existe sur le serveur."
                if jira_install_exists is True
                else
                "Répertoire contenant les binaires "
                "de l'installation Jira."
            )
        )
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="FILESYSTEM",
            check="Permissions des répertoires Jira",
            current_value=(
                f"Compte de service détecté : "
                f"{display_value(service_user)}"
            ),
            target_expected=(
                "Compte de service Jira disposant "
                "des droits nécessaires sur JIRA_HOME "
                "et le répertoire d'installation"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Valider les permissions filesystem"
            ),
            message=(
                "Le compte est détecté automatiquement, "
                "mais ses droits effectifs doivent être validés."
            )
        )
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="FILESYSTEM",
            check="Fichiers personnalisés / modifiés",
            current_value="À inventorier",
            target_expected=(
                "Toutes les modifications de fichiers "
                "identifiées avant upgrade"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Inventorier les fichiers Jira modifiés"
            ),
            message=(
                "Les personnalisations doivent pouvoir "
                "être réappliquées après upgrade."
            )
        )
    )

    # ========================================================
    # PROXY / TOMCAT
    # ========================================================

    reverse_proxy = first_value(
        baseline,
        "proxy.type",
        "architecture.reverseProxy",
        "proxy.name"
    )

    connector = first_value(
        baseline,
        "tomcat.connector",
        "proxy.connector",
        "tomcat.port"
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if reverse_proxy
                else "UNKNOWN"
            ),
            domain="PROXY",
            check="Reverse proxy",
            current_value=display_value(
                reverse_proxy
            ),
            target_expected=(
                "Reverse proxy identifié et "
                "configuration validée pour la cible"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Valider la configuration du proxy"
            ),
            message=(
                "IIS, Apache, Nginx ou autre "
                "selon l'architecture."
            )
        )
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if connector
                else "UNKNOWN"
            ),
            domain="PROXY",
            check="Connector / ports Tomcat",
            current_value=display_value(
                connector
            ),
            target_expected=(
                "Configuration Tomcat et ports "
                "identifiés et validés"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Valider connector et ports"
            ),
            message=(
                "Contrôle de la configuration "
                "réseau de Jira."
            )
        )
    )

    # ========================================================
    # AUTHENTICATION / LDAP
    # ========================================================

    auth_mode = first_value(
        baseline,
        "authentication.mode",
        "authentication.type"
    )

    sso = first_value(
        baseline,
        "authentication.sso",
        "authentication.saml"
    )

    ldap = first_value(
        baseline,
        "authentication.ldap",
        "ldap.configured"
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if auth_mode
                else "UNKNOWN"
            ),
            domain="AUTHENTICATION",
            check="Mode d'authentification",
            current_value=display_value(
                auth_mode
            ),
            target_expected=(
                "Modes d'authentification identifiés "
                "et scénarios de test définis"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Identifier et valider "
                "les mécanismes d'authentification"
            ),
            message=(
                "Authentification interne, "
                "SSO, LDAP ou autres."
            )
        )
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="AUTHENTICATION",
            check="SAML / SSO",
            current_value=display_value(
                sso,
                "À confirmer"
            ),
            target_expected=(
                f"SSO compatible avec {target_label} "
                "et test post-upgrade préparé"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Valider la compatibilité SSO "
                "et préparer le test de connexion"
            ),
            message=(
                "La compatibilité de l'application SSO "
                "sera également couverte dans APPLICATIONS."
            )
        )
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="LDAP",
            check="LDAP / Active Directory",
            current_value=display_value(
                ldap,
                "À confirmer"
            ),
            target_expected=(
                "Connexion annuaire validée et "
                "test post-upgrade préparé"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Valider l'annuaire externe"
            ),
            message=(
                "Contrôle des connexions utilisateurs "
                "et synchronisations d'annuaire."
            )
        )
    )

    # ========================================================
    # MAIL
    # ========================================================

    smtp = first_value(
        baseline,
        "mail.smtp",
        "mail.smtpHost",
        "smtp.host"
    )

    incoming_mail = first_value(
        baseline,
        "mail.incomingHandlers",
        "mail.incoming"
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="MAIL",
            check="SMTP du clone",
            current_value=display_value(
                smtp,
                "À confirmer"
            ),
            target_expected=(
                "SMTP production neutralisé ou remplacé "
                "par un SMTP de test sur le clone"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Neutraliser le SMTP production "
                "sur le clone"
            ),
            message=(
                "Évite l'envoi de notifications "
                "depuis l'environnement de test."
            )
        )
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="MAIL",
            check="Mail handlers entrants",
            current_value=display_value(
                incoming_mail,
                "À confirmer"
            ),
            target_expected=(
                "Flux e-mail entrants identifiés "
                "et neutralisés ou adaptés sur le clone"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Vérifier les mail handlers"
            ),
            message=(
                "Évite le traitement involontaire "
                "d'e-mails de production."
            )
        )
    )

    # ========================================================
    # AUTOMATION
    # ========================================================

    automation_rules = first_value(
        baseline,
        "automation.rulesCount",
        "automation.activeRules",
        "automation.rules"
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="AUTOMATION",
            check="Règles Automation",
            current_value=display_value(
                automation_rules,
                "À inventorier"
            ),
            target_expected=(
                "Règles identifiées et règles à risque "
                "neutralisées sur le clone"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Inventorier et neutraliser "
                "les automations nécessaires"
            ),
            message=(
                "Une automation peut déclencher des "
                "web requests ou autres actions externes."
            )
        )
    )

    # ========================================================
    # INTEGRATIONS
    # ========================================================

    webhooks = first_value(
        baseline,
        "integrations.webhooks",
        "integrations.webhooksCount"
    )

    application_links = first_value(
        baseline,
        "integrations.applicationLinks",
        "integrations.applicationLinksCount"
    )

    external_apis = first_value(
        baseline,
        "integrations.externalApis",
        "integrations.api"
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="INTEGRATIONS",
            check="Webhooks sortants",
            current_value=display_value(
                webhooks,
                "À inventorier"
            ),
            target_expected=(
                "Webhooks de production identifiés "
                "et neutralisés sur le clone"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Inventorier et neutraliser "
                "les webhooks concernés"
            ),
            message=(
                "Contrôle des flux sortants du clone."
            )
        )
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="INTEGRATIONS",
            check="Application Links",
            current_value=display_value(
                application_links,
                "À inventorier"
            ),
            target_expected=(
                "Application Links de production "
                "identifiés et adaptés ou neutralisés"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Vérifier les Application Links"
            ),
            message=(
                "Empêche le clone d'interagir "
                "involontairement avec la production."
            )
        )
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="INTEGRATIONS",
            check="Intégrations API externes",
            current_value=display_value(
                external_apis,
                "À inventorier"
            ),
            target_expected=(
                "Flux API sortants identifiés "
                "et maîtrisés sur le clone"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Identifier les intégrations API"
            ),
            message=(
                "Contrôle des appels sortants "
                "vers des systèmes externes."
            )
        )
    )

    # ========================================================
    # SCRIPTING
    # ========================================================

    scripts = first_value(
        baseline,
        "scripting.scripts",
        "scripting.scriptCount"
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="SCRIPTING",
            check="Scripts / listeners / jobs / endpoints",
            current_value=display_value(
                scripts,
                "À inventorier"
            ),
            target_expected=(
                "Scripts critiques identifiés "
                "et scénarios de validation préparés"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Identifier les scripts critiques "
                "et préparer les tests"
            ),
            message=(
                "Inclut notamment les éléments "
                "ScriptRunner/Groovy."
            )
        )
    )

    # ========================================================
    # INDEX
    # ========================================================

    index_state = first_value(
        baseline,
        "jira.indexState",
        "index.status",
        "index.state"
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if index_state
                else "NOT_ASSESSED"
            ),
            domain="INDEX",
            check="État de l'index Jira",
            current_value=display_value(
                index_state,
                "À contrôler"
            ),
            target_expected=(
                "Index sans anomalie bloquante "
                "avant la montée de version"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Contrôler l'état de l'index"
            ),
            message=(
                "Le contrôle permet de partir d'une "
                "instance source saine."
            )
        )
    )

    # ========================================================
    # DATA
    # ========================================================

    attachments = first_value(
        baseline,
        "data.attachments",
        "jira.attachments"
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="DATA",
            check="Stockage des pièces jointes",
            current_value=display_value(
                attachments,
                "À contrôler"
            ),
            target_expected=(
                "Stockage des pièces jointes "
                "accessible et cohérent"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Valider le stockage des pièces jointes"
            ),
            message=(
                "Contrôle du stockage des données Jira."
            )
        )
    )

    # ========================================================
    # BACKUP
    # ========================================================

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="BACKUP",
            check="Sauvegarde base de données",
            current_value="Non renseigné",
            target_expected=(
                "Sauvegarde complète de la base réalisée "
                "et restauration possible"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Valider avec l'infrastructure "
                "la sauvegarde DB"
            ),
            message=(
                "Prérequis du plan de retour arrière."
            )
        )
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="BACKUP",
            check="Sauvegarde JIRA_HOME",
            current_value="Non renseigné",
            target_expected=(
                "Sauvegarde complète de JIRA_HOME "
                "réalisée"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Valider avec l'infrastructure "
                "la sauvegarde JIRA_HOME"
            ),
            message=(
                "Prérequis du plan de retour arrière."
            )
        )
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="BACKUP",
            check="Sauvegarde répertoire d'installation",
            current_value="Non renseigné",
            target_expected=(
                "Répertoire d'installation sauvegardé "
                "ou procédure de restauration disponible"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Valider la stratégie de sauvegarde "
                "des binaires/configurations"
            ),
            message=(
                "Permet notamment de conserver les "
                "configurations spécifiques."
            )
        )
    )

    # ========================================================
    # ROLLBACK
    # ========================================================

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="ROLLBACK",
            check="Procédure de retour arrière",
            current_value="Non renseigné",
            target_expected=(
                "Procédure de rollback documentée "
                "et validée avec l'infrastructure"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Définir et valider le rollback"
            ),
            message=(
                "Le retour arrière doit permettre "
                "de restaurer l'état pré-upgrade."
            )
        )
    )

    # ========================================================
    # CLONE
    # ========================================================

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="CLONE",
            check="Clone de production disponible",
            current_value="À confirmer",
            target_expected=(
                "Clone représentatif de la production "
                "disponible pour la répétition"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Valider la disponibilité du clone"
            ),
            message=(
                "L'upgrade doit être répété sur "
                "un environnement de test représentatif."
            )
        )
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="CLONE",
            check="Isolation du clone",
            current_value="À confirmer",
            target_expected=(
                "Clone isolé des flux de production"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Valider la neutralisation "
                "des flux de production"
            ),
            message=(
                "Inclut notamment mails, automations, "
                "webhooks et intégrations sortantes."
            )
        )
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="CLONE",
            check="Base URL distincte de la production",
            current_value=display_value(
                base_url
            ),
            target_expected=(
                "Base URL du clone différente "
                "de la production"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Comparer la Base URL du clone "
                "à celle de la production"
            ),
            message=(
                "La Base URL détectée seule ne permet "
                "pas de confirmer l'isolation."
            )
        )
    )

    # ========================================================
    # TESTING
    # ========================================================

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="TESTING",
            check="Smoke tests pré-upgrade",
            current_value="À préparer",
            target_expected=(
                "Scénarios de référence exécutés "
                "sur la source avant upgrade"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Définir et exécuter les smoke tests PRE"
            ),
            message=(
                "Ces résultats serviront de référence "
                "pour les tests POST."
            )
        )
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="TESTING",
            check="Plan de tests post-upgrade",
            current_value="À préparer",
            target_expected=(
                "Plan de validation Jira, apps, SSO, "
                "workflows et intégrations défini"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Préparer le plan de tests POST"
            ),
            message=(
                "Les scénarios doivent être définis "
                "avant de lancer l'upgrade."
            )
        )
    )

    # ========================================================
    # ACCESS
    # ========================================================

    manual_access_checks = [
        (
            "Accès serveur Jira",
            "Accès serveur disponible pour l'équipe d'upgrade",
            "Confirmer les accès serveur"
        ),
        (
            "Accès base de données",
            "Accès DB ou support DBA disponible",
            "Confirmer les accès DB / DBA"
        ),
        (
            "Accès administrateur Jira",
            "Compte administrateur Jira disponible",
            "Confirmer l'accès administrateur Jira"
        )
    ]

    for (
        check,
        expected,
        action
    ) in manual_access_checks:

        results.append(
            readiness_finding(
                status="NOT_ASSESSED",
                domain="ACCESS",
                check=check,
                current_value="À confirmer",
                target_expected=expected,
                assessment_method="MANUAL",
                action_required=action,
                message=(
                    "Prérequis opérationnel "
                    "de la montée de version."
                )
            )
        )

    # ========================================================
    # LOGGING
    # ========================================================

    logs_path = first_value(
        baseline,
        "logging.jiraLog",
        "logging.logPath",
        "jira.logPath"
    )

    results.append(
        readiness_finding(
            status=(
                "INFO"
                if logs_path
                else "NOT_ASSESSED"
            ),
            domain="LOGGING",
            check="Accès aux logs Jira",
            current_value=display_value(
                logs_path,
                "À confirmer"
            ),
            target_expected=(
                "Logs Jira accessibles pendant "
                "et après l'upgrade"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Valider l'accès aux logs"
            ),
            message=(
                "Indispensable au diagnostic "
                "en cas de problème."
            )
        )
    )

    # ========================================================
    # LICENSING
    # ========================================================

    licence = first_value(
        baseline,
        "jira.license",
        "licensing.jira",
        "licence.jira"
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="LICENSING",
            check="Licence Jira cible",
            current_value=display_value(
                licence,
                "À confirmer"
            ),
            target_expected=(
                f"Licence permettant le démarrage "
                f"et la validation de {target_label}"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Vérifier la licence Jira "
                "pour l'environnement cible"
            ),
            message=(
                "Une licence valide est nécessaire "
                "pour une validation complète."
            )
        )
    )

    # ========================================================
    # MONITORING
    # ========================================================

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="MONITORING",
            check="Surveillance pendant l'upgrade",
            current_value="À préparer",
            target_expected=(
                "Logs et ressources système surveillés "
                "pendant l'opération"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Définir les éléments à surveiller"
            ),
            message=(
                "Facilite la détection et le diagnostic "
                "des anomalies."
            )
        )
    )

    # ========================================================
    # GOVERNANCE
    # ========================================================

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="GOVERNANCE",
            check="Critères Go / No-Go",
            current_value="À définir",
            target_expected=(
                "Critères de décision Go / No-Go "
                "définis avant la MEP"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Définir les critères de décision"
            ),
            message=(
                "Permet une décision objective "
                "après la répétition et les tests."
            )
        )
    )

    results.append(
        readiness_finding(
            status="NOT_ASSESSED",
            domain="GOVERNANCE",
            check="Intervenants upgrade identifiés",
            current_value="À confirmer",
            target_expected=(
                "Administrateurs, infrastructure, DBA "
                "et responsables de décision identifiés"
            ),
            assessment_method="MANUAL",
            action_required=(
                "Confirmer les rôles et disponibilités"
            ),
            message=(
                "Les acteurs nécessaires doivent être "
                "disponibles pendant la fenêtre d'upgrade."
            )
        )
    )

    # ========================================================
    # APPLICATIONS DYNAMIQUES
    #
    # Les applications ne sont jamais codées en dur.
    #
    # On combine :
    # - thirdPartyApps
    # - importantAtlassianApps
    #
    # Puis on supprime les doublons éventuels.
    # ========================================================

    all_apps = []
    seen_apps = set()

    for app_list in (
        third_party_apps,
        important_apps
    ):

        for app in app_list:

            if not isinstance(
                app,
                dict
            ):
                continue

            name = (
                app.get("name")
                or app.get("key")
                or "Application inconnue"
            )

            version = (
                app.get("version")
                or "Non déterminée"
            )

            unique_key = (
                str(name).strip().lower(),
                str(version).strip().lower()
            )

            if unique_key in seen_apps:
                continue

            seen_apps.add(
                unique_key
            )

            all_apps.append(
                {
                    "name": name,
                    "version": version
                }
            )

    if not all_apps:

        results.append(
            readiness_finding(
                status="INFO",
                domain="APPLICATIONS",
                check="Applications détectées",
                current_value="0",
                target_expected=(
                    "Inventaire des applications "
                    "de l'instance disponible"
                ),
                assessment_method="AUTO",
                action_required="Aucune",
                message=(
                    "Aucune application n'a été "
                    "détectée dans la baseline."
                )
            )
        )

    for app in all_apps:

        name = app[
            "name"
        ]

        version = app[
            "version"
        ]

        app_status = (
            "UNKNOWN"
            if version == "Non déterminée"
            else "NOT_ASSESSED"
        )

        results.append(
            readiness_finding(
                status=app_status,
                domain="APPLICATIONS",
                check=str(name),
                current_value=str(version),
                target_expected=(
                    f"Version {name} compatible "
                    f"avec {target_label}"
                ),
                selected_value="",
                assessment_method="EXTERNAL",
                action_required=(
                    f"Vérifier la compatibilité de "
                    f"{name} et retenir la version "
                    f"à utiliser"
                ),
                message=(
                    "Application ajoutée automatiquement "
                    "à partir de l'inventaire de l'instance."
                )
            )
        )

    # ========================================================
    # FIN
    # ========================================================
