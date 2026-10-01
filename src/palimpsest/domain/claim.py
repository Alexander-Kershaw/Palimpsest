from dataclasses import dataclass

from palimpsest.domain.asset import Asset
from palimpsest.domain.observation import Observation
from palimpsest.domain.predicates import Predicate


@dataclass(frozen=True, slots=True)
class Claim:
    subject: Asset
    predicate: Predicate
    object: Asset


@dataclass(frozen=True, slots=True)
class DirectClaim:
    claim: Claim
    observations: frozenset[
        Observation
    ]  # Frozrn set so evidence is immutable, unique and unordered

    def __post_init__(self) -> None:
        if not self.observations:
            raise ValueError("a direct claim requires at least one observation")

        for observation in self.observations:
            if not self._supports_claim(observation=observation):
                raise ValueError("observation does not support the claim")

    def _supports_claim(self, observation: Observation) -> bool:

        return (
            observation.subject == self.claim.subject
            and observation.predicate is self.claim.predicate
            and observation.object == self.claim.object
        )
