from __future__ import annotations

from mneme_service.config import Settings, StaticTokenSettings
from mneme_service.security import authenticate_bearer, bearer_token


def test_bearer_token_parses_only_bearer_scheme() -> None:
    assert bearer_token("Bearer secret-token") == "secret-token"
    assert bearer_token("Basic secret-token") is None
    assert bearer_token(None) is None


def test_authenticate_bearer_derives_owner_and_scoped_principals() -> None:
    settings = Settings(
        auth_token="owner-token",
        static_tokens=(
            StaticTokenSettings(
                name="repo-a",
                token="scoped-token",
                project_scopes=("project-a",),
                role="ADAPTER",
            ),
        ),
    )

    owner = authenticate_bearer("Bearer owner-token", settings)
    scoped = authenticate_bearer("Bearer scoped-token", settings)

    assert owner is not None
    assert owner.as_audit_principal() == {
        "name": "local-owner",
        "role": "OWNER",
        "project_scopes": ["*"],
    }
    assert owner.can_access_project("anything")
    assert scoped is not None
    assert scoped.as_audit_principal() == {
        "name": "repo-a",
        "role": "ADAPTER",
        "project_scopes": ["project-a"],
    }
    assert scoped.can_access_project("project-a")
    assert not scoped.can_access_project("project-b")
