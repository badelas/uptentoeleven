def compare_value(
    results: list,
    domain: str,
    field: str,
    pre,
    post,
    warn_if_changed: bool = True
):

    if pre == post:
        status = "PASS"
    else:
        status = (
            "WARNING"
            if warn_if_changed
            else "INFO"
        )

    results.append({
        "domain": domain,
        "field": field,
        "pre": pre,
        "post": post,
        "status": status
    })


def compare_baselines(
    pre: dict,
    post: dict
) -> list[dict]:

    results = []

    pre_jira = pre.get(
        "jira",
        {}
    )

    post_jira = post.get(
        "jira",
        {}
    )

    pre_config = pre.get(
        "jiraConfiguration",
        {}
    )

    post_config = post.get(
        "jiraConfiguration",
        {}
    )

    # Jira version doit normalement changer
    compare_value(
        results,
        "JIRA",
        "version",
        pre_jira.get("version"),
        post_jira.get("version"),
        warn_if_changed=False
    )

    # Base URL ne devrait pas changer
    compare_value(
        results,
        "JIRA",
        "baseUrl",
        pre_jira.get("baseUrl"),
        post_jira.get("baseUrl")
    )

    compare_value(
        results,
        "ARCHITECTURE",
        "clustered",
        pre.get(
            "architecture",
            {}
        ).get("clustered"),
        post.get(
            "architecture",
            {}
        ).get("clustered")
    )

    compare_value(
        results,
        "DATABASE",
        "type",
        pre.get(
            "database",
            {}
        ).get("type"),
        post.get(
            "database",
            {}
        ).get("type")
    )

    compare_value(
        results,
        "DATABASE",
        "schema",
        pre.get(
            "database",
            {}
        ).get("schema"),
        post.get(
            "database",
            {}
        ).get("schema")
    )

    for field in [
        "projects",
        "customFields",
        "issueTypes",
        "statuses",
        "workflows"
    ]:

        compare_value(
            results,
            "JIRA CONFIGURATION",
            field,
            pre_config.get(field),
            post_config.get(field)
        )

    return results