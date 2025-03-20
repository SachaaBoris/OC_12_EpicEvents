import time
import keyboard
from rich.color import ANSI_COLOR_NAMES
from rich import print
from rich.console import Console
from rich.table import Table
from epicevents.config import ITEMS_PER_PAGE


console = Console()
VALID_RICH_COLORS = list(ANSI_COLOR_NAMES.keys())


def validate_rich_color(color=None):
    """Returns a rich valid color anyways"""
    valid_colors = VALID_RICH_COLORS if isinstance(VALID_RICH_COLORS, list) else ["white"]
    if not isinstance(color, str) or color not in valid_colors:
        return "white"
    return color


def display_list(title: str, items: list, use_context: bool = False):
    """Displays a list of records with pagination."""

    # See https://rich.readthedocs.io/en/stable/protocol.html?highlight=__rich__#console-customization

    items_per_page = ITEMS_PER_PAGE
    total_items = len(items)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    current_page = 1

    while current_page <= total_pages:
        start_index = (current_page - 1) * items_per_page
        end_index = min(start_index + items_per_page, total_items)
        page_items = items[start_index:end_index]
        title_str = title if total_pages <= 1 else f"{title} (Page {current_page}/{total_pages})"

        table = Table(
            title=title_str,
            padding=(0, 1),
            header_style="blue bold",
            title_style="purple bold",
            title_justify="center",
        )

        if not page_items:
            console.print(format_text('bold', 'red', "❌ Aucun élément à afficher."))
            return

        headers = list(page_items[0].keys())

        if "Contexte" in headers:
            headers.remove("Contexte")

        for header in headers:
            table.add_column(header, style="cyan", justify="center")

        for item in page_items:
            values = [str(item[key]) for key in headers]
            color = validate_rich_color(item.get("Contexte", "white"))
            style = color if use_context else "white"
            table.add_row(*values, style=style)

        console.print(table)

        if current_page < total_pages:
            console.print(format_text('bold', 'yellow', "Appuyez sur 'Backspace' pour continuer, 'Echap' pour quitter."))
            time.sleep(0.2)

            # Wait for user input
            while True:
                if keyboard.is_pressed('backspace'):
                    current_page += 1
                    time.sleep(0.2)
                    break
                elif keyboard.is_pressed('escape'):
                    time.sleep(0.2)
                    return
                time.sleep(0.1)
        else:
            current_page += 1


def format_text(style: str, color: str, text: str) -> None:
    """
    Formats text with a Rich style and color.

    Args:
        style (str): Text style ('bold', 'italic', 'underline', 'strike', or 'normal')
        color (str): Desired color
        text (str): Text to format

    Returns:
        str: Text formatted with Rich tags

    Examples:
        error_text = format_text('bold', 'red', '❌ Error: Invalid role.')
        confirm = Confirm.ask(format_text('bold', 'yellow', '⚠ Confirmation required'))
        italic_warning = format_text('italic', 'red', 'Warning')
        underlined_text = format_text('underline', 'green', 'Important')
        striked_text = format_text('strike', 'red', 'Deleted')
        normal_text = format_text('normal', 'blue', 'Normal text')
    """

    color = validate_rich_color(color)

    style_map = {
        'bold': 'bold',
        'italic': 'italic',
        'underline': 'underline',
        'strike': 'strike'
    }

    valid_style = style in style_map
    if style == 'normal' or not valid_style:
        return f"[{color}]{text}[/{color}]"

    style_tag = style_map[style]
    return f"[{style_tag} {color}]{text}[/{style_tag} {color}]"


def welcome_user():
    """Logo display when logging-in."""
    print("")
    print(format_text('bold', 'deep_sky_blue1', "                        ###"))
    print(format_text('bold', 'deep_sky_blue1', "                      ###"))
    print(format_text('bold', 'deep_sky_blue1', "       ################    ####"))
    print(format_text('bold', 'deep_sky_blue1', "       #          ###         #"))
    print(format_text('bold', 'deep_sky_blue1', "       #        ###           #"))
    print(format_text('bold', 'deep_sky_blue1', "       #      ###             #"))
    print(format_text('bold', 'deep_sky_blue1', "       #    ###      ###      #"))
    print(format_text('bold', 'deep_sky_blue1', "       #  ###      ###        #"))
    print(format_text('bold', 'deep_sky_blue1', "       #         ###     ###  #"))
    print(format_text('bold', 'deep_sky_blue1', "       #       ###     ###    #"))
    print(format_text('bold', 'deep_sky_blue1', "       #     ###     ###      #"))
    print(format_text('bold', 'deep_sky_blue1', "       #           ###        #"))
    print(format_text('bold', 'deep_sky_blue1', "       #         ###          #"))
    print(format_text('bold', 'deep_sky_blue1', "       #####   ################"))
    print(format_text('bold', 'deep_sky_blue1', "             ###"))
    print(format_text('bold', 'deep_sky_blue1', "           ###"))
    print("")
    print("        WELCOME TO EPICEVENTS")
    print("  Customer Relationship Management")
    print("")
