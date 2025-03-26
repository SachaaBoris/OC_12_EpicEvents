import typer
from rich.console import Console
from datetime import datetime
from epicevents.permissions.auth import verify_token
from epicevents.permissions.perm import get_all_permissions
from epicevents.cli.utils import display_list
from epicevents.cli.utils import format_text

app = typer.Typer(help="Fonctions de debug (admin)")
console = Console()


@app.command("token")
def debug_token():
    """Displays token validity."""
    payload = verify_token()
    if payload is not None:
        exp_timestamp = payload['exp']
        exp_datetime = datetime.fromtimestamp(exp_timestamp).strftime('%d/%m/%y %H:%M')
        remaining_time = exp_timestamp - datetime.now().timestamp()
        if remaining_time > 0:
            hours, remainder = divmod(remaining_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            remaining_time_str = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        else:
            remaining_time_str = "Le token vient d'expirer."

        console.print(
            format_text('bold', 'blue', f"⏳ Token expire le : {exp_datetime} - Temps restant : {remaining_time_str}")
        )


@app.command("permissions")
def debug_permissions():
    """Displays all permissions."""
    all_permissions = get_all_permissions()
    display_list(title="Permissions disponibles", items=all_permissions)


def list_all_commands():
    """Lists all available CLI commands and subcommands in the Epicevents CLI."""
    from epicevents.cli.customers import app as customers_app
    from epicevents.cli.contracts import app as contracts_app
    from epicevents.cli.events import app as events_app
    from epicevents.cli.users import app as users_app

    command_groups = {}

    # Adding sub-comands to main groups
    customers_commands = [c.name for c in customers_app.registered_commands]
    contracts_commands = [c.name for c in contracts_app.registered_commands]
    events_commands = [c.name for c in events_app.registered_commands]
    users_commands = [c.name for c in users_app.registered_commands]
    debug_commands = [c.name for c in app.registered_commands]

    command_groups["customer"] = customers_commands
    command_groups["contract"] = contracts_commands
    command_groups["event"] = events_commands
    command_groups["user"] = users_commands
    command_groups["debug"] = debug_commands

    return command_groups


def print_command_list(user_role, filtered_command_groups):
    # Computing max table lines
    max_subcommands = max((len(subs) for subs in filtered_command_groups.values()), default=0)

    # Formatting data
    formatted_list = []
    for i in range(max_subcommands):
        row = {}
        for group in ["user", "customer", "contract", "event", "debug"]:
            commands = filtered_command_groups.get(group, [])
            row[group] = commands[i] if i < len(commands) else ""
        formatted_list.append(row)

    display_list(f"Liste des commandes ({user_role})", formatted_list)


def role_commands_filter(role: str, command_groups: dict) -> dict:
    """Filtering commands givern user role's permissions."""
    from epicevents.permissions.perm import ROLES_PERMISSIONS

    # Retrieve role's permissions
    role_permissions = ROLES_PERMISSIONS.get(role, {})

    # filtered commands dictionnary
    filtered_command_groups = {}

    # Browse all groups
    for group_name, commands in command_groups.items():
        filtered_commands = []

        # Browse group sub-commands
        for command in commands:
            # Check if command is allowed
            if group_name in role_permissions and command in role_permissions[group_name]:
                permission = role_permissions[group_name][command]

                # Adding custom permissions annotations
                if permission.__name__ == "is_self":
                    command += " (is self)"
                elif permission.__name__ == "is_owner":
                    command += " (is owner)"
                elif permission.__name__ == "is_my_customer":
                    command += " (is my customer)"

                # Add command to group list
                filtered_commands.append(command)

        # Add group to final dict
        if filtered_commands:
            filtered_command_groups[group_name] = filtered_commands

    return filtered_command_groups


@app.command("commands")
def list_commands(ctx: typer.Context):
    from epicevents.models.user import User

    # Get the user from the context
    user = User.get_or_none(User.id == ctx.obj)
    if not user:
        console.print(format_text('bold', 'red', "❌ Utilisateur introuvable."))
        raise typer.Exit(1)

    # Get the role from the user
    user_role = user.role.name

    # Get all command groups
    command_groups = list_all_commands()

    if user_role == "admin":
        # Admin doesn't need a filter
        print_command_list(user_role, command_groups)
    else:
        # Filter command groups based on the user's role
        filtered_command_groups = role_commands_filter(user_role, command_groups)
        print_command_list(user_role, filtered_command_groups)

@app.command("sentry")
def sentry_error():
    """Simple error test sent to sentry."""
    #  division_by_zero = 1 / 0
    raise RuntimeError("Erreur test envoyée à Sentry")