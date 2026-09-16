import argparse

from api_client import JiraApiClient

from baseline_analyzer import (
    analyze_baseline
)

from baseline_collector import (
    collect_baseline
)

from baseline_comparator import (
    compare_baselines
)

from readiness_analyzer import (
    analyze_readiness
)

from config import Settings

from excel_report import (
    generate_excel_report
)

from logger import (
    configure_logging,
    get_logger
)

from utils.files import (
    latest_file,
    load_json,
    safe_filename,
    save_json,
    timestamp
)


# ============================================================
# COLLECTE PRE / POST
# ============================================================

def collect_mode(
    phase: str,
    settings: Settings,
    logger
):

    client = JiraApiClient(
        settings
    )

    # --------------------------------------------------------
    # Collecte depuis ScriptRunner
    # --------------------------------------------------------

    baseline = collect_baseline(
        client,
        settings
    )

    # --------------------------------------------------------
    # Métadonnées locales
    # --------------------------------------------------------

    baseline[
        "collectionPhase"
    ] = phase.upper()

    baseline[
        "instanceName"
    ] = settings.instance_name

    # --------------------------------------------------------
    # Répertoires
    # --------------------------------------------------------

    json_dir = (
        settings.output_dir
        / "json"
    )

    excel_dir = (
        settings.output_dir
        / "excel"
    )

    instance = safe_filename(
        settings.instance_name
    )

    date_stamp = timestamp()

    # --------------------------------------------------------
    # Sauvegarde JSON
    # --------------------------------------------------------

    json_name = (
        f"{instance}_"
        f"{phase.upper()}_"
        f"{date_stamp}.json"
    )

    json_path = save_json(
        baseline,
        json_dir,
        json_name
    )

    # --------------------------------------------------------
    # Analyse de la baseline SOURCE
    # --------------------------------------------------------

    findings = analyze_baseline(
        baseline
    )

    # --------------------------------------------------------
    # Analyse de READINESS
    #
    # SOURCE détectée automatiquement depuis Jira
    # VS
    # CIBLE configurée dans .env
    # --------------------------------------------------------

    readiness = analyze_readiness(
        baseline,
        settings
    )

    # --------------------------------------------------------
    # Rapport Excel
    # --------------------------------------------------------

    excel_name = (
        f"{instance}_"
        f"{phase.upper()}_"
        f"{date_stamp}.xlsx"
    )

    excel_path = (
        excel_dir
        / excel_name
    )

    generate_excel_report(
        baseline=baseline,
        findings=findings,
        output_path=excel_path,
        readiness=readiness,
        target_family=(
            settings.target_jira_family
        ),
        target_version=(
            settings.target_jira_version
        )
    )

    # --------------------------------------------------------
    # Logs
    # --------------------------------------------------------

    logger.info(
        "JSON créé : %s",
        json_path
    )

    logger.info(
        "Excel créé : %s",
        excel_path
    )

    logger.info(
        "Statistiques API : %s",
        client.stats
    )

    print()

    print(
        "Collecte terminée."
    )

    print(
        f"JSON  : {json_path}"
    )

    print(
        f"Excel : {excel_path}"
    )


# ============================================================
# COMPARAISON PRE / POST
# ============================================================

def compare_mode(
    settings: Settings,
    logger
):

    json_dir = (
        settings.output_dir
        / "json"
    )

    instance = safe_filename(
        settings.instance_name
    )

    # --------------------------------------------------------
    # Dernières baselines PRE et POST
    # --------------------------------------------------------

    pre_path = latest_file(
        json_dir,
        f"{instance}_PRE_*.json"
    )

    post_path = latest_file(
        json_dir,
        f"{instance}_POST_*.json"
    )

    if not pre_path:

        raise RuntimeError(
            "Aucune baseline PRE trouvée."
        )

    if not post_path:

        raise RuntimeError(
            "Aucune baseline POST trouvée."
        )

    # --------------------------------------------------------
    # Chargement JSON
    # --------------------------------------------------------

    pre = load_json(
        pre_path
    )

    post = load_json(
        post_path
    )

    # --------------------------------------------------------
    # Comparaison PRE / POST
    #
    # IMPORTANT :
    #
    # Le comparateur reçoit maintenant la cible Jira.
    #
    # Exemple :
    #
    # PRE    = 10.3.25
    # POST   = 10.3.25
    # TARGET = 11.3
    #
    # => FAIL
    #
    # PRE    = 10.3.25
    # POST   = 11.3.11
    # TARGET = 11.3
    #
    # => PASS
    #
    # Les autres valeurs censées rester stables sont comparées
    # indépendamment.
    # --------------------------------------------------------

    comparison = compare_baselines(
        pre=pre,
        post=post,
        target_family=(
            settings.target_jira_family
        ),
        target_version=(
            settings.target_jira_version
        )
    )

    # --------------------------------------------------------
    # Findings sur l'état POST
    # --------------------------------------------------------

    findings = analyze_baseline(
        post
    )

    # --------------------------------------------------------
    # Readiness POST
    #
    # Vérifie l'état du Jira POST par rapport à la cible.
    # --------------------------------------------------------

    readiness = analyze_readiness(
        post,
        settings
    )

    # --------------------------------------------------------
    # Rapport Excel
    # --------------------------------------------------------

    excel_dir = (
        settings.output_dir
        / "excel"
    )

    excel_path = (
        excel_dir
        / (
            f"{instance}_COMPARE_"
            f"{timestamp()}.xlsx"
        )
    )

    generate_excel_report(
        baseline=post,
        findings=findings,
        output_path=excel_path,
        comparison=comparison,
        readiness=readiness,
        target_family=(
            settings.target_jira_family
        ),
        target_version=(
            settings.target_jira_version
        )
    )

    # --------------------------------------------------------
    # Logs
    # --------------------------------------------------------

    logger.info(
        "Comparaison PRE : %s",
        pre_path
    )

    logger.info(
        "Comparaison POST : %s",
        post_path
    )

    logger.info(
        "Cible utilisée pour la comparaison : "
        "famille=%s version=%s",
        (
            settings.target_jira_family
            or "NON DEFINIE"
        ),
        (
            settings.target_jira_version
            or "PATCH NON DEFINI"
        )
    )

    logger.info(
        "Rapport : %s",
        excel_path
    )

    print()

    print(
        "Comparaison terminée."
    )

    print(
        f"PRE   : {pre_path}"
    )

    print(
        f"POST  : {post_path}"
    )

    print(
        "Cible : "
        f"{settings.target_jira_version or settings.target_jira_family or 'NON DEFINIE'}"
    )

    print(
        f"Excel : {excel_path}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Jira Upgrade Baseline Toolkit"
        )
    )

    parser.add_argument(
        "--mode",
        choices=[
            "pre",
            "post",
            "compare"
        ],
        required=True
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # Configuration
    # --------------------------------------------------------

    settings = Settings.from_env()

    # --------------------------------------------------------
    # Logs
    # --------------------------------------------------------

    configure_logging(
        settings.output_dir
        / "logs"
    )

    logger = get_logger(
        "JiraUpgradeBaselineToolkit"
    )

    logger.info(
        "Démarrage mode %s",
        args.mode.upper()
    )

    logger.info(
        "Cible Jira : famille=%s version=%s",
        (
            settings.target_jira_family
            or "NON DEFINIE"
        ),
        (
            settings.target_jira_version
            or "PATCH NON DEFINI"
        )
    )

    # --------------------------------------------------------
    # Mode PRE / POST
    # --------------------------------------------------------

    if args.mode in {
        "pre",
        "post"
    }:

        collect_mode(
            args.mode,
            settings,
            logger
        )

    # --------------------------------------------------------
    # Mode COMPARE
    # --------------------------------------------------------

    elif args.mode == "compare":

        compare_mode(
            settings,
            logger
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()