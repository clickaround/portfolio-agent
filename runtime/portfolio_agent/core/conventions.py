"""Naming conventions shared by every author and backend (so none needs to import another)."""


def is_title(element_id: str) -> bool:
    """Elements whose id starts with 'title' are headings (rendered bold by backends)."""
    return element_id.startswith("title")


def is_footer(element_id: str) -> bool:
    return element_id.startswith(("folio", "rule"))
