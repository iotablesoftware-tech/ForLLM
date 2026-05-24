"""
LLM Assistant Tool-Calling Interface for Specifications.
Provides programmatic and command-line access to the Specifications Vector Database
and relational SQL tables, enabling downstream LLMs to query rules and designs with high precision.
"""

import sys
import os
import argparse
import numpy as np
import duckdb

# Configure Python path to import neighbor modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import embedding_engine

def get_default_index_dir():
    return os.path.join(os.getcwd(), ".llm_index")

def get_map(index_dir=None):
    if not index_dir:
        index_dir = get_default_index_dir()
    map_path = os.path.join(index_dir, "specs_map.json")
    if not os.path.exists(map_path):
        return f"Error: Specifications map not found at {map_path}. Please run pipeline.py first."
    with open(map_path, "r", encoding="utf-8") as f:
        return f.read()

def query_sql(sql_query, index_dir=None):
    if not index_dir:
        index_dir = get_default_index_dir()
        
    db_path = os.path.join(index_dir, "specs_database.db").replace("\\", "/")
    if not os.path.exists(db_path):
        return f"Error: Specifications database not found at {db_path}. Please run pipeline.py first."

    try:
        con = duckdb.connect(db_path, read_only=True)
        # Expose the tables as direct pandas DataFrames or read directly
        df = con.execute(sql_query).df()
        con.close()
        
        if df.empty:
            return "Query executed successfully, but returned 0 rows."
            
        # If the dataframe has an 'embedding' column, drop it from console print for readability
        if "embedding" in df.columns:
            df = df.drop(columns=["embedding"])
            
        return df.to_string(index=False)
    except Exception as e:
        return f"[-] SQL Execution error: {e}"

def search_semantic(query, limit=5, index_dir=None):
    if not index_dir:
        index_dir = get_default_index_dir()
        
    db_path = os.path.join(index_dir, "specs_database.db").replace("\\", "/")
    if not os.path.exists(db_path):
        return f"Error: Specifications database not found at {db_path}. Please run pipeline.py first."

    # 1. Initialize embedding engine and generate query vector
    encoder = embedding_engine.LocalEmbeddingEngine()
    
    # Load all records to fit TF-IDF vocabulary if neural engine is offline
    con = duckdb.connect(db_path, read_only=True)
    
    # We will search across two primary semantic layers: Rules and Decisions
    rules_df = con.execute("SELECT id, doc_id, rule_text, category, embedding FROM spec_rules").df()
    decisions_df = con.execute("SELECT id, doc_id, topic, decision_text, embedding FROM spec_decisions").df()
    docs_df = con.execute("SELECT id, title, file_path FROM spec_documents").df()
    con.close()
    
    # Build a quick document lookup map
    doc_map = {row["id"]: (row["title"], row["file_path"]) for _, row in docs_df.iterrows()}

    # Fitting vocabulary for fallback encoder
    if not encoder.use_neural:
        corpus = []
        corpus.extend(rules_df["rule_text"].tolist())
        corpus.extend((decisions_df["topic"] + " " + decisions_df["decision_text"]).tolist())
        encoder.fit_vocabulary(corpus)
        
    query_vector = encoder.encode(query)

    results = []

    # 2. Score Spec Rules
    for _, row in rules_df.iterrows():
        emb = row["embedding"]
        if emb is not None and len(emb) > 0:
            score = encoder.calculate_similarity(query_vector, emb)
            doc_title, doc_path = doc_map.get(row["doc_id"], ("Unknown Doc", "Unknown Path"))
            results.append({
                "type": "Rule",
                "id": row["id"],
                "title": f"Rule {row['id']} (Category: {row['category']})",
                "text": row["rule_text"],
                "doc_title": doc_title,
                "file_path": doc_path,
                "score": score
            })

    # 3. Score Spec Decisions
    for _, row in decisions_df.iterrows():
        emb = row["embedding"]
        if emb is not None and len(emb) > 0:
            score = encoder.calculate_similarity(query_vector, emb)
            doc_title, doc_path = doc_map.get(row["doc_id"], ("Unknown Doc", "Unknown Path"))
            results.append({
                "type": "Decision",
                "id": row["id"],
                "title": f"Decision: {row['topic']} ({row['id']})",
                "text": row["decision_text"],
                "doc_title": doc_title,
                "file_path": doc_path,
                "score": score
            })

    # 4. Sort and return top-k matches
    results.sort(key=lambda x: x["score"], reverse=True)
    top_matches = results[:limit]
    
    if not top_matches:
        return "No semantically matching specifications found."

    output = []
    output.append(f"=== Semantic Search Results for: '{query}' ===")
    for i, res in enumerate(top_matches, 1):
        output.append(f"{i}. [{res['type']}] {res['title']} (Score: {res['score']:.4f})")
        output.append(f"   Document: {res['doc_title']}")
        output.append(f"   File Path: specs/{res['file_path']}")
        output.append(f"   Content: {res['text'].strip()}")
        output.append("-" * 60)
        
    return "\n".join(output)

def trace_rule_dependencies(rule_id, index_dir=None):
    """
    Traces dependencies/references of a specific rule node in the GraphML file.
    """
    if not index_dir:
        index_dir = get_default_index_dir()
        
    graph_path = os.path.join(index_dir, "graph", "specs_graph.graphml")
    if not os.path.exists(graph_path):
        return f"Error: Specification GraphML file not found at {graph_path}. Please run pipeline.py first."

    import networkx as nx
    G = nx.read_graphml(graph_path)
    
    if rule_id not in G:
        return f"Error: Element '{rule_id}' not found in the specification Knowledge Graph."
        
    node_data = G.nodes[rule_id]
    output = []
    output.append(f"=== Dependency Tracing for Spec Element: '{rule_id}' ===")
    output.append(f"Type: {node_data.get('type')}")
    output.append(f"Label: {node_data.get('label')}")
    
    # 1. Outgoing edges (references this node makes)
    outgoing = list(G.out_edges(rule_id, data=True))
    if outgoing:
        output.append("\nOutgoing References (This element depends on):")
        for u, v, data in outgoing:
            target_data = G.nodes[v]
            output.append(f"  - [{data.get('relation')}] -> {v} ({target_data.get('type')}): {target_data.get('label')}")
            
    # 2. Incoming edges (references to this node)
    incoming = list(G.in_edges(rule_id, data=True))
    if incoming:
        output.append("\nIncoming References (Elements depending on this):")
        for u, v, data in incoming:
            source_data = G.nodes[u]
            output.append(f"  - <- [{data.get('relation')}] - {u} ({source_data.get('type')}): {source_data.get('label')}")
            
    if not outgoing and not incoming:
        output.append("\nThis element is isolated (has no structural links in the specifications graph).")
        
    return "\n".join(output)

def main():
    parser = argparse.ArgumentParser(description="LLM Tool-Calling Interface for Specifications CLI")
    parser.add_argument("--action", choices=["map", "sql", "search", "trace"], required=True,
                        help="Action to perform: 'map' (get structure), 'sql' (query metadata), 'search' (semantic vector search), 'trace' (trace dependencies)")
    parser.add_argument("--query", type=str, help="SQL query for 'sql' action, or semantic search term for 'search' action")
    parser.add_argument("--name", type=str, help="Rule ID or spec element name for 'trace' action")
    parser.add_argument("--limit", type=int, default=5, help="Limit the number of results for semantic search")
    parser.add_argument("--index-dir", type=str, default=None, help="Optional custom .llm_index directory path")
    
    args = parser.parse_args()
    
    if args.action == "map":
        print(get_map(args.index_dir))
    elif args.action == "sql":
        if not args.query:
            print("Error: --query is required for 'sql' action.")
            sys.exit(1)
        print(query_sql(args.query, args.index_dir))
    elif args.action == "search":
        if not args.query:
            print("Error: --query is required for 'search' action.")
            sys.exit(1)
        print(search_semantic(args.query, limit=args.limit, index_dir=args.index_dir))
    elif args.action == "trace":
        if not args.name:
            print("Error: --name (Rule/Decision ID) is required for 'trace' action.")
            sys.exit(1)
        print(trace_rule_dependencies(args.name, args.index_dir))

if __name__ == "__main__":
    main()
