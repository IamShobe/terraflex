import typer

from tfstate_git.server.app import start_server

app = typer.Typer()


@app.command()
def start(
    port: int = typer.Option(8600, help="Port to run the server on"),
):
    start_server(port)


def main():
    app()
