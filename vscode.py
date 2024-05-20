# coding: utf-8
import os
import sys
import dotbot
import shutil

from subprocess import check_output, call

class VSCode(dotbot.Plugin):
    DIRECTIVE_VSCODE = "vscode"
    DIRECTIVE_VSCODE_FILE = "vscodefile"

    DEFAULTS = {
        "exec": "code",
        "uninstall-not-listed": False,
        "extensions": []
    }

    def can_handle(self, directive):
        return directive in (self.DIRECTIVE_VSCODE, self.DIRECTIVE_VSCODE_FILE)

    def handle(self, directive, data):
        if directive == self.DIRECTIVE_VSCODE_FILE:
            return self._handle_vscodefile(data)
        elif directive == self.DIRECTIVE_VSCODE:
            return self._handle_vscode(data)

    def _handle_vscodefile(self, data):
        if not isinstance(data, dict):
            self._log.error("Error format, please refer to documentation.")
            return False

        exec = data['exec'] if 'exec' in data else self.DEFAULTS['exec']
        uninstall_not_listed = data['uninstall-not-listed'] if 'uninstall-not-listed' in data else self.DEFAULTS['uninstall-not-listed']
        vsfile = data['file'] if 'file' in data else None

        if exec is None or not isinstance(uninstall_not_listed, bool) or vsfile is None:
            self._log.error("Error format, please refer to documentation.")
            return False

        extensions = self._vscodefile_extensions(vsfile)

        return self._sync(extensions, exec, uninstall_not_listed)

    def _handle_vscode(self, data):
        if not isinstance(data, dict):
            self._log.error("Error format, please refer to documentation.")
            return False

        exec = data['exec'] if 'exec' in data else  self.DEFAULTS['exec']
        uninstall_not_listed = data['uninstall-not-listed'] if 'uninstall-not-listed' in data else self.DEFAULTS['uninstall-not-listed']
        extensions = data['extensions'] if 'extensions' in data else self.DEFAULTS['extensions']

        if exec is None or not isinstance(uninstall_not_listed, bool) or not isinstance(extensions, list):
            self._log.error("Error format, please refer to documentation.")
            return False

        return self._sync(extensions, exec, uninstall_not_listed)

    def _vscodefile_extensions(self, vsfile):
        try:
            with open(vsfile) as f:
                result = [e.strip().lower() for e in f.readlines()]

        except FileNotFoundError:
            self._log.error("Can not find vscodefile: {}".format(vsfile))
            return None

        return result

    def _sync(self, extensions, exec, uninstall_not_listed):
        try:
            code = VSCodeInstance(exec)

            installed_extensions = code.installed_extensions()
            need_install = []
            need_remove = []

            # need install
            need_install = [e for e in extensions if e.lower() not in installed_extensions]

            # need remove
            if uninstall_not_listed:
                need_remove = [e for e in installed_extensions if e.lower() not in extensions]

            for extension in need_install:
                code.install(extension)

            for extension in need_remove:
                code.uninstall(extension)
        except VSCodeError as e:
            self._log.error(e.message)
            return False
        return True


class VSCodeInstance(object):
    def __init__(self, exec):
        self._exec = exec if exec else "code"
        self._binary = shutil.which(self._exec)

    @property
    def installed(self):
        return self._binary is not None

    def installed_extensions(self):
        if not self.installed:
            raise VSCodeError("{} is not installed.".format(self._exec))
        output = check_output([self._binary, "--list-extensions"]).decode(
            sys.getdefaultencoding()
        )

        return set(line.lower() for line in output.splitlines())

    def install(self, extension):
        if not self.installed:
            raise VSCodeError("{} is not installed.".format(self._exec))
        call([self._binary, "--install-extension", extension])

    def uninstall(self, extension):
        if not self.installed:
            raise VSCodeError("{} is not installed.".format(self._exec))
        call([self._binary, "--uninstall-extension", extension])


class VSCodeError(Exception):
    def __init__(self, message):
        self.message = message
