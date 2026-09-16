from baseline_collector import (
    collect_baseline
)


class FakeClient:

    def get(self, path):
        return {
            "jira": {},
            "architecture": {},
            "java": {},
            "operatingSystem": {},
            "database": {}
        }


class FakeSettings:
    baseline_endpoint = "/baseline"


def test_collect_baseline():

    result = collect_baseline(
        FakeClient(),
        FakeSettings()
    )

    assert "jira" in result