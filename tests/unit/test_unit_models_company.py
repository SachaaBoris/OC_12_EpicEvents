import pytest


# Tests pour Company
def test_company_save(monkeypatch):
    """Test de la méthode save() de Company"""
    from epicevents.models.company import Company
    
    # Créer un compteur d'appels
    calls = {'save': 0}
    
    # Fonction de remplacement pour BaseModel.save
    def mock_save(self):
        calls['save'] += 1
    
    # Appliquer le patch
    monkeypatch.setattr('epicevents.models.company.BaseModel.save', mock_save)
    
    # Créer une instance d'entreprise
    company = Company(name="Test Company")
    
    # Appeler la méthode save()
    company.save()
    
    # Vérifier que la méthode a été appelée
    assert calls['save'] == 1


def test_company_validate_name_valid(monkeypatch):
    """Test de validation d'un nom d'entreprise valide"""
    from epicevents.models.company import Company
    
    # Simuler la méthode save pour éviter l'accès à la base de données
    def mock_save(self):
        pass
    
    monkeypatch.setattr('epicevents.models.company.Company.save', mock_save)
    
    # Créer une entreprise avec un nom valide
    company = Company(name="Valid Company Name")
    
    # Appeler la méthode de validation
    company._validate_name()
    
    # Aucune exception ne devrait être levée


def test_company_validate_name_empty(monkeypatch):
    """Test de validation d'un nom d'entreprise vide"""
    from epicevents.models.company import Company
    
    # Simuler la méthode save pour éviter l'accès à la base de données
    def mock_save(self):
        pass
    
    monkeypatch.setattr('epicevents.models.company.Company.save', mock_save)
    
    # Créer une entreprise avec un nom vide
    company = Company(name="")
    
    # La validation devrait lever une ValueError
    with pytest.raises(ValueError) as excinfo:
        company._validate_name()
    
    # Vérifier le message d'erreur
    assert "ne peut pas être vide." in str(excinfo.value).lower()
