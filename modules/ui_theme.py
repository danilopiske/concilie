# modules/ui_theme.py
import panel as pn

# 🎨 Vudovn Aesthetic Tokens (Concilie 2.0)
# Based on frontend-specialist & streamlit-specialist guidelines

CSS_THEME = """
/* Global Typography & Density (Kombai Standard) */
:root {
    --v-font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --v-bg-color: #0d1117;
    --v-card-bg: rgba(22, 27, 34, 0.7);
    --v-accent-color: #0366d6; /* Premium GitHub Blue */
    --v-border-color: rgba(240, 246, 252, 0.1);
}

body {
    font-family: var(--v-font-family) !important;
    font-size: 14px !important;
    background-color: var(--v-bg-color) !important;
    color: #c9d1d9 !important;
}

/* Glassmorphism Cards */
.bk-panel-models-layout-Card, .glass-card {
    background: var(--v-card-bg) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid var(--v-border-color) !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
    padding: 1.5rem !important;
}

.premium-header {
    font-size: 28px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    margin-bottom: 20px !important;
    letter-spacing: -0.02em !important;
}

/* Tabulator Styling */
.tabulator {
    background-color: transparent !important;
    border: none !important;
    font-size: 13px !important;
}

.tabulator-header {
    background-color: rgba(255, 255, 255, 0.05) !important;
    color: #8b949e !important;
    border-bottom: 2px solid var(--v-border-color) !important;
}

.tabulator-row {
    background-color: transparent !important;
    border-bottom: 1px solid var(--v-border-color) !important;
}

.tabulator-row:hover {
    background-color: rgba(255, 255, 255, 0.03) !important;
}

/* Custom Metric Style */
.metric-container {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
}

.metric-label {
    font-size: 12px;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.metric-value {
    font-size: 24px;
    font-weight: 600;
    color: #ffffff;
    margin-top: 4px;
}

/* Buttons */
.bk-btn-primary {
    background-color: var(--v-accent-color) !important;
    border-color: var(--v-accent-color) !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
}

.bk-btn-primary:hover {
    background-color: #2ea043 !important;
}

/* Sidebar Styling */
#sidebar {
    background-color: #010409 !important;
    border-right: 1px solid var(--v-border-color) !important;
}
"""

def apply_template_patch(template):
    \"\"\"Applies custom CSS and configurations to the Panel template.\"\"\"
    if hasattr(template, 'config'):
        template.config.raw_css.append(CSS_THEME)
    else:
        # Fallback for older versions or explicit injection
        pn.config.raw_css.append(CSS_THEME)
    
    # Modern font injection via HTML
    font_link = '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">'
    template.main.append(pn.pane.HTML(font_link, height=0, width=0))

def create_glass_card(content, title=None, **kwargs):
    \"\"\"Creates a premium glassmorphic card.\"\"\"
    return pn.Card(
        content,
        title=title,
        css_classes=['glass-card'],
        header_background='transparent',
        active_header_background='transparent',
        collapsible=False,
        **kwargs
    )

def premium_metric(label, value, prefix="", suffix="", color=None):
    \"\"\"Renders a high-fidelity metric component.\"\"\"
    val_style = f"color: {color};" if color else ""
    html = f\"\"\"
    <div class="metric-container">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="{val_style}">{prefix}{value}{suffix}</div>
    </div>
    \"\"\"
    return pn.pane.HTML(html, sizing_mode="stretch_width")
