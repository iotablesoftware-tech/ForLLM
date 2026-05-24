import os
import shutil
import tempfile
import unittest
import pandas as pd
import parser_core
import pipeline
import query_engine
import llm_interface

class TestCodeETL(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the mock codebase
        self.test_dir = tempfile.mkdtemp()
        self.mock_app_dir = os.path.join(self.test_dir, "mock_app")
        os.makedirs(self.mock_app_dir)

        # 1. Create a base class file
        self.core_py = os.path.join(self.mock_app_dir, "core.py")
        with open(self.core_py, "w", encoding="utf-8") as f:
            f.write('''"""Core arithmetic systems."""

class BaseCalculator:
    """Base class for calculations."""
    def __init__(self):
        self.name = "Base"

class TaxCalculator(BaseCalculator):
    """Handles financial tax calculations."""
    def calculate_kdv(self, price: float, rate: float = 0.20) -> float:
        """Calculates KDV value for standard sales."""
        return price * rate
''')

        # 2. Create a consumer file with calls and imports
        self.utils_py = os.path.join(self.mock_app_dir, "utils.py")
        with open(self.utils_py, "w", encoding="utf-8") as f:
            f.write('''"""Utility methods for accounting."""
from mock_app.core import TaxCalculator

def process_invoice(amount: float) -> None:
    """Calculates tax and registers transaction."""
    calc = TaxCalculator()
    kdv = calc.calculate_kdv(amount, 0.20)
    print(f"Invoice processed with KDV: {kdv}")
''')

        self.index_dir = os.path.join(self.test_dir, ".llm_index")

    def tearDown(self):
        # Clean up files
        shutil.rmtree(self.test_dir)

    def test_full_pipeline(self):
        # 1. Execute ETL Pipeline
        res = pipeline.run_etl(self.mock_app_dir, self.index_dir)
        self.assertTrue(res)

        # 2. Verify files exist
        raw_funcs_path = os.path.join(self.index_dir, "raw", "functions.jsonl")
        funcs_parquet_path = os.path.join(self.index_dir, "canonical", "functions.parquet")
        files_parquet_path = os.path.join(self.index_dir, "canonical", "files.parquet")
        map_path = os.path.join(self.index_dir, "codebase_map.md")
        
        self.assertTrue(os.path.exists(raw_funcs_path))
        self.assertTrue(os.path.exists(funcs_parquet_path))
        self.assertTrue(os.path.exists(files_parquet_path))
        self.assertTrue(os.path.exists(map_path))

        # 3. Verify module docstring extraction in files parquet
        df_files = pd.read_parquet(files_parquet_path)
        self.assertEqual(len(df_files), 2)
        docstrings = df_files["docstring"].tolist()
        self.assertIn("Core arithmetic systems.", docstrings)
        self.assertIn("Utility methods for accounting.", docstrings)

        # 4. Test Parquet content using Pandas
        df_funcs = pd.read_parquet(funcs_parquet_path)
        self.assertEqual(len(df_funcs), 3)  # __init__, calculate_kdv, process_invoice
        
        # Verify function name extraction
        func_names = df_funcs["name"].tolist()
        self.assertIn("calculate_kdv", func_names)
        self.assertIn("process_invoice", func_names)

        # 5. Test Analytical SQL Queries using DuckDB View registration
        res_sql = query_engine.query_codebase(
            "SELECT name, file_path FROM functions WHERE docstring LIKE '%KDV%'", 
            self.index_dir
        )
        self.assertIsNotNone(res_sql)
        self.assertEqual(len(res_sql), 1)
        self.assertEqual(res_sql.iloc[0]["name"], "calculate_kdv")

        # 6. Build and Test NetworkX directed Call & Inheritance Graph
        G = query_engine.build_knowledge_graph(self.index_dir)
        self.assertIsNotNone(G)
        
        # Verify edges exist
        edges = list(G.edges(data=True))
        relations = [e[2]["relation"] for e in edges]
        self.assertIn("inherits_from", relations)
        self.assertIn("calls", relations)

        # 7. Test Local Semantic/Docstring search
        searcher = query_engine.LocalSemanticSearcher(self.index_dir)
        matches = searcher.search("sales transaction tax calculations")
        self.assertTrue(len(matches) > 0)
        match_names = [m["name"] for m in matches]
        self.assertIn("calculate_kdv", match_names)

        # 8. Test llm_interface.py APIs
        # A. Read codebase map via interface
        map_content = llm_interface.get_map(self.index_dir)
        self.assertIn("Codebase Architectural Map & Index", map_content)
        self.assertIn("Core arithmetic systems.", map_content)
        self.assertIn("Utility methods for accounting.", map_content)

        # B. Test SQL Query via interface
        sql_res = llm_interface.query_sql("SELECT name FROM functions WHERE class_name = 'TaxCalculator'", self.index_dir)
        self.assertIn("calculate_kdv", sql_res)

        # C. Test semantic keyword search via interface
        search_res = llm_interface.search_semantic("invoice calculation", index_dir=self.index_dir)
        self.assertIn("process_invoice", search_res)

        # D. Test exact element retrieval via interface (function)
        code_res_func = llm_interface.get_code_element("calculate_kdv", index_dir=self.index_dir)
        self.assertIn("def calculate_kdv", code_res_func)
        self.assertIn("price * rate", code_res_func)

        # E. Test exact element retrieval via interface (class)
        code_res_class = llm_interface.get_code_element("TaxCalculator", index_dir=self.index_dir)
        self.assertIn("Class: TaxCalculator", code_res_class)
        self.assertIn("def calculate_kdv", code_res_class)

if __name__ == "__main__":
    unittest.main()
