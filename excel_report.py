from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import (
    Font,
    PatternFill,
    Alignment,
    Border,
    Side,
)
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule

from compatibility_matrix import build_supported_platforms_rows


# ============================================================
# OUTILS
# ============================================================

def flatten_dict(
    data,
    prefix=""
):
    rows = []

    if isinstance(data, dict):

        for key, value in data.items():

            new_key = (
                f"{prefix}.{key}"
                if prefix
                else key
            )

            rows.extend(
                flatten_dict(
                    value,
                    new_key
                )
            )

    elif isinstance(data, list):

        if all(
            not isinstance(
                value,
                (dict, list)
            )
            for value in data
        ):

            rows.append(
                (
                    prefix,
                    ", ".join(
                        str(value)
                        for value in data
                    )
                )
            )

        else:

            for index, value in enumerate(data):

                rows.extend(
                    flatten_dict(
                        value,
                        f"{prefix}[{index}]"
                    )
                )

    else:

        rows.append(
            (
                prefix,
                data
            )
        )

    return rows


def safe_string(value):
    """
    Convertit une valeur en chaîne pour Excel.
    Retourne une chaîne vide pour None.
    """

    if value is None:
        return ""

    return str(value)


def count_inventoried_apps(baseline: dict) -> int:
    """
    Compte les applications inventoriées sans doublon entre :
    - thirdPartyApps
    - importantAtlassianApps
    """

    seen = set()

    for app_list_name in (
        "thirdPartyApps",
        "importantAtlassianApps"
    ):

        for app in baseline.get(
            app_list_name,
            []
        ) or []:

            if not isinstance(app, dict):
                continue

            key = (
                app.get("key")
                or app.get("name")
            )

            if key:
                seen.add(
                    str(key).strip().lower()
                )

    return len(seen)


# ============================================================
# GENERATION DU RAPPORT EXCEL
# ============================================================

def generate_excel_report(
    baseline: dict,
    findings: list,
    output_path: Path,
    comparison: list | None = None,
    readiness: list | None = None,
    target_family: str | None = None,
    target_version: str | None = None,
    app_compatibility: list | None = None
):

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    workbook = Workbook()

    # ========================================================
    # STYLES GENERAUX
    # ========================================================

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="1F4E78"
    )

    header_font = Font(
        bold=True,
        color="FFFFFF"
    )

    manual_fill = PatternFill(
        fill_type="solid",
        fgColor="FFF2CC"
    )

    thin_border = Border(
        left=Side(
            style="thin",
            color="D9E1F2"
        ),
        right=Side(
            style="thin",
            color="D9E1F2"
        ),
        top=Side(
            style="thin",
            color="D9E1F2"
        ),
        bottom=Side(
            style="thin",
            color="D9E1F2"
        )
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    ws = workbook.active
    ws.title = "Summary"

    ws["A1"] = "Jira Upgrade Baseline Toolkit"

    ws["A1"].font = Font(
        bold=True,
        size=16
    )

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

    source_version = jira.get(
        "version"
    )

    target_display = (
        target_version
        if target_version
        else (
            f"{target_family}.x"
            if target_family
            else "Non définie"
        )
    )

    architecture_display = (
        "Cluster"
        if architecture.get("clustered") is True
        else "Single node"
        if architecture.get("clustered") is False
        else "Non déterminée"
    )

    third_party_count = len(
        baseline.get(
            "thirdPartyApps",
            []
        ) or []
    )

    important_atlassian_count = len(
        baseline.get(
            "importantAtlassianApps",
            []
        ) or []
    )

    inventoried_apps_count = count_inventoried_apps(
        baseline
    )

    summary = [
        (
            "Instance",
            baseline.get(
                "instanceName",
                ""
            )
        ),
        (
            "Phase",
            baseline.get(
                "collectionPhase",
                ""
            )
        ),
        (
            "Jira Source",
            source_version
        ),
        (
            "Jira Cible",
            target_display
        ),
        (
            "Base URL",
            jira.get("baseUrl")
        ),
        (
            "Architecture",
            architecture_display
        ),
        (
            "Java Source",
            java.get("version")
        ),
        (
            "Database",
            database.get("type")
        ),
        (
            "Applications inventoriées",
            inventoried_apps_count
        ),
        (
            "Applications tierces",
            third_party_count
        ),
        (
            "Applications Atlassian suivies",
            important_atlassian_count
        )
    ]

    row = 3

    for label, value in summary:

        ws.cell(
            row=row,
            column=1,
            value=label
        ).font = Font(
            bold=True
        )

        ws.cell(
            row=row,
            column=2,
            value=value
        )

        row += 1

    # ========================================================
    # BASELINE
    # ========================================================

    ws_baseline = workbook.create_sheet(
        "Baseline"
    )

    ws_baseline.append(
        [
            "Property",
            "Value"
        ]
    )

    for cell in ws_baseline[1]:

        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(
            vertical="center",
            wrap_text=True
        )

    for key, value in flatten_dict(
        baseline
    ):

        ws_baseline.append(
            [
                key,
                safe_string(value)
            ]
        )

    ws_baseline.freeze_panes = "A2"
    ws_baseline.auto_filter.ref = (
        f"A1:B{ws_baseline.max_row}"
    )

    # ========================================================
    # FINDINGS
    # ========================================================

    ws_findings = workbook.create_sheet(
        "Findings"
    )

    ws_findings.append(
        [
            "Severity",
            "Domain",
            "Message"
        ]
    )

    for cell in ws_findings[1]:

        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(
            vertical="center",
            wrap_text=True
        )

    for item in findings:

        ws_findings.append(
            [
                item.get("severity"),
                item.get("domain"),
                item.get("message")
            ]
        )

    ws_findings.freeze_panes = "A2"
    ws_findings.auto_filter.ref = (
        f"A1:C{ws_findings.max_row}"
    )

    # ========================================================
    # READINESS
    # ========================================================

    if readiness is not None:

        ws_readiness = workbook.create_sheet(
            "Readiness"
        )

        readiness_headers = [
            "Status",
            "Domain",
            "Check",
            "Current Value",
            "Target / Expected",
            "Version / valeur retenue",
            "Lien / téléchargement / source",
            "Assessment Method",
            "Responsable",
            "Action Required",
            "Message"
        ]

        ws_readiness.append(
            readiness_headers
        )

        for cell in ws_readiness[1]:

            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(
                vertical="center",
                horizontal="center",
                wrap_text=True
            )
            cell.border = thin_border

        for item in readiness:

            current_value = item.get(
                "current_value"
            )

            target_expected = item.get(
                "target_expected",
                item.get("target_value")
            )

            selected_value = item.get(
                "selected_value",
                ""
            )

            link_url = (
                item.get("link_url")
                or item.get("download_url")
                or item.get("source_url")
                or item.get("url")
                or item.get("source")
                or ""
            )

            assessment_method = item.get(
                "assessment_method",
                ""
            )

            responsible = item.get(
                "responsible",
                ""
            )

            action_required = item.get(
                "action_required",
                ""
            )

            message = item.get(
                "message",
                ""
            )

            ws_readiness.append(
                [
                    item.get("status"),
                    item.get("domain"),
                    item.get("check"),
                    safe_string(current_value),
                    safe_string(target_expected),
                    safe_string(selected_value),
                    safe_string(link_url),
                    safe_string(assessment_method),
                    safe_string(responsible),
                    safe_string(action_required),
                    safe_string(message)
                ]
            )

            # Si une URL est déjà fournie par l'analyseur,
            # elle devient directement cliquable dans Excel.
            if link_url and str(link_url).lower().startswith(
                ("http://", "https://")
            ):
                link_cell = ws_readiness.cell(
                    row=ws_readiness.max_row,
                    column=7
                )
                link_cell.hyperlink = str(link_url)
                link_cell.font = Font(
                    color="0563C1",
                    underline="single"
                )

        for row_number in range(
            2,
            ws_readiness.max_row + 1
        ):

            # Colonnes prévues pour la saisie / décision projet :
            # F = Version / valeur retenue
            # G = Lien / téléchargement / source
            for column_number in (6, 7):
                manual_cell = ws_readiness.cell(
                    row=row_number,
                    column=column_number
                )
                manual_cell.fill = manual_fill

        status_validation = DataValidation(
            type="list",
            formula1=(
                '"PASS,WARNING,FAIL,'
                'NOT_ASSESSED,UNKNOWN,INFO,N/A"'
            ),
            allow_blank=True
        )

        status_validation.error = (
            "Sélectionner un statut valide."
        )

        status_validation.errorTitle = (
            "Statut invalide"
        )

        status_validation.prompt = (
            "Sélectionner le statut du contrôle."
        )

        status_validation.promptTitle = (
            "Readiness Status"
        )

        ws_readiness.add_data_validation(
            status_validation
        )

        status_validation.add(
            f"A2:A{max(ws_readiness.max_row, 2)}"
        )

        responsible_validation = DataValidation(
            type="list",
            formula1=(
                '"OUTIL,PILOTE JIRA,INFRA,DB,'
                'PILOTE JIRA + INFRA,PILOTE JIRA + DB,'
                'INFRA + DB,PILOTE JIRA + INFRA + DB"'
            ),
            allow_blank=True
        )

        responsible_validation.error = (
            "Sélectionner un responsable prévu par le modèle."
        )
        responsible_validation.errorTitle = (
            "Responsable invalide"
        )
        responsible_validation.prompt = (
            "Indique l'équipe qui doit traiter, renseigner ou valider le contrôle."
        )
        responsible_validation.promptTitle = (
            "Responsable Readiness"
        )

        ws_readiness.add_data_validation(
            responsible_validation
        )
        responsible_validation.add(
            f"I2:I{max(ws_readiness.max_row, 2)}"
        )

        # La couleur s'applique à TOUTE la ligne Readiness,
        # pas uniquement à la cellule Status.
        status_range = (
            f"A2:K{max(ws_readiness.max_row, 2)}"
        )

        # Couleurs de FOND des lignes Readiness.
        #
        # IMPORTANT : on ne colore plus le texte.
        # La couleur est appliquée au fond de TOUTES les cellules
        # de la ligne (A:K).
        status_styles = {
            "PASS": "C6EFCE",          # vert
            "FAIL": "FFC7CE",          # rouge
            "NOT_ASSESSED": "D9EAF7",  # bleu
            "UNKNOWN": "FCE4D6",       # orange
            "WARNING": "E4DFEC",       # violet
            "INFO": "EDEDED",          # gris clair
            "N/A": "F2F2F2"            # gris
        }

        # 1) Application directe du fond à la génération.
        # Cela garantit que les cellules sont réellement remplies,
        # même si Excel n'évalue pas immédiatement la mise en forme
        # conditionnelle à l'ouverture du fichier.
        for row_number in range(
            2,
            ws_readiness.max_row + 1
        ):

            status_value = ws_readiness.cell(
                row=row_number,
                column=1
            ).value

            background = status_styles.get(
                str(status_value).strip()
                if status_value is not None
                else ""
            )

            if background:

                row_fill = PatternFill(
                    fill_type="solid",
                    start_color=background,
                    end_color=background
                )

                for column_number in range(1, 12):

                    ws_readiness.cell(
                        row=row_number,
                        column=column_number
                    ).fill = row_fill

        # 2) Mise en forme conditionnelle conservée afin que la couleur
        # se mette également à jour si le Status est modifié manuellement
        # plus tard dans Excel.
        for status_name, background in status_styles.items():

            ws_readiness.conditional_formatting.add(
                status_range,
                FormulaRule(
                    formula=[
                        f'$A2="{status_name}"'
                    ],
                    fill=PatternFill(
                        fill_type="solid",
                        start_color=background,
                        end_color=background
                    )
                )
            )

        ws_readiness.freeze_panes = "A2"
        ws_readiness.auto_filter.ref = (
            f"A1:K{ws_readiness.max_row}"
        )

        ws_readiness.row_dimensions[
            1
        ].height = 32

        for row in ws_readiness.iter_rows(
            min_row=2,
            max_row=ws_readiness.max_row
        ):

            for cell in row:

                cell.alignment = Alignment(
                    vertical="top",
                    wrap_text=True
                )
                cell.border = thin_border

        readiness_column_widths = {
            "A": 18,
            "B": 20,
            "C": 36,
            "D": 34,
            "E": 50,
            "F": 34,
            "G": 48,
            "H": 22,
            "I": 30,
            "J": 42,
            "K": 55
        }

        for (
            column,
            width
        ) in readiness_column_widths.items():

            ws_readiness.column_dimensions[
                column
            ].width = width

    # ========================================================
    # APP COMPATIBILITY
    # ========================================================

    if app_compatibility is not None:

        ws_apps = workbook.create_sheet(
            "App Compatibility"
        )

        app_headers = [
            "Status",
            "App",
            "Plugin Key",
            "Current Version",
            "Current Version URL",
            "Source Jira",
            "Source Build",
            "Current Compatible Source",
            "Latest Source-Compatible Version",
            "Target Jira",
            "Target Build",
            "Current Compatible Target",
            "Bridge Version",
            "Bridge Version URL",
            "Bridge Download URL",
            "Target-only Version",
            "Target-only Version URL",
            "Target-only Download URL",
            "Strategy",
            "Action Required",
            "Message"
        ]

        ws_apps.append(
            app_headers
        )

        for cell in ws_apps[1]:

            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(
                vertical="center",
                horizontal="center",
                wrap_text=True
            )
            cell.border = thin_border

        for item in app_compatibility:

            ws_apps.append(
                [
                    item.get("status"),
                    item.get("app"),
                    item.get("plugin_key"),
                    item.get("current_version"),
                    item.get("current_version_url"),
                    item.get("source_jira"),
                    item.get("source_build"),
                    item.get("current_compatible_source"),
                    item.get("latest_source_compatible_version"),
                    item.get("target_jira"),
                    item.get("target_build"),
                    item.get("current_compatible_target"),
                    item.get("bridge_version"),
                    item.get("bridge_version_url"),
                    item.get("bridge_download_url"),
                    item.get("target_only_version"),
                    item.get("target_only_version_url"),
                    item.get("target_only_download_url"),
                    item.get("strategy"),
                    item.get("action_required"),
                    item.get("message")
                ]
            )

            # URLs cliquables :
            # E  = version actuelle
            # N  = version pont
            # O  = téléchargement pont
            # Q  = version target-only
            # R  = téléchargement target-only
            for column_number in (
                5,
                14,
                15,
                17,
                18
            ):

                link_cell = ws_apps.cell(
                    row=ws_apps.max_row,
                    column=column_number
                )

                link_value = link_cell.value

                if (
                    link_value
                    and str(link_value).lower().startswith(
                        ("http://", "https://")
                    )
                ):

                    link_cell.hyperlink = str(
                        link_value
                    )

                    link_cell.font = Font(
                        color="0563C1",
                        underline="single"
                    )

        ws_apps.freeze_panes = "A2"
        ws_apps.auto_filter.ref = (
            f"A1:U{ws_apps.max_row}"
        )

        ws_apps.row_dimensions[1].height = 34

        app_status_styles = {
            "PASS": "C6EFCE",
            "FAIL": "FFC7CE",
            "WARNING": "E4DFEC",
            "UNKNOWN": "FCE4D6",
            "NOT_ASSESSED": "D9EAF7",
            "INFO": "EDEDED",
            "N/A": "F2F2F2"
        }

        app_status_range = (
            f"A2:U{max(ws_apps.max_row, 2)}"
        )

        # Fond initial + mise en forme conditionnelle.
        for row_number in range(
            2,
            ws_apps.max_row + 1
        ):

            status_value = ws_apps.cell(
                row=row_number,
                column=1
            ).value

            background = app_status_styles.get(
                str(status_value).strip()
                if status_value is not None
                else ""
            )

            if background:

                row_fill = PatternFill(
                    fill_type="solid",
                    start_color=background,
                    end_color=background
                )

                for column_number in range(
                    1,
                    22
                ):

                    ws_apps.cell(
                        row=row_number,
                        column=column_number
                    ).fill = row_fill

        for status_name, background in (
            app_status_styles.items()
        ):

            ws_apps.conditional_formatting.add(
                app_status_range,
                FormulaRule(
                    formula=[
                        f'$A2="{status_name}"'
                    ],
                    fill=PatternFill(
                        fill_type="solid",
                        start_color=background,
                        end_color=background
                    )
                )
            )

        for row in ws_apps.iter_rows(
            min_row=2,
            max_row=ws_apps.max_row
        ):

            for cell in row:

                cell.alignment = Alignment(
                    vertical="top",
                    wrap_text=True
                )
                cell.border = thin_border

        app_column_widths = {
            "A": 14,
            "B": 34,
            "C": 48,
            "D": 18,
            "E": 52,
            "F": 16,
            "G": 16,
            "H": 24,
            "I": 28,
            "J": 16,
            "K": 16,
            "L": 24,
            "M": 18,
            "N": 52,
            "O": 52,
            "P": 20,
            "Q": 52,
            "R": 52,
            "S": 34,
            "T": 58,
            "U": 68
        }

        for (
            column,
            width
        ) in app_column_widths.items():

            ws_apps.column_dimensions[
                column
            ].width = width

    # ========================================================
    # SUPPORTED PLATFORMS
    #
    # Matrice de compatibilité de la branche Jira cible.
    # Ex : 11.3.11 -> matrice Jira 11.3
    # ========================================================

    supported_platforms_rows = (
        build_supported_platforms_rows(
            target_version
        )
        if target_version
        else []
    )

    ws_supported = workbook.create_sheet(
        "Supported Platforms"
    )

    supported_headers = [
        "Jira Target",
        "Category",
        "Technology",
        "Version",
        "Support Status",
        "Notes",
        "Source"
    ]

    ws_supported.append(
        supported_headers
    )

    for cell in ws_supported[1]:

        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(
            vertical="center",
            horizontal="center",
            wrap_text=True
        )
        cell.border = thin_border

    if supported_platforms_rows:

        for item in supported_platforms_rows:

            ws_supported.append(
                [
                    item.get("target_version"),
                    item.get("category"),
                    item.get("technology"),
                    item.get("version"),
                    item.get("support_status"),
                    item.get("notes"),
                    item.get("source")
                ]
            )

    else:

        ws_supported.append(
            [
                target_version or "Non définie",
                "",
                "",
                "",
                "NOT_ASSESSED",
                (
                    "Aucune matrice de plateformes supportées "
                    "n'est disponible pour la cible configurée."
                ),
                ""
            ]
        )

    ws_supported.freeze_panes = "A2"
    ws_supported.auto_filter.ref = (
        f"A1:G{ws_supported.max_row}"
    )

    supported_status_range = (
        f"E2:E{max(ws_supported.max_row, 2)}"
    )

    supported_status_styles = {
        "SUPPORTED": {
            "background": "C6EFCE",
            "font": "006100"
        },
        "TESTED": {
            "background": "D9EAF7",
            "font": "1F4E78"
        },
        "DEPRECATED": {
            "background": "FFEB9C",
            "font": "9C6500"
        },
        "UNSUPPORTED": {
            "background": "FFC7CE",
            "font": "9C0006"
        },
        "NOT_ASSESSED": {
            "background": "E7E6E6",
            "font": "595959"
        }
    }

    for (
        support_status,
        style
    ) in supported_status_styles.items():

        ws_supported.conditional_formatting.add(
            supported_status_range,
            FormulaRule(
                formula=[
                    f'$E2="{support_status}"'
                ],
                fill=PatternFill(
                    fill_type="solid",
                    fgColor=style[
                        "background"
                    ]
                ),
                font=Font(
                    color=style[
                        "font"
                    ],
                    bold=True
                )
            )
        )

    for row in ws_supported.iter_rows(
        min_row=2,
        max_row=ws_supported.max_row
    ):

        for cell in row:

            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True
            )
            cell.border = thin_border

    supported_column_widths = {
        "A": 16,
        "B": 18,
        "C": 32,
        "D": 18,
        "E": 20,
        "F": 60,
        "G": 70
    }

    for (
        column,
        width
    ) in supported_column_widths.items():

        ws_supported.column_dimensions[
            column
        ].width = width

    # ========================================================
    # PRE / POST
    # ========================================================

    if comparison is not None:

        ws_compare = workbook.create_sheet(
            "PRE_POST"
        )

        ws_compare.append(
            [
                "Domain",
                "Field",
                "PRE",
                "POST",
                "Status"
            ]
        )

        for cell in ws_compare[1]:

            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(
                vertical="center",
                wrap_text=True
            )

        for item in comparison:

            ws_compare.append(
                [
                    item.get("domain"),
                    item.get("field"),
                    safe_string(
                        item.get("pre")
                    ),
                    safe_string(
                        item.get("post")
                    ),
                    item.get("status")
                ]
            )

        ws_compare.freeze_panes = "A2"
        ws_compare.auto_filter.ref = (
            f"A1:E{ws_compare.max_row}"
        )

    # ========================================================
    # LARGEUR AUTOMATIQUE DES AUTRES ONGLETS
    # ========================================================

    sheets_with_custom_widths = {
        "Readiness",
        "App Compatibility",
        "Supported Platforms"
    }

    for sheet in workbook.worksheets:

        if sheet.title in sheets_with_custom_widths:
            continue

        for column in sheet.columns:

            max_length = 0

            column_letter = (
                column[0].column_letter
            )

            for cell in column:

                value = cell.value

                if value is not None:

                    max_length = max(
                        max_length,
                        len(
                            str(value)
                        )
                    )

            sheet.column_dimensions[
                column_letter
            ].width = min(
                max_length + 2,
                80
            )

    # ========================================================
    # ALIGNEMENT GENERAL
    # ========================================================

    for sheet in workbook.worksheets:

        for row in sheet.iter_rows():

            for cell in row:

                if cell.row == 1:
                    continue

                if sheet.title not in (
                    "Readiness",
                    "App Compatibility",
                    "Supported Platforms"
                ):

                    cell.alignment = Alignment(
                        vertical="top",
                        wrap_text=True
                    )

    # ========================================================
    # SAUVEGARDE
    # ========================================================

    workbook.save(
        output_path
    )

    return output_path
