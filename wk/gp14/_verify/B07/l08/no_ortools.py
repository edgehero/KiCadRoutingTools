"""Run a script with ortools made unimportable (simulates a requirements.txt-only install)."""
import runpy, sys
class _Block:
    def find_spec(self, name, path=None, target=None):
        if name == 'ortools' or name.startswith('ortools.'):
            raise ModuleNotFoundError(f"No module named '{name}' (blocked by no_ortools.py)")
        return None
sys.meta_path.insert(0, _Block())
target = sys.argv[1]; sys.argv = sys.argv[1:]
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(target)))
runpy.run_path(target, run_name='__main__')
