"""Initialize Flask app."""
from flask import Flask
from flask_assets import Environment
from flask_login import LoginManager, login_required
from config import Config
from signals.users import User


def init_app():
    """Construct core Flask application with embedded Dash app."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config)
    assets = Environment()
    assets.init_app(app)

    with app.app_context():
        # Import parts of our core Flask app
        from signals import routes
        from signals.assets import compile_static_assets

        # Import and initialize each Dash applications
        from signals.strategies.pair_trading import dashboard as signal1
        from signals.strategies.index_regression import dashboard as signal2
        app = signal1.init_dashboard(app)
        app = signal2.init_dashboard(app)

        # Commenting this part for interviewer to run it easily, one simpley way of demo auth is using these two funcs
        # with password etc. details in routes.py
        # Set up auths
        # app = configure_auth(app)
        # app = protect_dash_views(app)

        app.config['LOGIN_DISABLED'] = True

        # Compile static assets
        compile_static_assets(assets)

        return app


def configure_auth(app):
    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User(user_id)

    return app


def protect_dash_views(app):
    for view_func in app.view_functions:
        if view_func.startswith(r'/'):
            app.view_functions[view_func] = login_required(app.view_functions[view_func])
    return app
