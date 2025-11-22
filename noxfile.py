import nox


@nox.session(python=["3.11", "3.12", "3.13"], venv_backend="conda")
def pytest(session):
    session.log(f"My python is {session.python}")
    session.install("uv")
    session.run(
        "uv",
        "sync",
        "--all-groups",
    )
    session.run("uv", "run", "pytest", "-s")
