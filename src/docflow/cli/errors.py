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
    dependency = OPTIONAL_DEPENDENCIES.get(error.name or "")
    if dependency is None:
        return None

    return (
        f"Missing optional dependency: {dependency.package_name}. "
        f"Install with `docflow[{dependency.extra}]` or `docflow[all]`."
    )
