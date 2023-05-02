"""
Plotly Dash HTML layout override.
If certain strategy needs a different layout, can apply here.
"""

html_layout = '''
<!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>Multi-Variate Index Regression</title>
            {%favicon%}
            {%css%}
        </head>
        <body class="dash-template">
            <header>
              <div class="nav-wrapper">
                <a href="/">
                    <h1>Multi-Variate Index Regression</h1>
                  </a>
                <nav>
                </nav>
            </div>
            </header>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
'''
