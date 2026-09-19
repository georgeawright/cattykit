def pytest_addoption(parser):
    group = parser.getgroup("copycat reproduction")
    group.addoption(
        "--basic",
        action="store_true",
        help="run the selected small Copycat reproduction sample (the default)",
    )
    group.addoption(
        "--full",
        action="store_true",
        help="run every Copycat reproduction problem",
    )
