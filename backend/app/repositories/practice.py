"""Session repository errors shared by the workflow service and persistence layer."""


class PracticeStorageError(Exception):
    pass


class PracticeNotFoundError(Exception):
    pass


class PracticeConflictError(Exception):
    pass
