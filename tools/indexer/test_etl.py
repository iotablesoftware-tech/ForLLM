import os
import shutil
import tempfile
import unittest
import pandas as pd
import pipeline
import llm_interface

class TestSpecsETL(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the mock project
        self.test_dir = tempfile.mkdtemp()
        self.mock_specs_dir = os.path.join(self.test_dir, "specs")
        os.makedirs(self.mock_specs_dir)

        # 1. Create a mock specification YAML file
        self.spec_yaml = os.path.join(self.mock_specs_dir, "00_meta_policies.yaml")
        with open(self.spec_yaml, "w", encoding="utf-8") as f:
            f.write('''document:
  id: 00-meta.meta-policies
  title: IoTable Meta Policies
  project: IoTable
  version: 1.0.0
  status: draft
binding_rules:
  - id: R-101
    rule: "All requirements must be verified."
required_behavior:
  - "Follow the task order sequentially."
architectural_decisions:
  - id: DEC-201
    topic: "Use PostgreSQL for tenancy"
    decision_text: "We will use PostgreSQL 17 for schema isolation."
''')

        self.index_dir = os.path.join(self.test_dir, ".llm_index")

    def tearDown(self):
        # Clean up files
        shutil.rmtree(self.test_dir)

    def test_full_pipeline(self):
        # 1. Execute ETL Pipeline
        res = pipeline.run_etl(self.test_dir, self.index_dir)
        self.assertTrue(res)

        # 2. Verify files exist
        raw_docs_path = os.path.join(self.index_dir, "raw", "documents.jsonl")
        docs_parquet_path = os.path.join(self.index_dir, "canonical", "documents.parquet")
        rules_parquet_path = os.path.join(self.index_dir, "canonical", "rules.parquet")
        db_path = os.path.join(self.index_dir, "specs_database.db")
        map_path = os.path.join(self.index_dir, "specs_map.json")
        
        self.assertTrue(os.path.exists(raw_docs_path))
        self.assertTrue(os.path.exists(docs_parquet_path))
        self.assertTrue(os.path.exists(rules_parquet_path))
        self.assertTrue(os.path.exists(db_path))
        self.assertTrue(os.path.exists(map_path))

        # 3. Verify document metadata extraction in Parquet
        df_docs = pd.read_parquet(docs_parquet_path)
        self.assertEqual(len(df_docs), 1)
        self.assertEqual(df_docs.iloc[0]["id"], "00-meta.meta-policies")
        self.assertEqual(df_docs.iloc[0]["title"], "IoTable Meta Policies")

        # 4. Verify rules content using Pandas
        df_rules = pd.read_parquet(rules_parquet_path)
        self.assertEqual(len(df_rules), 1)
        self.assertEqual(df_rules.iloc[0]["id"], "R-101")
        self.assertEqual(df_rules.iloc[0]["rule_text"], "All requirements must be verified.")

        # 5. Test llm_interface.py APIs
        # A. Read specs map via interface
        map_content = llm_interface.get_map(self.index_dir)
        self.assertIn("IoTable Meta Policies", map_content)
        self.assertIn("R-101", map_content)

        # B. Test SQL Query via interface
        sql_res = llm_interface.query_sql("SELECT rule_text FROM spec_rules WHERE id = 'R-101'", self.index_dir)
        self.assertIn("All requirements must be verified.", sql_res)

        # C. Test semantic keyword search via interface
        search_res = llm_interface.search_semantic("PostgreSQL tenancy", limit=1, index_dir=self.index_dir)
        self.assertIn("DEC-201", search_res)
        self.assertIn("PostgreSQL 17", search_res)

        # D. Test dependency tracing via interface
        trace_res = llm_interface.trace_rule_dependencies("R-101", self.index_dir)
        self.assertIn("R-101", trace_res)
        self.assertIn("type: rule", trace_res.lower())

if __name__ == "__main__":
    unittest.main()
