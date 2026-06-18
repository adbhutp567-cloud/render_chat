#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    def _add_project_venv_site_packages():
        """Try to locate a project virtualenv and add its site-packages to sys.path.

        Looks for common venv folders (myenv, .venv, venv, .env) and adds the
        platform-appropriate site-packages directory if found.
        Returns the path added or None.
        """
        project_root = os.path.dirname(os.path.abspath(__file__))
        candidates = ('myenv', '.venv', 'venv', '.env')
        for name in candidates:
            vpath = os.path.join(project_root, name)
            if not os.path.isdir(vpath):
                continue
            # Windows layout
            sp = os.path.join(vpath, 'Lib', 'site-packages')
            if os.path.isdir(sp):
                sys.path.insert(0, sp)
                return sp
            # Unix layout: lib/pythonX.Y/site-packages
            for pyver in (f'python{sys.version_info.major}.{sys.version_info.minor}', f'python{sys.version_info.major}'):
                sp = os.path.join(vpath, 'lib', pyver, 'site-packages')
                if os.path.isdir(sp):
                    sys.path.insert(0, sp)
                    return sp
        return None

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        added = _add_project_venv_site_packages()
        if added:
            try:
                from django.core.management import execute_from_command_line
            except ImportError as exc:
                raise ImportError(
                    "Couldn't import Django even after adding project venv site-packages ({0}).\n"
                    "Activate the virtual environment or run Django via the venv python:\n"
                    "    ./{1}/Scripts/Activate.ps1  (PowerShell)\n"
                    "    {1}/bin/activate  (bash)\n"
                    "Or run: {2} manage.py <command>".format(added, 'myenv', os.path.join(added.split(os.sep)[0], 'Scripts', 'python.exe'))
                ) from exc
        else:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?\n"
                "If you have a project venv, activate it, e.g.:\n"
                "    .\\myenv\\Scripts\\Activate.ps1  (PowerShell)\n"
                "    .\\myenv\\bin\\activate  (bash)\n"
                "Or run Django with the venv python: ".format()
            )
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
