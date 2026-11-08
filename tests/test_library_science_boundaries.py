from __future__ import annotations

import ast
import math
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zipfile import Path as ZipPath
from zipfile import ZipFile

import pytest

import mdkv.library as library
from mdkv.core.model import Track
from mdkv.storage import load_mdkv, save_mdkv


EXAMPLE_NAMES = {
    "active_inference.yaml",
    "bilingual_es.yaml",
    "code_snippets.yaml",
    "large_multilingual.yaml",
    "media_refs.yaml",
    "revisions.yaml",
    "small_en.yaml",
}


@pytest.mark.parametrize("created", ["2025-01-02T03:04:05+00:00", datetime(2025, 1, 2, 3, 4, 5, tzinfo=UTC)])
def test_definition_fields_survive_container_roundtrip(tmp_path: Path, created: str | datetime):
    definition = {
        "title": "Authored metadata",
        "authors": ["Example author"],
        "created": created,
        "version": "0.7",
        "metadata": {"license": "CC0", "provenance": "synthetic fixture"},
        "tracks": [{"id": "primary", "type": "primary", "language": "en", "content": "# Example\n"}],
    }
    document = library.build_document_from_definition(definition)
    expected_created = datetime(2025, 1, 2, 3, 4, 5, tzinfo=UTC)
    assert document.created == expected_created
    assert document.version == "0.7"
    assert document.metadata == definition["metadata"]
    destination = tmp_path / "metadata.mdkv"
    save_mdkv(document, destination)
    restored = load_mdkv(destination)
    assert restored.created == expected_created
    assert restored.version == "0.7"
    assert restored.metadata == definition["metadata"]
    assert restored.title == definition["title"]
    assert restored.authors == definition["authors"]
    assert restored.tracks["primary"].content == "# Example\n"
    document.metadata["license"] = "changed"
    document.authors.append("Another author")
    assert definition["metadata"]["license"] == "CC0"
    assert definition["authors"] == ["Example author"]


def test_canonical_resources_are_complete_and_checkout_independent(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def forbidden_save(*args, **kwargs):
        pytest.fail("Loading a bundled example must not save a generated container")

    monkeypatch.setattr(library, "save_mdkv", forbidden_save)
    directory = library.example_definitions_dir()
    names = {child.name for child in directory.iterdir() if child.is_file() and child.name.endswith(".yaml")}
    assert names == EXAMPLE_NAMES
    for name in sorted(names):
        definition = library.load_example_definition(directory.joinpath(name))
        document = library.load_example_document(name)
        assert document.title == definition["title"]
        assert set(document.tracks) == {track["id"] for track in definition["tracks"]}
    first = library.load_example_document("small_en.yaml")
    second = library.load_example_document("small_en.yaml")
    assert first is not second
    first.tracks["primary"].content = "modified in memory"
    assert second.tracks["primary"].content != "modified in memory"
    assert library.load_example_document("small_en.yaml").tracks["primary"].content != "modified in memory"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("name", ["../small_en.yaml", "/small_en.yaml", "definitions/small_en.yaml", "definitions\\small_en.yaml", "small_en.mdkv", "small_en.yaml\x00"])
def test_example_document_rejects_noncanonical_resource_names(name: str):
    with pytest.raises(ValueError, match="single canonical"):
        library.load_example_document(name)


def test_example_document_missing_resource():
    with pytest.raises(FileNotFoundError):
        library.load_example_document("does-not-exist.yaml")


def test_resource_api_accepts_nonfilesystem_traversables(tmp_path: Path, monkeypatch):
    authored = library.example_definitions_dir().joinpath("small_en.yaml").read_text(encoding="utf-8")
    archive = tmp_path / "resources.zip"
    with ZipFile(archive, "w") as handle:
        handle.writestr("definitions/small_en.yaml", authored)
    with ZipFile(archive, "r") as handle:
        def resource_files(package: str):
            assert package == "mdkv.resources"
            return ZipPath(handle)

        monkeypatch.setattr(library, "files", resource_files)
        resource = library.example_definitions_dir().joinpath("small_en.yaml")
        assert not isinstance(resource, Path)
        assert library.load_example_document("small_en.yaml").title == library.load_example_definition(resource)["title"]


@pytest.fixture
def science_tracks() -> dict[str, Track]:
    return library.load_example_document("active_inference.yaml").tracks


def execute_authored_python(track: Track) -> dict[str, Any]:
    blocks = re.findall(r"```python\n(.*?)```", track.content, flags=re.DOTALL)
    assert len(blocks) == 1
    tree = ast.parse(blocks[0])
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert imports
    assert all(isinstance(node, ast.ImportFrom) and node.module == "math" for node in imports)
    namespace: dict[str, Any] = {}
    exec(compile(tree, f"<authored:{track.track_id}>", "exec"), namespace)
    return namespace


@pytest.fixture
def simulation(science_tracks):
    return execute_authored_python(science_tracks["code-python-simulation"])


def make_agent(simulation, prior, likelihood=None):
    return simulation["DiscreteAIF"](
        likelihood if likelihood is not None else [[0.8, 0.2], [0.2, 0.8]],
        [[[1.0, 0.0], [0.0, 1.0]]],
        [0.0, 2.0],
        prior,
    )


def test_authored_bayes_update_uses_nonuniform_prior(simulation):
    prior = [0.9, 0.1]
    agent = make_agent(simulation, prior)
    posterior = agent.posterior_update(0)
    assert posterior == pytest.approx([0.72 / 0.74, 0.02 / 0.74])
    assert math.fsum(posterior) == pytest.approx(1.0)
    assert prior == [0.9, 0.1]
    posterior[0] = 0.0
    assert agent.Qs[0] == pytest.approx(0.72 / 0.74)


@pytest.mark.parametrize("prior", [[1.0, 0.0], [0.0, 1.0]])
def test_authored_update_preserves_zero_prior_states(simulation, prior):
    agent = make_agent(simulation, prior)
    assert agent.posterior_update(0) == prior


def test_authored_update_respects_zero_likelihood(simulation):
    agent = make_agent(simulation, [0.9, 0.1], [[0.0, 1.0], [1.0, 0.0]])
    assert agent.posterior_update(0) == [0.0, 1.0]


def test_authored_update_rejects_impossible_evidence_without_mutation(simulation):
    agent = make_agent(simulation, [1.0, 0.0], [[0.0, 1.0], [1.0, 0.0]])
    with pytest.raises(ValueError, match="zero evidence"):
        agent.posterior_update(0)
    assert agent.Qs == [1.0, 0.0]


def test_both_authored_python_examples_compute_declared_heuristic(science_tracks, simulation):
    primary = execute_authored_python(science_tracks["primary"])
    prior = [0.9, 0.1]
    likelihood = [[0.8, 0.2], [0.2, 0.8]]
    predictive = [0.74, 0.26]
    expected = -2.0 * predictive[1] - 0.1 * math.fsum(p * math.log(p) for p in predictive)
    assert primary["heuristic_policy_score"](prior, likelihood, [0.0, 2.0]) == pytest.approx(expected)
    agent = make_agent(simulation, prior)
    assert agent.heuristic_policy_score(0) == pytest.approx(expected)
    assert math.fsum(primary["softmax"]([-1000.0, -1001.0])) == pytest.approx(1.0)
    deterministic = make_agent(simulation, [1.0, 0.0], [[1.0, 0.0], [0.0, 1.0]])
    assert deterministic.heuristic_policy_score(0) == pytest.approx(0.0)


