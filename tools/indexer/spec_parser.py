"""
YAML Specification Parser.
Recursively scans the specs/ directory, parses YAML files, and extracts structured metadata
representing documents, rules, decisions, and boundaries.
Supports deeply nested recursive spec structures.
"""

import os
import yaml

def extract_nested_elements(data, doc_id, rules, behaviors, decisions):
    """
    Recursively scans a nested dictionary/list structure to extract rules, behaviors, and decisions.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "document":
                continue
                
            # Parse Rule Arrays (e.g. binding_rules, isolation_rules, project_dependency_rules)
            if "rules" in key or key.endswith("_rules"):
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            rule_id = item.get("id")
                            rule_text = item.get("rule") or item.get("rule_text")
                            if rule_id and rule_text:
                                rules.append({
                                    "id": rule_id,
                                    "doc_id": doc_id,
                                    "rule_text": rule_text,
                                    "category": key
                                })
                elif isinstance(value, dict) and "rules" in value:
                    nested_rules = value.get("rules")
                    if isinstance(nested_rules, list):
                        for item in nested_rules:
                            if isinstance(item, dict):
                                rule_id = item.get("id")
                                rule_text = item.get("rule") or item.get("rule_text")
                                if rule_id and rule_text:
                                    rules.append({
                                        "id": rule_id,
                                        "doc_id": doc_id,
                                        "rule_text": rule_text,
                                        "category": key
                                    })
            
            # Parse Behavior Arrays (e.g. forbidden_behavior, required_behavior)
            elif "behavior" in key or key.endswith("_behavior"):
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            behaviors.append({
                                "doc_id": doc_id,
                                "category": key,
                                "behavior_text": item
                            })
                        elif isinstance(item, dict):
                            desc = item.get("description") or item.get("substitution") or str(item)
                            behaviors.append({
                                "doc_id": doc_id,
                                "category": key,
                                "behavior_text": desc
                            })

            # Parse Decision Arrays (e.g. open_decisions, technology_decision_references)
            elif "decision" in key or key.endswith("_decisions") or key.endswith("_decision_references"):
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            dec_id = item.get("id")
                            dec_topic = item.get("topic") or item.get("title") or dec_id
                            dec_text = item.get("decision_text") or item.get("rule") or item.get("reason") or str(item)
                            if dec_id:
                                decisions.append({
                                    "id": dec_id,
                                    "doc_id": doc_id,
                                    "topic": dec_topic,
                                    "decision_text": dec_text
                                })
                        elif isinstance(item, str):
                            decisions.append({
                                "id": f"DEC-{hash(item) & 0xffff:04x}",
                                "doc_id": doc_id,
                                "topic": "General Decision",
                                "decision_text": item
                            })
            else:
                # Recurse further down the dictionary tree
                extract_nested_elements(value, doc_id, rules, behaviors, decisions)
                
    elif isinstance(data, list):
        for item in data:
            extract_nested_elements(item, doc_id, rules, behaviors, decisions)

def parse_spec_file(file_path, root_dir):
    """
    Parses a single YAML specification file and extracts relational structures.
    """
    rel_path = os.path.relpath(file_path, root_dir).replace("\\", "/")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
            data = yaml.safe_load(raw_text)
    except Exception as e:
        print(f"[-] Error reading/parsing YAML spec {rel_path}: {e}")
        return None

    if not data or not isinstance(data, dict):
        return None

    # 1. Extract Document Metadata
    doc_node = data.get("document", {})
    doc_id = doc_node.get("id")
    if not doc_id:
        # Fallback if no document ID is declared
        doc_id = os.path.splitext(os.path.basename(rel_path))[0]
        
    doc_record = {
        "id": doc_id,
        "title": doc_node.get("title", doc_id),
        "project": doc_node.get("project", "IoTable"),
        "version": doc_node.get("version", "1.0.0"),
        "status": doc_node.get("status", "draft"),
        "file_path": rel_path,
        "raw_text": raw_text
    }

    rules_records = []
    behavior_records = []
    decision_records = []

    # 2. Recursively Extract Rules, Behaviors, and Decisions
    extract_nested_elements(data, doc_id, rules_records, behavior_records, decision_records)

    return {
        "document": doc_record,
        "rules": rules_records,
        "behaviors": behavior_records,
        "decisions": decision_records
    }

def scan_specs_directory(specs_dir):
    """
    Recursively scans the specs directory and parses all YAML files.
    """
    all_documents = []
    all_rules = []
    all_behaviors = []
    all_decisions = []

    for root, _, filenames in os.walk(specs_dir):
        for filename in filenames:
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                abs_path = os.path.join(root, filename)
                res = parse_spec_file(abs_path, root_dir=specs_dir)
                if res:
                    all_documents.append(res["document"])
                    all_rules.extend(res["rules"])
                    all_behaviors.extend(res["behaviors"])
                    all_decisions.extend(res["decisions"])

    return {
        "documents": all_documents,
        "rules": all_rules,
        "behaviors": all_behaviors,
        "decisions": all_decisions
    }
