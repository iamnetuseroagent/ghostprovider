"""Entry point for `ghostprovider` command and `python -m ghostprovider`."""

def run() -> None:
    from ghostprovider.app import GhostProviderApp
    app = GhostProviderApp()
    app.run()


if __name__ == "__main__":
    run()
