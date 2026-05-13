from docflow_cli.shared import CommandResult


def test_command_result_exit_code_tracks_success() -> None:
    assert CommandResult(success=True, message="done").exit_code == 0
    assert CommandResult(success=False, message="failed").exit_code == 1
