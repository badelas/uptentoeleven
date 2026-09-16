def readiness_finding(
    status: str,
    domain: str,
    check: str,
    current_value,
    target_value,
    message: str
) -> dict:

    return {
        "status": status,
        "domain": domain,
        "check": check,
        "current_value": current_value,
        "target_value": target_value,
        "message": message
    }


def get_java_major(version: str):

    try:
        return int(
            version.split(".")[0]
        )

    except (
        AttributeError,
        ValueError,
        IndexError
    ):
        return None


def analyze_readiness(
    baseline: dict,
    settings
) -> list[dict]:

    """
    Analyse la readiness de l'instance source
    par rapport à la cible configurée.

    La version source est toujours récupérée
    automatiquement depuis la baseline.

    La cible provient du fichier .env :

    TARGET_JIRA_FAMILY=11.3
    TARGET_JIRA_VERSION=

    Tant que TARGET_JIRA_VERSION est vide,
    les contrôles nécessitant le patch exact
    restent NOT_ASSESSED.
    """

    results = []

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

    apps = baseline.get(
        "thirdPartyApps",
        []
    )

    important_apps = baseline.get(
        "importantAtlassianApps",
        []
    )

    # ========================================================
    # SOURCE / TARGET
    # ========================================================

    source_version = jira.get(
        "version"
    )

    target_family = (
        settings.target_jira_family
        or None
    )

    target_version = (
        settings.target_jira_version
        or None
    )

    results.append(
        readiness_finding(
            "INFO",
            "UPGRADE",
            "Version source Jira",
            source_version,
            target_family,
            (
                f"Upgrade analysé depuis Jira "
                f"{source_version or 'N/A'} vers "
                f"Jira {target_family or 'cible non définie'}."
            )
        )
    )

    # ========================================================
    # TARGET FAMILY
    # ========================================================

    if target_family:

        results.append(
            readiness_finding(
                "PASS",
                "TARGET",
                "Famille cible définie",
                source_version,
                target_family,
                (
                    f"La famille cible Jira "
                    f"{target_family} est définie."
                )
            )
        )

    else:

        results.append(
            readiness_finding(
                "FAIL",
                "TARGET",
                "Famille cible définie",
                source_version,
                None,
                (
                    "TARGET_JIRA_FAMILY "
                    "n'est pas configuré."
                )
            )
        )

    # ========================================================
    # TARGET EXACT VERSION
    # ========================================================

    if target_version:

        results.append(
            readiness_finding(
                "PASS",
                "TARGET",
                "Version cible exacte",
                source_version,
                target_version,
                (
                    f"Version cible exacte définie : "
                    f"{target_version}."
                )
            )
        )

    else:

        results.append(
            readiness_finding(
                "NOT_ASSESSED",
                "TARGET",
                "Version cible exacte",
                source_version,
                target_family,
                (
                    "La famille cible est connue, "
                    "mais le patch exact n'est pas "
                    "encore défini."
                )
            )
        )

    # ========================================================
    # BUILD JIRA / DATABASE
    # ========================================================

    builds_match = jira.get(
        "buildsMatch"
    )

    application_build = jira.get(
        "applicationBuildNumber"
    )

    database_build = jira.get(
        "databaseBuildNumber"
    )

    if builds_match is True:

        results.append(
            readiness_finding(
                "PASS",
                "JIRA",
                "Cohérence build Jira / DB",
                application_build,
                application_build,
                (
                    "Le build applicatif Jira et "
                    "le build de la base sont cohérents."
                )
            )
        )

    elif builds_match is False:

        results.append(
            readiness_finding(
                "FAIL",
                "JIRA",
                "Cohérence build Jira / DB",
                (
                    f"Application={application_build}, "
                    f"DB={database_build}"
                ),
                "Valeurs identiques",
                (
                    "Le build applicatif et le build "
                    "de la base sont différents."
                )
            )
        )

    else:

        results.append(
            readiness_finding(
                "NOT_ASSESSED",
                "JIRA",
                "Cohérence build Jira / DB",
                "Inconnu",
                "Valeurs identiques",
                (
                    "Impossible de déterminer "
                    "la cohérence des builds."
                )
            )
        )

    # ========================================================
    # JAVA
    #
    # Pour une cible Jira 11.x, le runtime cible
    # devra utiliser Java 21.
    #
    # Ici on ne dit pas que la source Jira 10 est
    # mal configurée : on indique l'action requise
    # pour l'environnement cible.
    # ========================================================

    java_version = java.get(
        "version"
    )

    java_major = get_java_major(
        java_version
    )

    if (
        target_family
        and target_family.startswith("11")
    ):

        if java_major is None:

            results.append(
                readiness_finding(
                    "NOT_ASSESSED",
                    "JAVA",
                    "Runtime Java cible",
                    java_version,
                    "Java 21",
                    (
                        "La version Java source "
                        "n'a pas pu être déterminée."
                    )
                )
            )

        elif java_major == 21:

            results.append(
                readiness_finding(
                    "PASS",
                    "JAVA",
                    "Runtime Java cible",
                    java_version,
                    "Java 21",
                    (
                        "Java 21 est déjà détecté."
                    )
                )
            )

        else:

            results.append(
                readiness_finding(
                    "WARNING",
                    "JAVA",
                    "Runtime Java cible",
                    java_version,
                    "Java 21",
                    (
                        f"Java {java_version} est utilisé "
                        "sur la source. "
                        "Prévoir Java 21 pour Jira 11."
                    )
                )
            )

    # ========================================================
    # BASE URL
    # ========================================================

    base_url = jira.get(
        "baseUrl",
        ""
    )

    if not base_url:

        results.append(
            readiness_finding(
                "WARNING",
                "JIRA",
                "Base URL",
                None,
                "URL publique valide",
                (
                    "La Base URL Jira "
                    "n'a pas été détectée."
                )
            )
        )

    elif "localhost" in base_url.lower():

        results.append(
            readiness_finding(
                "WARNING",
                "JIRA",
                "Base URL",
                base_url,
                "URL publique Jira",
                (
                    "La Base URL contient localhost. "
                    "Elle doit être contrôlée avant "
                    "l'upgrade en environnement réel."
                )
            )
        )

    else:

        results.append(
            readiness_finding(
                "PASS",
                "JIRA",
                "Base URL",
                base_url,
                base_url,
                (
                    "Une Base URL non locale "
                    "est configurée."
                )
            )
        )

    # ========================================================
    # ARCHITECTURE
    # ========================================================

    clustered = architecture.get(
        "clustered"
    )

    if clustered is False:

        results.append(
            readiness_finding(
                "INFO",
                "ARCHITECTURE",
                "Topologie Jira",
                "Single node",
                "À conserver / valider",
                (
                    "Instance source détectée "
                    "en single node."
                )
            )
        )

    elif clustered is True:

        results.append(
            readiness_finding(
                "INFO",
                "ARCHITECTURE",
                "Topologie Jira",
                "Cluster",
                "À conserver / valider",
                (
                    "Instance source détectée "
                    "en cluster."
                )
            )
        )

    # ========================================================
    # DATABASE
    #
    # On connaît actuellement le moteur DB,
    # mais pas forcément sa version exacte.
    #
    # La compatibilité précise doit être contrôlée
    # avec la Supported Platforms de la cible.
    # ========================================================

    database_type = database.get(
        "type"
    )

    results.append(
        readiness_finding(
            "NOT_ASSESSED",
            "DATABASE",
            "Compatibilité DB avec la cible",
            database_type or "Non détectée",
            (
                target_version
                or target_family
                or "Cible non définie"
            ),
            (
                "La compatibilité de la base doit être "
                "vérifiée avec la version Jira cible "
                "et la version exacte du moteur DB."
            )
        )
    )

    # ========================================================
    # THIRD-PARTY APPS
    # ========================================================

    if not apps:

        results.append(
            readiness_finding(
                "INFO",
                "APPLICATIONS",
                "Applications tierces",
                "0 application",
                target_family,
                (
                    "Aucune application tierce "
                    "n'a été détectée."
                )
            )
        )

    for app in apps:

        name = app.get(
            "name",
            "Application inconnue"
        )

        version = app.get(
            "version",
            "N/A"
        )

        results.append(
            readiness_finding(
                "NOT_ASSESSED",
                "APPLICATIONS",
                f"Compatibilité - {name}",
                version,
                (
                    target_version
                    or target_family
                    or "Cible non définie"
                ),
                (
                    f"La compatibilité de {name} "
                    f"version {version} doit être "
                    "vérifiée dans la matrice "
                    "de compatibilité."
                )
            )
        )

    # ========================================================
    # IMPORTANT ATLASSIAN APPS
    # ========================================================

    for app in important_apps:

        name = app.get(
            "name",
            "Application Atlassian"
        )

        version = app.get(
            "version",
            "N/A"
        )

        results.append(
            readiness_finding(
                "NOT_ASSESSED",
                "APPLICATIONS",
                f"Compatibilité - {name}",
                version,
                (
                    target_version
                    or target_family
                    or "Cible non définie"
                ),
                (
                    f"La version {version} de "
                    f"{name} doit être validée "
                    "pour la cible."
                )
            )
        )

    return results