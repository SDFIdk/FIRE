import click
from click.testing import CliRunner
from cli import cli

def do_test(runner, args):
    result = runner.invoke(cli, args)
    if result.exit_code != 0:
        click.echo("Failed: " + str(args))
        click.echo("Exception: " + result.output)
        return False, result.exception
    else:
        click.echo("Success: " + str(args))
        return True, result.output

if __name__ == "__main__":
    runner = CliRunner()
    args = ['write', '-o', 'output/cli_output_near_geometry.xml', '-g', 'POINT (10.4811749340072 56.3061226484564)', '-b', '10000', '-f', '7CA9F53D-DAE9-59C0-E053-1A041EAC5678']
    success, return_text = do_test(runner, args)
    args = ['write', '-o', 'output/cli_output_near_geometry_fra_til.xml', '-g', 'POINT (10.4811749340072 56.3061226484564)', '-b', '10000', '-f', '7CA9F53D-DAE9-59C0-E053-1A041EAC5678', '-df', '08-10-2015', '-dt', '09-10-2015']
    success, return_text = do_test(runner, args)
