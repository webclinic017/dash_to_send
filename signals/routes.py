"""Routes for parent Flask app."""
from flask import current_app as app
from flask import flash, redirect, render_template, request, session, url_for
from flask_login import login_required, login_user, logout_user

from signals.users import User


@app.route('/')
@login_required
def home():
    """Landing page."""
    return render_template(
        'index.jinja2',
        title='BlueCrest Signal Dashboards',
        description='Signal monitoring links',
        template='home-template',
        body=""
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['password'] == '123456':
            session['username'] = 'admin'
            login_user(User('admin'))
            flash('Logged in successfully.')
            return redirect(url_for('home'))
        else:
            error = 'Wrong password.'
    return render_template('login.jinja2', error=error)


@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    logout_user()
    session.pop('username', None)
    flash('Logged out successfully.')
    return redirect(url_for('home'))
