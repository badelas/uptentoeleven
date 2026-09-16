from __future__ import annotations

from typing import Any


def comparison_result(
    domain: str,
    field: str,
    pre: Any,
    post: Any,
    status: str,
    message: str,
) -> dict:
    return {
        "domain": domain,
        "field": field,
        "pre": pre,
        "post": post,
        "status": status,
        "message": message,
    }


def _normalize_version(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _version_matches_family(
    version: str,
    target_family: str,
) -> bool:
    """
    Exemple :
        version = 11.3.11
        target_family = 11.3

    Retourne True.
    """

    version = _normalize_version(version)
    target_family = _normalize_version(target_family)

    if not version or not target_family:
        return False

    return (
        version == target_family
        or version.startswith(target_family + ".")
    )


def _compare_target_version(
    pre_version: Any,
    post_version: Any,
    target_family: str | None,
    target_version: str | None,
) -> dict:

    pre = _normalize_version(pre_version)
    post = _normalize_version(post_version)

    target_family = _normalize_version(target_family)
    target_version = _normalize_version(target_version)

    # --------------------------------------------------------
    # Données manquantes
    # --------------------------------------------------------

    if not pre:
        return comparison_result(
            domain="JIRA",
            field="version",
            pre=pre_version,
            post=post_version,
            status="FAIL",
            message="Version Jira PRE absente.",
        )

    if not post:
        return comparison_result(
            domain="JIRA",
            field="version",
            pre=pre_version,
            post=post_version,
            status="FAIL",
            message="Version Jira POST absente.",
        )

    # --------------------------------------------------------
    # Cible exacte définie
    # --------------------------------------------------------

    if target_version:

        if post == target_version:

            return comparison_result(
                domain="JIRA",
                field="version",
                pre=pre,
                post=post,
                status="PASS",
                message=(
                    f"Version Jira POST conforme à la cible exacte "
                    f"{target_version}."
                ),
            )

        return comparison_result(
            domain="JIRA",
            field="version",
            pre=pre,
            post=post,
            status="FAIL",
            message=(
                f"Version Jira POST {post} différente de la cible "
                f"attendue {target_version}."
            ),
        )

    # --------------------------------------------------------
    # Cible par famille définie
    # Exemple : 11.3
    # --------------------------------------------------------

    if target_family:

        if _version_matches_family(
            post,
            target_family,
        ):

            return comparison_result(
                domain="JIRA",
                field="version",
                pre=pre,
                post=post,
                status="PASS",
                message=(
                    f"Version Jira POST conforme à la famille cible "
                    f"{target_family}.x."
                ),
            )

        if pre == post:

            return comparison_result(
                domain="JIRA",
                field="version",
                pre=pre,
                post=post,
                status="FAIL",
                message=(
                    f"La version Jira n'a pas changé. "
                    f"Cible attendue : {target_family}.x."
                ),
            )

        return comparison_result(
            domain="JIRA",
            field="version",
            pre=pre,
            post=post,
            status="FAIL",
            message=(
                f"La version Jira a changé de {pre} vers {post}, "
                f"mais ne correspond pas à la cible "
                f"{target_family}.x."
            ),
        )

    # --------------------------------------------------------
    # Pas de cible configurée
    # --------------------------------------------------------

    if pre == post:

        return comparison_result(
            domain="JIRA",
            field="version",
            pre=pre,
            post=post,
            status="WARNING",
            message=(
                "La version Jira PRE et POST est identique, "
                "mais aucune cible Jira n'est configurée."
            ),
        )

    return comparison_result(
        domain="JIRA",
        field="version",
        pre=pre,
        post=post,
        status="INFO",
        message=(
            f"La version Jira a changé de {pre} vers {post}. "
            "Aucune cible Jira n'est configurée pour valider "
            "le résultat."
        ),
    )


def _compare_stable_value(
    domain: str,
    field: str,
    pre: Any,
    post: Any,
) -> dict:

    if pre == post:

        return comparison_result(
            domain=domain,
            field=field,
            pre=pre,
            post=post,
            status="PASS",
            message="Valeur inchangée entre PRE et POST.",
        )

    return comparison_result(
        domain=domain,
        field=field,
        pre=pre,
        post=post,
        status="WARNING",
        message=(
            f"Valeur modifiée entre PRE et POST : "
            f"{pre!s} -> {post!s}."
        ),
    )


def compare_baselines(
    pre: dict,
    post: dict,
    target_family: str | None = None,
    target_version: str | None = None,
) -> list[dict]:

    comparisons: list[dict] = []

    # ========================================================
    # JIRA VERSION
    # ========================================================

    comparisons.append(
        _compare_target_version(
            pre_version=pre.get("jira", {}).get("version"),
            post_version=post.get("jira", {}).get("version"),
            target_family=target_family,
            target_version=target_version,
        )
    )

    # ========================================================
    # JIRA BASE URL
    # ========================================================

    comparisons.append(
        _compare_stable_value(
            domain="JIRA",
            field="baseUrl",
            pre=pre.get("jira", {}).get("baseUrl"),
            post=post.get("jira", {}).get("baseUrl"),
        )
    )

    # ========================================================
    # ARCHITECTURE
    # ========================================================

    comparisons.append(
        _compare_stable_value(
            domain="ARCHITECTURE",
            field="clustered",
            pre=pre.get(
                "architecture",
                {},
            ).get("clustered"),
            post=post.get(
                "architecture",
                {},
            ).get("clustered"),
        )
    )

    # ========================================================
    # DATABASE
    # ========================================================

    comparisons.append(
        _compare_stable_value(
            domain="DATABASE",
            field="type",
            pre=pre.get(
                "database",
                {},
            ).get("type"),
            post=post.get(
                "database",
                {},
            ).get("type"),
        )
    )

    comparisons.append(
        _compare_stable_value(
            domain="DATABASE",
            field="schema",
            pre=pre.get(
                "database",
                {},
            ).get("schema"),
            post=post.get(
                "database",
                {},
            ).get("schema"),
        )
    )

    # ========================================================
    # JIRA CONFIGURATION
    # ========================================================

    jira_configuration_fields = [
        "projects",
        "customFields",
        "issueTypes",
        "statuses",
        "workflows",
    ]

    pre_counts = pre.get(
        "jiraConfiguration",
        {},
    )

    post_counts = post.get(
        "jiraConfiguration",
        {},
    )

    for field in jira_configuration_fields:

        comparisons.append(
            _compare_stable_value(
                domain="JIRA CONFIGURATION",
                field=field,
                pre=pre_counts.get(field),
                post=post_counts.get(field),
            )
        )

    return comparisons