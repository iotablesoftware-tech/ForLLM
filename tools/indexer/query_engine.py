import os
import duckdb
import networkx as nx

def query_codebase(sql_query, index_dir):
    """
    Executes a SQL query over the Parquet canonical tables using DuckDB.
    Registers 'files', 'classes', and 'functions' as views.
    """
    files_pq = os.path.join(index_dir, "canonical", "files.parquet").replace("\\", "/")
    classes_pq = os.path.join(index_dir, "canonical", "classes.parquet").replace("\\", "/")
    funcs_pq = os.path.join(index_dir, "canonical", "functions.parquet").replace("\\", "/")

    con = duckdb.connect()
    
    # Check if files exist before creating views
    if os.path.exists(files_pq):
        con.execute(f"CREATE OR REPLACE TEMPORARY VIEW files AS SELECT * FROM read_parquet('{files_pq}')")
    if os.path.exists(classes_pq):
        con.execute(f"CREATE OR REPLACE TEMPORARY VIEW classes AS SELECT * FROM read_parquet('{classes_pq}')")
    if os.path.exists(funcs_pq):
        con.execute(f"CREATE OR REPLACE TEMPORARY VIEW functions AS SELECT * FROM read_parquet('{funcs_pq}')")

    try:
        df = con.execute(sql_query).df()
        return df
    except Exception as e:
        print(f"[-] SQL Execution error: {e}")
        return None

def build_knowledge_graph(index_dir):
    """
    Constructs a directed relationship graph (imports, inheritance, function calls)
    and saves it to GraphML format using NetworkX.
    """
    G = nx.DiGraph()

    # 1. Fetch tables using DuckDB
    files_df = query_codebase("SELECT file_path, imports FROM files", index_dir)
    classes_df = query_codebase("SELECT name, bases, file_path FROM classes", index_dir)
    funcs_df = query_codebase("SELECT name, class_name, calls, file_path FROM functions", index_dir)

    # Helper maps
    file_nodes = set()
    class_nodes = {} # name -> file
    func_nodes = {}  # (class_name, name) -> file / name -> file

    # 2. Add File Nodes
    if files_df is not None:
        for _, row in files_df.iterrows():
            fp = row["file_path"]
            G.add_node(fp, type="file", label=fp)
            file_nodes.add(fp)

    # 3. Add Class Nodes & Defines relationships
    if classes_df is not None:
        for _, row in classes_df.iterrows():
            c_name = row["name"]
            fp = row["file_path"]
            class_id = f"class:{fp}:{c_name}"
            G.add_node(class_id, type="class", name=c_name, label=f"class {c_name}")
            G.add_edge(fp, class_id, relation="defines_class")
            class_nodes[c_name] = class_id

    # 4. Add Function Nodes & Defines relationships
    if funcs_df is not None:
        for _, row in funcs_df.iterrows():
            f_name = row["name"]
            c_name = row["class_name"]
            fp = row["file_path"]
            
            if c_name:
                func_id = f"method:{fp}:{c_name}:{f_name}"
                parent_class_id = f"class:{fp}:{c_name}"
                G.add_node(func_id, type="method", name=f_name, label=f"method {f_name}")
                G.add_edge(parent_class_id, func_id, relation="defines_method")
                func_nodes[(c_name, f_name)] = func_id
            else:
                func_id = f"func:{fp}:{f_name}"
                G.add_node(func_id, type="function", name=f_name, label=f"func {f_name}")
                G.add_edge(fp, func_id, relation="defines_function")
                func_nodes[f_name] = func_id

    # 5. Connect Class Inheritances
    if classes_df is not None:
        for _, row in classes_df.iterrows():
            c_name = row["name"]
            bases = row["bases"]
            if bases is not None:
                for base in bases:
                    if base in class_nodes:
                        child_id = class_nodes[c_name]
                        parent_id = class_nodes[base]
                        G.add_edge(child_id, parent_id, relation="inherits_from")

    # 6. Connect Function Call Graphs
    if funcs_df is not None:
        for _, row in funcs_df.iterrows():
            f_name = row["name"]
            c_name = row["class_name"]
            fp = row["file_path"]
            calls = row["calls"]
            
            caller_id = func_nodes.get((c_name, f_name)) if c_name else func_nodes.get(f_name)
            if not caller_id or calls is None:
                continue

            for call in calls:
                callee_id = None
                if "." in call:
                    # Resolve dotted call: e.g. calc.calculate_kdv or module.func
                    parts = call.split(".")
                    method_name = parts[-1]
                    
                    # 1. First check if it matches a method in any class by matching the method name
                    for key, fid in func_nodes.items():
                        if isinstance(key, tuple) and key[1] == method_name:
                            callee_id = fid
                            break
                    
                    # 2. Fallback to exact tuple match if caller explicitly referenced Class.method
                    if not callee_id and len(parts) == 2:
                        callee_id = func_nodes.get((parts[0], parts[1]))
                else:
                    # Check top-level function
                    callee_id = func_nodes.get(call)
                    # Check method within same class
                    if not callee_id and c_name:
                        callee_id = func_nodes.get((c_name, call))

                if callee_id:
                    G.add_edge(caller_id, callee_id, relation="calls")

    # Save to GraphML
    graph_path = os.path.join(index_dir, "graph", "codebase_graph.graphml")
    nx.write_graphml(G, graph_path)
    print(f"[+] Knowledge Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    print(f"    - Graph saved to: {graph_path}")
    return G


# Pragmatic Text/Docstring Semantic search using TF-IDF representation
class LocalSemanticSearcher:
    def __init__(self, index_dir):
        self.index_dir = index_dir
        self.funcs_df = query_codebase("SELECT name, file_path, docstring, source_code FROM functions", index_dir)
        
    def search(self, query_text, limit=3):
        """
        Executes a simple tf-idf string overlap and keyword similarity search
        over docstrings and function names.
        """
        if self.funcs_df is None or self.funcs_df.empty:
            return []

        query_words = set(query_text.lower().split())
        results = []

        for _, row in self.funcs_df.iterrows():
            name = row["name"].lower()
            doc = str(row["docstring"]).lower()
            
            score = 0
            # Name match (highest weight)
            for word in query_words:
                if word in name:
                    score += 10
                if word in doc:
                    score += 2

            if score > 0:
                results.append({
                    "name": row["name"],
                    "file_path": row["file_path"],
                    "docstring": row["docstring"],
                    "source_code": row["source_code"],
                    "score": score
                })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
