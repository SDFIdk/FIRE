import click
from click.testing import CliRunner
from firegama.cli import gama

def do_test(runner, title, args):
    click.echo("\nTest: " + title)
    click.echo(" Emulating: python gama " + ' '.join(args))
    result = runner.invoke(gama, args)
    if result.exit_code != 0:
        click.echo(" Failed: " + str(args))
        click.echo(" Exception: " + str(result.exception))
        return False, result.exception
    else:
        click.echo(" Success: " + str(args))
        return True, result.output

if __name__ == "__main__":
    runner = CliRunner()
    
    title = "Read all points"
    args = ['read', '-i', 'input/near_geometry.xml', '-c', '4f8f29c8-c38f-4c69-ae28-c7737178de1f']
    do_test(runner, title, args)
