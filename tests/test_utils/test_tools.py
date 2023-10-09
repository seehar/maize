from maize.utils.tools import retry


@retry()
def test_retry():
    return 1 / 0
