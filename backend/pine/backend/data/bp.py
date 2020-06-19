# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

from . import users

def init_app(app):
    app.cli.add_command(users.print_users_command)
    app.cli.add_command(users.set_user_password)
    app.cli.add_command(users.add_admin_command)
    app.cli.add_command(users.reset_user_passwords)

