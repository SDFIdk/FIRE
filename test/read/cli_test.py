import click
from click.testing import CliRunner
from cli import cli

def do_test(runner, title, args):
    click.echo("\nTest: " + title)
    click.echo(" Emulating: python cli.py " + ' '.join(args))
    result = runner.invoke(cli, args)
    if result.exit_code != 0:
        click.echo(" Failed: " + str(args))
        click.echo(" Exception: " + result.exception)
        return False, result.exception
    else:
        click.echo(" Success: " + str(args))
        return True, result.output

if __name__ == "__main__":
    runner = CliRunner()
    
    title = "Read all points"
    args = ['read', '-i', 'input/all_points.xml', '-c', '3639726e-4dbd-44b5-9928-8ff1e8c970c2']
    do_test(runner, title, args)
