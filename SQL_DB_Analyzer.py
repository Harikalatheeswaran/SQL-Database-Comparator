#!/usr/bin/env python3
"""
SQLite Database Analyzer Tool
==============================
An interactive tool to explore and analyze SQLite database contents.

Author: Hari
Version: 1.0
Features:
- Display all tables in a database
- View schema in a beautiful tree structure
- Explore table columns
- View unique values in columns
- Search for keywords in columns
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Tuple, Set, Any
import tkinter as tk
from tkinter import filedialog
import re

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.prompt import Prompt, IntPrompt
from rich.text import Text
from rich import box
from rich.columns import Columns


class SQLiteAnalyzer:
    """Main class for analyzing SQLite databases."""
    
    # Color palette for tables
    TABLE_COLORS = [
        "cyan", "magenta", "green", "yellow", "blue", 
        "red", "bright_cyan", "bright_magenta", "bright_green",
        "bright_yellow", "bright_blue", "bright_red"
    ]
    
    def __init__(self, db_path: str):
        """
        Initialize the SQLite analyzer.
        
        Args:
            db_path: Path to the database file
            
        Raises:
            FileNotFoundError: If database file doesn't exist
        """
        self.db_path = Path(db_path)
        self.console = Console()
        self.tables = []
        self.current_table = None
        self.current_columns = []
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        # Load tables on initialization
        self.load_tables()
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Create a database connection.
        
        Returns:
            sqlite3.Connection: Database connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def load_tables(self):
        """Load all table names from the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            self.tables = [row[0] for row in cursor.fetchall()]
    
    def get_table_schema(self, table_name: str) -> List[Tuple]:
        """
        Get the schema of a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List[Tuple]: List of column definitions (cid, name, type, notnull, dflt_value, pk)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info([{table_name}])")
            return cursor.fetchall()
    
    def get_row_count(self, table_name: str) -> int:
        """
        Get the number of rows in a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            int: Number of rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
            return cursor.fetchone()[0]
    
    def get_distinct_values(self, table_name: str, column_name: str, limit: int = 100) -> List[Any]:
        """
        Get distinct values from a column.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
            limit: Maximum number of distinct values to return
            
        Returns:
            List[Any]: List of distinct values
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT DISTINCT [{column_name}] FROM [{table_name}] LIMIT {limit}")
            return [row[0] for row in cursor.fetchall()]
    
    def search_in_column(self, table_name: str, column_name: str, keyword: str, limit: int = 100) -> List[Any]:
        """
        Search for a keyword in a specific column and return matching values only.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
            keyword: Keyword to search for
            limit: Maximum number of results to return
            
        Returns:
            List[Any]: List of matching values from the column
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = f"SELECT [{column_name}] FROM [{table_name}] WHERE [{column_name}] LIKE ? LIMIT {limit}"
            cursor.execute(query, (f"%{keyword}%",))
            return [row[0] for row in cursor.fetchall()]
    
    def display_header(self):
        """Display the application header."""
        self.console.clear()
        header = Panel(
            Text("SQLite Database Analyzer", justify="center", style="bold white"),
            style="bold blue",
            box=box.DOUBLE
        )
        self.console.print(header)
        
        # Display database info
        info_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
        info_table.add_column("Label", style="bold cyan")
        info_table.add_column("Value", style="white")
        info_table.add_row("Database Path:", str(self.db_path))
        info_table.add_row("Total Tables:", str(len(self.tables)))
        self.console.print(info_table)
        self.console.print()
    
    def display_tables(self):
        """Display all tables in the database with numbering."""
        tables_panel = Panel(
            "📋 Tables in Database",
            style="bold green",
            box=box.HEAVY
        )
        self.console.print(tables_panel)
        
        # Create a table to display all tables
        display_table = Table(
            show_header=True,
            box=box.HEAVY_EDGE,
            border_style="green"
        )
        display_table.add_column("#", style="bold yellow", justify="right", width=5)
        display_table.add_column("Table Name", style="bold cyan", width=40)
        display_table.add_column("Row Count", style="magenta", justify="right", width=15)
        
        for idx, table_name in enumerate(self.tables, 1):
            row_count = self.get_row_count(table_name)
            display_table.add_row(
                str(idx),
                table_name,
                f"{row_count:,}"
            )
        
        self.console.print(display_table)
        self.console.print()
    
    def display_schema_tree(self):
        """Display database schema as a beautiful tree structure."""
        self.console.print()
        schema_panel = Panel(
            "🌳 Database Schema Tree",
            style="bold magenta",
            box=box.HEAVY
        )
        self.console.print(schema_panel)
        
        # Create main tree
        tree = Tree(
            f"[bold white]📁 {self.db_path.name}[/bold white]",
            guide_style="bright_black"
        )
        
        # Add each table as a branch
        for idx, table_name in enumerate(self.tables):
            # Assign color to table
            color = self.TABLE_COLORS[idx % len(self.TABLE_COLORS)]
            
            # Get row count and schema
            row_count = self.get_row_count(table_name)
            schema = self.get_table_schema(table_name)
            
            # Create table branch
            table_branch = tree.add(
                f"[bold {color}]📋 {table_name}[/bold {color}] "
                f"[dim white]({row_count:,} rows)[/dim white]"
            )
            
            # Add columns to table branch
            for col_info in schema:
                col_id, col_name, col_type, not_null, default_val, is_pk = col_info
                
                # Build column description
                col_desc = f"[{color}]{col_name}[/{color}]"
                col_desc += f" [{color}]({col_type})[/{color}]" if col_type else ""
                
                # Add constraints
                constraints = []
                if is_pk:
                    constraints.append("[bold yellow]PK[/bold yellow]")
                if not_null:
                    constraints.append("[red]NOT NULL[/red]")
                if default_val is not None:
                    constraints.append(f"[green]DEFAULT: {default_val}[/green]")
                
                if constraints:
                    col_desc += f" {' '.join(constraints)}"
                
                table_branch.add(col_desc)
        
        self.console.print(tree)
        self.console.print()
    
    def display_table_columns(self, table_name: str):
        """
        Display columns of a specific table with numbering.
        
        Args:
            table_name: Name of the table to display
        """
        schema = self.get_table_schema(table_name)
        self.current_columns = [col[1] for col in schema]  # Store column names
        
        self.console.print()
        columns_panel = Panel(
            f"📊 Columns in Table: {table_name}",
            style="bold cyan",
            box=box.HEAVY
        )
        self.console.print(columns_panel)
        
        # Create columns table
        columns_table = Table(
            show_header=True,
            box=box.HEAVY_EDGE,
            border_style="cyan"
        )
        columns_table.add_column("#", style="bold yellow", justify="right", width=5)
        columns_table.add_column("Column Name", style="bold cyan", width=30)
        columns_table.add_column("Type", style="magenta", width=20)
        columns_table.add_column("Constraints", style="white", width=30)
        
        for idx, col_info in enumerate(schema, 1):
            col_id, col_name, col_type, not_null, default_val, is_pk = col_info
            
            # Build constraints string
            constraints = []
            if is_pk:
                constraints.append("[bold yellow]PRIMARY KEY[/bold yellow]")
            if not_null:
                constraints.append("[red]NOT NULL[/red]")
            if default_val is not None:
                constraints.append(f"[green]DEFAULT: {default_val}[/green]")
            
            constraints_str = ", ".join(constraints) if constraints else "[dim]None[/dim]"
            
            columns_table.add_row(
                str(idx),
                col_name,
                col_type or "[dim]No Type[/dim]",
                constraints_str
            )
        
        self.console.print(columns_table)
        self.console.print()
    
    def display_distinct_values(self, table_name: str, column_name: str):
        """
        Display distinct values in a column.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
        """
        distinct_values = self.get_distinct_values(table_name, column_name)
        
        self.console.print()
        distinct_panel = Panel(
            f"🔍 Distinct Values in [{table_name}].[{column_name}]",
            style="bold green",
            box=box.HEAVY
        )
        self.console.print(distinct_panel)
        
        if not distinct_values:
            self.console.print("[yellow]No data found in this column.[/yellow]\n")
            return
        
        # Create table for distinct values
        distinct_table = Table(
            show_header=True,
            box=box.HEAVY_EDGE,
            border_style="green"
        )
        distinct_table.add_column("#", style="bold yellow", justify="right", width=8)
        distinct_table.add_column("Value", style="cyan", width=70)
        distinct_table.add_column("Type", style="magenta", width=15)
        
        for idx, value in enumerate(distinct_values, 1):
            value_str = str(value) if value is not None else "[dim]NULL[/dim]"
            value_type = type(value).__name__
            
            # Truncate long values
            if len(value_str) > 70:
                value_str = value_str[:67] + "..."
            
            distinct_table.add_row(
                str(idx),
                value_str,
                value_type
            )
        
        self.console.print(distinct_table)
        
        if len(distinct_values) >= 100:
            self.console.print(
                "[yellow]⚠ Showing first 100 distinct values only.[/yellow]\n"
            )
        else:
            self.console.print(
                f"[green]✓ Total distinct values: {len(distinct_values)}[/green]\n"
            )
    
    def display_search_results(self, table_name: str, column_name: str, keyword: str):
        """
        Display search results for a keyword in a column (matching values only).
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
            keyword: Keyword to search for
        """
        # Get only the matching column values
        results = self.search_in_column(table_name, column_name, keyword)
        
        self.console.print()
        search_panel = Panel(
            f"🔎 Search Results for '{keyword}' in [{table_name}].[{column_name}]",
            style="bold yellow",
            box=box.HEAVY
        )
        self.console.print(search_panel)
        
        if not results:
            self.console.print(
                f"[red]✗ No results found for keyword: '{keyword}'[/red]\n"
            )
            return
        
        # Create table for matching values
        results_table = Table(
            show_header=True,
            box=box.HEAVY_EDGE,
            border_style="yellow"
        )
        results_table.add_column("#", style="bold yellow", justify="right", width=8)
        results_table.add_column("Matching Value", style="cyan", width=80)
        
        for idx, value in enumerate(results, 1):
            value_str = str(value) if value is not None else "[dim]NULL[/dim]"
            
            # Highlight keyword in value (case insensitive)
            if keyword and value_str != "[dim]NULL[/dim]":
                # Create a highlighted version
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                # Find all matches and highlight them
                highlighted = pattern.sub(
                    lambda m: f"[bold black on yellow]{m.group()}[/bold black on yellow]",
                    value_str
                )
                value_str = highlighted
            
            # Truncate long values (but account for rich markup)
            plain_text = re.sub(r'\[.*?\]', '', value_str)
            if len(plain_text) > 80:
                # Find where to cut
                value_str = value_str[:150] + "..."
            
            results_table.add_row(str(idx), value_str)
        
        self.console.print(results_table)
        
        if len(results) >= 100:
            self.console.print(
                "[yellow]⚠ Showing first 100 matching results only.[/yellow]\n"
            )
        else:
            self.console.print(
                f"[green]✓ Total matching results: {len(results)}[/green]\n"
            )
    
    def show_main_menu(self) -> int:
        """
        Display main menu and get user choice.
        
        Returns:
            int: User's menu choice
        """
        menu_panel = Panel(
            "[bold white]Main Menu[/bold white]\n\n"
            "[cyan]1.[/cyan] Show Schema\n"
            "[cyan]2.[/cyan] Choose Table to View Columns\n"
            "[cyan]3.[/cyan] Exit",
            style="bold blue",
            box=box.ROUNDED,
            title="Options"
        )
        self.console.print(menu_panel)
        
        choice = IntPrompt.ask(
            "[bold yellow]Enter your choice[/bold yellow]",
            choices=["1", "2", "3"],
            default="1"
        )
        return choice
    
    def show_column_menu(self) -> int:
        """
        Display column operations menu and get user choice.
        
        Returns:
            int: User's menu choice
        """
        column_menu_panel = Panel(
            "[bold white]Column Operations Menu[/bold white]\n\n"
            "[cyan]1.[/cyan] Show Unique Values in Selected Column\n"
            "[cyan]2.[/cyan] Search by Keyword in Column\n"
            "[cyan]3.[/cyan] Go to Previous Options",
            style="bold magenta",
            box=box.ROUNDED,
            title="Column Options"
        )
        self.console.print(column_menu_panel)
        
        choice = IntPrompt.ask(
            "[bold yellow]Enter your choice[/bold yellow]",
            choices=["1", "2", "3"],
            default="3"
        )
        return choice
    
    def select_table(self) -> str:
        """
        Let user select a table from the list.
        
        Returns:
            str: Selected table name or None if cancelled
        """
        table_num = IntPrompt.ask(
            f"[bold yellow]Enter table number (1-{len(self.tables)})[/bold yellow]",
            default=1
        )
        
        if 1 <= table_num <= len(self.tables):
            return self.tables[table_num - 1]
        else:
            self.console.print("[red]Invalid table number![/red]\n")
            return None
    
    def select_column(self) -> str:
        """
        Let user select a column from the current table.
        
        Returns:
            str: Selected column name or None if cancelled
        """
        if not self.current_columns:
            self.console.print("[red]No columns available![/red]\n")
            return None
        
        col_num = IntPrompt.ask(
            f"[bold yellow]Enter column number (1-{len(self.current_columns)})[/bold yellow]",
            default=1
        )
        
        if 1 <= col_num <= len(self.current_columns):
            return self.current_columns[col_num - 1]
        else:
            self.console.print("[red]Invalid column number![/red]\n")
            return None
    
    def run(self):
        """Main application loop."""
        try:
            # Display header ONCE at the start
            self.display_header()
            self.display_tables()
            
            while True:
                # Main menu (don't refresh header here)
                choice = self.show_main_menu()
                
                if choice == 1:
                    # Show Schema (don't clear screen, just display)
                    self.display_schema_tree()
                    self.console.input("\n[dim]Press Enter to continue...[/dim]")
                    # Clear and redisplay tables for clean view
                    self.console.clear()
                    self.display_header()
                    self.display_tables()
                    
                elif choice == 2:
                    # Choose table to view columns
                    table_name = self.select_table()
                    if not table_name:
                        continue
                    
                    self.current_table = table_name
                    
                    # Column operations loop
                    while True:
                        self.console.clear()
                        self.display_header()
                        self.display_table_columns(self.current_table)
                        
                        col_choice = self.show_column_menu()
                        
                        if col_choice == 1:
                            # Show unique values
                            column_name = self.select_column()
                            if column_name:
                                self.display_distinct_values(self.current_table, column_name)
                                self.console.input("\n[dim]Press Enter to continue...[/dim]")
                        
                        elif col_choice == 2:
                            # Search by keyword
                            column_name = self.select_column()
                            if column_name:
                                keyword = Prompt.ask(
                                    "[bold yellow]Enter keyword to search[/bold yellow]"
                                )
                                if keyword:
                                    self.display_search_results(
                                        self.current_table, 
                                        column_name, 
                                        keyword
                                    )
                                    self.console.input("\n[dim]Press Enter to continue...[/dim]")
                        
                        elif col_choice == 3:
                            # Go back to main menu
                            self.console.clear()
                            self.display_header()
                            self.display_tables()
                            break
                
                elif choice == 3:
                    # Exit
                    self.console.print(
                        Panel(
                            "[bold green]Thank you for using SQLite Database Analyzer![/bold green]",
                            style="green",
                            box=box.DOUBLE
                        )
                    )
                    break
        
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Application interrupted by user.[/yellow]")
        except Exception as e:
            self.console.print(f"\n[bold red]An error occurred: {e}[/bold red]")
            import traceback
            traceback.print_exc()


def main():
    """Main function to run the database analyzer."""
    console = Console()
    
    # Display welcome screen
    console.print(Panel(
        "SQLite Database Analyzer",
        style="bold blue",
        box=box.DOUBLE
    ))
    
    # Get database path using file dialog
    console.print("[cyan]Please select a SQLite database file...[/cyan]")
    
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    db_path = filedialog.askopenfilename(
        title="Select SQLite Database File",
        filetypes=[
            ("SQLite Database", "*.db"),
            ("SQLite Database", "*.sqlite"),
            ("SQLite Database", "*.sqlite3"),
            ("All Files", "*.*")
        ],
        parent=root
    )
    
    root.destroy()
    
    if not db_path:
        console.print("[bold red]No file selected. Exiting...[/bold red]")
        return
    
    console.print(f"[green]✓ Selected: {db_path}[/green]\n")
    
    try:
        # Create analyzer and run
        analyzer = SQLiteAnalyzer(db_path)
        analyzer.run()
    
    except FileNotFoundError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An error occurred: {e}[/bold red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
