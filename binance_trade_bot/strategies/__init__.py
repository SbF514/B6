import importlib
import os


def get_strategy(name):
    for dirpath, _, filenames in os.walk(os.path.dirname(__file__)):
        filename: str
        for filename in filenames:
            if filename.endswith("_strategy.py"):
                if filename.replace("_strategy.py", "") == name:
                    spec = importlib.util.spec_from_file_location(name, os.path.join(dirpath, filename))
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    # Try both Strategy and RSIStrategy class names
                    if hasattr(module, 'RSIStrategy'):
                        return module.RSIStrategy
                    if hasattr(module, 'Strategy'):
                        return module.Strategy
                    # Also check for function
                    if hasattr(module, 'get_strategy'):
                        fn = getattr(module, 'get_strategy')
                        if callable(fn):
                            result = fn(name)
                            if result:
                                return result
    return None
