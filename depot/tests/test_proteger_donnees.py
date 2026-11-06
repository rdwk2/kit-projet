"""Tests du hook de protection des données (``scripts/hooks/proteger_donnees.py``).

Gabarit du kit (module ``donnees-privees``). Aucune variable du kit : les tests lisent
la configuration du hook lui-même (``VARIABLE``, ``COMMANDES_DONNEES``…). Chaque test
lance le hook comme Claude Code le lance : un processus neuf, l'appel d'outil en JSON
sur l'entrée standard ; puis il lit le code de sortie (0 passe, 2 refuse). Les chemins
de style Windows se testent sous tout système : le hook les lit comme des textes.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

HOOK = Path(__file__).resolve().parents[1] / "scripts" / "hooks" / "proteger_donnees.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("proteger_donnees", HOOK)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONFIG = _load()
VARIABLE: str = CONFIG.VARIABLE
COMMANDS: list[list[str]] = [
    line.split("#", 1)[0].split()
    for line in CONFIG.COMMANDES_DONNEES.splitlines()
    if line.split("#", 1)[0].split()
]
PAIRS = [(words[0], sub) for words in COMMANDS for sub in words[1:]]


def _environment(home: Path | str | None, **extra: str) -> dict[str, str]:
    """L'environnement du hook : sans la variable ni ses levées (que l'environnement
    ou ``.env`` auraient posées), le dossier personnel éventuel, et ``extra``."""
    environment = {k: v for k, v in os.environ.items() if not k.startswith(VARIABLE)}
    if home is not None:
        environment["HOME"] = str(home)
        environment["USERPROFILE"] = str(home)
    environment.update(extra)
    return environment


def run(
    call: dict[str, object] | str,
    project: Path | str,
    *,
    hook: Path = HOOK,
    home: Path | str | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Lance le hook sur ``call`` (un appel d'outil, ou un texte brut), avec
    ``CLAUDE_PROJECT_DIR`` sur ``project``."""
    payload = call if isinstance(call, str) else json.dumps(call)
    return subprocess.run(
        [sys.executable, str(hook)],
        input=payload,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=_environment(home, CLAUDE_PROJECT_DIR=str(project), **(env or {})),
        check=False,
    )


def tool(name: str, cwd: Path | str, **tool_input: object) -> dict[str, object]:
    return {"tool_name": name, "tool_input": tool_input, "cwd": str(cwd)}


@pytest.fixture
def world(tmp_path: Path) -> tuple[Path, Path]:
    """Un projet et, à côté, le dossier des données, nommé dans le ``.env``."""
    project = tmp_path / "projet"
    (project / ".claude").mkdir(parents=True)
    data = tmp_path / "donnees"
    (data / "raw").mkdir(parents=True)
    (project / ".env").write_text(f"{VARIABLE}={data.as_posix()}\n", encoding="utf-8")
    return project, data


def _variant(pattern: str, replacement: str, tmp_path: Path) -> Path:
    """Une copie du hook dont une ligne de configuration est changée."""
    source, count = re.subn(
        pattern, replacement, HOOK.read_text(encoding="utf-8"), count=1, flags=re.M
    )
    assert count == 1, pattern
    copy = tmp_path / "variante" / "proteger_donnees.py"
    copy.parent.mkdir(parents=True, exist_ok=True)
    copy.write_text(source, encoding="utf-8")
    return copy


# ── Outils de fichiers et recherches ─────────────────────────────────────────


def test_a_file_of_the_project_is_read(world: tuple[Path, Path]) -> None:
    project, _ = world
    assert (
        run(
            tool("Read", project, file_path=str(project / "README.md")), project
        ).returncode
        == 0
    )


@pytest.mark.parametrize("name", ["Read", "Write", "Edit", "MultiEdit"])
def test_a_file_tool_under_the_data_is_refused(
    world: tuple[Path, Path], name: str
) -> None:
    project, data = world
    result = run(tool(name, project, file_path=str(data / "raw" / "a.json")), project)
    assert result.returncode == 2
    assert "dossier des données" in result.stderr


def test_a_relative_path_that_climbs_into_the_data_is_refused(
    world: tuple[Path, Path],
) -> None:
    project, _ = world
    call = tool("Write", project, file_path="../donnees/raw/a.json", content="x")
    assert run(call, project).returncode == 2


def test_a_sibling_folder_with_a_longer_name_passes(world: tuple[Path, Path]) -> None:
    project, data = world
    sibling = data.parent / (data.name + "2") / "a.json"
    assert run(tool("Read", project, file_path=str(sibling)), project).returncode == 0
    assert (
        run(tool("Bash", project, command=f"ls {sibling.parent}"), project).returncode
        == 0
    )


def test_a_search_over_a_parent_of_the_data_is_refused(
    world: tuple[Path, Path],
) -> None:
    project, data = world
    call = tool("Grep", project, pattern="x", path=str(data.parent))
    assert run(call, project).returncode == 2


def test_a_glob_whose_fixed_part_reaches_the_data_is_refused(
    world: tuple[Path, Path],
) -> None:
    project, _ = world
    assert (
        run(tool("Glob", project, pattern="../donnees/**/*.json"), project).returncode
        == 2
    )


def test_a_search_inside_the_project_passes(world: tuple[Path, Path]) -> None:
    project, _ = world
    assert (
        run(tool("Grep", project, pattern="x", path=str(project)), project).returncode
        == 0
    )
    assert run(tool("Glob", project, pattern="src/**/*.py"), project).returncode == 0


def test_lsp_reads_every_text_as_a_path(world: tuple[Path, Path]) -> None:
    project, data = world
    call = tool("LSP", project, operation="hover", filePath=str(data / "x.py"))
    assert run(call, project).returncode == 2


# ── Commandes ────────────────────────────────────────────────────────────────


def test_a_command_naming_the_folder_is_refused(world: tuple[Path, Path]) -> None:
    project, data = world
    for command in (f"ls {data}", f"ls {str(data).upper()}", f"cat {data}\\raw/a.json"):
        assert run(tool("Bash", project, command=command), project).returncode == 2, (
            command
        )


def test_a_command_naming_the_folder_from_home_is_refused(
    world: tuple[Path, Path],
) -> None:
    project, data = world
    for command in (
        "cat ~/donnees/raw/a.json",
        "cat $HOME/donnees",
        "type %USERPROFILE%\\donnees",
    ):
        result = run(tool("Bash", project, command=command), project, home=data.parent)
        assert result.returncode == 2, command


def test_a_command_naming_the_variable_is_refused(world: tuple[Path, Path]) -> None:
    project, _ = world
    result = run(tool("Bash", project, command=f"echo ${VARIABLE.lower()}"), project)
    assert result.returncode == 2
    assert VARIABLE in result.stderr


@pytest.mark.skipif(not PAIRS, reason="aucune commande de données configurée")
@pytest.mark.parametrize(
    "form",
    [
        "{p} {s}",
        "{p}.exe {s}",
        '{p} "{s}"',
        "{P} {S}",
        "{p} --flag valeur {s}",
        "{p} -q {s} --x",
        "{p} NOM=1 {s}",
        "{p} --set nom valeur {s}",
        "uv run {p} {s}",
        "cd src && {p} {s}",
    ],
)
def test_the_data_commands_are_refused(world: tuple[Path, Path], form: str) -> None:
    project, _ = world
    for program, sub in PAIRS:
        command = form.format(p=program, s=sub, P=program.upper(), S=sub.upper())
        result = run(tool("Bash", project, command=command), project)
        assert result.returncode == 2, command


@pytest.mark.skipif(not PAIRS, reason="aucune commande de données configurée")
def test_other_subcommands_pass(world: tuple[Path, Path]) -> None:
    project, _ = world
    for program, sub in PAIRS:
        for command in (f"{program} {sub}-autre", f"{program} test -k {sub}"):
            result = run(tool("Bash", project, command=command), project)
            assert result.returncode == 0, command


def test_the_data_commands_are_refused_without_a_known_folder(tmp_path: Path) -> None:
    if not PAIRS:
        pytest.skip("aucune commande de données configurée")
    program, sub = PAIRS[0]
    call = tool("Bash", tmp_path, command=f"{program} {sub}")
    assert run(call, tmp_path).returncode == 2
    assert run(tool("Read", tmp_path, file_path="/x/y.json"), tmp_path).returncode == 0


# ── Chemins Windows (lus comme des textes) ───────────────────────────────────


@pytest.mark.parametrize(
    ("path", "code"),
    [
        ("C:\\Users\\Moi\\donnees\\raw\\a.json", 2),
        ("c:/users/moi/DONNEES/a.json", 2),
        ("/c/Users/Moi/donnees/a.json", 2),
        ("/mnt/c/Users/Moi/donnees/a.json", 2),
        ("C:/Users/Moi/donnees2/a.json", 0),
        ("C:/Users/Moi/projet/src/a.py", 0),
    ],
)
def test_windows_paths(tmp_path: Path, path: str, code: int) -> None:
    call = tool("Read", "C:/Users/Moi/projet", file_path=path)
    result = run(call, tmp_path, env={VARIABLE: "C:/Users/Moi/donnees"})
    assert result.returncode == code, path


@pytest.mark.parametrize(("platform", "under"), [("darwin", True), ("linux", False)])
def test_macos_paths_are_compared_without_case(
    monkeypatch: pytest.MonkeyPatch, platform: str, under: bool
) -> None:
    monkeypatch.setattr(sys, "platform", platform)
    path, root = "/Users/Moi/DONNEES/a.json", "/Users/Moi/donnees"
    assert CONFIG._under(path, root, "/Users/Moi/projet") is under


def test_a_powershell_command_from_the_profile_is_refused(tmp_path: Path) -> None:
    call = tool(
        "PowerShell",
        "C:/Users/Moi/projet",
        command="Get-Content $env:USERPROFILE\\Donnees\\a.json",
    )
    result = run(
        call, tmp_path, home="C:/Users/Moi", env={VARIABLE: "C:/Users/Moi/donnees"}
    )
    assert result.returncode == 2


# ── Entrées inattendues, outils non contrôlés, levées ────────────────────────


@pytest.mark.parametrize(
    "call",
    [
        "pas du JSON",
        "[1, 2]",
        json.dumps({"tool_name": "Read", "tool_input": "x"}),
        json.dumps({"tool_name": "Read", "tool_input": {"file_path": 3}}),
        json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}, "cwd": 3}),
    ],
)
def test_an_unexpected_input_is_refused(world: tuple[Path, Path], call: str) -> None:
    project, _ = world
    result = run(call, project)
    assert result.returncode == 2
    assert "erreur" in result.stderr


def test_an_uncontrolled_tool_passes(world: tuple[Path, Path]) -> None:
    project, data = world
    call = tool("WebFetch", project, url=f"file://{data}/a.json")
    assert run(call, project).returncode == 0


def test_an_env_naming_the_variable_without_value_refuses_everything(
    tmp_path: Path,
) -> None:
    (tmp_path / ".env").write_text(f"{VARIABLE}=\n", encoding="utf-8")
    result = run(
        tool("Read", tmp_path, file_path=str(tmp_path / "README.md")), tmp_path
    )
    assert result.returncode == 2


def test_the_bypass_lifts_the_control(world: tuple[Path, Path]) -> None:
    project, data = world
    call = tool("Read", project, file_path=str(data / "a.json"))
    assert run(call, project, env={CONFIG.BYPASS: "1"}).returncode == 0
    assert run(call, project, env={CONFIG.BYPASS: "oui"}).returncode == 2


# ── Le hook lui-même ─────────────────────────────────────────────────────────


@pytest.mark.skipif(not CONFIG.PROTEGER_LE_HOOK, reason="PROTEGER_LE_HOOK désactivé")
def test_the_hook_configuration_is_protected(world: tuple[Path, Path]) -> None:
    project, _ = world
    local = str(project / ".claude" / "settings.local.json")
    assert (
        run(tool("Write", project, file_path=local, content="{}"), project).returncode
        == 2
    )
    assert run(tool("Edit", project, file_path=str(HOOK)), project).returncode == 2
    assert run(tool("Read", project, file_path=local), project).returncode == 0
    command = "echo '{\"disableAllHooks\": true}' > x"
    assert run(tool("Bash", project, command=command), project).returncode == 2
    lifted = run(
        tool("Write", project, file_path=local), project, env={CONFIG.BYPASS_HOOK: "1"}
    )
    assert lifted.returncode == 0


def test_an_unfilled_template_refuses_everything(
    world: tuple[Path, Path], tmp_path: Path
) -> None:
    project, _ = world
    placeholder = "{" * 2 + " var_donnees " + "}" * 2
    copy = _variant(r'^VARIABLE = ".*"$', f'VARIABLE = "{placeholder}"', tmp_path)
    result = run(
        tool("Read", project, file_path=str(project / "README.md")), project, hook=copy
    )
    assert result.returncode == 2
    assert "non configuré" in result.stderr


def test_a_required_folder_refuses_everything_when_unknown(tmp_path: Path) -> None:
    copy = _variant(r"^EXIGER_DOSSIER = False$", "EXIGER_DOSSIER = True", tmp_path)
    result = run(
        tool("Read", tmp_path, file_path=str(tmp_path / "a.py")), tmp_path, hook=copy
    )
    assert result.returncode == 2
    assert "inconnu" in result.stderr
