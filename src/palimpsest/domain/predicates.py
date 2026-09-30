"""Relationship vocabulary definitions"""

from enum import StrEnum


class Predicate(StrEnum):
    READS_FROM = "READS_FROM"
    WRITES_TO = "WRITES_TO"
    EXECUTES = "EXECUTES"
    DOCUMENTS = "DOCUMENTS"
