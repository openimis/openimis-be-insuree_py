from pathlib import Path


def read_sql(name):
    return (Path(__file__).parent / name).read_text()
