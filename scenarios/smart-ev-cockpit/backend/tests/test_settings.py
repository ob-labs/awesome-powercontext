from app.settings import BACKEND_ROOT, REPOSITORY_ROOT, Settings


def test_settings_uses_absolute_repository_root_env_when_backend_is_working_directory(
    monkeypatch,
):
    monkeypatch.chdir(BACKEND_ROOT)

    env_files = Settings.model_config["env_file"]

    assert REPOSITORY_ROOT / ".env" in env_files
    assert BACKEND_ROOT / ".env" in env_files
    assert all(path.is_absolute() for path in env_files)
