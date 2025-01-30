import subprocess
import sys
import importlib.util
from pathlib import Path
from _logging import log_to_gui

class ModuleManager:
    """
    Manages Python module dependencies, ensuring they are installed and available.
    """

    def __init__(self, requirements):
        """
        Initialize with a list of required Python modules.

        Args:
            requirements (list): List of module names as strings.
        """
        self.requirements = requirements

    def is_pip_installed(self):
        """
        Check if pip is installed on the system.

        Returns:
            bool: True if pip is installed, False otherwise.
        """
        return importlib.util.find_spec("pip") is not None

    def is_module_installed(self, module_name):
        """
        Check if a specific module is installed.

        Args:
            module_name (str): The name of the module.

        Returns:
            bool: True if the module is installed, False otherwise.
        """
        return importlib.util.find_spec(module_name) is not None

    def install_module(self, module_name):
        """
        Install a specific module using pip.

        Args:
            module_name (str): The name of the module to install.

        Raises:
            RuntimeError: If the installation fails.
        """
        try:
            print(f"Installing module: {module_name}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
            print(f"Module {module_name} installed successfully.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to install {module_name}: {e}")

    def install_modules(self):
        """
        Install all required modules.

        Raises:
            EnvironmentError: If pip is not installed.
        """
        if not self.is_pip_installed():
            raise EnvironmentError("pip is not installed. Please install pip and try again.")

        for module in self.requirements:
            if not self.is_module_installed(module):
                self.install_module(module)

    def verify_and_install(self):
        """
        Verify that all required modules are installed. If not, attempt to install them.
        """
        try:
            self.install_modules()
        except EnvironmentError as env_error:
            print(f"Environment Error: {env_error}")
            sys.exit(1)
        except RuntimeError as runtime_error:
            print(f"Runtime Error: {runtime_error}")
            sys.exit(1)

        # Restart the script if modules were installed
        if any(not self.is_module_installed(mod) for mod in self.requirements):
            print("Modules installed. Restarting the application...")

            # Convert os.execl to Path and subprocess
            python_path = Path(sys.executable)  # Get the executable path as a Path object
            subprocess.run([python_path, *sys.argv])  # Restart the application

if __name__ == "__main__":
    required_modules = ["PyQt5", "schedule", "timedelta"]
    manager = ModuleManager(required_modules)
    manager.verify_and_install()
