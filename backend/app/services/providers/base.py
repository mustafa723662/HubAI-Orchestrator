class ProviderNotConfigured(Exception):
    """Raised when a provider is chosen but its API key/SDK isn't set up yet."""


class ProviderUnsupported(Exception):
    """Raised when a provider has no automated way to be called at all."""
