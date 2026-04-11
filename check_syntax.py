try:
    import industryanalysis
    print("✅ Syntax check passed: industryanalysis.py imported successfully.")
except ImportError as e:
    print(f"❌ ImportError: {e}")
except SyntaxError as e:
    print(f"❌ SyntaxError: {e}")
except Exception as e:
    print(f"❌ Other Error: {e}")
