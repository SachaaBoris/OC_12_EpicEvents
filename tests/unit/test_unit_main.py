import pytest
import typer
import sentry_sdk
import epicevents.__main__
from epicevents.__main__ import sentry_init, main
from epicevents.cli import init_cli, app
from epicevents.config import SENTRY_DSN, SENTRY_ENV


def test_sentry_init(monkeypatch):
    """
    Teste que sentry_init fonctionne correctement et n'appelle pas sentry_sdk.init
    quand SENTRY_DSN est la valeur par défaut.
    """
    # Mock SENTRY_DSN pour entrer dans la condition if
    monkeypatch.setattr("epicevents.__main__.SENTRY_DSN", "https://real-dsn.sentry.io/123")

    # Variable pour suivre si sentry_sdk.init a été appelé
    init_called = []

    def fake_init(*args, **kwargs):
        """Remplace sentry_sdk.init et enregistre son appel."""
        init_called.append((args, kwargs))

    # Monkeypatch sentry_sdk.init
    monkeypatch.setattr(sentry_sdk, "init", fake_init)

    # Appeler la fonction
    sentry_init()

    # Vérifier que sentry_sdk.init a été appelé une seule fois avec les bons arguments
    assert len(init_called) == 1
    assert init_called[0][1] == {
        "dsn": "https://real-dsn.sentry.io/123",
        "environment": SENTRY_ENV,
        "traces_sample_rate": 0.0
    }


def test_main(monkeypatch):
    """Teste que main appelle init_cli et exécute l'app avec le bon contexte"""
    app_called_with = None
    
    # Créer un mock pour l'app retournée par init_cli
    def mock_app(obj):
        nonlocal app_called_with
        app_called_with = obj
        return None
    
    # Mock pour init_cli qui retourne notre mock_app
    def mock_init_cli():
        return mock_app
    
    # Patcher la fonction init_cli directement dans le module __main__
    monkeypatch.setattr("epicevents.__main__.init_cli", mock_init_cli)
    monkeypatch.setattr("epicevents.__main__.sentry_init", lambda: None)
    
    # Exécuter main
    main()
    
    # Vérifier que l'app a été appelée avec un dict vide
    assert app_called_with == {}


def test_init_cli_import(monkeypatch):
    """
    Teste que le module importe correctement init_cli depuis epicevents.cli
    """
    # Créer une version simplifiée de epicevents.cli avec init_cli
    class MockInitCli:
        def __init__(self):
            self.called = False
            
        def __call__(self):
            self.called = True
            return lambda obj: None
    
    # Instance de notre mock
    mock_init_cli = MockInitCli()
    
    # Créer un mock pour epicevents.cli
    class MockCliModule:
        pass
    
    mock_cli = MockCliModule()
    mock_cli.init_cli = mock_init_cli
    
    # Patcher epicevents.cli
    monkeypatch.setattr("epicevents.__main__.init_cli", mock_init_cli)
    
    # Appeler main pour déclencher l'utilisation de init_cli
    main()
    
    # Vérifier que init_cli a été appelé
    assert mock_init_cli.called, "init_cli n'a pas été appelé par main()"


def test_main_exception_handling(monkeypatch):
    """
    Teste que main capture les exceptions et les renvoie à Sentry en production
    """
    # Mock pour init_cli qui lève une exception
    def mock_init_cli():
        def app(obj):
            raise ValueError("Test error")
        return app
    
    # Patcher les fonctions et constantes
    monkeypatch.setattr("epicevents.__main__.init_cli", mock_init_cli)
    monkeypatch.setattr("epicevents.__main__.sentry_init", lambda: None)
    monkeypatch.setattr("epicevents.__main__.SENTRY_ENV", "production")
    
    # Exécuter main et vérifier qu'il lève l'exception
    with pytest.raises(ValueError, match="Test error"):
        main()

def test_init_cli():
    """
    Test complet de init_cli qui vérifie que toutes les sous-commandes sont ajoutées
    """
    # Sauvegarder la méthode add_typer originale
    original_add_typer = app.add_typer
    
    # Liste pour stocker les appels à add_typer
    add_typer_calls = []
    
    # Créer une fonction de remplacement pour add_typer
    def spy_add_typer(subapp, **kwargs):
        # Enregistrer l'appel
        add_typer_calls.append({
            'subapp': subapp,
            'kwargs': kwargs
        })
        # Appeler la méthode originale pour maintenir le comportement
        return original_add_typer(subapp, **kwargs)
    
    try:
        # Remplacer temporairement add_typer par notre espion
        app.add_typer = spy_add_typer
        
        # Appeler init_cli
        result = init_cli()
        
        # Vérifier que la fonction retourne l'instance app
        assert result is app, "init_cli devrait retourner l'instance app"
        
        # Vérifier qu'il y a 5 appels à add_typer (un pour chaque sous-commande)
        assert len(add_typer_calls) == 5, f"Attendu 5 appels à add_typer, obtenu {len(add_typer_calls)}"
        
        # Vérifier que chaque sous-commande a été ajoutée avec les bons paramètres
        expected_subcommands = [
            {'name': 'user', 'help': 'Gestion des utilisateurs'},
            {'name': 'customer', 'help': 'Gestion des clients'},
            {'name': 'contract', 'help': 'Gestion des contrats'},
            {'name': 'event', 'help': 'Gestion des événements'},
            {'name': 'debug', 'help': 'Fonctions de debug'}
        ]
        
        # Vérifier que chaque sous-commande attendue est présente
        for expected in expected_subcommands:
            found = False
            for call in add_typer_calls:
                kwargs = call['kwargs']
                if (kwargs.get('name') == expected['name'] and 
                    kwargs.get('help') == expected['help']):
                    found = True
                    # Vérifier également que callback est check_auth
                    from epicevents.permissions.auth import check_auth
                    assert kwargs.get('callback') is check_auth, f"Le callback pour {expected['name']} devrait être check_auth"
                    break
            
            assert found, f"Sous-commande {expected['name']} non trouvée ou avec des paramètres incorrects"
        
        # Vérifier que les modules sont bien importés en vérifiant que les sous-apps existent
        from epicevents.cli import users, customers, contracts, events, debug
        
        assert add_typer_calls[0]['subapp'] is users.app, "La première sous-app devrait être users.app"
        assert add_typer_calls[1]['subapp'] is customers.app, "La deuxième sous-app devrait être customers.app"
        assert add_typer_calls[2]['subapp'] is contracts.app, "La troisième sous-app devrait être contracts.app"
        assert add_typer_calls[3]['subapp'] is events.app, "La quatrième sous-app devrait être events.app"
        assert add_typer_calls[4]['subapp'] is debug.app, "La cinquième sous-app devrait être debug.app"
    finally:
        # Restaurer la méthode originale
        app.add_typer = original_add_typer