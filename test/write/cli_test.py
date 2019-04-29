
import click
from click.testing import CliRunner
from firegama.cli import cli

def do_test(runner, title, args):
    click.echo("\nTest: " + title)
    click.echo(" Emulating: python cli.py " + ' '.join(args))
    result = runner.invoke(cli, args)
    if result.exit_code != 0:
        click.echo(" Failed: " + str(args))
        click.echo(" Exception: " + str(result.exception))
        return False, result.exception
    else:
        click.echo(" Success: " + str(args))
        return True, result.output

if __name__ == "__main__":
    runner = CliRunner()
    
    title = "Within distance of point (wkt)"
    args = ['write', '-o', 'output/cli_output_near_geometry.xml', '-g', 'POINT (12.5983815323665 55.7039994123763)', '-b', '10000', '-f', '814E9044-1AAB-5A4E-E053-1A041EACF9E4']
    do_test(runner, title, args)

    title = "Within distance of point (wkt) - time interval"
    args = ['write', '-o', 'output/cli_output_near_geometry_fra_til.xml', '-g', 'POINT (12.5983815323665 55.7039994123763)', '-b', '10000', '-f', '814E9044-1AAB-5A4E-E053-1A041EACF9E4', '-df', '08-10-2015', '-dt', '09-10-2018']
    do_test(runner, title, args)

    title = "Within distance of point (wkt from file) - time interval"
    args = ['write', '-o', 'output/cli_output_near_geometry_file_fra_til.xml', '-gf', 'geometry.wkt', '-b', '10000', '-f', '814E9044-1AAB-5A4E-E053-1A041EACF9E4', '-df', '08-10-2015', '-dt', '09-10-2018']
    do_test(runner, title, args)

    title = "Within distance of point (wkt from file) - fixed points from file - time interval"
    args = ['write', '-o', 'output/cli_output_near_geometry_file_fra_til.xml', '-gf', 'geometry.wkt', '-b', '10000', '-ff', 'fixed_points.csv', '-df', '08-10-2015', '-dt', '09-10-2018']
    do_test(runner, title, args)
