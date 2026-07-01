import inspect

from marimo._dependencies.errors import ManyModulesNotFoundError
from marimo._runtime.runtime import Kernel


class _FakePackageManager:
    name = "fake"

    def __init__(self) -> None:
        self._attempted: set[str] = set()

    def should_auto_install(self) -> bool:
        return False

    def attempted_to_install(self, package: str) -> bool:
        return package in self._attempted

    def module_to_package(self, mod: str) -> str:
        return mod


class _FakeModuleRegistry:
    def missing_modules(self) -> set[str]:
        return set()


class _FakeRunner:
    def __init__(self, exc: BaseException) -> None:
        self.exceptions = {0: exc}


def _make_many_modules_not_found_error(package_names: list[str]) -> ManyModulesNotFoundError:
    """
    Construct ManyModulesNotFoundError in a way that's compatible with the repo's
    actual signature (which may be positional-only or have different arg names).
    """
    sig = inspect.signature(ManyModulesNotFoundError)
    params = list(sig.parameters.values())

    # Try (package_names,) if the first param looks like it corresponds to package_names
    # (common for custom error types).
    try:
        return ManyModulesNotFoundError(package_names)  # type: ignore[arg-type]
    except TypeError:
        pass

    # Try (message, package_names)
    try:
        return ManyModulesNotFoundError("missing packages", package_names)  # type: ignore[arg-type]
    except TypeError:
        pass

    # Try keyword-only / keyword-capable if present
    if any(p.name == "package_names" for p in params):
        try:
            return ManyModulesNotFoundError(package_names=package_names)  # type: ignore[call-arg]
        except TypeError:
            pass
        try:
            return ManyModulesNotFoundError("missing packages", package_names=package_names)  # type: ignore[call-arg]
        except TypeError:
            pass

    raise RuntimeError(
        "Unable to construct ManyModulesNotFoundError with package_names; "
        f"signature was: {sig}"
    )


def test_broadcast_missing_packages_handles_many_modules_error_as_packages_not_modules():
    """
    When a ManyModulesNotFoundError provides package_names, those should be treated
    as packages directly and should NOT be fed through module_to_package.

    This is observable by ensuring module_to_package is never called when the only
    missing info comes from ManyModulesNotFoundError.package_names.
    """
    k = Kernel.__new__(Kernel)
    k.package_manager = _FakePackageManager()
    k.module_registry = _FakeModuleRegistry()

    called_with: list[str] = []

    def recording_module_to_package(mod: str) -> str:
        called_with.append(mod)
        return mod

    # Record any conversions; correct code should not convert package_names.
    k.package_manager.module_to_package = recording_module_to_package  # type: ignore[method-assign]

    # Ensure no side effects if reached.
    k._execute_install_missing_packages_callback = lambda *args, **kwargs: None  # type: ignore[method-assign]

    exc = _make_many_modules_not_found_error(["sklearn", "pandas"])
    runner = _FakeRunner(exc)

    k._broadcast_missing_packages(runner)

    assert called_with == [], (
        "Expected ManyModulesNotFoundError.package_names to be treated as "
        "packages directly (no module_to_package calls). "
        f"Got module_to_package called with: {called_with}"
    )