import typer

app = typer.Typer(help="Gestion des contrats")

@app.command("create")
def create_contract(
    c: int = typer.Option(..., "--c", help="Numéro du client"),
    st: float = typer.Option(..., "--st", help="Montant total"),
    sd: float = typer.Option(None, "--sd", help="Montant restant dû"),
    si: bool = typer.Option(False, "--si", help="Statut de la signature (True: Signé, False: Non signé)"),
    u: int = typer.Option(0, "--u", help="Numéro du commercial en charge")
):
    """Creates a new contract."""
    typer.echo(f"Contrat créé pour le client {c}, montant: {st}, signé: {si}")

@app.command("filter")
def filter_contracts(
    ns: bool = typer.Option(False, "-ns", help="Filtre les contrats non signés"),
    up: bool = typer.Option(False, "-up", help="Filtre les contrats non payés en totalité")
):
    """Contracts filters."""
    typer.echo(f"Filtrage des contrats - Non signés: {ns}, Non payés: {up}")

@app.command("list")
def list_contracts():
    """List all contracts."""
    contracts = Contract.select()
    if not contracts.count():
        typer.echo("❌ Aucun contrat n'est enregistré dans la bdd.")
        return

    for contract in contracts:
        typer.echo(f"{contract.id}: user:{contract.team_contact}, client:{contract.customer}")

@app.command("update")
def update_contract(
    contract_id: int = typer.Argument(..., help="N° du contrat à modifier"),
    new_value: str = typer.Argument(..., help="Nouvelle valeur à appliquer"),
    c: bool = typer.Option(False, "-c", help="Modifier l'id du client"),
    u: bool = typer.Option(False, "-u", help="Modifier l'id de l'utilisateur"),
    st: bool = typer.Option(False, "-st", help="Modifier le montant total"),
    sd: bool = typer.Option(False, "-sd", help="Modifier le montant dû"),
    e: bool = typer.Option(False, "-e", help="Modifier le statut de la signature")
):
    """Updates existing contract."""
    typer.echo(f"Modification du contrat {contract_id}: {new_value}")

if __name__ == "__main__":
    app()
