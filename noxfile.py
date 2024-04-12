import nox


@nox.session(python=["3.8", "3.9", "3.10", "3.11"], venv_backend="conda")
def pytest(session):
    session.log(f"My python is {session.python}")
    session.install("poetry")
    session.run_always("poetry", "install", "--no-root", external=True)
    session.run("poetry", "install", "--no-root")
    session.run("poetry", "run", "pytest", "-s")
