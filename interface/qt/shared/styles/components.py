"""Component-specific style definitions"""

from .colors import COLORS

# Metadata panel styles
METADATA_PANEL_STYLE = f"""
    QWidget {{
        background-color: {COLORS['background']};
        color: {COLORS['text']};
    }}
    QLabel {{
        color: {COLORS['text']};
    }}
    QLineEdit, QTextEdit {{
        background-color: {COLORS['secondary']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        padding: 4px;
    }}
"""

# Information panel styles
INFO_PANEL_STYLE = """
    QTextBrowser {
        background-color: #2d2d2d;
        color: #ffffff;
        border: none;
        font-family: 'Segoe UI', Arial, sans-serif;
        padding: 0;
        margin: 0;
    }
"""

# HTML template for metadata display
METADATA_HTML_TEMPLATE = """
<style>
    body { background-color: %(bg)s; color: %(text)s; padding: 10px; }
    .label { color: %(secondary)s; }
    .value { color: %(text)s; }
    .section { margin-bottom: 10px; }
</style>
<div class="metadata">
    %(content)s
</div>
"""

# HTML template for information display
INFO_HTML_TEMPLATE = """
    <style type="text/css">
        body {
            background-color: #2d2d2d;
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 10px;
        }
        .container {
            max-width: 100%;
        }
        .section {
            background-color: #363636;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 15px;
        }
        h2 {
            color: #0078d4;
            font-size: 16px;
            margin: 0 0 10px 0;
        }
        .info-grid {
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 5px 10px;
        }
        .info-label {
            color: #888888;
            font-weight: bold;
        }
        .info-value {
            color: #ffffff;
        }
        pre {
            background-color: #2d2d2d;
            padding: 5px;
            border-radius: 3px;
            margin: 0;
            white-space: pre-wrap;
            font-family: 'Consolas', monospace;
        }
    </style>
"""

__all__ = [
    'METADATA_PANEL_STYLE',
    'INFO_PANEL_STYLE',
    'METADATA_HTML_TEMPLATE',
    'INFO_HTML_TEMPLATE'
] 