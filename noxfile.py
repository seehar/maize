import nox


@nox.session(python=["3.11", "3.12"], venv_backend="conda")
def pytest(session):
    session.log(f"My python is {session.python}")
    session.install("poetry")
    session.run_always("poetry", "install", "--no-root", external=True)
    session.run("poetry", "install", "--all-extras", "--no-root")
    session.run("poetry", "run", "pytest", "-s")
