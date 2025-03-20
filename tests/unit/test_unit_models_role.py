import pytest
from epicevents.models.role import Role


def test_role_save(monkeypatch):
    """Test de la méthode save() de Role"""
    # Créer un compteur d'appels
    calls = {'save': 0}
    
    # Fonction de remplacement pour BaseModel.save
    def mock_save(self):
        calls['save'] += 1
    
    # Appliquer le patch
    monkeypatch.setattr('epicevents.models.role.BaseModel.save', mock_save)
    
    # Créer une instance de rôle
    role = Role(name="Test Role")
    
    # Appeler la méthode save()
    role.save()
    
    # Vérifier que la méthode a été appelée
    assert calls['save'] == 1


def test_role_validate_name_valid(monkeypatch):
    """Test de validation d'un nom de rôle valide"""
    # Simuler la méthode save pour éviter l'accès à la base de données
    monkeypatch.setattr('epicevents.models.role.Role.save', lambda self: None)
    
    # Créer un rôle avec un nom valide
    role = Role(name="Valid Role Name")
    
    # Appeler la méthode de validation
    role._validate_name()
    
    # Aucune exception ne devrait être levée


def test_role_validate_name_empty(monkeypatch):
    """Test de validation d'un nom de rôle vide"""
    # Simuler la méthode save pour éviter l'accès à la base de données
    monkeypatch.setattr('epicevents.models.role.Role.save', lambda self: None)
    
    # Créer un rôle avec un nom vide
    role = Role(name="")
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        role._validate_name()
    
    # Vérifier le message d'erreur
    assert "ne peut pas être vide." in str(excinfo.value).lower()