import click
from click.testing import CliRunner
from cli import cli

if __name__ == "__main__":
    runner = CliRunner()
    result = runner.invoke(cli, ['write', '-o output/cli_output.xml', '-g POINT (10.4811749340072 56.3061226484564)', '-b 10000', '-f 7CA9F53D-DAE9-59C0-E053-1A041EAC5678'])
    a = 2
    
