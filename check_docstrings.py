#!/usr/bin/env python3
"""
Script to check docstring coverage in Python files.

This is a simple alternative to tools like 'interrogate' for checking
documentation coverage in Python code.
"""
import ast
import os
import sys
from typing import Dict, List, Set, Tuple


def has_docstring(node: ast.AST) -> bool:
    """
    Check if an AST node has a docstring.

    Args:
        node: The AST node to check

    Returns:
        bool: True if the node has a docstring, False otherwise
    """
    if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
        return False
    
    # Check for docstring
    if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Str)):
        return True
    return False


def get_docstring_stats(file_path: str) -> Tuple[int, int, List[str]]:
    """
    Get docstring statistics for a Python file.

    Args:
        file_path: Path to the Python file

    Returns:
        Tuple[int, int, List[str]]: Count of nodes that need docstrings, 
                                    count of nodes that have docstrings,
                                    list of missing docstring locations
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        print(f"Syntax error in file: {file_path}")
        return 0, 0, []
    
    missing: List[str] = []
    need_docstring_count = 0
    has_docstring_count = 0
    
    # Check module docstring
    if has_docstring(tree):
        has_docstring_count += 1
    else:
        need_docstring_count += 1
        missing.append(f"Module docstring in {file_path}")
    
    # Check functions and classes
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            if has_docstring(node):
                has_docstring_count += 1
            else:
                need_docstring_count += 1
                if isinstance(node, ast.ClassDef):
                    missing.append(f"Class '{node.name}' at line {node.lineno}")
                else:
                    missing.append(f"Function '{node.name}' at line {node.lineno}")
    
    return need_docstring_count, has_docstring_count, missing


def check_directory(directory: str, exclude: Set[str] = None) -> Dict[str, Tuple[int, int]]:
    """
    Check docstring coverage for all Python files in a directory.

    Args:
        directory: The directory to check
        exclude: Set of directory or file names to exclude

    Returns:
        Dict[str, Tuple[int, int]]: Dictionary mapping file paths to 
                                     tuple of (need_docstring_count, has_docstring_count)
    """
    if exclude is None:
        exclude = set()
        
    results = {}
    
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in exclude and not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                need_count, has_count, missing = get_docstring_stats(file_path)
                
                if need_count + has_count > 0:  # Only include files with at least one function/class
                    results[file_path] = (need_count, has_count)
    
    return results


def calculate_coverage(results: Dict[str, Tuple[int, int]]) -> float:
    """
    Calculate the overall docstring coverage percentage.

    Args:
        results: Dictionary mapping file paths to 
                tuple of (need_docstring_count, has_docstring_count)

    Returns:
        float: The overall docstring coverage percentage
    """
    total_need = sum(need for need, _ in results.values())
    total_has = sum(has for _, has in results.values())
    
    if total_need + total_has == 0:
        return 100.0
    
    return (total_has / (total_need + total_has)) * 100.0


def main(directories: List[str], min_percentage: float = 90.0) -> None:
    """
    Main function to check docstring coverage.

    Args:
        directories: List of directories to check
        min_percentage: Minimum acceptable coverage percentage

    Returns:
        None
    """
    exclude = {'__pycache__', 'venv', '.venv', 'env', '.env', '.git', 'migrations'}
    
    all_results = {}
    for directory in directories:
        results = check_directory(directory, exclude)
        all_results.update(results)
    
    coverage = calculate_coverage(all_results)
    
    print(f"Docstring coverage: {coverage:.2f}%")
    
    if coverage < min_percentage:
        print(f"Coverage below the minimum requirement of {min_percentage}%")
        sys.exit(1)
    else:
        print(f"Coverage meets or exceeds the minimum requirement of {min_percentage}%")
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_docstrings.py directory1 [directory2 ...] [--min-percentage=90.0]")
        sys.exit(1)
    
    dirs = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    
    min_pct = 90.0
    for arg in sys.argv[1:]:
        if arg.startswith('--min-percentage='):
            try:
                min_pct = float(arg.split('=')[1])
            except (IndexError, ValueError):
                print(f"Invalid min-percentage value: {arg}")
                sys.exit(1)
    
    main(dirs, min_pct) 