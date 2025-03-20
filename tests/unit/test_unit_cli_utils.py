import pytest
from epicevents.cli.utils import welcome_user
from epicevents.cli.utils import display_list
from epicevents.cli.utils import format_text


def test_format_text_color_fallback():
    result = format_text("bold", "invalid_color", "Test")
    assert "white" in result

def test_display_list_pagination(monkeypatch):
    items = [{"ID": i, "Name": f"Item {i}"} for i in range(10)]
    
    # Simule l'appui sur Echap
    monkeypatch.setattr(
        'epicevents.cli.utils.keyboard.is_pressed', 
        lambda key: key == 'escape'
    )
    
    display_list("Test Pagination", items)

def test_welcome_user(capsys):
    """Test de la fonction welcome_user en capturant la sortie"""
    welcome_user()
    
    # Capturer la sortie
    captured = capsys.readouterr()
    
    # Vérifier que le texte attendu est bien présent dans la sortie
    assert "WELCOME TO EPICEVENTS" in captured.out
