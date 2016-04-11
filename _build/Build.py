# -*- coding: utf-8 -*-
#
# This file is part of EventGhost.
# Copyright © 2005-2016 EventGhost Project <http://www.eventghost.net/>
#
# EventGhost is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 2 of the License, or (at your option)
# any later version.
#
# EventGhost is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with EventGhost. If not, see <http://www.gnu.org/licenses/>.

"""
This script creates the EventGhost setup installer.
"""
import sys
import os
from os.path import abspath, dirname, exists, join
from glob import glob
from inspect import stack

# local imports
import builder
from builder.Logging import LogToFile
from builder.Utils import ListDir


EXCLUDE_DIRS = [
    # Files and folders beginning with "." are excluded automatically.
    "build",
]

INCLUDE_FILES = [
    "CHANGELOG.TXT",
    "EventGhost.chm",
    "EventGhost.exe",
    "Example.xml",
    "LICENSE.TXT",
    "msvcm90.dll",
    "msvcp90.dll",
    "msvcr90.dll",
    "py.exe",
    "pyw.exe",
    "python27.dll",
]


class MyBuilder(builder.Builder):
    name = "EventGhost"
    description = "EventGhost Automation Tool"
    companyName = "EventGhost Project"
    copyright = u"Copyright © 2005-2016 EventGhost Project"
    mainScript = "EventGhost.pyw"

    includeModules = [
        "wx",
        "PIL",
        "comtypes",
        "pywin32",
        "pythoncom",
        "isapi",
        "win32com",
        "docutils",
        "Crypto",
        "jinja2",
    ]
    excludeModules = [
        "lib2to3",
        "idlelib",
        "gopherlib",
        "Tix",
        "test",
        "Tkinter",
        "_tkinter",
        "Tkconstants",
        "FixTk",
        "tcl",
        "turtle", # another Tkinter module

        "distutils.command.bdist_packager",
        "distutils.mwerkscompiler",
        "curses",
        #"ctypes.macholib", # seems to be for Apple

        "wx.lib.vtk",
        "wx.tools.Editra",
        "wx.tools.XRCed",
        "wx.lib.plot", # needs NumPy
        "wx.lib.floatcanvas", # needs NumPy

        "ImageTk", # py2exe seems to hang if not removed
        "ImageGL",
        "ImageQt",
        "WalImageFile", # odd syntax error in file
        # and no TCL through PIL
        "_imagingtk",
        "PIL._imagingtk",
        "PIL.ImageTk",
        "FixTk",

        "win32com.gen_py",
        "win32com.demos",
        "win32com.axdebug",
        "win32com.axscript",
        "pywin",
        "comtypes.gen",
        "eg",
    ]


    def GetSetupFiles(self):
        """
        Return all files needed by the installer.

        The code scans for all files in the working copy and adds
        them to the list, except if a "noinstall" property is set for the file
        or a parent directory of the file.

        Plugins with a "noinclude" file are also skipped.
        """
        srcDir = self.sourceDir
        files = set(ListDir(srcDir, EXCLUDE_DIRS, fullpath=False))

        noincludes = ["."]
        coreplugins = []
        for f in files.copy():
            if f.endswith("noinclude"):
                noincludes.append(f.replace("noinclude", ""))
            elif f.endswith("core-plugin"):
                coreplugins.append(f.replace("core-plugin", ""))
                files.remove(f)

        installFiles = []
        for f in files:
            if not f.startswith(tuple(noincludes)):
                if f.count("\\") == 0 and f not in INCLUDE_FILES:
                    pass
                else:
                    #if f.startswith(tuple(coreplugins)):
                    installFiles.append([f, "{app}"])
                    #else:
                        # Install to ProgramData\EventGhost\plugins
                        #installFiles.append([f,
                            #"{commonappdata}\\%s" % self.appName])

        return installFiles


    def CreateInstaller(self):
        """
        Create and compile the Inno Setup installer script.
        """
        from builder.InnoSetup import InnoInstaller
        inno = InnoInstaller(self)
        plugins = {}
        for filename, prefix in self.GetSetupFiles():
            if filename.startswith("plugins\\"):
                pluginFolder = filename.split("\\")[1]
                plugins[pluginFolder] = True
            if (
                filename.startswith("lib")
                and not filename.startswith("lib%s\\" % self.pyVersionStr)
            ) or (
                len(filename) < 10
                and filename.startswith("py")
                and filename.endswith(".exe")
            ):
                continue
            inno.AddFile(join(self.sourceDir, filename), dirname(filename), prefix=prefix)
        for filename in glob(join(self.libraryDir, '*.*')):
            inno.AddFile(filename, self.libraryName)
        inno.AddFile(
            join(self.sourceDir, "py%s.exe" % self.pyVersionStr),
            destName="py.exe"
        )
        inno.AddFile(
            join(self.sourceDir, "pyw%s.exe" % self.pyVersionStr),
            destName="pyw.exe"
        )
        inno.AddFile(
            join(self.tmpDir, "VersionInfo.py"),
            destDir="eg\\Classes"
        )
        # create entries in the [InstallDelete] section of the Inno script to
        # remove all known plugin directories before installing the new
        # plugins.
        for plugin in plugins.keys():
            inno.Add(
                "InstallDelete",
                'Type: filesandordirs; Name: "{app}\\plugins\\%s"' % plugin
            )
        inno.Add(
            "InstallDelete",
            'Type: files; Name: "{app}\\lib%s\\*.*"' % self.pyVersionStr
        )
        inno.ExecuteInnoSetup()



# Always execute build from build folder.
os.chdir(dirname(abspath(stack()[0][1])))

# Create output folder.
if not exists("output"):
    os.mkdir("output")

# Initialize logging.
LogToFile(join("output", "Build.log"))

# Search virtualenv for modules last so stock distutils is used.
if hasattr(sys, "real_prefix"):
    for path in sys.path[:]:
        if path.startswith(sys.prefix):
            sys.path.remove(path)
            sys.path.append(path)

MyBuilder().Start()
