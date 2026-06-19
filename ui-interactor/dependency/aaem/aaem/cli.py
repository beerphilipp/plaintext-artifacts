import click
import aaem.avd.avd as a

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

@cli.group()
def avd():
    """
    Android Virtual Device (AVD) management
    """
    pass

@avd.command("duplicate")
@click.argument("base_name")
@click.argument("new_name")
@click.argument("amount", type=int)
def duplicate_avd_cli(base_name, new_name, amount):
    a.duplicate_avd(base_name, new_name, amount, force=False)

@avd.command("start")
@click.argument("avd_name")
def start_avd(avd_name: str):
    matching_avds = a.get_avds_matching_prefix(avd_name)
    print(f"Starting AVDs: {matching_avds}")
    started_avds = a.start_avd(avd_name)
    if len(matching_avds) != len(started_avds):
        click.echo("Some AVDs could not be started!")

@avd.command("stop")
@click.argument("avd_name")
@click.option("--force", is_flag=True)
def stop_avd(avd_name, force):
    if force:
        a.force_kill_avd(avd_name)
    else:
        a.stop_avd(avd_name)
    pass

@avd.command("create-snapshot")
def create_avd_snapshot():
    raise NotImplementedError("Not implemented yet")

@avd.command("restore-snapshot")
def restore_avd_snapshot():
    raise NotImplementedError("Not implemented yet")

@avd.command("compress")
@click.argument("avd_name")
@click.argument("out")
def compress_avd(avd_name, out):
    a.compress_avd(avd_name, out)

@avd.command("decompress")
@click.argument("compressed_avd")
@click.argument("new_avd_name")
def decompress_avd(compressed_avd, new_avd_name):
    a.decompress_avd(compressed_avd, new_avd_name)