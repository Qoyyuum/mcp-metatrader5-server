#!/usr/bin/env python
"""
Script to inspect a FastMCP object and print its attributes.
This helps us understand how to properly access the ASGI functionality.
"""

import sys
import inspect
from mt5_server import mcp

def inspect_object(obj, name="object", level=0):
    """Inspect an object and print its attributes and methods."""
    indent = "  " * level
    print(f"{indent}{name} ({type(obj).__name__}):")
    
    # Get all attributes
    attrs = dir(obj)
    
    # Print callable attributes first
    for attr_name in attrs:
        if attr_name.startswith("__"):
            continue  # Skip dunder methods
            
        try:
            attr = getattr(obj, attr_name)
            if callable(attr):
                if inspect.iscoroutinefunction(attr):
                    print(f"{indent}  {attr_name}: async callable")
                else:
                    print(f"{indent}  {attr_name}: callable")
        except Exception as e:
            print(f"{indent}  {attr_name}: <Error accessing: {e}>")
    
    # Print non-callable attributes
    for attr_name in attrs:
        if attr_name.startswith("__"):
            continue  # Skip dunder methods
            
        try:
            attr = getattr(obj, attr_name)
            if not callable(attr):
                if isinstance(attr, (str, int, float, bool, list, dict, tuple, set)):
                    print(f"{indent}  {attr_name}: {type(attr).__name__} = {attr}")
                else:
                    print(f"{indent}  {attr_name}: {type(attr).__name__}")
        except Exception as e:
            print(f"{indent}  {attr_name}: <Error accessing: {e}>")

if __name__ == "__main__":
    print("Inspecting FastMCP object...")
    inspect_object(mcp, "mcp")
    
    # Specifically look for ASGI app candidates
    print("\nPotential ASGI app candidates:")
    for attr_name in dir(mcp):
        if attr_name.startswith("_") and not attr_name.startswith("__"):
            try:
                attr = getattr(mcp, attr_name)
                if callable(attr) and inspect.iscoroutinefunction(attr):
                    print(f"  {attr_name}: async callable")
            except Exception:
                pass
    
    print("\nTrying to access mcp.asgi or mcp._asgi:")
    for name in ["asgi", "_asgi"]:
        try:
            attr = getattr(mcp, name, None)
            if attr is not None:
                print(f"  mcp.{name} exists: {type(attr).__name__}")
                if callable(attr):
                    print(f"  mcp.{name} is callable")
                    if inspect.iscoroutinefunction(attr):
                        print(f"  mcp.{name} is a coroutine function")
        except Exception as e:
            print(f"  Error accessing mcp.{name}: {e}") 