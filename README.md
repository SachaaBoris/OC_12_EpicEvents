# OC_12 EpicEvents BackEnd CRM  

<p align="center"><img src="https://github.com/SachaaBoris/OC_12_EpicEvents/blob/main/static/logo_w.png" width="346"/></p>
  
# ● Description du projet  
EpicEvents CRM est une application de gestion locale, conçue pour collecter, traiter et organiser les données relatives aux clients, contrats et événements. Fonctionnant sous la forme d’une interface en ligne de commande (CLI), elle permet d’effectuer les opérations CRUD sur les utilisateurs, les clients, les contrats et les événements, offrant ainsi un suivi efficace et centralisé.  
  
# ● Comment installer et démarrer l'application  
1. Prérequis :  
    Avoir Python 3 et PostgreSql installés  
    Avoir téléchargé et dézipé l'archive du projet sur votre disque dur,  
    Ou clonez le repo avec cette commande :  
  ```  
  git clone https://github.com/SachaaBoris/OC_12_EpicEvents.git "local\folder"
  ```  
  
2. Configurer l'environement :    
	Rennomez .env.sample en .env  
	Editez les différentes variables selon vos préférences / votre config.

3. Démarrer le serveur :  
	Depuis votre console favorite, rendez-vous dans le dossier d'installation PostGre et executez : `pg_ctl -D chemin\vers\votre\bdd start`

4. Installer l'environnement virtuel et les librairies :  
    Toujours depuis votre console, naviguez jusqu'au repertoire de l'app EpicEvents  
    Pour créer l'environnement virtuel rentrez la ligne de commande : `py -m venv ./venv`  
    Activez ensuite l'environnement virtuel en rentrant la commande : `venv\Scripts\activate`  
    Installer les requirements du projet avec la commande : `py -m pip install -r requirements.txt`  
  
5. Creer la nouvelle table :  
    Maintenant que votre environement est prêt, rentrez la commande : `py -m epicevents create_db.py`
  
  
# ● Comment utiliser l'application  
Les différents points d'entrées sont :
--help		  Print l'aide (accessible dans tous les points d'entrées)
login         Authentification
logout        Déconnexion
debug_token   Checking token validity
users         Gestion des utilisateurs
customers     Gestion des clients
contracts     Gestion des contrats
events		  Gestion des évenements

Exemple de commande : `py epicevents login --username Admin_test --password ADMIN_PASS`  
  
  
6. Arrêter le serveur :   
    Quittez votre environement virtuel et utilisez cette commande pour arreter le serveur : `pg_ctl -D chemin\vers\votre\bdd stop`
  
---  
  
[![CC BY 4.0][cc-by-shield]][cc-by]  
  
This work is licensed under a [Creative Commons Attribution 4.0 International License][cc-by].  
  
[cc-by]: http://creativecommons.org/licenses/by/4.0/  
[cc-by-shield]: https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg  
