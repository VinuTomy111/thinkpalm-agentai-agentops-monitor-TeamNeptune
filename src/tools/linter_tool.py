import ast
import re
import logging
from typing import List

logger = logging.getLogger(__name__)

class ASTLinterVisitor(ast.NodeVisitor):
    """
    AST Visitor to traverse the python syntax tree and detect naming and usage anomalies.
    """
    def __init__(self):
        self.issues = []
        self.assigned_vars = set()
        self.used_vars = set()

    def visit_FunctionDef(self, node):
        # Detect bad function naming
        if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
            self.issues.append(f"Bad naming function: '{node.name}' on line {node.lineno} should be snake_case.")
        
        # Check function arguments
        for arg in node.args.args:
            if not re.match(r'^[a-z_][a-z0-9_]*$', arg.arg):
                self.issues.append(f"Bad naming argument: '{arg.arg}' on line {node.lineno} should be snake_case.")
            self.assigned_vars.add(arg.arg)

        # Continue traversing children
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        # Detect bad class naming
        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
            self.issues.append(f"Bad naming class: '{node.name}' on line {node.lineno} should be PascalCase.")
        self.generic_visit(node)

    def visit_Name(self, node):
        # Understand if the variable is being assigned (Store) or utilized (Load)
        if isinstance(node.ctx, ast.Store):
            # Ignore constants which correctly use uppercase
            if not re.match(r'^[a-z_][a-z0-9_]*$', node.id) and not node.id.isupper():
                self.issues.append(f"Bad naming variable: '{node.id}' on line {node.lineno} should be snake_case.")
            self.assigned_vars.add(node.id)
        
        elif isinstance(node.ctx, ast.Load):
            self.used_vars.add(node.id)
            
        self.generic_visit(node)

def analyze_code(code: str) -> List[str]:
    """
    Evaluates python source code via abstract syntax tree parsing to return basic local lint issues.
    """
    logger.info("LinterTool: Starting static code analysis.")
    issues = []
    
    # 1. Parse into AST securely
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        logger.error(f"LinterTool: Syntax error detected preventing execution: {e}")
        return [f"Syntax Error: {e.msg} at line {e.lineno}"]
    
    # 2. Walk the syntax tree
    visitor = ASTLinterVisitor()
    visitor.visit(tree)
    
    issues.extend(visitor.issues)
    
    # 3. Detect global un-utilized assignment
    unused = visitor.assigned_vars - visitor.used_vars
    # Ignore purely conventional throwaway variables
    unused = {var for var in unused if not var.startswith('_')}
    
    for var in unused:
        issues.append(f"Unused variable detected: '{var}' was assigned but never used.")
        
    logger.info(f"LinterTool: Code analysis completed. Found {len(issues)} issues overall.")
    return issues
