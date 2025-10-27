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
        html += f"<h3>📋 {filename}</h3>"
        html += "<table style='width:100%; border-collapse: collapse; margin-bottom: 20px;'>"
        html += """
        <tr style='background-color: #f0f0f0; border-bottom: 2px solid #ccc;'>
            <th style='padding: 8px; text-align: left;'>Extractor</th>
            <th style='padding: 8px; text-align: left;'>Time</th>
            <th style='padding: 8px; text-align: left;'>Chars / Words</th>
            <th style='padding: 8px; text-align: left;'>Status</th>
        </tr>
        """

        for extractor_name, result in extractors.items():
            status = "✓ OK" if not result.error else f"✗ Error"
            cost_str = f" (~${result.cost_estimate:.3f})" if result.cost_estimate else ""

            html += f"""
            <tr style='border-bottom: 1px solid #eee;'>
                <td style='padding: 8px;'>{result.extractor_name}</td>
                <td style='padding: 8px;'>{result.execution_time:.1f}s{cost_str}</td>
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
            html += f"<div style='color: red; padding: 10px; background: #fee; border-radius: 4px; margin-bottom: 20px;'>Error: {result.error}</div>"
            continue

        # Rendered markdown preview
        html += "<div style='margin: 10px 0;'>"
        html += "<strong>Rendered Markdown:</strong>"
        rendered_html = md.markdown(result.markdown, extensions=['extra', 'nl2br', 'sane_lists'])
        html += f"<div style='border: 1px solid #ddd; padding: 15px; background: white; border-radius: 4px; max-height: 400px; overflow-y: auto;'>{rendered_html}</div>"
        html += "</div>"

        # Raw markdown
        html += "<div style='margin: 10px 0;'>"
        html += "<strong>Raw Markdown:</strong>"
        html += f"<pre style='border: 1px solid #ddd; padding: 15px; background: #f5f5f5; border-radius: 4px; max-height: 300px; overflow-y: auto; white-space: pre-wrap;'>{result.markdown}</pre>"
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

    html = "<div style='font-family: system-ui, -apple-system, sans-serif;'>"
    html += f"<h3>📊 Side-by-Side Comparison - {filename}</h3>"

    # Create columns
    html += "<div style='display: flex; gap: 20px; overflow-x: auto;'>"

    for extractor_name, result in extractor_results.items():
        html += f"<div style='flex: 1; min-width: 400px; border: 1px solid #ddd; border-radius: 8px; padding: 15px;'>"
        html += f"<h4 style='margin-top: 0;'>{extractor_name}</h4>"

        if result.error:
            html += f"<div style='color: red; padding: 10px; background: #fee; border-radius: 4px;'>Error: {result.error}</div>"
        else:
            html += f"<div style='font-size: 0.9em; color: #666; margin-bottom: 10px;'>"
            html += f"Time: {result.execution_time:.1f}s | {result.word_count:,} words"
            if result.cost_estimate:
                html += f" | ~${result.cost_estimate:.3f}"
            html += "</div>"

            # Rendered preview
            markdown_preview = result.markdown[:2000] + ('...' if len(result.markdown) > 2000 else '')
            rendered_preview = md.markdown(markdown_preview, extensions=['extra', 'nl2br', 'sane_lists'])
            html += f"<div style='border: 1px solid #ddd; padding: 10px; background: white; border-radius: 4px; max-height: 500px; overflow-y: auto; font-size: 0.9em;'>{rendered_preview}</div>"

        html += "</div>"

    html += "</div>"
    html += "</div>"
    return html
