#!/usr/bin/env python3
"""
Script to check code maintainability metrics.

This is a simple alternative to tools like 'radon' for checking
code maintainability metrics in Python code.
"""
import ast
import math
import os
import sys
from typing import Dict, List, Set, Tuple, Optional


def calculate_cyclomatic_complexity(node: ast.AST) -> int:
    """
    Calculate the cyclomatic complexity of an AST node.

    Args:
        node: The AST node

    Returns:
        int: The cyclomatic complexity value
    """
    complexity = 1  # Base complexity
    
    for child in ast.walk(node):
        # Control flow statements increase complexity
        if isinstance(child, (ast.If, ast.While, ast.For)):
            complexity += 1
        # Logical operators are counted
        elif isinstance(child, ast.BoolOp) and isinstance(child.op, ast.And):
            complexity += len(child.values) - 1
        elif isinstance(child, ast.BoolOp) and isinstance(child.op, ast.Or):
            complexity += len(child.values) - 1
        # Exception handlers
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        # Return statements in generators
        elif isinstance(child, ast.Return) and isinstance(node, ast.AsyncFunctionDef):
            complexity += 1
        # Comprehensions
        elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            complexity += len(child.generators)
    
    return complexity


def calculate_halstead_metrics(code: str) -> Dict[str, float]:
    """
    Calculate Halstead complexity metrics.

    Args:
        code: Source code string

    Returns:
        Dict[str, float]: Halstead metrics
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {"volume": 0, "difficulty": 0, "effort": 0}
    
    # Collect operators and operands
    operators = set()
    operands = set()
    
    for node in ast.walk(tree):
        # Operators
        if isinstance(node, ast.operator):
            operators.add(ast.dump(node))
        elif isinstance(node, ast.BinOp):
            operators.add(type(node.op).__name__)
        elif isinstance(node, ast.UnaryOp):
            operators.add(type(node.op).__name__)
        elif isinstance(node, ast.Compare):
            for op in node.ops:
                operators.add(type(op).__name__)
        
        # Operands
        if isinstance(node, ast.Name):
            operands.add(node.id)
        elif isinstance(node, ast.Num):
            operands.add(str(node.n))
        elif isinstance(node, ast.Str):
            operands.add(node.s)
    
    # Calculate metrics
    n1 = len(operators)  # Number of distinct operators
    n2 = len(operands)   # Number of distinct operands
    
    if n1 == 0 or n2 == 0:
        return {"volume": 0, "difficulty": 0, "effort": 0}
    
    N1 = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.operator, ast.BinOp, ast.UnaryOp, ast.Compare)))
    N2 = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.Name, ast.Num, ast.Str)))
    
    # Handle case where counts are zero
    if N1 == 0 or N2 == 0 or n2 == 0:
        return {"volume": 0, "difficulty": 0, "effort": 0}
    
    vocabulary = n1 + n2
    length = N1 + N2
    
    volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
    difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
    effort = difficulty * volume
    
    return {
        "volume": volume,
        "difficulty": difficulty,
        "effort": effort
    }


def calculate_maintainability_index(code: str, complexity: int) -> float:
    """
    Calculate the maintainability index for a piece of code.

    Args:
        code: Source code string
        complexity: Cyclomatic complexity

    Returns:
        float: Maintainability Index value (0-100)
    """
    halstead = calculate_halstead_metrics(code)
    
    # If there's no code or metrics, return maximum maintainability
    if not code.strip() or halstead["effort"] == 0:
        return 100.0
    
    # Count logical lines of code (non-blank, non-comment)
    lines = [line.strip() for line in code.split('\n')]
    loc = len([line for line in lines if line and not line.startswith('#')])
    
    if loc == 0:
        return 100.0
    
    # Original maintainability index formula with adjustments
    halstead_volume = halstead["volume"]
    
    # Avoid math domain errors with log
    if halstead_volume <= 0:
        halstead_volume = 1
    
    # Apply a slightly simplified formula
    try:
        raw_mi = 171 - 5.2 * math.log(halstead_volume) - 0.23 * complexity - 16.2 * math.log(loc)
        normalized_mi = max(0, min(100, (raw_mi * 100) / 171))
    except (ValueError, TypeError, ZeroDivisionError):
        normalized_mi = 50  # Default value for error cases
    
    return normalized_mi


def analyze_file(file_path: str) -> Dict[str, any]:
    """
    Analyze a Python file for maintainability metrics.

    Args:
        file_path: Path to the Python file

    Returns:
        Dict[str, any]: Dictionary of metrics for the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except (IOError, UnicodeDecodeError):
        print(f"Error reading file: {file_path}")
        return {"cc": 0, "mi": 0, "file_path": file_path}
    
    try:
        tree = ast.parse(code)
    except SyntaxError:
        print(f"Syntax error in file: {file_path}")
        return {"cc": 0, "mi": 0, "file_path": file_path}
    
    # Calculate metrics for the whole file
    file_complexity = calculate_cyclomatic_complexity(tree)
    file_mi = calculate_maintainability_index(code, file_complexity)
    
    # Calculate metrics for each function
    functions = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_name = node.name
            func_code = ast.get_source_segment(code, node)
            if func_code:
                func_complexity = calculate_cyclomatic_complexity(node)
                func_mi = calculate_maintainability_index(func_code, func_complexity)
                functions[func_name] = {
                    "cc": func_complexity,
                    "mi": func_mi,
                    "lineno": node.lineno
                }
    
    return {
        "cc": file_complexity,
        "mi": file_mi,
        "file_path": file_path,
        "functions": functions
    }


def analyze_directory(directory: str, exclude: Set[str] = None) -> List[Dict[str, any]]:
    """
    Analyze all Python files in a directory for maintainability metrics.

    Args:
        directory: The directory to analyze
        exclude: Set of directory or file names to exclude

    Returns:
        List[Dict[str, any]]: List of metrics for each file
    """
    if exclude is None:
        exclude = set()
        
    results = []
    
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in exclude and not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                results.append(analyze_file(file_path))
    
    return results


def calculate_average_mi(results: List[Dict[str, any]]) -> float:
    """
    Calculate the average Maintainability Index across all files.

    Args:
        results: List of file metrics

    Returns:
        float: Average Maintainability Index
    """
    if not results:
        return 0.0
    
    total_mi = sum(result["mi"] for result in results)
    return total_mi / len(results)


def main(directories: List[str], min_mi: float = 70.0) -> None:
    """
    Main function to analyze code maintainability.

    Args:
        directories: List of directories to analyze
        min_mi: Minimum acceptable Maintainability Index

    Returns:
        None
    """
    exclude = {'__pycache__', 'venv', '.venv', 'env', '.env', '.git', 'migrations'}
    
    all_results = []
    for directory in directories:
        results = analyze_directory(directory, exclude)
        all_results.extend(results)
    
    average_mi = calculate_average_mi(all_results)
    
    print(f"Average Maintainability Index: {average_mi:.2f}")
    
    # List files with low maintainability
    low_mi_files = [result for result in all_results if result["mi"] < min_mi]
    if low_mi_files:
        print("\nFiles with low maintainability (< 70):")
        for file in low_mi_files:
            print(f"  {file['file_path']}: MI = {file['mi']:.2f}")
    
    if average_mi < min_mi:
        print(f"Average maintainability below the minimum requirement of {min_mi}")
        sys.exit(1)
    else:
        print(f"Maintainability meets or exceeds the minimum requirement of {min_mi}")
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_maintainability.py directory1 [directory2 ...] [--min-mi=70.0]")
        sys.exit(1)
    
    dirs = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    
    min_maintainability = 70.0
    for arg in sys.argv[1:]:
        if arg.startswith('--min-mi='):
            try:
                min_maintainability = float(arg.split('=')[1])
            except (IndexError, ValueError):
                print(f"Invalid min-mi value: {arg}")
                sys.exit(1)
    
    main(dirs, min_maintainability) 