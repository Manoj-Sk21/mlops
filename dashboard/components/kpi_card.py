import streamlit as st

def render_kpi_card(title, value, delta=None, delta_color='normal', icon=None, border_color='#4ECDC4'):
    """Render a custom styled KPI metric card."""
    icon_html = f'<span style="font-size:1.5rem;margin-right:8px;">{icon}</span>' if icon else ''
    
    delta_html = ''
    if delta is not None:
        symbol = ''
        color_class = 'neutral'
        try:
            val = float(str(delta).replace('%','').replace(',','').replace('+',''))
            if delta_color == 'normal':
                if val < 0:
                    color_class = 'negative'
                elif val > 0:
                    color_class = 'positive'
                    symbol = '+'
            elif delta_color == 'inverse':
                if val < 0:
                    color_class = 'positive'
                elif val > 0:
                    color_class = 'negative'
                    symbol = '+'
        except (ValueError, TypeError):
            pass
        delta_html = f'<div class="kpi-delta {color_class}">{symbol}{delta}</div>'
    
    html = f"""
    <div class="kpi-card" style="border-left:5px solid {border_color};">
        <div class="kpi-title">{icon_html}{title}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_kpi_row(kpis):
    """Render a row of KPI cards.
    
    Args:
        kpis: list of dicts with keys: title, value, delta (opt), icon (opt), border_color (opt)
    """
    cols = st.columns(len(kpis))
    for col, kpi in zip(cols, kpis):
        with col:
            render_kpi_card(
                title=kpi.get('title', ''),
                value=kpi.get('value', '—'),
                delta=kpi.get('delta'),
                delta_color=kpi.get('delta_color', 'normal'),
                icon=kpi.get('icon'),
                border_color=kpi.get('border_color', '#4ECDC4'),
            )
