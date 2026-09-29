from importlib.metadata import version


def test_palimpsest_dist_is_installed() -> None:
    assert version("palimpsest") == "0.1.0"
