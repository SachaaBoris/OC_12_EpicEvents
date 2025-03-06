import pytest
import typer
import sys
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from epicevents.__main__ import app


@pytest.fixture
def runner():
    return CliRunner()


@patch('epicevents.__main__.app')
def test_main_app_invocation(mock_app):
    """Test que le point d'entrée appelle l'application Typer"""
    from epicevents.__main__ import main
    
    main()  # Exécution de la fonction main
    
    # Vérifie que app() est appelée avec les bons paramètres
    mock_app.assert_called_once_with(obj={})


def test_main_command_help(runner):
    """Test de la commande d'aide"""
    # Importer l'application depuis le module __main__
    from epicevents.__main__ import app

    # Exécuter la commande avec --help
    result = runner.invoke(app, ["--help"])
    
    # Vérifier que la commande a réussi et affiche l'aide
    assert result.exit_code == 0
    assert "Usage" in result.output
    assert "Options" in result.output


@patch('epicevents.__main__.typer.Typer')
def test_main_app_structure(mock_typer_class):
    """Test que l'application principale est correctement structurée"""
    # Réinitialiser le module pour forcer une nouvelle importation
    if 'epicevents.__main__' in sys.modules:
        del sys.modules['epicevents.__main__']
    
    # Importer le module pour déclencher sa configuration
    import epicevents.__main__
    
    # Vérifier que typer.Typer a été appelé
    mock_typer_class.assert_called_once()  # Vérifie que Typer() est appelé une fois
    
    # Récupérer l'instance de l'application Typer
    mock_app = mock_typer_class.return_value
    
    # Vérifier que les sous-commandes ont été ajoutées
    assert mock_app.add_typer.call_count >= 4  # au moins users, customers, contracts, events


@patch('epicevents.permissions.auth.check_auth')
def test_main_token_debug_command(mock_check_auth):
    """Test de la commande token-debug sans utilisateur connecté"""

    runner = CliRunner()  # Ensure CliRunner is used for Typer

    # Simuler une authentification échouée (utilisateur non connecté)
    mock_check_auth.side_effect = typer.Exit(1)

    # Exécuter la commande via la sous-commande "util"
    result = runner.invoke(app, ["util", "debug_token"])

    # Vérifier que la commande a échoué avec le bon message
    assert "❌ Vous devez être connecté pour exécuter cette commande." in result.output


@patch('epicevents.__main__.check_auth')
def test_main_perms_debug_command(mock_check_auth):
    """Test de la commande debug_permissions"""

    runner = CliRunner()  # Ensure CliRunner is used for Typer

    # Simuler une authentification échouée (utilisateur non connecté)
    mock_check_auth.side_effect = typer.Exit(1)

    # Exécuter la commande via la sous-commande "util"
    result = runner.invoke(app, ["util", "debug_permissions"])

    # Vérifier que la commande a échoué avec le bon message
    assert "❌ Vous devez être connecté pour exécuter cette commande." in result.output


@patch('epicevents.__main__.check_auth')
def test_main_comlist_debug_command(mock_check_auth):
    """Test de la commande debug_commands"""

    runner = CliRunner()  # Ensure CliRunner is used for Typer

    # Simuler une authentification échouée (utilisateur non connecté)
    mock_check_auth.side_effect = typer.Exit(1)

    # Exécuter la commande via la sous-commande "util"
    result = runner.invoke(app, ["util", "debug_commands"])

    # Vérifier que la commande a échoué avec le bon message
    assert "❌ Vous devez être connecté pour exécuter cette commande." in result.output
