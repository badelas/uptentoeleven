def finding(
    severity: str,
    domain: str,
    message: str
) -> dict:

    return {
        "severity": severity,
        "domain": domain,
        "message": message
    }


def analyze_baseline(
    baseline: dict
) -> list[dict]:

    """
    Analyse uniquement l'état de la source Jira.

    Aucun contrôle de compatibilité avec la cible Jira
    n'est effectué ici.
    """

    findings = []

    jira = baseline.get("jira", {})
    java = baseline.get("java", {})
    database = baseline.get("database", {})
    disk = baseline.get("disk", {})
    architecture = baseline.get("architecture", {})
    jira_configuration = baseline.get(
        "jiraConfiguration",
        {}
    )

    # ========================================================
    # JIRA VERSION
    # ========================================================

    jira_version = jira.get("version")

    if jira_version:
        findings.append(
            finding(
                "INFO",
                "JIRA",
                f"Version Jira source détectée : {jira_version}"
            )
        )
    else:
        findings.append(
            finding(
                "WARNING",
                "JIRA",
                "Version Jira source non détectée."
            )
        )

    # ========================================================
    # BUILD JIRA / DB
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

    if builds_match is True:

        findings.append(
            finding(
                "PASS",
                "JIRA",
                (
                    "Build application et build DB "
                    f"sont cohérents ({application_build})."
                )
            )
        )

    elif builds_match is False:

        findings.append(
            finding(
                "FAIL",
                "JIRA",
                (
                    "Build application et build DB "
                    "sont différents : "
                    f"application={application_build}, "
                    f"database={database_build}."
                )
            )
        )

    else:

        findings.append(
            finding(
                "WARNING",
                "JIRA",
                (
                    "Impossible de déterminer la cohérence "
                    "entre le build Jira et le build DB."
                )
            )
        )

    # ========================================================
    # ARCHITECTURE
    # ========================================================

    clustered = architecture.get("clustered")

    if clustered is True:

        findings.append(
            finding(
                "INFO",
                "ARCHITECTURE",
                "Instance Jira configurée en cluster."
            )
        )

    elif clustered is False:

        findings.append(
            finding(
                "INFO",
                "ARCHITECTURE",
                "Instance Jira configurée en single node."
            )
        )

    else:

        findings.append(
            finding(
                "WARNING",
                "ARCHITECTURE",
                "Type d'architecture Jira non déterminé."
            )
        )

    # ========================================================
    # JAVA
    # ========================================================

    java_version = java.get("version")
    java_vendor = java.get("vendor")

    if java_version:

        message = (
            f"Version Java source détectée : "
            f"{java_version}"
        )

        if java_vendor:
            message += f" ({java_vendor})"

        findings.append(
            finding(
                "INFO",
                "JAVA",
                message
            )
        )

    else:

        findings.append(
            finding(
                "WARNING",
                "JAVA",
                "Version Java non détectée."
            )
        )

    # ========================================================
    # JVM MEMORY
    # ========================================================

    xms = java.get("xms")
    xmx = java.get("xmx")

    if xms or xmx:

        findings.append(
            finding(
                "INFO",
                "JAVA",
                (
                    "Configuration mémoire JVM détectée : "
                    f"Xms={xms or 'N/A'}, "
                    f"Xmx={xmx or 'N/A'}."
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

        findings.append(
            finding(
                "WARNING",
                "JIRA",
                "Base URL Jira non détectée."
            )
        )

    elif "localhost" in base_url.lower():

        findings.append(
            finding(
                "WARNING",
                "JIRA",
                (
                    "La Base URL contient localhost : "
                    f"{base_url}. "
                    "À vérifier si l'instance est utilisée "
                    "via un reverse proxy ou depuis le réseau."
                )
            )
        )

    else:

        findings.append(
            finding(
                "INFO",
                "JIRA",
                f"Base URL détectée : {base_url}"
            )
        )

    # ========================================================
    # DATABASE
    # ========================================================

    database_type = database.get("type")
    database_schema = database.get("schema")
    database_driver = database.get("jdbcDriver")

    if database_type:

        message = (
            f"Base de données détectée : "
            f"{database_type}"
        )

        if database_schema:
            message += f", schema={database_schema}"

        if database_driver:
            message += f", driver={database_driver}"

        findings.append(
            finding(
                "INFO",
                "DATABASE",
                message
            )
        )

    else:

        findings.append(
            finding(
                "WARNING",
                "DATABASE",
                "Type de base de données non détecté."
            )
        )

    # ========================================================
    # DISK
    # ========================================================

    total_gb = disk.get("totalGB")

    free_gb = (
        disk.get("usableGB")
        or disk.get("freeGB")
    )

    if free_gb is not None:

        if total_gb is not None:

            findings.append(
                finding(
                    "INFO",
                    "DISK",
                    (
                        f"Espace disque disponible : "
                        f"{free_gb} GB sur {total_gb} GB."
                    )
                )
            )

        else:

            findings.append(
                finding(
                    "INFO",
                    "DISK",
                    (
                        f"Espace disque disponible : "
                        f"{free_gb} GB."
                    )
                )
            )

    else:

        findings.append(
            finding(
                "WARNING",
                "DISK",
                (
                    "Impossible de déterminer "
                    "l'espace disque disponible."
                )
            )
        )

    # ========================================================
    # CONFIGURATION JIRA
    # ========================================================

    projects = jira_configuration.get("projects")
    custom_fields = jira_configuration.get(
        "customFields"
    )
    issue_types = jira_configuration.get(
        "issueTypes"
    )
    statuses = jira_configuration.get(
        "statuses"
    )
    workflows = jira_configuration.get(
        "workflows"
    )

    findings.append(
        finding(
            "INFO",
            "JIRA_CONFIGURATION",
            (
                "Configuration Jira détectée : "
                f"{projects if projects is not None else 'N/A'} projets, "
                f"{custom_fields if custom_fields is not None else 'N/A'} custom fields, "
                f"{issue_types if issue_types is not None else 'N/A'} issue types, "
                f"{statuses if statuses is not None else 'N/A'} statuses, "
                f"{workflows if workflows is not None else 'N/A'} workflows."
            )
        )
    )

    # ========================================================
    # APPLICATIONS TIERCES
    # ========================================================

    apps = baseline.get(
        "thirdPartyApps",
        []
    )

    findings.append(
        finding(
            "INFO",
            "APPLICATIONS",
            (
                f"{len(apps)} application(s) "
                "tierce(s) détectée(s)."
            )
        )
    )

    for app in apps:

        app_name = app.get(
            "name",
            "Application inconnue"
        )

        app_version = app.get(
            "version",
            "N/A"
        )

        app_enabled = app.get(
            "enabled"
        )

        if app_enabled is True:
            state = "ACTIVE"

        elif app_enabled is False:
            state = "DESACTIVEE"

        else:
            state = "ETAT INCONNU"

        findings.append(
            finding(
                "INFO",
                "APPLICATIONS",
                (
                    f"{app_name} "
                    f"- version {app_version} "
                    f"- {state}."
                )
            )
        )

    # ========================================================
    # APPLICATIONS ATLASSIAN IMPORTANTES
    # ========================================================

    important_apps = baseline.get(
        "importantAtlassianApps",
        []
    )

    for app in important_apps:

        app_name = app.get(
            "name",
            "Application Atlassian"
        )

        app_version = app.get(
            "version",
            "N/A"
        )

        app_enabled = app.get(
            "enabled"
        )

        if app_enabled is True:
            state = "ACTIVE"

        elif app_enabled is False:
            state = "DESACTIVEE"

        else:
            state = "ETAT INCONNU"

        findings.append(
            finding(
                "INFO",
                "APPLICATIONS",
                (
                    f"{app_name} "
                    f"- version {app_version} "
                    f"- {state}."
                )
            )
        )

    # ========================================================
    # IMPORTANT :
    # La fonction doit toujours retourner la liste
    # ========================================================

    return findings