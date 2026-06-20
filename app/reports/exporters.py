from app.reports.generator import GeneratedReport


def export_report_markdown(report: GeneratedReport) -> str:
    lines = [
        f"# {report.title}",
        "",
    ]

    for section in report.sections:
        lines.extend(
            [
                f"## {section.title}",
                "",
                section.content,
                "",
            ]
        )

    return "\n".join(lines).strip() + "\n"
