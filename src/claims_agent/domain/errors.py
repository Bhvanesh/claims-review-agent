class DuplicateClaimError(Exception):
    """Raised when a claim ID already exists within a tenant."""