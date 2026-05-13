"""CLI error formatting."""

from dataclasses import dataclass


@dataclass(frozen=True)
class OptionalDependency:
    package_name: str
    extra: str


OPTIONAL_DEPENDENCIES = {
    "PIL": OptionalDependency("Pillow", "image"),
    "fitz": OptionalDependency("PyMuPDF", "ocr"),
    "pypdf": OptionalDependency("pypdf", "pdf"),
    "reportlab": OptionalDependency("reportlab", "image"),
}


def format_optional_dependency_error(error: ModuleNotFoundError) -> str | None:
    dependency = get_optional_dependency(error)
    if dependency is None:
        return None

    return (
        f"Missing optional dependency: {dependency.package_name}. "
        f"Install with `pliage[{dependency.extra}]` or `pliage[all]`."
    )


def get_optional_dependency(error: ModuleNotFoundError) -> OptionalDependency | None:
    return OPTIONAL_DEPENDENCIES.get(error.name or "")
