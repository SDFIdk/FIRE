from pathlib import Path

import click

from click.testing import CliRunner
from fire.cli.gama import gama


def _run_cli(runner, title, args, used_files=[]):
    click.echo("\nTest: " + title)
    click.echo(" Emulating: python gama " + " ".join(args))

    # kopier ini-fil til isoleret filsystem
    files = []
    for filename in used_files:
        with open(Path(__file__).resolve().parent / filename) as f:
            files.append((filename, f.readlines()))
    with runner.isolated_filesystem():
        for (filename, data) in files:
            with open(filename, "w") as f:
                f.writelines(data)

        result = runner.invoke(gama, args)

    if result.exit_code != 0:
        click.echo(" Failed: " + str(args))
        click.echo(" Exception: " + str(result.exception))
        click.echo(" Output: " + str(result.output))
        return False
    else:
        click.echo(" Success: " + str(args))
        return True


def test_within_distance_of_point1(tmp_path):
    runner = CliRunner()

    title = "Within distance of point (wkt)"
    args = [
        "write",
        "-o",
        "cli_output_near_geometry.xml",
        "-g",
        "POINT (10.200000 56.100000)",
        "-b",
        "10000",
        "-f",
        "67e3987a-dc6b-49ee-8857-417ef35777af",
        "-pf",
        "fire-gama.ini",
    ]

    assert _run_cli(runner, title, args, ["fire-gama.ini"])


def test_within_distance_of_point2():
    runner = CliRunner()

    title = "Within distance of point (wkt) - time interval"
    args = [
        "write",
        "-o",
        "cli_output_near_geometry_fra_til.xml",
        "-g",
        "POINT (10.200000 56.100000)",
        "-b",
        "10000",
        "-f",
        "67e3987a-dc6b-49ee-8857-417ef35777af",
        "-df",
        "08-10-2015",
        "-dt",
        "09-10-2018",
        "-pf",
        "fire-gama.ini",
    ]

    assert _run_cli(runner, title, args, ["fire-gama.ini"])


def test_within_distance_of_point3():
    runner = CliRunner()

    title = "Within distance of point (wkt from file) - time interval"
    args = [
        "write",
        "-o",
        "cli_output_near_geometry_file_fra_til.xml",
        "-gf",
        "geometry.wkt",
        "-b",
        "10000",
        "-f",
        "67e3987a-dc6b-49ee-8857-417ef35777af",
        "-df",
        "08-10-2015",
        "-dt",
        "09-10-2018",
        "-pf",
        "fire-gama.ini",
    ]
    assert _run_cli(runner, title, args, ["geometry.wkt", "fire-gama.ini"])


def test_within_distance_of_point4():
    runner = CliRunner()

    title = (
        "Within distance of point (wkt from file) - "
        "fixed points from file - time interval"
    )
    args = [
        "write",
        "-o",
        "cli_output_near_geometry_file_fixed_from_file_fra_til.xml",
        "-gf",
        "geometry.wkt",
        "-b",
        "10000",
        "-ff",
        "fixed_points.csv",
        "-df",
        "08-10-2015",
        "-dt",
        "09-10-2018",
        "-pf",
        "fire-gama.ini",
    ]

    assert _run_cli(
        runner, title, args, ["geometry.wkt", "fixed_points.csv", "fire-gama.ini"]
    )
