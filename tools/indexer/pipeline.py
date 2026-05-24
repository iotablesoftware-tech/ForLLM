"""
Specification ETL Pipeline.
Coordinates the extraction of YAML specifications, canonical storage inside Parquet/JSONL,
generation of local semantic embeddings, and ingestion into a single-file DuckDB Vector DB.
"""

import sys
import os
import json
import pandas as pd
import numpy as np
import duckdb

# Configure Python path to import neighbor modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import spec_parser
import embedding_engine
import graph_engine

def setup_directories(index_dir):
    """
    Ensures that the directory structure for .llm_index exists.
    """
    subdirs = ["raw", "canonical", "graph"]
    for sd in subdirs:
        os.makedirs(os.path.join(index_dir, sd), exist_ok=True)

def write_jsonl(data_list, output_path):
    """
    Writes a list of dictionaries to a JSONL file.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for entry in data_list:
            # Safe serialize for numpy types
            def default_serializer(obj):
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                raise TypeError
            f.write(json.dumps(entry, ensure_ascii=False, default=default_serializer) + "\n")

def convert_to_parquet(data_list, output_path, cols):
    """
    Converts list of dictionaries to a Parquet file.
    """
    if not data_list:
        df = pd.DataFrame(columns=cols)
    else:
        df = pd.DataFrame(data_list)
        # Ensure all columns exist
        for col in cols:
            if col not in df.columns:
                df[col] = None
    
    # Write as Parquet
    df.to_parquet(output_path, engine="pyarrow", index=False)

def populate_duckdb(index_dir, docs, rules, behaviors, decisions):
    """
    Creates and populates a single-file DuckDB database with specifications
    and high-dimensional vector embeddings.
    """
    db_path = os.path.join(index_dir, "specs_database.db").replace("\\", "/")
    
    # Remove existing database if present
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception as e:
            print(f"[-] Warning: could not remove existing DuckDB database: {e}")

    con = duckdb.connect(db_path)
    
    print("[*] Creating DuckDB relational and vector tables...")
    
    # 1. Documents Table
    con.execute("""
        CREATE TABLE spec_documents (
            id VARCHAR PRIMARY KEY,
            title VARCHAR,
            project VARCHAR,
            version VARCHAR,
            status VARCHAR,
            file_path VARCHAR,
            raw_text VARCHAR,
            embedding FLOAT[]
        )
    """)
    
    # 2. Rules Table
    con.execute("""
        CREATE TABLE spec_rules (
            id VARCHAR,
            doc_id VARCHAR,
            rule_text VARCHAR,
            category VARCHAR,
            embedding FLOAT[]
        )
    """)
    
    # 3. Behaviors Table
    con.execute("""
        CREATE TABLE spec_behaviors (
            doc_id VARCHAR,
            category VARCHAR,
            behavior_text VARCHAR,
            embedding FLOAT[]
        )
    """)
    
    # 4. Decisions Table
    con.execute("""
        CREATE TABLE spec_decisions (
            id VARCHAR,
            doc_id VARCHAR,
            topic VARCHAR,
            decision_text VARCHAR,
            embedding FLOAT[]
        )
    """)
    
    # Ingest Data using executemany for clean batch injection
    print(f"[*] Ingesting specs into DuckDB...")
    if docs:
        con.executemany("INSERT INTO spec_documents VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                       [[d["id"], d["title"], d["project"], d["version"], d["status"], d["file_path"], d["raw_text"], d["embedding"]] for d in docs])
    if rules:
        con.executemany("INSERT INTO spec_rules VALUES (?, ?, ?, ?, ?)", 
                       [[r["id"], r["doc_id"], r["rule_text"], r["category"], r["embedding"]] for r in rules])
    if behaviors:
        con.executemany("INSERT INTO spec_behaviors VALUES (?, ?, ?, ?)", 
                       [[b["doc_id"], b["category"], b["behavior_text"], b["embedding"]] for b in behaviors])
    if decisions:
        con.executemany("INSERT INTO spec_decisions VALUES (?, ?, ?, ?, ?)", 
                       [[d["id"], d["doc_id"], d["topic"], d["decision_text"], d["embedding"]] for d in decisions])
                       
    con.close()
    print(f"[+] DuckDB Vector and Metadata database compiled successfully: {db_path}")

def generate_specs_map(index_dir, docs, rules, behaviors, decisions):
    """
    Generates a high-level structured JSON map of the specs (.llm_index/specs_map.json).
    """
    # --- MACHINE FRIENDLY JSON GENERATION ---
    def serialize_numpy(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return str(obj)

    json_data = {
        "statistics": {
            "total_documents": len(docs),
            "total_rules": len(rules),
            "total_behaviors": len(behaviors),
            "total_decisions": len(decisions)
        },
        "documents": docs,
        "rules": rules,
        "behaviors": behaviors,
        "decisions": decisions
    }
    
    json_path = os.path.join(index_dir, "specs_map.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2, default=serialize_numpy)
        
    root_json_path = os.path.join(os.path.dirname(index_dir), "specs_map.json")
    with open(root_json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2, default=serialize_numpy)
        
    compat_json_path = os.path.join(index_dir, "codebase_map.json")
    with open(compat_json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2, default=serialize_numpy)
        
    root_compat_json_path = os.path.join(os.path.dirname(index_dir), "codebase_map.json")
    with open(root_compat_json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2, default=serialize_numpy)
        
    print(f"[+] Specifications Architectural Map successfully written to: {json_path} and codebase_map.json")

def run_etl(target_dir, index_dir=None):
    """
    Runs the full Extract-Transform-Load (ETL) pipeline on the specs directory.
    """
    specs_dir = os.path.join(target_dir, "specs")
    if not os.path.exists(specs_dir):
        print(f"[-] Error: Specs folder not found inside {target_dir}")
        return False
        
    if not index_dir:
        index_dir = os.path.join(target_dir, ".llm_index")
        
    print(f"[*] Starting AI-Native Specifications ETL pipeline...")
    print(f"[*] Target Directory: {target_dir}")
    print(f"[*] Index Directory: {index_dir}")
    
    # 1. Setup Folders
    setup_directories(index_dir)
    
    # 2. Extract structured metadata from specs
    extracted = spec_parser.scan_specs_directory(specs_dir)
    docs = extracted["documents"]
    rules = extracted["rules"]
    behaviors = extracted["behaviors"]
    decisions = extracted["decisions"]
    
    print(f"[+] YAML Specifications Extraction complete:")
    print(f"    - Documents processed: {len(docs)}")
    print(f"    - Binding & Design Rules extracted: {len(rules)}")
    print(f"    - Behaviors extracted: {len(behaviors)}")
    print(f"    - Architectural Decisions extracted: {len(decisions)}")
    
    # 3. Generate Semantic Embeddings (Vector Generation)
    print(f"[*] Activating Local Semantic Embedding Engine...")
    encoder = embedding_engine.LocalEmbeddingEngine()
    
    # Pre-fit vocabulary for TF-IDF fallback if neural engine is offline
    if not encoder.use_neural:
        # Build training corpus from all texts
        corpus = []
        corpus.extend([d["title"] + " " + d["raw_text"][:500] for d in docs])
        corpus.extend([r["rule_text"] for r in rules])
        corpus.extend([b["behavior_text"] for b in behaviors])
        corpus.extend([dec["topic"] + " " + dec["decision_text"] for dec in decisions])
        encoder.fit_vocabulary(corpus)
        
    # Generate vectors for documents
    print("[*] Generating semantic vectors for documents...")
    for d in docs:
        d["embedding"] = encoder.encode(d["title"] + " " + d["raw_text"][:200])
        
    # Generate vectors for rules
    print("[*] Generating semantic vectors for rules...")
    for r in rules:
        r["embedding"] = encoder.encode(r["rule_text"])
        
    # Generate vectors for behaviors
    print("[*] Generating semantic vectors for behaviors...")
    for b in behaviors:
        b["embedding"] = encoder.encode(b["behavior_text"])
        
    # Generate vectors for decisions
    print("[*] Generating semantic vectors for decisions...")
    for dec in decisions:
        dec["embedding"] = encoder.encode(dec["topic"] + " " + dec["decision_text"])
        
    # 4. Load - Write JSONL (Raw Ingest)
    print(f"[*] Saving Raw Ingest (JSONL) files...")
    write_jsonl(docs, os.path.join(index_dir, "raw", "documents.jsonl"))
    write_jsonl(rules, os.path.join(index_dir, "raw", "rules.jsonl"))
    write_jsonl(behaviors, os.path.join(index_dir, "raw", "behaviors.jsonl"))
    write_jsonl(decisions, os.path.join(index_dir, "raw", "decisions.jsonl"))
    
    # 5. Load - Write Parquet (Canonical Store)
    print(f"[*] Saving Canonical Storage (Parquet) files...")
    convert_to_parquet(docs, os.path.join(index_dir, "canonical", "documents.parquet"), ["id", "title", "project", "version", "status", "file_path", "raw_text", "embedding"])
    convert_to_parquet(rules, os.path.join(index_dir, "canonical", "rules.parquet"), ["id", "doc_id", "rule_text", "category", "embedding"])
    convert_to_parquet(behaviors, os.path.join(index_dir, "canonical", "behaviors.parquet"), ["doc_id", "category", "behavior_text", "embedding"])
    convert_to_parquet(decisions, os.path.join(index_dir, "canonical", "decisions.parquet"), ["id", "doc_id", "topic", "decision_text", "embedding"])
    
    # 6. Load - Populate DuckDB central relational/vector database
    populate_duckdb(index_dir, docs, rules, behaviors, decisions)
    
    # 7. Generate Specs Architectural Map
    generate_specs_map(index_dir, docs, rules, behaviors, decisions)
    
    # 8. Generate directed Knowledge Graph (GraphML)
    graph_engine.build_specs_graph(index_dir, docs, rules, behaviors, decisions)
    
    print("[+] Specifications ETL pipeline execution completed successfully!")
    return True

if __name__ == "__main__":
    # Default to scanning current working directory
    target = os.getcwd()
    if len(sys.argv) > 1:
        target = sys.argv[1]
    run_etl(target)
