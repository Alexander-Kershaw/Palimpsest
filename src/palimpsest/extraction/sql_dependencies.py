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

        tables = self._read_tables(statement)

        locators: list[str] = sorted(
            {self._table_locator(table=table) for table in tables}
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

        target = self._write_target(statement)

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

    @staticmethod
    def _statement_target(statement: exp.Expression) -> exp.Table | None:

        target = statement.this

        if isinstance(target, exp.Table):
            return target

        if isinstance(target, exp.Expression):
            return target.find(exp.Table)

        return None

    @classmethod
    def _physical_tables_in_clause(
        cls,
        *,
        clause: exp.Expression,
        statement: exp.Expression,
    ) -> set[exp.Table]:

        cte_names: set[str] = cls._cte_names(statement)

        tables: set[exp.Table] = set(clause.find_all(exp.Table))

        if isinstance(clause, exp.Table):
            tables.add(clause)

        return {
            table
            for table in tables
            if not (len(table.parts) == 1 and table.name in cte_names)
        }

    @staticmethod
    def _cte_names(
        statement: exp.Expression,
    ) -> set[str]:

        with_clause = statement.args.get("with_")

        if not isinstance(with_clause, exp.With):
            return set()

        return {
            cte.alias_or_name for cte in with_clause.expressions if cte.alias_or_name
        }

    @classmethod
    def _read_tables(cls, statement: exp.Expression) -> set[exp.Table]:

        if isinstance(statement, exp.Insert):
            if statement.expression is None:
                return set()

        if isinstance(statement, exp.Create):
            if statement.kind != "TABLE":
                return set()

            if statement.expression is None:
                return set()

            return set(find_tables(statement.expression))

        if isinstance(statement, exp.Update):
            tables: set[exp.Table] = set(find_tables(expression=statement))

            target: exp.Table | None = cls._statement_target(statement)

            if target is not None:
                tables.add(target)

            from_clause = statement.args.get("from_")

            if isinstance(from_clause, exp.Expression):
                tables.update(
                    cls._physical_tables_in_clause(
                        clause=from_clause,
                        statement=statement,
                    )
                )

            return tables

        if isinstance(statement, exp.Delete):
            tables = set(find_tables(expression=statement))

            target = cls._statement_target(statement)

            if target is not None:
                tables.add(target)

            using_clause = statement.args.get("using")

            if isinstance(using_clause, list):
                for relation in using_clause:
                    if isinstance(relation, exp.Expression):
                        tables.update(
                            cls._physical_tables_in_clause(
                                clause=relation,
                                statement=statement,
                            )
                        )

            elif isinstance(using_clause, exp.Expression):
                tables.update(
                    cls._physical_tables_in_clause(
                        clause=using_clause,
                        statement=statement,
                    )
                )

            return tables

        return set(find_tables(expression=statement))

    @classmethod
    def _write_target(cls, statement: exp.Expression) -> exp.Table | None:

        if isinstance(statement, (exp.Insert, exp.Update, exp.Delete)):
            return cls._statement_target(statement)

        if isinstance(statement, exp.Create) and statement.kind == "TABLE":
            return cls._statement_target(statement)

        return None
