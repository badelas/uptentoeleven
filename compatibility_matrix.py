# ============================================================
# JIRA COMPATIBILITY MATRIX
#
# Source de référence interne pour les plateformes supportées
# par la version Jira Data Center cible.
#
# IMPORTANT :
# Les Supported Platforms Atlassian sont publiées au niveau
# de la branche fonctionnelle (ex : Jira 11.3), pas pour
# chaque bugfix release (ex : 11.3.11).
#
# Jira 11.3.11 utilise donc la matrice Jira 11.3.
# ============================================================


# ============================================================
# SOURCES OFFICIELLES
# ============================================================

ATLASSIAN_SUPPORTED_PLATFORMS_URL = (
    "https://confluence.atlassian.com/"
    "adminjiraserver/supported-platforms-938846830.html"
)

ATLASSIAN_UPGRADE_MATRIX_URL = (
    "https://confluence.atlassian.com/"
    "adminjiraserver/upgrade-matrix-966063322.html"
)


# ============================================================
# MATRICES
#
# Une nouvelle entrée pourra être ajoutée plus tard pour :
#
# 11.4
# 11.5
# etc.
# ============================================================

SUPPORTED_PLATFORMS = {

    "11.3": [

        # ====================================================
        # JAVA
        # ====================================================

        {
            "category": "JAVA",
            "technology": "Oracle JDK/JRE",
            "version": "21",
            "status": "SUPPORTED",
            "notes": (
                "Jira 11.3 fonctionne uniquement "
                "avec Java 21."
            ),
            "source": ATLASSIAN_SUPPORTED_PLATFORMS_URL
        },

        {
            "category": "JAVA",
            "technology": "Eclipse Temurin / Adoptium",
            "version": "21",
            "status": "SUPPORTED",
            "notes": (
                "Java 21 runtime level. "
                "Distribution utilisée par Atlassian "
                "pour reproduire les problèmes."
            ),
            "source": ATLASSIAN_SUPPORTED_PLATFORMS_URL
        },

        {
            "category": "JAVA",
            "technology": "Java",
            "version": "17",
            "status": "UNSUPPORTED",
            "notes": (
                "Le support de Java 17 est supprimé "
                "avec Jira 11."
            ),
            "source": ATLASSIAN_UPGRADE_MATRIX_URL
        },

        {
            "category": "JAVA",
            "technology": "Java",
            "version": "11",
            "status": "UNSUPPORTED",
            "notes": (
                "Jira 11.3 ne peut pas fonctionner "
                "sur Java 11."
            ),
            "source": ATLASSIAN_SUPPORTED_PLATFORMS_URL
        },

        {
            "category": "JAVA",
            "technology": "Java",
            "version": "8",
            "status": "UNSUPPORTED",
            "notes": (
                "Jira 11.3 ne peut pas fonctionner "
                "sur Java 8."
            ),
            "source": ATLASSIAN_SUPPORTED_PLATFORMS_URL
        },


        # ====================================================
        # POSTGRESQL
        # ====================================================

        {
            "category": "DATABASE",
            "technology": "PostgreSQL",
            "version": "17",
            "status": "SUPPORTED",
            "notes": (
                "Version PostgreSQL supportée "
                "par Jira 11.3."
            ),
            "source": ATLASSIAN_SUPPORTED_PLATFORMS_URL
        },

        {
            "category": "DATABASE",
            "technology": "PostgreSQL",
            "version": "16",
            "status": "DEPRECATED",
            "notes": (
                "Encore utilisable avec Jira 11.3, "
                "mais support déprécié."
            ),
            "source": ATLASSIAN_UPGRADE_MATRIX_URL
        },

        {
            "category": "DATABASE",
            "technology": "PostgreSQL",
            "version": "15",
            "status": "UNSUPPORTED",
            "notes": (
                "Support supprimé avec Jira 11."
            ),
            "source": ATLASSIAN_UPGRADE_MATRIX_URL
        },

        {
            "category": "DATABASE",
            "technology": "PostgreSQL",
            "version": "14",
            "status": "UNSUPPORTED",
            "notes": (
                "Support supprimé avec Jira 11."
            ),
            "source": ATLASSIAN_UPGRADE_MATRIX_URL
        },

        {
            "category": "DATABASE",
            "technology": "PostgreSQL",
            "version": "13",
            "status": "UNSUPPORTED",
            "notes": (
                "Support supprimé avec Jira 11."
            ),
            "source": ATLASSIAN_UPGRADE_MATRIX_URL
        },

        {
            "category": "DATABASE",
            "technology": "PostgreSQL",
            "version": "12",
            "status": "UNSUPPORTED",
            "notes": (
                "Support supprimé avec Jira 11."
            ),
            "source": ATLASSIAN_UPGRADE_MATRIX_URL
        },


        # ====================================================
        # POSTGRESQL JDBC
        # ====================================================

        {
            "category": "JDBC",
            "technology": "PostgreSQL JDBC Driver",
            "version": "42.7.3",
            "status": "TESTED",
            "notes": (
                "Driver PostgreSQL utilisé et testé "
                "par Atlassian avec Jira 11.3. "
                "Un driver plus récent adapté à la "
                "version PostgreSQL peut être utilisé, "
                "mais n'est pas nécessairement testé "
                "avec Jira."
            ),
            "source": ATLASSIAN_SUPPORTED_PLATFORMS_URL
        },


        # ====================================================
        # MYSQL
        # ====================================================

        {
            "category": "DATABASE",
            "technology": "MySQL",
            "version": "8.4",
            "status": "SUPPORTED",
            "notes": (
                "Version MySQL supportée "
                "par Jira 11.3."
            ),
            "source": ATLASSIAN_SUPPORTED_PLATFORMS_URL
        },

        {
            "category": "DATABASE",
            "technology": "MySQL",
            "version": "8.0",
            "status": "UNSUPPORTED",
            "notes": (
                "Support supprimé avec Jira 11."
            ),
            "source": ATLASSIAN_UPGRADE_MATRIX_URL
        },

        {
            "category": "DATABASE",
            "technology": "MariaDB",
            "version": "Toutes",
            "status": "UNSUPPORTED",
            "notes": (
                "MariaDB n'est pas supporté "
                "pour Jira 11.3."
            ),
            "source": ATLASSIAN_SUPPORTED_PLATFORMS_URL
        },

        {
            "category": "DATABASE",
            "technology": "PerconaDB",
            "version": "Toutes",
            "status": "UNSUPPORTED",
            "notes": (
                "PerconaDB n'est pas supporté "
                "pour Jira 11.3."
            ),
            "source": ATLASSIAN_SUPPORTED_PLATFORMS_URL
        },


        # ====================================================
        # ORACLE
        # ====================================================

        {
            "category": "DATABASE",
            "technology": "Oracle Database",
            "version": "23ai",
            "status": "SUPPORTED",
            "notes": (
                "Version Oracle supportée "
                "par Jira 11.3."
            ),
            "source": ATLASSIAN_SUPPORTED_PLATFORMS_URL
        },

        {
            "category": "DATABASE",
            "technology": "Oracle Database",
            "version": "19c",
            "status": "DEPRECATED",
            "notes": (
                "Encore utilisable avec Jira 11.3, "
                "mais support déprécié."
            ),
            "source": ATLASSIAN_SUPPORTED_PLATFORMS_URL
        },


        # ====================================================
        # SQL SERVER
        # ====================================================

        {
            "category": "DATABASE",
            "technology": "Microsoft SQL Server",
            "version": "2022",
            "status": "SUPPORTED",
            "notes": (
                "Version SQL Server supportée "
                "par Jira 11.3."
            ),
            "source": ATLASSIAN_SUPPORTED_PLATFORMS_URL
        },

        {
            "category": "DATABASE",
            "technology": "Microsoft SQL Server",
            "version": "2019",
            "status": "DEPRECATED",
            "notes": (
                "Encore utilisable avec Jira 11.3, "
                "mais support déprécié."
            ),
            "source": ATLASSIAN_SUPPORTED_PLATFORMS_URL
        },

        {
            "category": "DATABASE",
            "technology": "Microsoft SQL Server",
            "version": "2017",
            "status": "UNSUPPORTED",
            "notes": (
                "Support supprimé avec Jira 11."
            ),
            "source": ATLASSIAN_UPGRADE_MATRIX_URL
        },


        # ====================================================
        # OPERATING SYSTEMS
        #
        # Atlassian documente les familles d'OS supportées.
        # On n'invente donc pas de version Windows précise.
        # ====================================================

        {
            "category": "OS",
            "technology": "Microsoft Windows",
            "version": "Famille Windows",
            "status": "SUPPORTED",
            "notes": (
                "Jira est supporté sur Microsoft Windows "
                "sous réserve du respect des autres "
                "prérequis de plateforme."
            ),
            "source": ATLASSIAN_SUPPORTED_PLATFORMS_URL
        },

        {
            "category": "OS",
            "technology": "Linux",
            "version": "Famille Linux",
            "status": "SUPPORTED",
            "notes": (
                "Jira est supporté sur Linux. "
                "Atlassian effectue notamment ses tests "
                "sur Ubuntu."
            ),
            "source": ATLASSIAN_SUPPORTED_PLATFORMS_URL
        },


        # ====================================================
        # CLOUD INFRASTRUCTURE
        # ====================================================

        {
            "category": "INFRASTRUCTURE",
            "technology": "Microsoft Azure",
            "version": "N/A",
            "status": "SUPPORTED",
            "notes": (
                "Déploiement possible si les composants "
                "utilisés sont également supportés "
                "par Jira et Azure."
            ),
            "source": ATLASSIAN_SUPPORTED_PLATFORMS_URL
        },

        {
            "category": "INFRASTRUCTURE",
            "technology": "Amazon Web Services",
            "version": "N/A",
            "status": "SUPPORTED",
            "notes": (
                "Infrastructure cloud supportée sous "
                "réserve des composants Jira utilisés."
            ),
            "source": ATLASSIAN_SUPPORTED_PLATFORMS_URL
        }
    ]
}


# ============================================================
# UTILITAIRES
# ============================================================

def get_target_family(
    target_version: str | None
) -> str | None:
    """
    Convertit une version Jira exacte en famille.

    Exemple :
        11.3.11 -> 11.3
    """

    if not target_version:
        return None

    parts = str(
        target_version
    ).strip().split(".")

    if len(parts) < 2:
        return None

    return (
        f"{parts[0]}.{parts[1]}"
    )


def get_supported_platforms(
    target_version: str | None
) -> list[dict]:
    """
    Retourne la matrice de plateformes correspondant
    à la version Jira cible.

    Exemple :
        11.3.11 -> matrice 11.3
    """

    target_family = get_target_family(
        target_version
    )

    if not target_family:
        return []

    return SUPPORTED_PLATFORMS.get(
        target_family,
        []
    )


def find_platform(
    target_version: str,
    category: str,
    technology: str,
    version: str | None = None
) -> list[dict]:
    """
    Recherche une technologie dans la matrice.

    Exemple :

        find_platform(
            "11.3.11",
            "DATABASE",
            "PostgreSQL",
            "17"
        )
    """

    matrix = get_supported_platforms(
        target_version
    )

    results = []

    for item in matrix:

        if (
            item.get(
                "category",
                ""
            ).lower()
            !=
            category.lower()
        ):
            continue

        if (
            item.get(
                "technology",
                ""
            ).lower()
            !=
            technology.lower()
        ):
            continue

        if version is not None:

            if (
                str(
                    item.get(
                        "version",
                        ""
                    )
                ).lower()
                !=
                str(version).lower()
            ):
                continue

        results.append(
            item
        )

    return results


def get_supported_versions(
    target_version: str,
    category: str,
    technology: str
) -> list[dict]:
    """
    Retourne toutes les versions connues pour
    une technologie.

    Exemple :

        get_supported_versions(
            "11.3.11",
            "DATABASE",
            "PostgreSQL"
        )
    """

    return find_platform(
        target_version=target_version,
        category=category,
        technology=technology
    )


def evaluate_platform_version(
    target_version: str,
    category: str,
    technology: str,
    current_version: str
) -> dict:
    """
    Compare une version détectée avec la matrice.

    Retour :

        {
            "found": True,
            "status": "SUPPORTED",
            "matrix_item": {...}
        }

    ou :

        {
            "found": False,
            "status": "UNKNOWN",
            "matrix_item": None
        }
    """

    matches = find_platform(
        target_version=target_version,
        category=category,
        technology=technology,
        version=current_version
    )

    if not matches:

        return {
            "found": False,
            "status": "UNKNOWN",
            "matrix_item": None
        }

    item = matches[0]

    return {
        "found": True,
        "status": item.get(
            "status"
        ),
        "matrix_item": item
    }


# ============================================================
# CONVERSION VERS L'ONGLET EXCEL
# ============================================================

def build_supported_platforms_rows(
    target_version: str | None
) -> list[dict]:
    """
    Prépare les données destinées à l'onglet Excel
    'Supported Platforms'.
    """

    matrix = get_supported_platforms(
        target_version
    )

    rows = []

    for item in matrix:

        rows.append(
            {
                "target_version":
                    target_version or "",

                "category":
                    item.get(
                        "category",
                        ""
                    ),

                "technology":
                    item.get(
                        "technology",
                        ""
                    ),

                "version":
                    item.get(
                        "version",
                        ""
                    ),

                "support_status":
                    item.get(
                        "status",
                        ""
                    ),

                "notes":
                    item.get(
                        "notes",
                        ""
                    ),

                "source":
                    item.get(
                        "source",
                        ""
                    )
            }
        )

    return rows