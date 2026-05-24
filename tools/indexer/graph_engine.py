"""
Specification Knowledge Graph Engine.
Constructs a directed relationship graph mapping connections between specifications,
binding rules, architectural decisions, and compliance behaviors using NetworkX.
Exports the graph in GraphML format.
"""

import os
import re
import networkx as nx

def build_specs_graph(index_dir, docs, rules, behaviors, decisions):
    """
    Constructs a semantic directed graph representing specification relationships
    and saves it to GraphML format.
    """
    G = nx.DiGraph()
    
    print("[*] Generating directed Knowledge Graph of specifications...")
    
    # 1. Add Document Nodes
    for d in docs:
        doc_id = d["id"]
        G.add_node(
            doc_id,
            type="document",
            label=f"doc: {d['title']}",
            title=d["title"],
            version=d["version"],
            status=d["status"],
            file_path=d["file_path"]
        )
        
    # 2. Add Rule Nodes and Defines relations
    for r in rules:
        rule_id = r["id"]
        doc_id = r["doc_id"]
        G.add_node(
            rule_id,
            type="rule",
            label=f"rule: {rule_id}",
            rule_text=r["rule_text"],
            category=r["category"]
        )
        if doc_id in G:
            G.add_edge(doc_id, rule_id, relation="defines_rule")
            
    # 3. Add Behavior Nodes and Defines relations
    for idx, b in enumerate(behaviors):
        # Generate stable behavior ID
        beh_id = f"BEH-{idx:04d}"
        doc_id = b["doc_id"]
        G.add_node(
            beh_id,
            type="behavior",
            label=f"behavior: {b['category']}",
            behavior_text=b["behavior_text"],
            category=b["category"]
        )
        if doc_id in G:
            G.add_edge(doc_id, beh_id, relation="defines_behavior")
            
    # 4. Add Decision Nodes and Defines relations
    for dec in decisions:
        dec_id = dec["id"]
        doc_id = dec["doc_id"]
        G.add_node(
            dec_id,
            type="decision",
            label=f"decision: {dec['topic']}",
            topic=dec["topic"],
            decision_text=dec["decision_text"]
        )
        if doc_id in G:
            G.add_edge(doc_id, dec_id, relation="defines_decision")

    # 5. Extract cross-rule dependencies dynamically (Rule references another Rule)
    # E.g. Rule text contains "TVB-001" or "BSS-002"
    all_rule_ids = {r["id"] for r in rules}
    for r in rules:
        rule_id = r["id"]
        text = r["rule_text"]
        
        # Regex to find rule ID patterns in text
        found_refs = re.findall(r'\b[A-Z]{3,}-[0-9]{3}\b', text)
        for ref in found_refs:
            if ref in all_rule_ids and ref != rule_id:
                G.add_edge(rule_id, ref, relation="references_rule")

    # 6. Extract rule-to-decision dependencies dynamically
    # E.g. Rule referencing Decision reference ID
    all_dec_ids = {dec["id"] for dec in decisions}
    for r in rules:
        rule_id = r["id"]
        text = r["rule_text"]
        found_refs = re.findall(r'\b[A-Z]{3,}-OD-[0-9]{3}\b|\bTDR-[0-9]{3}\b', text)
        for ref in found_refs:
            if ref in all_dec_ids:
                G.add_edge(rule_id, ref, relation="references_decision")

    # Save to GraphML
    graph_path = os.path.join(index_dir, "graph", "specs_graph.graphml")
    try:
        nx.write_graphml(G, graph_path)
        print(f"[+] Knowledge Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
        print(f"    - Graph saved to: {graph_path}")
    except Exception as e:
        print(f"[-] Error writing GraphML file: {e}")
        
    return G
