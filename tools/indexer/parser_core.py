import ast
import os
import sys

class ASTExtractor(ast.NodeVisitor):
    def __init__(self, source_code, file_path):
        self.source_code = source_code
        self.file_path = file_path
        self.imports = []
        self.classes = []
        self.functions = []
        self.current_class = None

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({
                "name": alias.name,
                "asname": alias.asname,
                "line": node.lineno
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ""
        for alias in node.names:
            self.imports.append({
                "name": f"{module}.{alias.name}" if module else alias.name,
                "asname": alias.asname,
                "line": node.lineno
            })
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(self._get_attribute_name(base))
            else:
                bases.append("Unknown")
        
        docstring = ast.get_docstring(node) or ""
        
        self.classes.append({
            "name": node.name,
            "bases": bases,
            "docstring": docstring,
            "line_start": node.lineno,
            "line_end": getattr(node, "end_lineno", node.lineno)
        })
        
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node):
        self._extract_function(node)

    def visit_AsyncFunctionDef(self, node):
        self._extract_function(node)

    def _extract_function(self, node):
        docstring = ast.get_docstring(node) or ""
        
        # Parse arguments with type hints
        args = []
        for arg in node.args.args:
            annotation = ""
            if arg.annotation:
                annotation = self._get_annotation_str(arg.annotation)
            args.append(f"{arg.arg}: {annotation}" if annotation else arg.arg)
            
        returns = ""
        if node.returns:
            returns = self._get_annotation_str(node.returns)
            
        # Safely extract exact source segment
        try:
            source_code = ast.get_source_segment(self.source_code, node) or ""
        except Exception:
            # Fallback line slicing if segment fails
            lines = self.source_code.splitlines()
            start = node.lineno - 1
            end = getattr(node, "end_lineno", len(lines))
            source_code = "\n".join(lines[start:end])
        
        # Analyze internal function calls
        called_functions = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func_name = self._get_call_name(child.func)
                if func_name:
                    called_functions.append(func_name)
                    
        self.functions.append({
            "name": node.name,
            "class_name": self.current_class,
            "args": args,
            "returns": returns,
            "docstring": docstring,
            "calls": list(set(called_functions)),
            "line_start": node.lineno,
            "line_end": getattr(node, "end_lineno", node.lineno),
            "source_code": source_code
        })

    def _get_annotation_str(self, node):
        try:
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                return self._get_attribute_name(node)
            elif isinstance(node, ast.Subscript):
                value = self._get_annotation_str(node.value)
                slice_val = self._get_annotation_str(node.slice)
                return f"{value}[{slice_val}]"
            elif isinstance(node, ast.Tuple):
                elements = [self._get_annotation_str(el) for el in node.elts]
                return ", ".join(elements)
            elif isinstance(node, ast.List):
                elements = [self._get_annotation_str(el) for el in node.elts]
                return f"[{', '.join(elements)}]"
            elif isinstance(node, ast.Constant):
                return str(node.value)
            elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
                left = self._get_annotation_str(node.left)
                right = self._get_annotation_str(node.right)
                return f"{left} | {right}"
        except Exception:
            pass
        return "Unknown"

    def _get_attribute_name(self, node):
        parts = []
        curr = node
        while isinstance(curr, ast.Attribute):
            parts.append(curr.attr)
            curr = curr.value
        if isinstance(curr, ast.Name):
            parts.append(curr.id)
        return ".".join(reversed(parts))

    def _get_call_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attribute_name(node)
        return None


def parse_file(file_path, root_dir=None):
    """
    Parses a single Python file and returns structured data representation.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}", file=sys.stderr)
        return None

    try:
        tree = ast.parse(source_code, filename=file_path)
    except SyntaxError as se:
        print(f"Syntax error in file {file_path}: {se}", file=sys.stderr)
        return None

    extractor = ASTExtractor(source_code, file_path)
    extractor.visit(tree)

    # Compute relative path
    rel_path = os.path.relpath(file_path, root_dir) if root_dir else file_path
    rel_path = rel_path.replace("\\", "/") # Normalize path separators for cross-platform matching

    # Assemble File-level summary
    file_record = {
        "file_path": rel_path,
        "line_count": len(source_code.splitlines()),
        "char_count": len(source_code),
        "imports": [imp["name"] for imp in extractor.imports],
        "docstring": ast.get_docstring(tree) or ""
    }

    # Bind file_path metadata to child structures
    for cls in extractor.classes:
        cls["file_path"] = rel_path
    for func in extractor.functions:
        func["file_path"] = rel_path

    return {
        "file": file_record,
        "classes": extractor.classes,
        "functions": extractor.functions
    }


def scan_directory(target_dir):
    """
    Scans a directory recursively and parses all Python files found.
    """
    all_files = []
    all_classes = []
    all_functions = []

    for root, _, filenames in os.walk(target_dir):
        # Ignore common directories to avoid noise
        if any(ignored in root for ignored in [".git", "__pycache__", ".venv", ".llm_index"]):
            continue

        for filename in filenames:
            if filename.endswith(".py"):
                abs_path = os.path.join(root, filename)
                res = parse_file(abs_path, root_dir=target_dir)
                if res:
                    all_files.append(res["file"])
                    all_classes.extend(res["classes"])
                    all_functions.extend(res["functions"])

    return {
        "files": all_files,
        "classes": all_classes,
        "functions": all_functions
    }
