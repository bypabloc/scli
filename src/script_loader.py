import importlib.util
from pathlib import Path
from typing import Any, Dict


class ScriptLoader:
    def __init__(self, scripts_dir: str = "scripts"):
        self.scripts_dir = Path(scripts_dir)

    def discover_scripts(self) -> Dict[str, Dict[str, Any]]:
        scripts = {}

        if not self.scripts_dir.exists():
            return scripts

        for script_file in self.scripts_dir.glob("*.py"):
            if script_file.name == "__init__.py":
                continue

            script_name = script_file.stem
            try:
                script_info = self._load_script_info(script_file)
                if script_info:
                    scripts[script_name] = script_info
            except Exception as e:
                print(f"Error loading script {script_name}: {e}")

        return scripts

    def _load_script_info(self, script_path: Path) -> Dict[str, Any]:
        spec = importlib.util.spec_from_file_location(script_path.stem, script_path)
        if not spec or not spec.loader:
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        main_func = getattr(module, "main", None)
        if not main_func or not callable(main_func):
            return None

        description = getattr(module, "DESCRIPTION", script_path.stem)

        return {
            "path": script_path,
            "module": module,
            "main_func": main_func,
            "description": description,
        }

    def execute_script(
        self, script_name: str, scripts: Dict[str, Dict[str, Any]], args: list = None
    ) -> bool:
        if script_name not in scripts:
            return False

        try:
            # Set sys.argv for the script to use argparse
            import sys

            original_argv = sys.argv.copy()

            # Set the script name as argv[0] and pass remaining arguments
            script_path = scripts[script_name]["path"]
            sys.argv = [str(script_path)] + (args or [])

            try:
                scripts[script_name]["main_func"]()
                return True
            finally:
                # Restore original argv
                sys.argv = original_argv
        except Exception as e:
            print(f"Error executing script {script_name}: {e}")
            return False
