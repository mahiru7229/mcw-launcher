import json

from src.core.modrinth.modrinth_client import ModrinthClient


def test_search_builds_fabric_facets_and_parses_projects(monkeypatch):
    captured = {}

    def fake_get_json(path, params=None, ttl=0, force_refresh=False):
        captured.update(path=path, params=params, ttl=ttl)
        return {
            "hits": [{
                "project_id": "abc123",
                "slug": "example",
                "title": "Example Mod",
                "description": "Example",
                "project_type": "mod",
                "author": "Author",
                "downloads": 42,
                "categories": ["fabric"],
                "client_side": "required",
            }],
            "total_hits": 1,
            "offset": 0,
            "limit": 25,
        }

    monkeypatch.setattr(ModrinthClient, "_get_json", fake_get_json)

    result = ModrinthClient.search_projects("mod", "example", game_version="1.20.1", loader="fabric")

    facets = json.loads(captured["params"]["facets"])
    assert ["project_type:mod"] in facets
    assert ["categories:fabric"] in facets
    assert ["versions:1.20.1"] in facets
    assert result.projects[0].title == "Example Mod"
    assert result.projects[0].client_side == "required"


def test_versions_are_sorted_featured_release_first(monkeypatch):
    monkeypatch.setattr(ModrinthClient, "_get_json", lambda *args, **kwargs: [
        {
            "id": "beta",
            "project_id": "project",
            "name": "Beta",
            "version_number": "2.0-beta",
            "version_type": "beta",
            "game_versions": ["1.20.1"],
            "loaders": ["fabric"],
            "featured": False,
            "date_published": "2026-07-12T00:00:00Z",
            "files": [{"url": "https://cdn.modrinth.com/beta.jar", "filename": "beta.jar", "hashes": {"sha1": "a", "sha512": "b"}, "size": 1, "primary": True}],
        },
        {
            "id": "release",
            "project_id": "project",
            "name": "Release",
            "version_number": "1.0",
            "version_type": "release",
            "game_versions": ["1.20.1"],
            "loaders": ["fabric"],
            "featured": True,
            "date_published": "2026-07-10T00:00:00Z",
            "files": [{"url": "https://cdn.modrinth.com/release.jar", "filename": "release.jar", "hashes": {"sha1": "c", "sha512": "d"}, "size": 1, "primary": True}],
        },
    ])

    versions = ModrinthClient.list_project_versions("project", loader="fabric", game_version="1.20.1")

    assert [version.version_id for version in versions] == ["release", "beta"]
    assert versions[0].primary_file(".jar").filename == "release.jar"


def test_user_agent_identifies_launcher():
    assert "mcw-launcher" in ModrinthClient.USER_AGENT
    assert "mahiru7229" in ModrinthClient.USER_AGENT
