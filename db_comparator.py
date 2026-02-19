"""
SQLite Database Comparison Tool
================================
A comprehensive tool to compare two SQLite database files and visualize differences.

"""

import sqlite3
import sys
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import filedialog
from typing import Any, Dict, List, Set, Tuple

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree


@dataclass
class TableComparison:
    """Data class to store table comparison results."""

    table_name: str
    exists_in_db1: bool = True
    exists_in_db2: bool = True
    schema_match: bool = True
    row_count_db1: int = 0
    row_count_db2: int = 0
    schema_diff: List[str] = field(default_factory=list)
    data_differences: Dict[str, Any] = field(default_factory=dict)
    is_identical: bool = True


@dataclass
class DatabaseComparison:
    """Data class to store overall database comparison results."""

    db1_path: str
    db2_path: str
    tables_only_in_db1: Set[str] = field(default_factory=set)
    tables_only_in_db2: Set[str] = field(default_factory=set)
    common_tables: Set[str] = field(default_factory=set)
    table_comparisons: Dict[str, TableComparison] = field(default_factory=dict)
    is_identical: bool = True


class SQLiteComparator:
    """Main class for comparing two SQLite databases."""

    def __init__(self, db1_path: str, db2_path: str):
        """
        Initialize the SQLite comparator.

        Args:
            db1_path: Path to the first database file
            db2_path: Path to the second database file

        Raises:
            FileNotFoundError: If either database file doesn't exist
        """
        self.db1_path = Path(db1_path)
        self.db2_path = Path(db2_path)
        self.console = Console()

        if not self.db1_path.exists():
            raise FileNotFoundError(f"Database 1 not found: {db1_path}")
        if not self.db2_path.exists():
            raise FileNotFoundError(f"Database 2 not found: {db2_path}")

    def get_connection(self, db_path: Path) -> sqlite3.Connection:
        """
        Create a database connection.

        Args:
            db_path: Path to the database file

        Returns:
            sqlite3.Connection: Database connection object
        """
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_table_names(self, conn: sqlite3.Connection) -> Set[str]:
        """
        Get all table names from a database.

        Args:
            conn: Database connection

        Returns:
            Set[str]: Set of table names
        """
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        return {row[0] for row in cursor.fetchall()}

    def get_table_schema(self, conn: sqlite3.Connection, table_name: str) -> List[Tuple]:
        """
        Get the schema of a specific table.

        Args:
            conn: Database connection
            table_name: Name of the table

        Returns:
            List[Tuple]: List of column definitions
        """
        cursor = conn.cursor()
        # Use square brackets to properly quote table names
        cursor.execute(f"PRAGMA table_info([{table_name}])")
        return cursor.fetchall()

    def get_row_count(self, conn: sqlite3.Connection, table_name: str) -> int:
        """
        Get the number of rows in a table.

        Args:
            conn: Database connection
            table_name: Name of the table

        Returns:
            int: Number of rows
        """
        cursor = conn.cursor()
        # Use square brackets to properly quote table names
        cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
        return cursor.fetchone()[0]

    def get_table_data(self, conn: sqlite3.Connection, table_name: str) -> List[Dict]:
        """
        Get all data from a table.

        Args:
            conn: Database connection
            table_name: Name of the table

        Returns:
            List[Dict]: List of rows as dictionaries
        """
        cursor = conn.cursor()
        # Use square brackets to properly quote table names
        cursor.execute(f"SELECT * FROM [{table_name}]")
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def compare_schemas(
        self, schema1: List[Tuple], schema2: List[Tuple]
    ) -> Tuple[bool, List[str]]:
        """
        Compare two table schemas.

        Args:
            schema1: Schema from database 1
            schema2: Schema from database 2

        Returns:
            Tuple[bool, List[str]]: (schemas_match, list_of_differences)
        """
        differences = []

        # Convert to dictionaries for easier comparison
        schema1_dict = {col[1]: col for col in schema1}  # col[1] is column name
        schema2_dict = {col[1]: col for col in schema2}

        # Check for columns only in schema1
        for col_name in schema1_dict:
            if col_name not in schema2_dict:
                differences.append(f"Column '{col_name}' exists in DB1 but not in DB2")

        # Check for columns only in schema2
        for col_name in schema2_dict:
            if col_name not in schema1_dict:
                differences.append(f"Column '{col_name}' exists in DB2 but not in DB1")

        # Check for column definition differences
        for col_name in schema1_dict:
            if col_name in schema2_dict:
                if schema1_dict[col_name] != schema2_dict[col_name]:
                    differences.append(
                        f"Column '{col_name}' has different definitions: "
                        f"DB1={schema1_dict[col_name][2]} vs DB2={schema2_dict[col_name][2]}"
                    )

        return len(differences) == 0, differences

    def compare_table_data(
        self, data1: List[Dict], data2: List[Dict]
    ) -> Dict[str, Any]:
        """
        Compare data between two tables.

        Args:
            data1: Data from database 1
            data2: Data from database 2

        Returns:
            Dict[str, Any]: Dictionary containing comparison results
        """
        differences = {
            "row_count_match": len(data1) == len(data2),
            "rows_only_in_db1": 0,
            "rows_only_in_db2": 0,
            "modified_rows": 0,
            "identical_rows": 0,
            "is_data_identical": False,
        }

        # If both are empty, they're identical
        if len(data1) == 0 and len(data2) == 0:
            differences["is_data_identical"] = True
            return differences

        # Normalize data for comparison (handle None, strip strings, etc.)
        def normalize_row(row: Dict) -> frozenset:
            """Normalize a row for comparison."""
            normalized = {}
            for key, value in row.items():
                # Handle None values
                if value is None:
                    normalized[key] = None
                # Strip whitespace from strings
                elif isinstance(value, str):
                    normalized[key] = value.strip()
                # Handle floating point numbers (round to avoid precision issues)
                elif isinstance(value, float):
                    normalized[key] = round(value, 10)
                else:
                    normalized[key] = value
            return frozenset(normalized.items())

        # Convert to sets for comparison
        try:
            data1_set = {normalize_row(row) for row in data1}
            data2_set = {normalize_row(row) for row in data2}

            # Calculate differences
            only_in_db1 = data1_set - data2_set
            only_in_db2 = data2_set - data1_set
            identical = data1_set & data2_set

            differences["rows_only_in_db1"] = len(only_in_db1)
            differences["rows_only_in_db2"] = len(only_in_db2)
            differences["identical_rows"] = len(identical)

            # Check if data is truly identical
            differences["is_data_identical"] = (
                len(only_in_db1) == 0
                and len(only_in_db2) == 0
                and len(data1) == len(data2)
            )

        except Exception as e:
            # Fallback to simple comparison if normalization fails
            differences["comparison_error"] = str(e)
            differences["rows_only_in_db1"] = len(data1)
            differences["rows_only_in_db2"] = len(data2)

        return differences

    def compare_table(
        self, conn1: sqlite3.Connection, conn2: sqlite3.Connection, table_name: str
    ) -> TableComparison:
        """
        Compare a single table between two databases.

        Args:
            conn1: Connection to database 1
            conn2: Connection to database 2
            table_name: Name of the table to compare

        Returns:
            TableComparison: Comparison results for the table
        """
        comparison = TableComparison(table_name=table_name)

        # Get schemas
        schema1 = self.get_table_schema(conn1, table_name)
        schema2 = self.get_table_schema(conn2, table_name)

        # Compare schemas
        comparison.schema_match, comparison.schema_diff = self.compare_schemas(
            schema1, schema2
        )

        # Get row counts
        comparison.row_count_db1 = self.get_row_count(conn1, table_name)
        comparison.row_count_db2 = self.get_row_count(conn2, table_name)

        # Compare data if schemas match
        if comparison.schema_match:
            data1 = self.get_table_data(conn1, table_name)
            data2 = self.get_table_data(conn2, table_name)
            comparison.data_differences = self.compare_table_data(data1, data2)

        # Determine if table is identical - UPDATED LOGIC
        comparison.is_identical = (
            comparison.schema_match
            and comparison.row_count_db1 == comparison.row_count_db2
            and comparison.data_differences.get("is_data_identical", False)
        )

        return comparison

    def compare_databases(self) -> DatabaseComparison:
        """
        Perform complete comparison of two databases.

        Returns:
            DatabaseComparison: Complete comparison results
        """
        comparison = DatabaseComparison(
            db1_path=str(self.db1_path), db2_path=str(self.db2_path)
        )

        with (
            self.get_connection(self.db1_path) as conn1,
            self.get_connection(self.db2_path) as conn2,
        ):
            # Get table names
            tables1 = self.get_table_names(conn1)
            tables2 = self.get_table_names(conn2)

            # Find table differences
            comparison.tables_only_in_db1 = tables1 - tables2
            comparison.tables_only_in_db2 = tables2 - tables1
            comparison.common_tables = tables1 & tables2

            # Compare common tables
            for table_name in comparison.common_tables:
                table_comp = self.compare_table(conn1, conn2, table_name)
                comparison.table_comparisons[table_name] = table_comp
                if not table_comp.is_identical:
                    comparison.is_identical = False

            # If there are tables only in one database, they're not identical
            if comparison.tables_only_in_db1 or comparison.tables_only_in_db2:
                comparison.is_identical = False

        return comparison

    def display_results(self, comparison: DatabaseComparison):
        """
        Display comparison results using Rich formatting.

        Args:
            comparison: DatabaseComparison object with results
        """
        self.console.print("\n")

        # Header
        header = Panel(
            Text(
                "SQLite Database Comparison Report",
                justify="center",
                style="bold white",
            ),
            style="bold blue",
            box=box.DOUBLE,
        )
        self.console.print(header)

        # Database paths
        paths_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
        paths_table.add_column("Label", style="bold cyan")
        paths_table.add_column("Path", style="white")
        paths_table.add_row("Database 1:", comparison.db1_path)
        paths_table.add_row("Database 2:", comparison.db2_path)
        self.console.print(paths_table)
        self.console.print()

        # Overall summary
        if comparison.is_identical:
            summary_panel = Panel(
                Text("✓ DATABASES ARE IDENTICAL", justify="center", style="bold green"),
                style="green",
                box=box.DOUBLE,
            )
            self.console.print(summary_panel)
        else:
            summary_panel = Panel(
                Text(
                    "✗ DATABASES HAVE DIFFERENCES", justify="center", style="bold red"
                ),
                style="red",
                box=box.DOUBLE,
            )
            self.console.print(summary_panel)

        self.console.print()

        # Table structure comparison
        structure_table = Table(title="Table Structure Comparison", box=box.HEAVY_EDGE)
        structure_table.add_column("Category", style="bold")
        structure_table.add_column("Count", justify="right")
        structure_table.add_column("Tables", style="italic")

        total_tables_db1 = len(comparison.common_tables) + len(
            comparison.tables_only_in_db1
        )
        total_tables_db2 = len(comparison.common_tables) + len(
            comparison.tables_only_in_db2
        )

        structure_table.add_row(
            "Total Tables in DB1",
            str(total_tables_db1),
            ", ".join(sorted(comparison.common_tables | comparison.tables_only_in_db1))
            or "None",
        )
        structure_table.add_row(
            "Total Tables in DB2",
            str(total_tables_db2),
            ", ".join(sorted(comparison.common_tables | comparison.tables_only_in_db2))
            or "None",
        )
        structure_table.add_row(
            "[green]Common Tables[/green]",
            f"[green]{len(comparison.common_tables)}[/green]",
            f"[green]{', '.join(sorted(comparison.common_tables)) or 'None'}[/green]",
        )

        if comparison.tables_only_in_db1:
            structure_table.add_row(
                "[red]Only in DB1[/red]",
                f"[red]{len(comparison.tables_only_in_db1)}[/red]",
                f"[red]{', '.join(sorted(comparison.tables_only_in_db1))}[/red]",
            )

        if comparison.tables_only_in_db2:
            structure_table.add_row(
                "[red]Only in DB2[/red]",
                f"[red]{len(comparison.tables_only_in_db2)}[/red]",
                f"[red]{', '.join(sorted(comparison.tables_only_in_db2))}[/red]",
            )

        self.console.print(structure_table)
        self.console.print()

        # Detailed table comparisons
        if comparison.common_tables:
            self.console.print(Panel("Detailed Table Comparisons", style="bold yellow"))

            for table_name in sorted(comparison.common_tables):
                table_comp = comparison.table_comparisons[table_name]

                # Determine border color
                border_style = "green" if table_comp.is_identical else "red"
                status_symbol = "✓" if table_comp.is_identical else "✗"
                status_text = (
                    "IDENTICAL" if table_comp.is_identical else "DIFFERENCES FOUND"
                )

                # Create table details
                details_table = Table(
                    title=f"{status_symbol} Table: {table_name} - {status_text}",
                    box=box.HEAVY_HEAD,
                    border_style=border_style,
                    show_header=True,
                )
                details_table.add_column("Property", style="bold")
                details_table.add_column("DB1", justify="right")
                details_table.add_column("DB2", justify="right")
                details_table.add_column("Status", justify="center")

                # Row count comparison
                row_status = (
                    "✓" if table_comp.row_count_db1 == table_comp.row_count_db2 else "✗"
                )
                row_style = (
                    "green"
                    if table_comp.row_count_db1 == table_comp.row_count_db2
                    else "red"
                )
                details_table.add_row(
                    "Row Count",
                    str(table_comp.row_count_db1),
                    str(table_comp.row_count_db2),
                    f"[{row_style}]{row_status}[/{row_style}]",
                )

                # Schema comparison
                schema_status = "✓" if table_comp.schema_match else "✗"
                schema_style = "green" if table_comp.schema_match else "red"
                details_table.add_row(
                    "Schema Match",
                    "-",
                    "-",
                    f"[{schema_style}]{schema_status}[/{schema_style}]",
                )

                self.console.print(details_table)

                # Schema differences
                if table_comp.schema_diff:
                    diff_panel = Panel(
                        "\n".join(f"• {diff}" for diff in table_comp.schema_diff),
                        title="Schema Differences",
                        style="red",
                        box=box.ROUNDED,
                    )
                    self.console.print(diff_panel)

                # Data differences
                if table_comp.data_differences:
                    data_table = Table(box=box.SIMPLE, show_header=True)
                    data_table.add_column("Metric", style="bold")
                    data_table.add_column("Count", justify="right")

                    diff_data = table_comp.data_differences

                    if diff_data.get("identical_rows", 0) > 0:
                        data_table.add_row(
                            "[green]Identical Rows[/green]",
                            f"[green]{diff_data['identical_rows']}[/green]",
                        )

                    if diff_data.get("rows_only_in_db1", 0) > 0:
                        data_table.add_row(
                            "[red]Rows only in DB1[/red]",
                            f"[red]{diff_data['rows_only_in_db1']}[/red]",
                        )

                    if diff_data.get("rows_only_in_db2", 0) > 0:
                        data_table.add_row(
                            "[red]Rows only in DB2[/red]",
                            f"[red]{diff_data['rows_only_in_db2']}[/red]",
                        )

                    if data_table.row_count > 0:
                        self.console.print(data_table)

                self.console.print()

        # Final summary
        self.console.print(Panel("Summary", style="bold magenta"))

        summary_tree = Tree("📊 Comparison Summary")

        if comparison.is_identical:
            summary_tree.add(
                "[bold green]✓ Databases are completely identical[/bold green]"
            )
        else:
            diff_node = summary_tree.add("[bold red]✗ Differences detected:[/bold red]")

            if comparison.tables_only_in_db1:
                db1_only_node = diff_node.add(
                    f"[red]• {len(comparison.tables_only_in_db1)} table(s) only in DB1[/red]"
                )
                for table in sorted(comparison.tables_only_in_db1):
                    db1_only_node.add(f"[red]└─ {table}[/red]")

            if comparison.tables_only_in_db2:
                db2_only_node = diff_node.add(
                    f"[red]• {len(comparison.tables_only_in_db2)} table(s) only in DB2[/red]"
                )
                for table in sorted(comparison.tables_only_in_db2):
                    db2_only_node.add(f"[red]└─ {table}[/red]")

            non_identical_tables = [
                name
                for name, comp in comparison.table_comparisons.items()
                if not comp.is_identical
            ]

            if non_identical_tables:
                tables_diff_node = diff_node.add(
                    f"[red]• {len(non_identical_tables)} common table(s) with differences:[/red]"
                )

                for table_name in sorted(non_identical_tables):
                    table_comp = comparison.table_comparisons[table_name]
                    table_node = tables_diff_node.add(
                        f"[yellow]📋 {table_name}[/yellow]"
                    )

                    # Schema differences
                    if not table_comp.schema_match:
                        schema_node = table_node.add("[red]⚠ Schema mismatch[/red]")
                        for diff in table_comp.schema_diff[
                            :3
                        ]:  # Show first 3 differences
                            schema_node.add(f"[red]• {diff}[/red]")
                        if len(table_comp.schema_diff) > 3:
                            schema_node.add(
                                f"[red]• ... and {len(table_comp.schema_diff) - 3} more[/red]"
                            )

                    # Row count differences
                    if table_comp.row_count_db1 != table_comp.row_count_db2:
                        table_node.add(
                            f"[red]⚠ Row count: DB1={table_comp.row_count_db1} vs DB2={table_comp.row_count_db2} "
                            f"(Δ {abs(table_comp.row_count_db1 - table_comp.row_count_db2)})[/red]"
                        )

                    # Data differences
                    if table_comp.data_differences:
                        diff_data = table_comp.data_differences

                        # Check if data is actually identical
                        if diff_data.get("is_data_identical", False):
                            table_node.add(
                                f"[green]✓ All {diff_data.get('identical_rows', 0)} rows are identical[/green]"
                            )
                        else:
                            if diff_data.get("rows_only_in_db1", 0) > 0:
                                table_node.add(
                                    f"[red]⚠ {diff_data['rows_only_in_db1']} row(s) only in DB1[/red]"
                                )

                            if diff_data.get("rows_only_in_db2", 0) > 0:
                                table_node.add(
                                    f"[red]⚠ {diff_data['rows_only_in_db2']} row(s) only in DB2[/red]"
                                )

                            if diff_data.get("identical_rows", 0) > 0:
                                table_node.add(
                                    f"[green]✓ {diff_data['identical_rows']} identical row(s)[/green]"
                                )
        self.console.print(summary_tree)
        self.console.print()

        # Add a detailed differences table
        if not comparison.is_identical:
            self.console.print()
            diff_summary_table = Table(
                title="📋 Quick Differences Overview",
                box=box.HEAVY_EDGE,
                border_style="red",
            )
            diff_summary_table.add_column("Table", style="bold yellow")
            diff_summary_table.add_column("Issue Type", style="bold")
            diff_summary_table.add_column("Details", style="white")

            # Tables only in one DB
            for table in sorted(comparison.tables_only_in_db1):
                diff_summary_table.add_row(
                    table,
                    "[red]Missing in DB2[/red]",
                    "Table exists only in Database 1",
                )

            for table in sorted(comparison.tables_only_in_db2):
                diff_summary_table.add_row(
                    table,
                    "[red]Missing in DB1[/red]",
                    "Table exists only in Database 2",
                )

            # Common tables with differences
            for table_name in sorted(non_identical_tables):  # type: ignore
                table_comp = comparison.table_comparisons[table_name]
                issues = []

                if not table_comp.schema_match:
                    issues.append(
                        f"Schema: {len(table_comp.schema_diff)} difference(s)"
                    )

                if table_comp.row_count_db1 != table_comp.row_count_db2:
                    issues.append(
                        f"Rows: {table_comp.row_count_db1} vs {table_comp.row_count_db2}"
                    )

                if table_comp.data_differences:
                    diff_data = table_comp.data_differences
                    data_issues = []

                    if diff_data.get("rows_only_in_db1", 0) > 0:
                        data_issues.append(
                            f"{diff_data['rows_only_in_db1']} unique to DB1"
                        )

                    if diff_data.get("rows_only_in_db2", 0) > 0:
                        data_issues.append(
                            f"{diff_data['rows_only_in_db2']} unique to DB2"
                        )

                    if data_issues:
                        issues.append(f"Data: {', '.join(data_issues)}")

                diff_summary_table.add_row(
                    table_name,
                    "[red]Data/Schema Diff[/red]",
                    " | ".join(issues) if issues else "Unknown difference",
                )

            self.console.print(diff_summary_table)
            self.console.print()
            self.display_detailed_differences(comparison)

    # --------- Additional helper methods for future enhancements (e.g., export results, generate reports, etc.) can be added here ---------

    def analyze_row_differences(
        self,
        data1: List[Dict],
        data2: List[Dict],
        table_name: str,
        max_samples: int = 5,
    ) -> Dict[str, Any]:
        """
        Analyze detailed differences between rows in two datasets.

        Args:
            data1: Data from database 1
            data2: Data from database 2
            table_name: Name of the table being compared
            max_samples: Maximum number of sample differences to show

        Returns:
            Dict containing detailed difference analysis
        """
        analysis = {
            "type_mismatches": [],
            "value_mismatches": [],
            "sample_rows_db1_only": [],
            "sample_rows_db2_only": [],
            "is_type_only_difference": False,
        }

        if not data1 or not data2:
            return analysis

        # Get column names
        columns = list(data1[0].keys()) if data1 else []

        # Create lookup dictionaries with string keys for matching
        def create_lookup_key(row: Dict) -> str:
            """Create a string key from row values for matching."""
            return "|".join(str(v) if v is not None else "NULL" for v in row.values())

        # Map rows by their string representation
        data1_by_key = {create_lookup_key(row): row for row in data1}
        data2_by_key = {create_lookup_key(row): row for row in data2}

        # Find rows that match by value but might have type differences
        type_mismatch_count = 0

        for key1, row1 in list(data1_by_key.items())[: max_samples * 2]:
            # Check if this row exists in DB2 with same string values
            if key1 in data2_by_key:
                row2 = data2_by_key[key1]

                # Check for type differences
                for col in columns:
                    val1 = row1.get(col)
                    val2 = row2.get(col)

                    # Check if values are equal but types differ
                    if str(val1) == str(val2) and type(val1) != type(val2):  # noqa: E721
                        type_mismatch_count += 1
                        if len(analysis["type_mismatches"]) < max_samples:
                            analysis["type_mismatches"].append(
                                {
                                    "column": col,
                                    "value": str(val1),
                                    "type_db1": type(val1).__name__,
                                    "type_db2": type(val2).__name__,
                                    "sample_row": {
                                        k: str(v)[:50] for k, v in row1.items()
                                    },
                                }
                            )

        # Find actual data mismatches (different values)
        keys1_only = set(data1_by_key.keys()) - set(data2_by_key.keys())
        keys2_only = set(data2_by_key.keys()) - set(data1_by_key.keys())

        # Sample rows only in DB1
        for key in list(keys1_only)[:max_samples]:
            row = data1_by_key[key]
            analysis["sample_rows_db1_only"].append(
                {k: str(v)[:100] if v is not None else "NULL" for k, v in row.items()}
            )

        # Sample rows only in DB2
        for key in list(keys2_only)[:max_samples]:
            row = data2_by_key[key]
            analysis["sample_rows_db2_only"].append(
                {k: str(v)[:100] if v is not None else "NULL" for k, v in row.items()}
            )

        # Determine if differences are type-only
        analysis["is_type_only_difference"] = (
            len(analysis["type_mismatches"]) > 0
            and len(keys1_only) == 0
            and len(keys2_only) == 0
        )

        return analysis

    def display_detailed_differences_old(self, comparison: DatabaseComparison):
        """
        Display detailed row-level differences for tables with mismatches.

        Args:
            comparison: DatabaseComparison object with results
        """
        non_identical_tables = [
            name
            for name, comp in comparison.table_comparisons.items()
            if not comp.is_identical
        ]

        if not non_identical_tables:
            return

        self.console.print("\n")
        self.console.print(
            Panel("🔍 Detailed Difference Analysis", style="bold cyan", box=box.DOUBLE)
        )

        with (
            self.get_connection(self.db1_path) as conn1,
            self.get_connection(self.db2_path) as conn2,
        ):
            for table_name in sorted(non_identical_tables):
                table_comp = comparison.table_comparisons[table_name]

                self.console.print(f"\n[bold yellow]{'=' * 80}[/bold yellow]")
                self.console.print(f"[bold cyan]Table: {table_name}[/bold cyan]")
                self.console.print(f"[bold yellow]{'=' * 80}[/bold yellow]\n")

                # Get data for detailed analysis
                data1 = self.get_table_data(conn1, table_name)
                data2 = self.get_table_data(conn2, table_name)

                # Analyze differences
                analysis = self.analyze_row_differences(data1, data2, table_name)

                # Display type mismatches (WARNING - Yellow)
                if analysis["type_mismatches"]:
                    type_panel = Panel(
                        "[bold yellow]⚠ DATA TYPE DIFFERENCES DETECTED[/bold yellow]\n"
                        "[yellow]Values are identical but stored as different data types[/yellow]",
                        style="yellow",
                        box=box.ROUNDED,
                        title="Type Mismatch Warning",
                    )
                    self.console.print(type_panel)

                    type_table = Table(
                        title="Data Type Mismatches",
                        box=box.SIMPLE_HEAD,
                        border_style="yellow",
                    )
                    type_table.add_column("Column", style="bold yellow")
                    type_table.add_column("Sample Value", style="white")
                    type_table.add_column("Type in DB1", style="cyan")
                    type_table.add_column("Type in DB2", style="magenta")

                    for mismatch in analysis["type_mismatches"]:
                        type_table.add_row(
                            mismatch["column"],
                            mismatch["value"][:50],
                            mismatch["type_db1"],
                            mismatch["type_db2"],
                        )

                    self.console.print(type_table)
                    self.console.print()

                # Display actual data differences (ERROR - Red)
                if analysis["sample_rows_db1_only"] or analysis["sample_rows_db2_only"]:
                    if not analysis["is_type_only_difference"]:
                        data_panel = Panel(
                            "[bold red]✗ ACTUAL DATA DIFFERENCES DETECTED[/bold red]\n"
                            "[red]Rows exist in one database but not the other[/red]",
                            style="red",
                            box=box.ROUNDED,
                            title="Data Mismatch Error",
                        )
                        self.console.print(data_panel)

                    # Rows only in DB1
                    if analysis["sample_rows_db1_only"]:
                        self.console.print(
                            f"\n[bold red]Sample rows ONLY in DB1:[/bold red] "
                            f"(Showing {len(analysis['sample_rows_db1_only'])} of "
                            f"{table_comp.data_differences.get('rows_only_in_db1', 0)})"
                        )

                        for idx, row in enumerate(analysis["sample_rows_db1_only"], 1):
                            row_table = Table(
                                title=f"Row #{idx}",
                                box=box.SIMPLE,
                                border_style="red",
                                show_header=True,
                            )
                            row_table.add_column("Column", style="bold")
                            row_table.add_column("Value", style="white")

                            for col, val in row.items():
                                row_table.add_row(col, val)

                            self.console.print(row_table)

                    # Rows only in DB2
                    if analysis["sample_rows_db2_only"]:
                        self.console.print(
                            f"\n[bold red]Sample rows ONLY in DB2:[/bold red] "
                            f"(Showing {len(analysis['sample_rows_db2_only'])} of "
                            f"{table_comp.data_differences.get('rows_only_in_db2', 0)})"
                        )

                        for idx, row in enumerate(analysis["sample_rows_db2_only"], 1):
                            row_table = Table(
                                title=f"Row #{idx}",
                                box=box.SIMPLE,
                                border_style="red",
                                show_header=True,
                            )
                            row_table.add_column("Column", style="bold")
                            row_table.add_column("Value", style="white")

                            for col, val in row.items():
                                row_table.add_row(col, val)

                            self.console.print(row_table)

                # Summary for this table
                if analysis["is_type_only_difference"]:
                    summary_text = (
                        "[bold yellow]✓ CONCLUSION:[/bold yellow] "
                        "[yellow]All data values are identical. "
                        "Differences are only in data types (e.g., string vs integer).[/yellow]"
                    )
                else:
                    summary_text = (
                        "[bold red]✗ CONCLUSION:[/bold red] "
                        "[red]Actual data differences exist beyond just data types.[/red]"
                    )

                self.console.print(Panel(summary_text, box=box.ROUNDED))

    def display_detailed_differences(self, comparison: DatabaseComparison):
        """
        Display detailed row-level differences for tables with mismatches.

        Args:
            comparison: DatabaseComparison object with results
        """
        non_identical_tables = [
            name
            for name, comp in comparison.table_comparisons.items()
            if not comp.is_identical
        ]

        if not non_identical_tables:
            return

        self.console.print("\n")
        self.console.print(
            Panel(
                "🔍 Detailed Difference Analysis - Side by Side Comparison",
                style="bold cyan",
                box=box.DOUBLE,
            )
        )

        with (
            self.get_connection(self.db1_path) as conn1,
            self.get_connection(self.db2_path) as conn2,
        ):
            for table_name in sorted(non_identical_tables):
                table_comp = comparison.table_comparisons[table_name]

                self.console.print(f"\n[bold yellow]{'=' * 100}[/bold yellow]")
                self.console.print(f"[bold cyan]📋 Table: {table_name}[/bold cyan]")
                self.console.print(f"[bold yellow]{'=' * 100}[/bold yellow]\n")

                # Get data for detailed analysis
                data1 = self.get_table_data(conn1, table_name)
                data2 = self.get_table_data(conn2, table_name)

                # Analyze differences
                analysis = self.analyze_row_differences(
                    data1, data2, table_name, max_samples=10
                )

                # Display type mismatches (WARNING - Yellow)
                if analysis["type_mismatches"]:
                    type_panel = Panel(
                        "[bold yellow]⚠ DATA TYPE DIFFERENCES DETECTED[/bold yellow]\n"
                        "[yellow]Values are identical but stored as different data types[/yellow]",
                        style="yellow",
                        box=box.ROUNDED,
                        title="Type Mismatch Warning",
                    )
                    self.console.print(type_panel)

                    type_table = Table(
                        title="Data Type Mismatches - Side by Side",
                        box=box.HEAVY_HEAD,
                        border_style="yellow",
                    )
                    type_table.add_column("Column", style="bold yellow", width=20)
                    type_table.add_column("Sample Value", style="white", width=30)
                    type_table.add_column(
                        "DB1 Type", style="cyan", justify="center", width=15
                    )
                    type_table.add_column(
                        "DB2 Type", style="magenta", justify="center", width=15
                    )
                    type_table.add_column("Match?", justify="center", width=10)

                    for mismatch in analysis["type_mismatches"]:
                        type_table.add_row(
                            mismatch["column"],
                            mismatch["value"][:30] + "..."
                            if len(mismatch["value"]) > 30
                            else mismatch["value"],
                            f"[cyan]{mismatch['type_db1']}[/cyan]",
                            f"[magenta]{mismatch['type_db2']}[/magenta]",
                            "[yellow]Type ≠[/yellow]",
                        )

                    self.console.print(type_table)
                    self.console.print()

                # Display side-by-side row comparisons
                if analysis["sample_rows_db1_only"] or analysis["sample_rows_db2_only"]:
                    if not analysis["is_type_only_difference"]:
                        data_panel = Panel(
                            "[bold red]✗ ACTUAL DATA DIFFERENCES DETECTED[/bold red]\n"
                            "[red]Rows exist in one database but not the other[/red]",
                            style="red",
                            box=box.ROUNDED,
                            title="Data Mismatch Error",
                        )
                        self.console.print(data_panel)

                    # Get all columns for side-by-side comparison
                    all_columns = set()
                    for row in (
                        analysis["sample_rows_db1_only"]
                        + analysis["sample_rows_db2_only"]
                    ):
                        all_columns.update(row.keys())
                    all_columns = sorted(all_columns)

                    # Display side-by-side comparison
                    max_rows = max(
                        len(analysis["sample_rows_db1_only"]),
                        len(analysis["sample_rows_db2_only"]),
                    )

                    if max_rows > 0:
                        self.console.print(
                            "\n[bold white]Side-by-Side Row Comparison:[/bold white]"
                        )
                        self.console.print(
                            f"[dim]Showing up to {max_rows} sample rows[/dim]\n"
                        )

                        for idx in range(max_rows):
                            # Create side-by-side table for each row pair
                            comparison_table = Table(
                                title=f"Row Comparison #{idx + 1}",
                                box=box.HEAVY_EDGE,
                                show_header=True,
                                border_style="red",
                            )

                            comparison_table.add_column(
                                "Column", style="bold white", width=25
                            )
                            comparison_table.add_column(
                                "DB1 Value", style="cyan", width=35
                            )
                            comparison_table.add_column(
                                "DB2 Value", style="magenta", width=35
                            )
                            comparison_table.add_column(
                                "Status", justify="center", width=10
                            )

                            # Get rows from both databases
                            row_db1 = (
                                analysis["sample_rows_db1_only"][idx]
                                if idx < len(analysis["sample_rows_db1_only"])
                                else {}
                            )
                            row_db2 = (
                                analysis["sample_rows_db2_only"][idx]
                                if idx < len(analysis["sample_rows_db2_only"])
                                else {}
                            )

                            # Compare each column
                            for col in all_columns:
                                val_db1 = row_db1.get(col, "[dim]<missing>[/dim]")
                                val_db2 = row_db2.get(col, "[dim]<missing>[/dim]")

                                # Truncate long values
                                if isinstance(val_db1, str) and len(val_db1) > 35:
                                    val_db1 = val_db1[:32] + "..."
                                if isinstance(val_db2, str) and len(val_db2) > 35:
                                    val_db2 = val_db2[:32] + "..."

                                # Determine status
                                if val_db1 == "[dim]<missing>[/dim]":
                                    status = "[red]DB1 ✗[/red]"
                                    val_db1_display = "[red]" + val_db1 + "[/red]"
                                    val_db2_display = (
                                        "[green]" + str(val_db2) + "[/green]"
                                    )
                                elif val_db2 == "[dim]<missing>[/dim]":
                                    status = "[red]DB2 ✗[/red]"
                                    val_db1_display = (
                                        "[green]" + str(val_db1) + "[/green]"
                                    )
                                    val_db2_display = "[red]" + val_db2 + "[/red]"
                                elif str(val_db1) == str(val_db2):
                                    status = "[green]✓[/green]"
                                    val_db1_display = str(val_db1)
                                    val_db2_display = str(val_db2)
                                else:
                                    status = "[red]≠[/red]"
                                    val_db1_display = (
                                        "[yellow]" + str(val_db1) + "[/yellow]"
                                    )
                                    val_db2_display = (
                                        "[yellow]" + str(val_db2) + "[/yellow]"
                                    )

                                comparison_table.add_row(
                                    col, val_db1_display, val_db2_display, status
                                )

                            self.console.print(comparison_table)
                            self.console.print()

                # Summary for this table
                summary_table = Table(
                    title=f"Summary for {table_name}",
                    box=box.DOUBLE_EDGE,
                    show_header=True,
                )
                summary_table.add_column("Metric", style="bold")
                summary_table.add_column("Count", justify="right")

                summary_table.add_row(
                    "Total Rows in DB1", f"[cyan]{table_comp.row_count_db1}[/cyan]"
                )
                summary_table.add_row(
                    "Total Rows in DB2",
                    f"[magenta]{table_comp.row_count_db2}[/magenta]",
                )

                if table_comp.data_differences:
                    diff_data = table_comp.data_differences

                    if diff_data.get("identical_rows", 0) > 0:
                        summary_table.add_row(
                            "Identical Rows",
                            f"[green]{diff_data['identical_rows']}[/green]",
                        )

                    if diff_data.get("rows_only_in_db1", 0) > 0:
                        summary_table.add_row(
                            "Rows Only in DB1",
                            f"[red]{diff_data['rows_only_in_db1']}[/red]",
                        )

                    if diff_data.get("rows_only_in_db2", 0) > 0:
                        summary_table.add_row(
                            "Rows Only in DB2",
                            f"[red]{diff_data['rows_only_in_db2']}[/red]",
                        )

                self.console.print(summary_table)

                # Conclusion for this table
                if analysis["is_type_only_difference"]:
                    conclusion_text = (
                        "[bold yellow]✓ CONCLUSION:[/bold yellow] "
                        "[yellow]All data values are identical. "
                        "Differences are only in data types (e.g., string vs integer).[/yellow]"
                    )
                    conclusion_style = "yellow"
                else:
                    conclusion_text = (
                        "[bold red]✗ CONCLUSION:[/bold red] "
                        "[red]Actual data differences exist beyond just data types.[/red]"
                    )
                    conclusion_style = "red"

                self.console.print(
                    Panel(conclusion_text, box=box.ROUNDED, style=conclusion_style)
                )
                self.console.print()

    # --------- Additional helper methods for future enhancements (e.g., export results, generate reports, etc.) can be added here ---------


def main():
    """Main function to run the database comparison."""

    console = Console()

    # Get database paths from user
    console.print(
        Panel("SQLite Database Comparator", style="bold blue", box=box.DOUBLE)
    )

    if len(sys.argv) == 3:
        db1_path = sys.argv[1]
        db2_path = sys.argv[2]
    else:
        # Create a hidden tkinter root window
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.attributes("-topmost", True)  # Bring dialogs to front

        console.print("[cyan]Please select Database 1 file...[/cyan]")
        db1_path = filedialog.askopenfilename(
            title="Select Database 1 (.db file)",
            filetypes=[
                ("SQLite Database", "*.db"),
                ("SQLite Database", "*.sqlite"),
                ("SQLite Database", "*.sqlite3"),
                ("All Files", "*.*"),
            ],
            parent=root,
        )

        if not db1_path:
            console.print(
                "[bold red]No file selected for Database 1. Exiting...[/bold red]"
            )
            root.destroy()
            sys.exit(0)

        console.print(f"[green]✓ Selected DB1: {db1_path}[/green]")

        console.print("[cyan]Please select Database 2 file...[/cyan]")
        db2_path = filedialog.askopenfilename(
            title="Select Database 2 (.db file)",
            filetypes=[
                ("SQLite Database", "*.db"),
                ("SQLite Database", "*.sqlite"),
                ("SQLite Database", "*.sqlite3"),
                ("All Files", "*.*"),
            ],
            parent=root,
        )

        if not db2_path:
            console.print(
                "[bold red]No file selected for Database 2. Exiting...[/bold red]"
            )
            root.destroy()
            sys.exit(0)

        console.print(f"[green]✓ Selected DB2: {db2_path}[/green]")

        # Destroy the tkinter root window
        root.destroy()

    try:
        # Create comparator and run comparison
        comparator = SQLiteComparator(db1_path, db2_path)

        with console.status("[bold green]Comparing databases...", spinner="dots"):
            comparison_result = comparator.compare_databases()

        # Display results
        comparator.display_results(comparison_result)

    except FileNotFoundError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]An error occurred: {e}[/bold red]")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
