#!/usr/bin/env python3
"""Test script to check imports."""

try:
    import os
    import requests
    print("✓ Basic imports ok")
    
    import sys
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    try:
        import dotenv
        print("✓ dotenv ok")
    except Exception as e:
        print(f"✗ dotenv error: {e}")
    
    try:
        from duckduckgo_search import DDGS
        print("✓ duckduckgo ok")
    except Exception as e:
        print(f"✗ duckduckgo error: {e}")
    
    try:
        from langchain_openai import ChatOpenAI
        print("✓ langchain_openai ok")
    except Exception as e:
        print(f"✗ langchain_openai error: {e}")
    
    try:
        from langchain.agents import Tool, create_react_agent, AgentExecutor
        print("✓ langchain.agents ok")
    except Exception as e:
        print(f"✗ langchain.agents error: {e}")
    
    print("\nAll tests completed!")
    
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
