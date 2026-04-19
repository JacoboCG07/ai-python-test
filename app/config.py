"""
Configuración central de la aplicación (valores estáticos del reto / entorno local).
"""
from dataclasses import dataclass, field
from pathlib import Path


def _prompts_dir(
) -> Path:
    return Path(__file__).resolve().parent / "prompts"


def _load_extraction_system_prompt(
    *,
    path: Path | None = None,
) -> str:
    """
    Carga el system prompt de extracción desde Markdown en disco.
    """
    prompt_path = path or (_prompts_dir() / "extraction_system.md")
    if not prompt_path.is_file():
        raise FileNotFoundError(
            f"No se encuentra el prompt de extracción: {prompt_path}",
        )
    return prompt_path.read_text(encoding="utf-8").strip()


@dataclass(frozen=True)
class Settings:
    """
    Parámetros del proveedor simulado y límites de concurrencia hacia él.
    """

    api_key: str = "test-dev-2026"
    provider_base: str = "http://127.0.0.1:3001"
    extract_path: str = "/v1/ai/extract"
    notify_path: str = "/v1/notify"
    provider_max_parallel: int = 45
    http_timeout_seconds: float = 60.0
    extraction_system_prompt: str = field(default_factory=_load_extraction_system_prompt)


def get_settings(
    *,
    extraction_prompt_path: Path | None = None,
) -> Settings:
    """
    Factoría de ajustes. Permite inyectar una ruta de prompt alternativa (p. ej. tests).
    """
    if extraction_prompt_path is None:
        return Settings()
    return Settings(
        extraction_system_prompt=_load_extraction_system_prompt(
            path=extraction_prompt_path,
        ),
    )
