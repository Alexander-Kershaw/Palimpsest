from collections import defaultdict
from collections.abc import Iterable

from palimpsest.domain.claim import Claim, DirectClaim
from palimpsest.domain.observation import Observation

"""
========================================================================================================

DIRECT CLAIMS

========================================================================================================

Different artifacts can independently produce the same observations, for example:

Artifact A
    ↓
Observation
load_customer.sql READS_FROM stg_customer

But also there is,

Artifact B
    ↓
Observation
load_customer.sql READS_FROM stg_customer


These are not considered two different propositions. There is but one unifying proposition:

load_customer.sql READS_FROM stg_customer

with two supporting observations.

Observations can be shared between claims. So I am distinguishing claims with direct propositions
and those that have evidential support by a multitude of other Claims observations.

so, I am defining:

Claim
    = normalized proposition

DirectClaim
    = proposition + supporting observations


Therefore, the general structure for a Claim is as follows:

Claim
   │
   ├── DirectClaim
   │      supported by Observations
   │
   └── DerivedClaim
          supported by other Claims


========================================================================================================
"""


def build_direct_claims(
    observations: Iterable[Observation],
) -> tuple[DirectClaim, ...]:
    """
    ===================================================================================================

    This function essentially takes observations and groups them into claims, for example:

            Observation 1:
            A READS_FROM B
            artifact X

            Observation 2:
            A READS_FROM B
            artifact Y

            Observation 3:
            A WRITES_TO C
            artifact X


    These observations are grouping into claims:

            Claim:
        A READS_FROM B
            │
            ├── Observation 1
            └── Observation 2


            Claim:
        A WRITES_TO C
            │
            └── Observation 3

    ===================================================================================================
    """

    grouped: dict[Claim, set[Observation]] = defaultdict(set)

    for observation in observations:
        claim = Claim(
            subject=observation.subject,
            predicate=observation.predicate,
            object=observation.object,
        )

        grouped[claim].add(observation)

    direct_claims: list[DirectClaim] = [
        DirectClaim(
            claim=claim,
            observations=frozenset(support),
        )
        for claim, support in grouped.items()
    ]

    return tuple(
        sorted(
            direct_claims,
            key=_claim_sort_key,
        )
    )


def _claim_sort_key(
    direct_claim: DirectClaim,
) -> tuple[str, ...]:

    claim: Claim = direct_claim.claim

    return (
        claim.subject.identity.source_namespace,
        claim.subject.identity.kind.value,
        claim.subject.identity.locator,
        claim.predicate.value,
        claim.object.identity.source_namespace,
        claim.object.identity.kind.value,
        claim.object.identity.locator,
    )
