try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    # For Python <3.8, fallback to importlib-metadata package
    from importlib_metadata import version, PackageNotFoundError

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    __version__ = "unknown"
