import hashlib
from typing import Iterable, Optional


def build_failure_signature(
    failed_tests: Iterable[str],
    stack_excerpt: str,
    api_error: Optional[str] = None,
    screenshot_note: Optional[str] = None,
) -> str:
    tests = "|".join(sorted(item.strip() for item in failed_tests if item.strip()))
    normalized = "::".join(
        [
            tests,
            stack_excerpt.strip(),
            (api_error or "").strip(),
            (screenshot_note or "").strip(),
        ]
    )
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]
    return "tests:%s|sig:%s" % (tests or "none", digest)

