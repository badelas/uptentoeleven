from baseline_comparator import (
    compare_baselines
)


def test_compare_same_project_count():

    pre = {
        "jira": {},
        "architecture": {},
        "database": {},
        "jiraConfiguration": {
            "projects": 4
        }
    }

    post = {
        "jira": {},
        "architecture": {},
        "database": {},
        "jiraConfiguration": {
            "projects": 4
        }
    }

    result = compare_baselines(
        pre,
        post
    )

    projects = [
        item
        for item in result
        if item["field"] == "projects"
    ][0]

    assert projects["status"] == "PASS"