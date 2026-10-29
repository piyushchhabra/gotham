from gotham.__main__ import main


def test_demo_runs(capsys):
    main()
    out = capsys.readouterr().out
    assert "== Bat-Signal ==" in out
    assert "Scarecrow admitted to cell A-01" in out
