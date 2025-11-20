import pytest
from click.testing import CliRunner
from getconfig import main  # import your click command

@pytest.fixture
def runner():
    return CliRunner()

def test_show_help_when_no_options(runner):
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert "Get Configuration" in result.output  # help text shown

def test_exclusive_options_error(runner):
    # Passing both --command and --commandfile should raise UsageError
    result = runner.invoke(main, ["-c", "show run", "-cf", "commands.txt"])
    assert result.exit_code != 0
    assert "Only one of --command, --commandfile, or --interactive" in result.output

def test_command_option(runner, tmp_path):
    # Create a fake device list CSV
    csv_file = tmp_path / "devices.csv"
    csv_file.write_text("Name,Host,Username,Password\nsite1,1.1.1.1,user,pass\n")

    result = runner.invoke(
        main,
        ["-l", str(csv_file), "-c", "show version", "-d", "site1"]
    )
    # Exit code may vary depending on mocked run_parallel, but we can check output
    assert result.exit_code == 0
    assert "Finished after" in result.output

def test_commandfile_option(runner, tmp_path):
    csv_file = tmp_path / "devices.csv"
    csv_file.write_text("Name,Host,Username,Password\nsite1,1.1.1.1,user,pass\n")

    cmd_file = tmp_path / "commands.txt"
    cmd_file.write_text("show ip int brief\n")

    result = runner.invoke(
        main,
        ["-l", str(csv_file), "-cf", str(cmd_file), "-d", "site1"]
    )
    assert result.exit_code == 0
    assert "Finished after" in result.output

# def test_interactive_option(runner, tmp_path):
#     csv_file = tmp_path / "devices.csv"
#     csv_file.write_text("Name,Host,Username,Password\nsite1,1.1.1.1,user,pass\n")

#     result = runner.invoke(
#         main,
#         ["-l", str(csv_file), "-i", "-d", "site1"]
#     )
#     # Interactive mode should run without error
#     assert result.exit_code == 0
