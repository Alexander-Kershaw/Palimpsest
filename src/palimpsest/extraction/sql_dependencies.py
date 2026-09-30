from uuid import UUID

from sqlglot import exp, find_tables

from palimpsest.domain.asset import Asset, AssetIdentity, AssetKind
from palimpsest.domain.observation import Observation
from palimpsest.domain.predicates import Predicate


class SqlDependencyExtractor:
    name: str = "SqlDependencyExtractor"

    def extract(
        self,
        *,
        statements: tuple[exp.Expression, ...],
        subject: Asset,
        artifact_id: UUID,
        relation_namespace: str,
    ) -> tuple[Observation, ...]:

        if subject.identity.kind is not AssetKind.SQL_SCRIPT:
            raise ValueError(
                "SQL dependency extraction requires a SQL_SCRIPT subject (Asset)"
            )

        self._validate_namespace(relation_namespace)

        observations: list[Observation] = []

        for statement_nbr, statement in enumerate(iterable=statements, start=1):
            location: str = f"statement {statement_nbr}"

            observations.extend(
                self._extract_reads(
                    statement=statement,
                    subject=subject,
                    artifact_id=artifact_id,
                    relation_namespace=relation_namespace,
                    location=location,
                )
            )

            observations.extend(
                self._extract_writes(
                    statement=statement,
                    subject=subject,
                    artifact_id=artifact_id,
                    relation_namespace=relation_namespace,
                    location=location,
                )
            )

        return tuple(observations)

    def _extract_reads(
        self,
        *,
        statement: exp.Expression,
        subject: Asset,
        artifact_id: UUID,
        relation_namespace: str,
        location: str,
    ) -> tuple[Observation, ...]:

        locators: list[str] = sorted(
            {
                self._table_locator(table=tbl)
                for tbl in find_tables(expression=statement)
            }
        )

        return tuple(
            Observation(
                subject=subject,
                predicate=Predicate.READS_FROM,
                object=self._relation_asset(
                    locator=locator, relation_namespace=relation_namespace
                ),
                artifact_id=artifact_id,
                extractor=self.name,
                location=location,
            )
            for locator in locators
        )

    def _extract_writes(
        self,
        *,
        statement: exp.Expression,
        subject: Asset,
        artifact_id: UUID,
        relation_namespace: str,
        location: str,
    ) -> tuple[Observation, ...]:

        if not isinstance(statement, exp.Insert):
            return ()

        target: exp.Table | None = self._insert_target(statement)

        if target is None:
            return ()

        return (
            Observation(
                subject=subject,
                predicate=Predicate.WRITES_TO,
                object=self._relation_asset(
                    locator=self._table_locator(table=target),
                    relation_namespace=relation_namespace,
                ),
                artifact_id=artifact_id,
                extractor=self.name,
                location=location,
            ),
        )

    @staticmethod
    def _insert_target(
        statement: exp.Insert,
    ) -> exp.Table | None:

        target = statement.this

        if isinstance(target, exp.Table):
            return target

        return target.find(exp.Table)

    @staticmethod
    def _table_locator(table: exp.Table) -> str:

        return ".".join(part.name for part in table.parts)

    @staticmethod
    def _relation_asset(
        *,
        locator: str,
        relation_namespace: str,
    ) -> Asset:

        return Asset(
            identity=AssetIdentity(
                kind=AssetKind.TABLE,
                source_namespace=relation_namespace,
                locator=locator,
            )
        )

    @staticmethod
    def _validate_namespace(
        relation_namespace: str,
    ) -> None:

        if not relation_namespace.strip():
            raise ValueError("relation_namespace cannot be blank")

        if relation_namespace != relation_namespace.strip():
            raise ValueError(
                "relation_namespace cannot contain leading or trailing whitespace"
            )
