import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

import polars as pl


class ParserService:
    @staticmethod
    def read_excel_polars(file_path: str) -> Dict[str, Any]:
        """
        High-performance Excel reader using Polars.
        For .xlsx, it uses the 'calamine' engine (extremely fast Rust reader).
        Returns a dictionary with metadata and the Polars DataFrame.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = file_path.stat().st_size
        ext = file_path.suffix.lower()

        try:
            # Polars' read_excel with engine='calamine' is currently the fastest method in Python ecosystem
            # It avoids the overhead of openpyxl

            # 1. Read Raw Data (No Header)
            # We read with has_header=False to perform our own heuristic detection
            df = pl.read_excel(
                source=file_path,
                engine="calamine", # Requires 'fastexcel' or 'calamine' installed, usually bundles with polars extras or separate
                read_options={"header_row": None}, # Read all rows as data
                infer_schema_length=0 # Force all as string initially for safety
            )

            # 2. Heuristic Header Detection
            header_idx, score = ParserService._detect_header_row(df)

            # 3. Reload or Slice with correct header
            if header_idx is not None:
                # Get header names from the detected row
                header_row = df.row(header_idx)
                # Slice data after header
                data = df.slice(header_idx + 1)
                # Rename columns
                col_map = {old: (new if new else f"col_{i}") for i, (old, new) in enumerate(zip(data.columns, header_row))}
                data = data.rename(col_map)
            else:
                data = df

            # 4. Filter Empty Rows
            data = data.filter(~pl.all_horizontal(pl.all().is_null()))

            return {
                "success": True,
                "rows": data.height,
                "cols": len(data.columns),
                "columns": data.columns,
                "df": data # Returning the Polars DataFrame object for further processing
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def _detect_header_row(df: pl.DataFrame) -> Tuple[int, int]:
        """
        Scans the first 20 rows to find the most likely header row.
        Returns (row_index, score).
        """
        best_idx = None
        best_score = 0

        # Keywords that strongly suggest a header row
        keywords = {
            "data", "valor", "cpf", "cnpj", "agencia", "conta", "banco",
            "venda", "recebimento", "status", "taxa", "liquido", "bruto"
        }

        # Scan top 20 rows
        for i in range(min(20, df.height)):
            row_values = [str(x).lower().strip() for x in df.row(i) if x is not None]

            # Skip empty rows
            if not any(row_values):
                continue

            # Score this row
            score = 0
            matches = 0

            for cell in row_values:
                if any(k in cell for k in keywords):
                    matches += 1

            # Heuristic scoring
            score = matches * 2

            # Penalize if too many cells are empty (headers usually cover most cols)
            filled_ratio = len(row_values) / len(df.columns)
            if filled_ratio > 0.5:
                score += 3

            if score > best_score:
                best_score = score
                best_idx = i

        # Threshold to accept as header
        if best_score >= 4:
            return best_idx, best_score

        return None, 0

    @staticmethod
    def normalize_columns(df: pl.DataFrame) -> pl.DataFrame:
        """
        standardizes column names (snake_case, ascii).
        """
        import unidecode

        new_cols = []
        for col in df.columns:
            # Lowercase, remove accents, replace spaces with _
            clean = unidecode.unidecode(col).lower().strip()
            clean = "".join(c if c.isalnum() else "_" for c in clean)
            clean = clean.replace("__", "_").strip("_")
            new_cols.append(clean)

        return df.rename(dict(zip(df.columns, new_cols)))
