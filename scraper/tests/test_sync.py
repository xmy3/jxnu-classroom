from argparse import Namespace

import pytest

from jxnu_classroom import cli


@pytest.mark.parametrize("missing", ["rooms", "semester"])
def test_invalid_second_timetable_preserves_previous_data(tmp_path, monkeypatch, missing):
    title = '<span id="lblTitle">春季学期</span>'
    row = '<table><tr><td width="1%">W1101</td>' + "<td></td>" * 49 + "</tr></table>"
    pages = {1: title + row, 2: title if missing == "rooms" else row}
    monkeypatch.setattr(cli, "fetch_public_classroom", lambda t, session: pages[t])

    output = tmp_path / "classrooms.json"
    output.write_text('{"previous":true}', encoding="utf-8")
    args = Namespace(output=output, verbose=False, pretty=False)

    assert cli.cmd_sync(args) == 1
    assert output.read_text(encoding="utf-8") == '{"previous":true}'
