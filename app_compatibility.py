import os
import time
from urllib.parse import parse_qs, quote, urlparse

import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth


# ============================================================
# CONSTANTES MARKETPLACE
# ============================================================

API_ROOT = "https://api.atlassian.com/marketplace"
API_BASE = f"{API_ROOT}/rest/3"

PUBLIC_MARKETPLACE_ROOT = "https://marketplace.atlassian.com"

PUBLIC_API_V2_BASE = f"{PUBLIC_MARKETPLACE_ROOT}/rest/2"


# ============================================================
# POLITIQUES DES APPS ATLASSIAN BUNDLEES
# ============================================================

ATLASSIAN_BUNDLED_APPS = {
    "com.codebarrel.addons.automation": {
        "app_type": "ATLASSIAN_BUNDLED",
        "management_mode": "BUNDLED_WITH_JIRA",
        "strategy": "BUNDLED_WITH_JIRA",
        "status": "PASS",
        "reference_url": (
            "https://support.atlassian.com/automation/kb/"
            "automation-for-jira-incompatibility-during-jira-10x-upgrade-check/"
        ),
        "message": (
            "À partir de Jira Data Center 10.0, Jira automation est "
            "uniquement fourni comme composant bundlé avec Jira. "
            "Aucune version pont Marketplace n'est nécessaire."
        )
    },
    "com.atlassian.plugins.authentication.atlassian-authentication-plugin": {
        "app_type": "ATLASSIAN_BUNDLED",
        "management_mode": "BUNDLED_UPDATABLE",
        "strategy": "BUNDLED_WITH_JIRA",
        "status": "PASS",
        "reference_url": (
            "https://confluence.atlassian.com/security/"
            "saml-sso-for-jira-data-center-applications-1409092936.html"
        ),
        "message": (
            "SSO for Atlassian Data Center est fourni avec Jira Data Center. "
            "La cible Jira fournit sa version bundlée. Une mise à jour séparée "
            "peut ensuite être décidée vers la dernière version supportée, "
            "puis l'authentification doit être testée."
        )
    },
    "com.atlassian.jira.migration.jira-migration-plugin": {
        "app_type": "ATLASSIAN_BUNDLED",
        "management_mode": "BUNDLED_UPDATABLE",
        "strategy": "BUNDLED_WITH_JIRA",
        "status": "PASS",
        "reference_url": (
            "https://support.atlassian.com/migration/docs/"
            "update-or-install-the-jira-cloud-migration-assistant/"
        ),
        "message": (
            "Jira Cloud Migration Assistant est préinstallé/bundlé avec les "
            "versions récentes de Jira. Il n'a pas besoin d'une version pont "
            "pour l'upgrade Jira. Une mise à jour vers une version récente "
            "supportée sera à prévoir avant les travaux de migration Cloud."
        )
    }
}


# ============================================================
# OUTILS GENERIQUES
# ============================================================

def normalize(value):
    if value is None:
        return ""

    return str(value).strip()


def yes_no_unknown(value):
    if value is True:
        return "YES"

    if value is False:
        return "NO"

    return "UNKNOWN"


def collect_apps(baseline: dict) -> list[dict]:
    """
    Combine les applications tierces et les applications Atlassian
    suivies, puis supprime les doublons.

    La clé Marketplace est prioritaire pour l'identification.
    """

    apps = []
    seen = set()

    for list_name in (
        "thirdPartyApps",
        "importantAtlassianApps"
    ):
        for app in baseline.get(list_name, []) or []:
            if not isinstance(app, dict):
                continue

            name = (
                app.get("name")
                or app.get("key")
                or "Application inconnue"
            )

            plugin_key = normalize(
                app.get("key")
            )

            current_version = normalize(
                app.get("version")
            )

            unique_key = (
                plugin_key.lower()
                if plugin_key
                else normalize(name).lower()
            )

            if unique_key in seen:
                continue

            seen.add(unique_key)

            apps.append(
                {
                    "name": normalize(name),
                    "plugin_key": plugin_key,
                    "current_version": current_version,
                    "vendor": normalize(app.get("vendor")),
                    "enabled": app.get("enabled"),
                    "inventory_source": list_name
                }
            )

    return apps



# ============================================================
# CLASSIFICATION DES APPS
# ============================================================

def jira_major(version: str) -> int | None:
    try:
        return int(normalize(version).split(".")[0])
    except (AttributeError, IndexError, TypeError, ValueError):
        return None


def get_bundled_policy(
    app: dict,
    source_version: str,
    target_version: str
) -> dict | None:

    plugin_key = normalize(app.get("plugin_key"))
    policy = ATLASSIAN_BUNDLED_APPS.get(plugin_key)

    if not policy:
        return None

    if plugin_key == "com.codebarrel.addons.automation":
        target_major = jira_major(target_version)

        if target_major is not None and target_major < 10:
            return None

    return dict(policy)


def analyze_bundled_app(
    app: dict,
    source_version: str,
    target_version: str,
    policy: dict
) -> dict:

    name = normalize(app.get("name"))
    plugin_key = normalize(app.get("plugin_key"))
    current_version = normalize(app.get("current_version"))
    mode = policy.get("management_mode", "BUNDLED_WITH_JIRA")
    status = policy.get("status", "PASS")
    reference_url = policy.get("reference_url", "")

    # Pour le Readiness d'upgrade Jira, une app bundlée n'impose
    # pas de version pont ni de mise à jour séparée AVANT l'upgrade.
    # Les vérifications fonctionnelles après upgrade sont traitées
    # dans le plan de tests POST, pas comme un WARNING de compatibilité.
    action_required = "Aucune pour l'upgrade Jira"
    selected_value = f"Bundlé avec Jira {target_version}"

    if plugin_key == "com.codebarrel.addons.automation":
        post_upgrade_note = (
            "Après upgrade, vérifier que Jira automation est disponible "
            "et exécuter les tests des règles critiques prévues dans le plan POST."
        )

    elif plugin_key == (
        "com.atlassian.plugins.authentication.atlassian-authentication-plugin"
    ):
        post_upgrade_note = (
            "Après upgrade, vérifier la version bundlée puis tester SAML/OIDC, "
            "la connexion administrateur et le mode de secours. Une mise à jour "
            "séparée pourra être décidée ensuite si nécessaire."
        )

    elif plugin_key == "com.atlassian.jira.migration.jira-migration-plugin":
        post_upgrade_note = (
            "Après validation de l'upgrade Jira, vérifier JCMA. Sa mise à jour "
            "éventuelle concerne la préparation de la migration Cloud, pas la "
            "compatibilité de l'upgrade Jira lui-même."
        )

    else:
        post_upgrade_note = (
            "Après upgrade, vérifier la présence et le fonctionnement du composant "
            "dans le cadre du plan de tests POST."
        )

    message = (
        policy.get("message", "").rstrip()
        + " "
        + post_upgrade_note
    ).strip()

    return {
        "status": status,
        "app": name,
        "app_type": policy.get("app_type", "ATLASSIAN_BUNDLED"),
        "management_mode": mode,
        "plugin_key": plugin_key,
        "current_version": current_version,
        "current_version_url": "",
        "source_jira": source_version,
        "source_build": "",
        "current_compatible_source": "YES",
        "latest_source_compatible_version": "",
        "target_jira": target_version,
        "target_build": "",
        "current_compatible_target": "N/A",
        "bridge_version": "N/A",
        "bridge_version_url": "",
        "bridge_download_url": "",
        "target_only_version": f"Bundled with Jira {target_version}",
        "target_only_version_url": "",
        "target_only_download_url": "",
        "latest_target_compatible_version": f"Bundled with Jira {target_version}",
        "strategy": policy.get("strategy", "BUNDLED_WITH_JIRA"),
        "reference_url": reference_url,
        "assessment_method": "EXTERNAL",
        "action_required": action_required,
        "message": message,
        "selected_value": selected_value,
        "selected_url": reference_url
    }


# ============================================================
# CLIENT MARKETPLACE
# ============================================================

class MarketplaceClient:

    def __init__(
        self,
        email: str,
        api_token: str,
        timeout: int = 30,
        max_attempts: int = 5
    ):
        self.timeout = timeout
        self.max_attempts = max_attempts

        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(
            email,
            api_token
        )
        self.session.headers.update(
            {
                "Accept": "application/json"
            }
        )

        # Session publique séparée : les liens destinés à Excel
        # doivent s'ouvrir sans transmettre le token API.
        self.public_session = requests.Session()
        self.public_session.headers.update(
            {
                "Accept": "application/json"
            }
        )

        self._public_app_url_cache = {}
        self._public_version_links_cache = {}

    def get_json(
        self,
        url: str,
        params: dict | None = None
    ):
        last_error = None

        for attempt in range(
            1,
            self.max_attempts + 1
        ):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )
            except requests.RequestException as error:
                last_error = error

                if attempt >= self.max_attempts:
                    raise

                time.sleep(
                    min(2 ** (attempt - 1), 15)
                )

                continue

            if response.status_code == 429:
                retry_after = response.headers.get(
                    "Retry-After"
                )

                try:
                    wait_seconds = float(
                        retry_after
                    )
                except (
                    TypeError,
                    ValueError
                ):
                    wait_seconds = min(
                        2 ** (attempt - 1),
                        15
                    )

                if attempt >= self.max_attempts:
                    response.raise_for_status()

                time.sleep(wait_seconds)
                continue

            if 500 <= response.status_code <= 599:
                if attempt >= self.max_attempts:
                    response.raise_for_status()

                time.sleep(
                    min(2 ** (attempt - 1), 15)
                )

                continue

            response.raise_for_status()
            return response.json()

        if last_error:
            raise last_error

        raise RuntimeError(
            "Échec inattendu de l'appel Marketplace."
        )

    def get_jira_build(
        self,
        version_number: str
    ) -> int:
        url = (
            f"{API_BASE}/parent-software/"
            f"jira/versions/number/{version_number}"
        )

        data = self.get_json(url)

        return int(
            data["buildNumber"]
        )

    def get_datacenter_app_software_id(
        self,
        app_key: str
    ) -> str | None:
        url = (
            f"{API_BASE}/app-software/"
            f"app-key/{app_key}"
        )

        mappings = self.get_json(url)

        for mapping in mappings:
            if normalize(
                mapping.get("hosting")
            ).lower() == "datacenter":
                return mapping.get(
                    "appSoftwareId"
                )

        return None

    @staticmethod
    def extract_cursor(
        next_link: str | None
    ) -> str | None:
        if not next_link:
            return None

        parsed = urlparse(next_link)
        query = parse_qs(parsed.query)
        cursors = query.get("cursor", [])

        if not cursors:
            return None

        return cursors[0]

    def get_all_versions(
        self,
        app_software_id: str
    ) -> list[dict]:
        """
        Le chemin officiel /marketplace/rest/3/... est conservé
        pour chaque page. Seul le cursor fourni par links.next
        est réinjecté.
        """

        endpoint = (
            f"{API_BASE}/app-software/"
            f"{app_software_id}/versions"
        )

        all_versions = []
        cursor = None

        while True:
            params = {
                "limit": 50
            }

            if cursor:
                params["cursor"] = cursor

            data = self.get_json(
                endpoint,
                params=params
            )

            versions = (
                data.get("versions", [])
                or []
            )

            all_versions.extend(versions)

            next_link = (
                data.get("links", {})
                .get("next")
            )

            cursor = self.extract_cursor(
                next_link
            )

            if not cursor:
                break

        return all_versions

    # --------------------------------------------------------
    # LIENS PUBLICS MARKETPLACE (REST v2)
    # --------------------------------------------------------

    @staticmethod
    def _public_href(
        href: str | None
    ) -> str:
        href = normalize(href)

        if not href:
            return ""

        if href.lower().startswith(
            ("http://", "https://")
        ):
            return href

        if not href.startswith("/"):
            href = "/" + href

        return PUBLIC_MARKETPLACE_ROOT + href

    def _public_get_json(
        self,
        url: str
    ) -> dict | None:
        for attempt in range(
            1,
            self.max_attempts + 1
        ):
            try:
                response = self.public_session.get(
                    url,
                    timeout=self.timeout
                )
            except requests.RequestException:
                if attempt >= self.max_attempts:
                    return None

                time.sleep(
                    min(2 ** (attempt - 1), 15)
                )
                continue

            if response.status_code == 404:
                return None

            if response.status_code == 429:
                retry_after = response.headers.get(
                    "Retry-After"
                )

                try:
                    wait_seconds = float(
                        retry_after
                    )
                except (
                    TypeError,
                    ValueError
                ):
                    wait_seconds = min(
                        2 ** (attempt - 1),
                        15
                    )

                if attempt >= self.max_attempts:
                    return None

                time.sleep(wait_seconds)
                continue

            if 500 <= response.status_code <= 599:
                if attempt >= self.max_attempts:
                    return None

                time.sleep(
                    min(2 ** (attempt - 1), 15)
                )
                continue

            if not response.ok:
                return None

            try:
                return response.json()
            except ValueError:
                return None

        return None

    def get_public_app_url(
        self,
        app_key: str
    ) -> str:
        app_key = normalize(app_key)

        if not app_key:
            return ""

        if app_key in self._public_app_url_cache:
            return self._public_app_url_cache[
                app_key
            ]

        encoded_key = quote(
            app_key,
            safe=""
        )

        data = self._public_get_json(
            f"{PUBLIC_API_V2_BASE}/addons/{encoded_key}"
        )

        alternate = ""

        if data:
            alternate = (
                data.get("_links", {})
                .get("alternate", {})
                .get("href")
            )

        public_url = self._public_href(
            alternate
        )

        self._public_app_url_cache[
            app_key
        ] = public_url

        return public_url

    def get_public_version_links(
        self,
        app_key: str,
        version: dict | None
    ) -> dict:
        """
        Retourne une page Marketplace publique et, si disponible,
        le binaire public de la version.

        Le REST v3 authentifié reste la source de compatibilité.
        Le REST v2 public sert uniquement à produire des liens
        ouvrables directement depuis Excel.
        """

        if not version:
            return {
                "version_url": "",
                "download_url": ""
            }

        build_number = version.get(
            "buildNumber"
        )

        if build_number is None:
            return {
                "version_url": "",
                "download_url": ""
            }

        app_key = normalize(app_key)
        cache_key = (
            app_key,
            str(build_number)
        )

        if cache_key in self._public_version_links_cache:
            return dict(
                self._public_version_links_cache[
                    cache_key
                ]
            )

        encoded_key = quote(
            app_key,
            safe=""
        )

        data = self._public_get_json(
            f"{PUBLIC_API_V2_BASE}/addons/"
            f"{encoded_key}/versions/build/"
            f"{build_number}"
        )

        version_href = ""
        binary_href = ""

        if data:
            version_href = (
                data.get("_links", {})
                .get("alternate", {})
                .get("href")
            )

            binary_href = (
                data.get("_embedded", {})
                .get("artifact", {})
                .get("_links", {})
                .get("binary", {})
                .get("href")
            )

            if not binary_href:
                binary_href = (
                    data.get("vendorLinks", {})
                    .get("binary")
                )

        version_url = self._public_href(
            version_href
        )

        download_url = self._public_href(
            binary_href
        )

        if not version_url:
            version_url = self.get_public_app_url(
                app_key
            )

        result = {
            "version_url": version_url,
            "download_url": download_url
        }

        self._public_version_links_cache[
            cache_key
        ] = dict(result)

        return result


# ============================================================
# COMPATIBILITE
# ============================================================

def supports_jira_build(
    app_version: dict,
    jira_build: int
) -> bool:
    compatibilities = (
        app_version.get(
            "compatibilities",
            []
        )
        or []
    )

    for compatibility in compatibilities:
        if compatibility.get(
            "parentSoftwareId"
        ) != "jira":
            continue

        min_build = compatibility.get(
            "minBuildNumber"
        )

        max_build = compatibility.get(
            "maxBuildNumber"
        )

        min_ok = (
            min_build is None
            or jira_build >= int(min_build)
        )

        max_ok = (
            max_build is None
            or jira_build <= int(max_build)
        )

        if min_ok and max_ok:
            return True

    return False


def is_usable_version(
    version: dict
) -> bool:
    if version.get("beta") is True:
        return False

    if version.get("supported") is False:
        return False

    state = version.get("state")

    if state not in (
        None,
        "active"
    ):
        return False

    return True


def latest_version(
    versions: list[dict]
) -> dict | None:
    if not versions:
        return None

    return max(
        versions,
        key=lambda item: int(
            item.get("buildNumber", 0)
            or 0
        )
    )


def find_exact_version(
    versions: list[dict],
    version_number: str
) -> dict | None:
    wanted = normalize(
        version_number
    )

    for version in versions:
        if normalize(
            version.get("versionNumber")
        ) == wanted:
            return version

    return None


# ============================================================
# URLS MARKETPLACE
# ============================================================

def version_api_url(
    app_software_id: str,
    version: dict | None
) -> str:
    if not version:
        return ""

    build_number = version.get(
        "buildNumber"
    )

    if build_number is None:
        return ""

    return (
        f"{API_BASE}/app-software/"
        f"{app_software_id}/versions/"
        f"{build_number}"
    )


def artifact_download_url(
    version: dict | None
) -> str:
    if not version:
        return ""

    framework = (
        version.get(
            "frameworkDetails",
            {}
        )
        or {}
    )

    attributes = (
        framework.get(
            "attributes",
            {}
        )
        or {}
    )

    artifact_id = attributes.get(
        "artifactId"
    )

    if not artifact_id:
        return ""

    return (
        f"{API_BASE}/artifacts/"
        f"{artifact_id}/download"
    )


def version_number(
    version: dict | None
) -> str:
    if not version:
        return ""

    return normalize(
        version.get("versionNumber")
    )


# ============================================================
# RESULTAT EN CAS D'ERREUR / ANALYSE MANUELLE
# ============================================================

def manual_review_row(
    app: dict,
    source_version: str,
    source_build,
    target_version: str,
    target_build,
    message: str
) -> dict:
    return {
        "status": "UNKNOWN",
        "app": app.get("name", ""),
        "app_type": (
            "ATLASSIAN_APP"
            if app.get("inventory_source") == "importantAtlassianApps"
            else "MARKETPLACE_APP"
        ),
        "management_mode": "MARKETPLACE_COMPATIBILITY",
        "plugin_key": app.get("plugin_key", ""),
        "current_version": app.get(
            "current_version",
            ""
        ),
        "current_version_url": "",
        "source_jira": source_version,
        "source_build": source_build or "",
        "current_compatible_source": "UNKNOWN",
        "latest_source_compatible_version": "",
        "target_jira": target_version,
        "target_build": target_build or "",
        "current_compatible_target": "UNKNOWN",
        "bridge_version": "",
        "bridge_version_url": "",
        "bridge_download_url": "",
        "target_only_version": "",
        "target_only_version_url": "",
        "target_only_download_url": "",
        "latest_target_compatible_version": "",
        "strategy": "MANUAL_REVIEW",
        "reference_url": "",
        "assessment_method": "EXTERNAL",
        "action_required": (
            "Vérifier manuellement la compatibilité "
            "de l'application avec Jira source et cible"
        ),
        "message": message,
        "selected_value": "",
        "selected_url": ""
    }


# ============================================================
# ANALYSE D'UNE APPLICATION
# ============================================================

def analyze_one_app(
    client: MarketplaceClient,
    app: dict,
    source_version: str,
    source_build: int,
    target_version: str,
    target_build: int
) -> dict:
    name = app.get(
        "name",
        "Application inconnue"
    )

    plugin_key = app.get(
        "plugin_key",
        ""
    )

    current_app_version = app.get(
        "current_version",
        ""
    )

    if not plugin_key:
        return manual_review_row(
            app,
            source_version,
            source_build,
            target_version,
            target_build,
            (
                "Aucune clé Marketplace n'a été détectée "
                "pour cette application."
            )
        )

    try:
        app_software_id = (
            client.get_datacenter_app_software_id(
                plugin_key
            )
        )
    except requests.RequestException as error:
        return manual_review_row(
            app,
            source_version,
            source_build,
            target_version,
            target_build,
            (
                "Impossible d'interroger Marketplace pour "
                f"{name}: {error}"
            )
        )

    if not app_software_id:
        return manual_review_row(
            app,
            source_version,
            source_build,
            target_version,
            target_build,
            (
                "Aucune entrée Data Center Marketplace "
                "n'a été trouvée pour cette clé d'application."
            )
        )

    try:
        versions = client.get_all_versions(
            app_software_id
        )
    except requests.RequestException as error:
        return manual_review_row(
            app,
            source_version,
            source_build,
            target_version,
            target_build,
            (
                "Impossible de récupérer les versions Marketplace "
                f"de {name}: {error}"
            )
        )

    usable_versions = [
        version
        for version in versions
        if is_usable_version(version)
    ]

    current_record = find_exact_version(
        versions,
        current_app_version
    )

    source_versions = [
        version
        for version in usable_versions
        if supports_jira_build(
            version,
            source_build
        )
    ]

    target_versions = [
        version
        for version in usable_versions
        if supports_jira_build(
            version,
            target_build
        )
    ]

    bridge_versions = [
        version
        for version in usable_versions
        if (
            supports_jira_build(
                version,
                source_build
            )
            and
            supports_jira_build(
                version,
                target_build
            )
        )
    ]

    target_only_versions = [
        version
        for version in usable_versions
        if (
            supports_jira_build(
                version,
                target_build
            )
            and
            not supports_jira_build(
                version,
                source_build
            )
        )
    ]

    latest_source = latest_version(
        source_versions
    )

    latest_target = latest_version(
        target_versions
    )

    latest_bridge = latest_version(
        bridge_versions
    )

    latest_target_only = latest_version(
        target_only_versions
    )

    current_source_ok = (
        supports_jira_build(
            current_record,
            source_build
        )
        if current_record
        else None
    )

    current_target_ok = (
        supports_jira_build(
            current_record,
            target_build
        )
        if current_record
        else None
    )

    # --------------------------------------------------------
    # LIENS PUBLICS MARKETPLACE
    # --------------------------------------------------------

    current_public_links = (
        client.get_public_version_links(
            plugin_key,
            current_record
        )
    )

    bridge_public_links = (
        client.get_public_version_links(
            plugin_key,
            latest_bridge
        )
    )

    target_only_public_links = (
        client.get_public_version_links(
            plugin_key,
            latest_target_only
        )
    )

    # --------------------------------------------------------
    # STRATEGIE
    # --------------------------------------------------------

    if current_record is None:
        # La version installée est connue, mais Marketplace ne permet
        # pas de l'évaluer automatiquement. Ce n'est pas UNKNOWN :
        # l'information existe, l'évaluation reste à faire.
        status = "NOT_ASSESSED"
        strategy = "MANUAL_REVIEW"
        action_required = (
            "Vérifier manuellement la version actuelle et "
            "le chemin de mise à jour de l'application"
        )
        message = (
            f"La version actuelle {current_app_version or 'non renseignée'} "
            "n'a pas été retrouvée exactement dans Marketplace. "
            "Les versions candidates sont affichées mais aucune stratégie "
            "automatique n'est appliquée."
        )
        selected_value = ""
        selected_url = ""

    elif current_source_ok is False:
        status = "WARNING"
        strategy = "MANUAL_REVIEW"
        action_required = (
            "Contrôler la compatibilité déclarée de la version "
            "actuelle avec Jira source avant toute décision"
        )
        message = (
            "Marketplace ne déclare pas la version actuellement installée "
            "comme compatible avec Jira source. Comme l'application peut "
            "néanmoins être active sur l'instance, une revue manuelle est "
            "nécessaire avant de conclure."
        )
        selected_value = ""
        selected_url = ""

    elif current_target_ok is True:
        status = "PASS"
        strategy = "KEEP"
        action_required = (
            "Conserver la version actuelle pendant l'upgrade Jira; "
            "une mise à jour ultérieure reste optionnelle"
        )
        message = (
            "La version actuelle est déclarée compatible avec Jira source "
            "et Jira cible."
        )
        selected_value = current_app_version
        selected_url = (
            current_public_links.get("version_url")
            or ""
        )

    elif latest_bridge:
        status = "WARNING"

        if latest_target_only:
            strategy = (
                "PRE_UPGRADE_BRIDGE_THEN_POST"
            )
            action_required = (
                f"Mettre {name} à jour vers {version_number(latest_bridge)} "
                "avant Jira; après validation de Jira cible, mettre "
                f"éventuellement à jour vers {version_number(latest_target_only)}"
            )
            message = (
                "Une version pont compatible source+cible existe. "
                "Elle permet de faire traverser l'application pendant "
                "la montée de version Jira."
            )
            selected_value = (
                f"Pont {version_number(latest_bridge)} -> "
                f"Cible {version_number(latest_target_only)}"
            )
        else:
            strategy = "PRE_UPGRADE_BRIDGE"
            action_required = (
                f"Mettre {name} à jour vers {version_number(latest_bridge)} "
                "avant l'upgrade Jira"
            )
            message = (
                "Une version pont compatible Jira source et Jira cible "
                "a été trouvée."
            )
            selected_value = version_number(
                latest_bridge
            )

        selected_url = (
            bridge_public_links.get("download_url")
            or bridge_public_links.get("version_url")
            or ""
        )

    elif latest_target_only:
        status = "WARNING"
        strategy = (
            "DISABLE_THEN_POST_UPGRADE"
        )
        action_required = (
            f"Désactiver {name} avant l'upgrade Jira, monter Jira vers "
            f"{target_version}, installer {version_number(latest_target_only)}, "
            "réactiver l'application puis exécuter les tests fonctionnels"
        )
        message = (
            "Aucune version pont compatible à la fois avec Jira source "
            "et Jira cible n'a été trouvée. La mise à jour de l'application "
            "doit être réalisée après l'upgrade Jira."
        )
        selected_value = version_number(
            latest_target_only
        )
        selected_url = (
            target_only_public_links.get("download_url")
            or target_only_public_links.get("version_url")
            or ""
        )

    else:
        status = "FAIL"
        strategy = "NO_TARGET_VERSION"
        action_required = (
            "Identifier avec l'éditeur une version supportant Jira cible "
            "ou revoir la cible avant l'upgrade"
        )
        message = (
            "Aucune version active/stable/supportée de l'application "
            f"n'a été trouvée compatible avec Jira {target_version}."
        )
        selected_value = ""
        selected_url = ""

    return {
        "status": status,
        "app": name,
        "app_type": (
            "ATLASSIAN_APP"
            if app.get("inventory_source") == "importantAtlassianApps"
            else "MARKETPLACE_APP"
        ),
        "management_mode": "MARKETPLACE_COMPATIBILITY",
        "plugin_key": plugin_key,
        "current_version": current_app_version,
        "current_version_url": (
            current_public_links.get("version_url")
            or ""
        ),
        "source_jira": source_version,
        "source_build": source_build,
        "current_compatible_source": yes_no_unknown(
            current_source_ok
        ),
        "latest_source_compatible_version": version_number(
            latest_source
        ),
        "target_jira": target_version,
        "target_build": target_build,
        "current_compatible_target": yes_no_unknown(
            current_target_ok
        ),
        "bridge_version": version_number(
            latest_bridge
        ),
        "bridge_version_url": (
            bridge_public_links.get("version_url")
            or ""
        ),
        "bridge_download_url": (
            bridge_public_links.get("download_url")
            or ""
        ),
        "target_only_version": version_number(
            latest_target_only
        ),
        "target_only_version_url": (
            target_only_public_links.get("version_url")
            or ""
        ),
        "target_only_download_url": (
            target_only_public_links.get("download_url")
            or ""
        ),
        "latest_target_compatible_version": version_number(
            latest_target
        ),
        "strategy": strategy,
        "reference_url": (
            client.get_public_app_url(plugin_key)
            or ""
        ),
        "assessment_method": "EXTERNAL",
        "action_required": action_required,
        "message": message,
        "selected_value": selected_value,
        "selected_url": selected_url
    }


# ============================================================
# ANALYSE COMPLETE
# ============================================================

def analyze_app_compatibility(
    baseline: dict,
    settings
) -> list[dict]:

    load_dotenv()

    apps = collect_apps(baseline)

    if not apps:
        return []

    source_version = normalize(
        baseline.get("jira", {}).get("version")
    )

    target_version = normalize(
        getattr(settings, "target_jira_version", None)
    )

    rows = []
    marketplace_apps = []

    for app in apps:
        policy = get_bundled_policy(
            app,
            source_version,
            target_version
        )

        if policy:
            rows.append(
                analyze_bundled_app(
                    app=app,
                    source_version=source_version,
                    target_version=target_version,
                    policy=policy
                )
            )
        else:
            marketplace_apps.append(app)

    if not marketplace_apps:
        return rows

    if not source_version or not target_version:
        message = (
            "La version Jira source ou la version cible exacte manque. "
            "L'analyse automatique Marketplace ne peut pas être réalisée."
        )
        rows.extend(
            manual_review_row(
                app, source_version, "", target_version, "", message
            )
            for app in marketplace_apps
        )
        return rows

    email = (
        os.getenv("MARKETPLACE_EMAIL")
        or os.getenv("JIRA_EMAIL")
    )

    api_token = (
        os.getenv("MARKETPLACE_API_TOKEN")
        or os.getenv("JIRA_API_TOKEN")
    )

    if not email or not api_token:
        message = (
            "Identifiants Marketplace manquants. Renseigner "
            "MARKETPLACE_EMAIL / MARKETPLACE_API_TOKEN ou utiliser "
            "JIRA_EMAIL / JIRA_API_TOKEN."
        )
        rows.extend(
            manual_review_row(
                app, source_version, "", target_version, "", message
            )
            for app in marketplace_apps
        )
        return rows

    client = MarketplaceClient(email, api_token)

    try:
        source_build = client.get_jira_build(source_version)
        target_build = client.get_jira_build(target_version)
    except (
        requests.RequestException,
        KeyError,
        TypeError,
        ValueError
    ) as error:
        message = (
            "Impossible de résoudre les builds Marketplace de Jira source "
            f"et/ou cible: {error}"
        )
        rows.extend(
            manual_review_row(
                app, source_version, "", target_version, "", message
            )
            for app in marketplace_apps
        )
        return rows

    for app in marketplace_apps:
        rows.append(
            analyze_one_app(
                client=client,
                app=app,
                source_version=source_version,
                source_build=source_build,
                target_version=target_version,
                target_build=target_build
            )
        )

    return rows


# ============================================================
# ENRICHISSEMENT READINESS
# ============================================================

def apply_app_compatibility_to_readiness(
    readiness: list[dict],
    app_compatibility: list[dict]
) -> list[dict]:
    """
    Injecte la synthèse Marketplace dans les lignes APPLICATIONS
    déjà construites par readiness_analyzer.py.

    Le détail complet reste dans l'onglet App Compatibility.
    """

    if not readiness or not app_compatibility:
        return readiness

    by_name = {
        normalize(item.get("app")).lower(): item
        for item in app_compatibility
        if normalize(item.get("app"))
    }

    for row in readiness:
        if normalize(
            row.get("domain")
        ).upper() != "APPLICATIONS":
            continue

        check_name = normalize(
            row.get("check")
        ).lower()

        compatibility = by_name.get(
            check_name
        )

        if not compatibility:
            continue

        row["status"] = compatibility.get(
            "status",
            row.get("status")
        )

        management_mode = compatibility.get(
            "management_mode",
            "MARKETPLACE_COMPATIBILITY"
        )

        if management_mode in (
            "BUNDLED_WITH_JIRA",
            "BUNDLED_UPDATABLE"
        ):
            row["target_expected"] = (
                f"Composant Atlassian fourni/bundlé avec Jira "
                f"{compatibility.get('target_jira') or 'cible'} "
                "et validation fonctionnelle préparée"
            )
        else:
            row["target_expected"] = (
                f"Version compatible avec Jira "
                f"{compatibility.get('target_jira') or 'cible'}"
            )

        row["target_value"] = row["target_expected"]

        row["selected_value"] = (
            compatibility.get(
                "selected_value"
            )
            or ""
        )

        row["link_url"] = (
            compatibility.get(
                "selected_url"
            )
            or ""
        )

        row["assessment_method"] = (
            compatibility.get("assessment_method")
            or "EXTERNAL"
        )

        row["action_required"] = (
            compatibility.get(
                "action_required"
            )
            or ""
        )

        row["message"] = (
            compatibility.get("message")
            or ""
        )

    return readiness
