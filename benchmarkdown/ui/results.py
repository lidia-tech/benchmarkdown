"""
Results viewing and comparison functions for the Benchmarkdown UI.
"""

import markdown as md


def generate_results_table(results: dict) -> str:
    """Generate HTML table of results.

    Args:
        results: Dictionary mapping filename to extractor results

    Returns:
        HTML string with results table
    """
    if not results:
        return "<p>No results yet. Upload documents and click 'Run Extraction' to begin.</p>"

    html = "<div style='font-family: monospace;'>"

    for filename, extractors in results.items():
        # Get page count from first result (all results for same file have same page count)
        page_count = None
        for result in extractors.values():
            if result.page_count:
                page_count = result.page_count
                break

        page_info = f" ({page_count} pages)" if page_count else ""
        html += f"<h3>📋 {filename}{page_info}</h3>"
        html += "<table style='width:100%; border-collapse: collapse; margin-bottom: 20px;'>"
        html += """
        <tr style='background: var(--background-fill-secondary); border-bottom: 2px solid var(--border-color-primary); color: var(--body-text-color);'>
            <th style='padding: 8px; text-align: left;'>Extractor</th>
            <th style='padding: 8px; text-align: left;'>Time</th>
            <th style='padding: 8px; text-align: left;'>Sec/Page</th>
            <th style='padding: 8px; text-align: left;'>Chars / Words</th>
            <th style='padding: 8px; text-align: left;'>Status</th>
        </tr>
        """

        for extractor_name, result in extractors.items():
            status = "✓ OK" if not result.error else f"✗ Error"
            cost_str = f" (~${result.cost_estimate:.3f})" if result.cost_estimate else ""

            # Calculate seconds per page
            sec_per_page = ""
            if result.page_count and result.page_count > 0 and not result.error:
                sec_per_page = f"{result.execution_time / result.page_count:.2f}"

            html += f"""
            <tr style='border-bottom: 1px solid var(--border-color-primary); color: var(--body-text-color);'>
                <td style='padding: 8px;'>{result.extractor_name}</td>
                <td style='padding: 8px;'>{result.execution_time:.1f}s{cost_str}</td>
                <td style='padding: 8px;'>{sec_per_page}</td>
                <td style='padding: 8px;'>{result.character_count:,} / {result.word_count:,}</td>
                <td style='padding: 8px;'>{status}</td>
            </tr>
            """

        html += "</table>"

    html += "</div>"
    return html


def generate_comparison_view_tabbed(results: dict, filename: str) -> str:
    """Generate tabbed comparison view for a specific document.

    Args:
        results: Dictionary mapping filename to extractor results
        filename: The filename to generate comparison for

    Returns:
        HTML string with tabbed comparison view
    """
    if filename not in results:
        return "<p>No results for this document.</p>"

    extractor_results = results[filename]

    # Create tabs for each extractor
    html = "<div style='font-family: system-ui, -apple-system, sans-serif;'>"
    html += f"<h3>📊 Extraction Comparison - {filename}</h3>"

    for extractor_name, result in extractor_results.items():
        html += f"<h4>{extractor_name}</h4>"

        if result.error:
            html += f"<div style='color: var(--error-text-color, #dc2626); padding: 10px; background: var(--error-background-fill, rgba(239, 68, 68, 0.1)); border: 1px solid var(--error-border-color, rgba(239, 68, 68, 0.3)); border-radius: 4px; margin-bottom: 20px;'>Error: {result.error}</div>"
            continue

        # Rendered markdown preview
        html += "<div style='margin: 10px 0;'>"
        html += "<strong>Rendered Markdown:</strong>"
        rendered_html = md.markdown(result.markdown, extensions=['extra', 'nl2br', 'sane_lists'])
        html += f"<div style='border: 1px solid var(--border-color-primary); padding: 15px; background: var(--background-fill-primary); color: var(--body-text-color); border-radius: 4px; max-height: 400px; overflow-y: auto;'>{rendered_html}</div>"
        html += "</div>"

        # Raw markdown
        html += "<div style='margin: 10px 0;'>"
        html += "<strong>Raw Markdown:</strong>"
        html += f"<pre style='border: 1px solid var(--border-color-primary); padding: 15px; background: var(--background-fill-secondary); color: var(--body-text-color); border-radius: 4px; max-height: 300px; overflow-y: auto; white-space: pre-wrap;'>{result.markdown}</pre>"
        html += "</div>"

        if result.warnings:
            html += "<div style='margin: 10px 0;'>"
            html += "<strong>⚠️ Warnings:</strong>"
            html += "<ul>"
            for warning in result.warnings:
                html += f"<li>{warning}</li>"
            html += "</ul>"
            html += "</div>"

        html += "<hr style='margin: 30px 0;'>"

    html += "</div>"
    return html


def generate_comparison_view_sidebyside(results: dict, filename: str) -> str:
    """Generate side-by-side comparison view for a specific document.

    Args:
        results: Dictionary mapping filename to extractor results
        filename: The filename to generate comparison for

    Returns:
        HTML string with side-by-side comparison view
    """
    if filename not in results:
        return "<p>No results for this document.</p>"

    extractor_results = results[filename]

    # Get page count from first result
    page_count = None
    for result in extractor_results.values():
        if result.page_count:
            page_count = result.page_count
            break

    html = "<div style='font-family: system-ui, -apple-system, sans-serif;'>"
    page_info = f" ({page_count} pages)" if page_count else ""
    html += f"<h3>📊 Side-by-Side Comparison - {filename}{page_info}</h3>"

    # Create columns
    html += "<div style='display: flex; gap: 20px; overflow-x: auto;'>"

    for extractor_name, result in extractor_results.items():
        html += f"<div style='flex: 1; min-width: 400px; border: 1px solid var(--border-color-primary); border-radius: 8px; padding: 15px;'>"
        html += f"<h4 style='margin-top: 0;'>{extractor_name}</h4>"

        if result.error:
            html += f"<div style='color: var(--error-text-color, #dc2626); padding: 10px; background: var(--error-background-fill, rgba(239, 68, 68, 0.1)); border: 1px solid var(--error-border-color, rgba(239, 68, 68, 0.3)); border-radius: 4px;'>Error: {result.error}</div>"
        else:
            html += f"<div style='font-size: 0.9em; color: var(--body-text-color-subdued, #666); margin-bottom: 10px;'>"
            html += f"Time: {result.execution_time:.1f}s"

            # Add sec/page if available
            if result.page_count and result.page_count > 0:
                sec_per_page = result.execution_time / result.page_count
                html += f" ({sec_per_page:.2f}s/page)"

            html += f" | {result.word_count:,} words"
            if result.cost_estimate:
                html += f" | ~${result.cost_estimate:.3f}"
            html += "</div>"

            # Rendered preview
            markdown_preview = result.markdown[:2000] + ('...' if len(result.markdown) > 2000 else '')
            rendered_preview = md.markdown(markdown_preview, extensions=['extra', 'nl2br', 'sane_lists'])
            html += f"<div style='border: 1px solid var(--border-color-primary); padding: 10px; background: var(--background-fill-primary); color: var(--body-text-color); border-radius: 4px; max-height: 500px; overflow-y: auto; font-size: 0.9em;'>{rendered_preview}</div>"

        html += "</div>"

    html += "</div>"
    html += "</div>"
    return html
