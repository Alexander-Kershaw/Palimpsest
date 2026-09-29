from dataclasses import dataclass, field
from datetime import datetime 
from hashlib import sha256
from uuid import UUID

from palimpsest.domain.asset import Asset

@dataclass(frozen=True, slots=True)
class Artifact:

    """
    ==========================================================================================
    
    ARTIFACT OBJECT

    ==========================================================================================

    The Artifact dataclass introduces the evidence layer to Palimpsest.

    Palimpsest discovers Assets with its Scan protocol. Artifacts represent the evidential
    content within an Asset found in a Scan.

    Consider Palimpsest doscovers an Asset like a SQL script. Also consider 2 scans, Scan A 
    and Scan B.

    The same Asset can have different content over the different Scans, yielding different
    Artifacts for the same Asset, for example:

    ------------------------------------------------------------------------------------------

                    Asset
          sql/10_merge_customers.sql
                      │
             ┌────────┴────────┐
             │                 │
          Scan A            Scan B
             │                 │
             ▼                 ▼
        Artifact A        Artifact B
        hash: abc...      hash: def...

    ------------------------------------------------------------------------------------------

    Regarding Artifacts themselves, an artifact has two different kinds of identity 
    information: the Artifact ID, and the content hash.

    The content hash IS NOT the same as the artifact ID

    the content hash is the collected bytes of the actual content

    While the Artifact ID refers to the evidence collection event

    Consider the following:

    ------------------------------------------------------------------------------------------

            Scan 001
                ↓
            Artifact 001
            content hash = abc123

            Scan 002
                ↓
            Artifact 002
            content hash = abc123

    ------------------------------------------------------------------------------------------

    Over the sequence of Scan events, the content hash is the same, the bytes are identical
    However, the Artifact ID is different, since these are DIFFERENT evidence collection
    events.

    Overall, the relationship between Scan, Asset, and Artifact is as follows:

        Artifact
            │
            ├── belongs to → Scan
            │
            └── snapshot of → Asset

    Note: storing raw bytes for now rather than string representation of the Artifact 
    contents. raw bytes are stronger evidence. The later structure intended is:

        Collector → Artifact bytes
        Parser    → decoded/structured representation

    ==========================================================================================
    """

    artifact_id: UUID
    scan_id: UUID
    asset: Asset
    collected_at: datetime
    content_type: str
    content: bytes
    content_hash: str = field(init=False)

    def __post_init__(self) -> None: 

        self._require_timezone_aware(self.collected_at)

        if not self.content_type.strip():
            raise ValueError("content_type cannot be blank")

        if self.content_type != self.content_type.strip():
            raise ValueError("content_type cannot contain leading or trailing whitespace")

        object.__setattr__(
            self,
            "content_hash",
            sha256(self.content).hexdigest() # deterministic SHA hashing
        )

    @staticmethod
    def _require_timezone_aware(value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("collected_at must be timezone aware")
