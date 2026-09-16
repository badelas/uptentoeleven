from config import Settings


def test_settings_loaded():

    settings = Settings.from_env()

    assert settings.jira_url
    assert settings.jira_pat