import ast
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class CodeExtractionVisitor(ast.NodeVisitor):
    """
    AST Visitor designed to traverse and extract top-level structure elements 
    like Classes and Functions from Python source code.
    """
    def __init__(self):
        self.functions = []
        self.classes = []

    def visit_FunctionDef(self, node):
        self.functions.append({
            "name": node.name,
            "line_number": node.lineno,
            "args": [arg.arg for arg in node.args.args],
            "is_async": False
        })
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.functions.append({
            "name": node.name,
            "line_number": node.lineno,
            "args": [arg.arg for arg in node.args.args],
            "is_async": True
        })
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        class_info = {
            "name": node.name,
            "line_number": node.lineno,
            "base_classes": [base.id for base in node.bases if isinstance(base, ast.Name)]
        }
        self.classes.append(class_info)
        self.generic_visit(node)

def parse_code(code: str) -> Dict[str, Any]:
    """
    Analyzes Python code strings and returns structured structural metadata.
    """
    logger.info("CodeParserTool: Starting structural code parsing extraction.")
    
    # Safely abstract the tree
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        logger.error(f"CodeParserTool: Fatal Syntax error prevented extraction: {e}")
        return {
            "error": f"SyntaxError at line {e.lineno}: {e.msg}",
            "classes": [],
            "functions": []
        }
        
    # Traverse payload
    visitor = CodeExtractionVisitor()
    visitor.visit(tree)
    
    # Collate outputs
    result = {
        "classes": visitor.classes,
        "functions": visitor.functions
    }
    
    logger.info(f"CodeParserTool: Code parse successful. Extracted {len(visitor.classes)} classes and {len(visitor.functions)} functions.")
    
    return result
