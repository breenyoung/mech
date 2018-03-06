# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 German Mendez Bravo (Kronuz)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#

from __future__ import print_function

import os
import sys
import logging
import subprocess

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_fallback_executable():
    if 'PATH' in os.environ:
        for path in os.environ['PATH'].split(os.pathsep):
            vmrun = os.path.join(path, 'vmrun')
            if os.path.exists(vmrun):
                return vmrun
            vmrun = os.path.join(path, 'vmrun.exe')
            if os.path.exists(vmrun):
                return vmrun


def get_darwin_executable():
    vmrun = '/Applications/VMware Fusion.app/Contents/Library/vmrun'
    if os.path.exists(vmrun):
        return vmrun
    return get_fallback_executable()


def get_win32_executable():
    import _winreg
    reg = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
    try:
        key = _winreg.OpenKey(reg, 'SOFTWARE\\VMware, Inc.\\VMware Workstation')
        try:
            return os.path.join(_winreg.QueryValueEx(key, 'InstallPath')[0], 'vmrun.exe')
        finally:
            _winreg.CloseKey(key)
    except WindowsError:
        key = _winreg.OpenKey(reg, 'SOFTWARE\\WOW6432Node\\VMware, Inc.\\VMware Workstation')
        try:
            return os.path.join(_winreg.QueryValueEx(key, 'InstallPath')[0], 'vmrun.exe')
        finally:
            _winreg.CloseKey(key)
    finally:
        reg.Close()
    return get_fallback_executable()


class VMrun(object):
    if sys.platform == 'darwin':
        provider = 'fusion'
        default_executable = get_darwin_executable()
    elif sys.platform == 'win32':
        provider = 'ws'
        default_executable = get_win32_executable()
    else:
        provider = 'ws'
        default_executable = get_fallback_executable()

    def __init__(self, vmx_file=None, user=None, password=None, executable=None):
        self.vmx_file = vmx_file
        self.user = user
        self.password = password
        self.executable = executable or self.default_executable

    def vmrun(self, cmd, *args):
        cmds = [self.executable]
        cmds.append('-T')
        cmds.append(self.provider)
        if self.user:
            cmds.append('-gu')
            cmds.append(self.user)
        if self.password:
            cmds.append('-gp')
            cmds.append(self.password)
        cmds.append(cmd)
        cmds.extend(filter(None, args))

        logger.debug(" ".join(cmds))

        proc = subprocess.Popen(cmds, stdout=subprocess.PIPE)
        stdoutdata, stderrdata = proc.communicate()

        if stderrdata:
            print(stderrdata, file=sys.stderr)

        return stdoutdata

    ############################################################################
    # POWER COMMANDS           PARAMETERS           DESCRIPTION
    # --------------           ----------           -----------
    # start                    Path to vmx file     Start a VM or Team
    #                          [gui|nogui]
    #
    # stop                     Path to vmx file     Stop a VM or Team
    #                          [hard|soft]
    #
    # reset                    Path to vmx file     Reset a VM or Team
    #                          [hard|soft]
    #
    # suspend                  Path to vmx file     Suspend a VM or Team
    #                          [hard|soft]
    #
    # pause                    Path to vmx file     Pause a VM
    #
    # unpause                  Path to vmx file     Unpause a VM
    #

    def start(self, gui=False):
        '''Start a VM or Team'''
        return self.vmrun('start', self.vmx_file, 'gui' if gui else 'nogui')

    def stop(self, mode='soft'):
        '''Stop a VM or Team'''
        return self.vmrun('stop', self.vmx_file, mode)

    def reset(self, mode='soft'):
        '''Reset a VM or Team'''
        return self.vmrun('reset', self.vmx_file, mode)

    def suspend(self, mode='soft'):
        '''Suspend a VM or Team'''
        return self.vmrun('suspend', self.vmx_file, mode)

    def pause(self):
        '''Pause a VM'''
        return self.vmrun('pause', self.vmx_file)

    def unpause(self):
        '''Unpause a VM'''
        return self.vmrun('unpause', self.vmx_file)

    ############################################################################
    # SNAPSHOT COMMANDS        PARAMETERS           DESCRIPTION
    # -----------------        ----------           -----------
    # listSnapshots            Path to vmx file     List all snapshots in a VM
    #                          [showTree]
    #
    # snapshot                 Path to vmx file     Create a snapshot of a VM
    #                          Snapshot name
    #
    # deleteSnapshot           Path to vmx file     Remove a snapshot from a VM
    #                          Snapshot name
    #                          [andDeleteChildren]
    #
    # revertToSnapshot         Path to vmx file     Set VM state to a snapshot
    #                          Snapshot name
    #

    def listSnapshots(self, show_tree=False):
        '''List all snapshots in a VM'''
        return self.vmrun('listSnapshots', self.vmx_file, 'showTree' if show_tree else None)

    def snapshot(self, snap_name):
        '''Create a snapshot of a VM'''
        return self.vmrun('snapshot', self.vmx_file, snap_name)

    def deleteSnapshot(self, snap_name, and_delete_children=False):
        '''Remove a snapshot from a VM'''
        return self.vmrun('deleteSnapshot', self.vmx_file, snap_name, 'andDeleteChildren' if and_delete_children else None)

    def revertToSnapshot(self, snap_name):
        '''Set VM state to a snapshot'''
        return self.vmrun('revertToSnapshot', self.vmx_file, snap_name)

    ############################################################################
    # NETWORKADAPTER COMMANDS  PARAMETERS           DESCRIPTION
    # -----------------------  ----------           -----------
    # listNetworkAdapters      Path to vmx file     List all network adapters in a VM
    #
    #
    # addNetworkAdapter        Path to vmx file     Add a network adapter on a VM
    #                          Network adapter type
    #                          [Host nework]
    #
    #
    # setNetworkAdapter        Path to vmx file     Update a network adapter on a VM
    #                          Network adapter index
    #                          Network adapter type
    #                          [Host network]
    #
    #
    # deleteNetworkAdapter     Path to vmx file     Remove a network adapter on a VM
    #                          Network adapter index

    def listNetworkAdapters(self):
        '''List all network adapters in a VM'''
        return self.vmrun('listNetworkAdapters', self.vmx_file)

    def addNetworkAdapter(self, adapter_type, host_network=None):
        '''Add a network adapter on a VM'''
        return self.vmrun('addNetworkAdapter', self.vmx_file, adapter_type, host_network)

    def setNetworkAdapter(self, adapter_index, adapter_type, host_network=None):
        '''Update a network adapter on a VM'''
        return self.vmrun('setNetworkAdapter', self.vmx_file, adapter_index, adapter_type, host_network)

    def deleteNetworkAdapter(self, adapter_index):
        '''Remove a network adapter on a VM'''
        return self.vmrun('deleteNetworkAdapter', self.vmx_file, adapter_index)

    ############################################################################
    # HOST NETWORK COMMANDS    PARAMETERS           DESCRIPTION
    # ---------------------    ----------           -----------
    # listHostNetworks                              List all networks in the host
    #
    # listPortForwardings      Host network name    List all available port forwardings on a host network
    #
    #
    # setPortForwarding        Host network name    Add or update a port forwarding on a host network
    #                          Protocol
    #                          Host port
    #                          Guest ip
    #                          Guest port
    #                          [Description]
    #
    # deletePortForwarding     Host network name    Delete a port forwarding on a host network
    #                          Protocol
    #                          Host port

    def listHostNetworks(self):
        '''List all networks in the host'''
        return self.vmrun('listHostNetworks')

    def listPortForwardings(self, host_network):
        '''List all available port forwardings on a host network'''
        return self.vmrun('listPortForwardings', host_network)

    def setPortForwarding(self, host_network, protocol, host_port, guest_ip, guest_port, description=None):
        '''Add or update a port forwarding on a host network'''
        return self.vmrun('setPortForwarding', host_network, protocol, host_port, guest_ip, guest_port, description)

    def deletePortForwarding(self, host_network, protocol, host_port):
        '''Delete a port forwarding on a host network'''
        return self.vmrun('deletePortForwarding', host_network, protocol, host_port)

    ############################################################################
    # GUEST OS COMMANDS        PARAMETERS           DESCRIPTION
    # -----------------        ----------           -----------
    # runProgramInGuest        Path to vmx file     Run a program in Guest OS
    #                          [-noWait]
    #                          [-activeWindow]
    #                          [-interactive]
    #                          Complete-Path-To-Program
    #                          [Program arguments]
    #
    # fileExistsInGuest        Path to vmx file     Check if a file exists in Guest OS
    #                          Path to file in guest
    #
    # directoryExistsInGuest   Path to vmx file     Check if a directory exists in Guest OS
    #                          Path to directory in guest
    #
    # setSharedFolderState     Path to vmx file     Modify a Host-Guest shared folder
    #                          Share name
    #                          Host path
    #                          writable | readonly
    #
    # addSharedFolder          Path to vmx file     Add a Host-Guest shared folder
    #                          Share name
    #                          New host path
    #
    # removeSharedFolder       Path to vmx file     Remove a Host-Guest shared folder
    #                          Share name
    #
    # enableSharedFolders      Path to vmx file     Enable shared folders in Guest
    #                          [runtime]
    #
    # disableSharedFolders     Path to vmx file     Disable shared folders in Guest
    #                          [runtime]
    #
    # listProcessesInGuest     Path to vmx file     List running processes in Guest OS
    #
    # killProcessInGuest       Path to vmx file     Kill a process in Guest OS
    #                          process id
    #
    # runScriptInGuest         Path to vmx file     Run a script in Guest OS
    #                          [-noWait]
    #                          [-activeWindow]
    #                          [-interactive]
    #                          Interpreter path
    #                          Script text
    #
    # deleteFileInGuest        Path to vmx file     Delete a file in Guest OS
    #                          Path in guest
    #
    # createDirectoryInGuest   Path to vmx file     Create a directory in Guest OS
    #                          Directory path in guest
    #
    # deleteDirectoryInGuest   Path to vmx file     Delete a directory in Guest OS
    #                          Directory path in guest
    #
    # CreateTempfileInGuest    Path to vmx file     Create a temporary file in Guest OS
    #
    # listDirectoryInGuest     Path to vmx file     List a directory in Guest OS
    #                          Directory path in guest
    #
    # CopyFileFromHostToGuest  Path to vmx file     Copy a file from host OS to guest OS
    #                          Path on host
    #                          Path in guest
    #
    # CopyFileFromGuestToHost  Path to vmx file     Copy a file from guest OS to host OS
    #                          Path in guest
    #                          Path on host
    #
    # renameFileInGuest        Path to vmx file     Rename a file in Guest OS
    #                          Original name
    #                          New name
    #
    # typeKeystrokesInGuest    Path to vmx file     Type Keystrokes in Guest OS
    #                          keystroke string
    #
    # connectNamedDevice       Path to vmx file     Connect the named device in the Guest OS
    #                          device name
    #
    # disconnectNamedDevice    Path to vmx file     Disconnect the named device in the Guest OS
    #                          device name
    #
    # captureScreen            Path to vmx file     Capture the screen of the VM to a local file
    #                          Path on host
    #
    # writeVariable            Path to vmx file     Write a variable in the VM state
    #                          [runtimeConfig|guestEnv|guestVar]
    #                          variable name
    #                          variable value
    #
    # readVariable             Path to vmx file     Read a variable in the VM state
    #                          [runtimeConfig|guestEnv|guestVar]
    #                          variable name
    #
    # getGuestIPAddress        Path to vmx file     Gets the IP address of the guest
    #                          [-wait]
    #

    def runProgramInGuest(self, program_path, *args, **kwargs):
        wait = kwargs.pop('wait', True)
        activate_window = kwargs.pop('activate_window', False)
        interactive = kwargs.pop('interactive', False)
        return self.vmrun('runProgramInGuest', self.vmx_file, None if wait else '-noWait', '-activateWindow' if activate_window else None, '-interactive' if interactive else None, program_path, *args)

    def fileExistsInGuest(self, file):
        '''Check if a file exists in Guest OS'''
        return 'not' not in self.execute('fileExistsInGuest', self.vmx_file, file)

    def directoryExistsInGuest(self, path):
        '''Check if a directory exists in Guest OS'''
        return 'not' not in self.execute('directoryExistsInGuest', self.vmx_file, path)

    def setSharedFolderState(self, share_name, new_path, mode='readonly'):
        '''Modify a Host-Guest shared folder'''
        return self.vmrun('setSharedFolderState', self.vmx_file, share_name, new_path, mode)

    def addSharedFolder(self, share_name, host_path):
        '''Add a Host-Guest shared folder'''
        return self.vmrun('addSharedFolder', self.vmx_file, share_name, host_path)

    def removeSharedFolder(self, share_name):
        '''Remove a Host-Guest shared folder'''
        return self.vmrun('removeSharedFolder', self.vmx_file, share_name)

    def enableSharedFolders(self, runtime=None):
        return self.vmrun('enableSharedFolders', self.vmx_file, runtime)

    def disableSharedFolders(self, runtime=None):
        '''Disable shared folders in Guest'''
        return self.vmrun('disableSharedFolders', self.vmx_file, runtime)

    def listProcessesInGuest(self):
        '''List running processes in Guest OS'''
        return self.vmrun('listProcessesInGuest', self.vmx_file)

    def killProcessInGuest(self, pid):
        '''Kill a process in Guest OS'''
        return self.vmrun('killProcessInGuest', self.vmx_file, pid)

    def runScriptInGuest(self, interpreter_path, script, wait=True, activate_window=False, interactive=False):
        '''Run a script in Guest OS'''
        return self.vmrun('runScriptInGuest', self.vmx_file, interpreter_path, script, None if wait else '-noWait', '-activateWindow' if activate_window else None, '-interactive' if interactive else None)

    def deleteFileInGuest(self, file):
        '''Delete a file in Guest OS'''
        return self.vmrun('deleteFileInGuest', self.vmx_file, file)

    def createDirectoryInGuest(self, path):
        '''Create a directory in Guest OS'''
        return self.vmrun('createDirectoryInGuest', self.vmx_file, path)

    def deleteDirectoryInGuest(self, path):
        '''Delete a directory in Guest OS'''
        return self.vmrun('deleteDirectoryInGuest', self.vmx_file, path)

    def CreateTempfileInGuest(self):
        '''Create a temporary file in Guest OS'''
        return self.vmrun('CreateTempfileInGuest', self.vmx_file)

    def listDirectoryInGuest(self, path):
        '''List a directory in Guest OS'''
        return self.vmrun('listDirectoryInGuest', self.vmx_file, path)

    def copyFileFromHostToGuest(self, host_path, guest_path):
        '''Copy a file from host OS to guest OS'''
        return self.vmrun('copyFileFromHostToGuest', self.vmx_file, host_path, guest_path)

    def copyFileFromGuestToHost(self, guest_path, host_path):
        '''Copy a file from guest OS to host OS'''
        return self.vmrun('copyFileFromGuestToHost', self.vmx_file, guest_path, host_path)

    def renameFileInGuest(self, original_name, new_name):
        '''Rename a file in Guest OS'''
        return self.vmrun('renameFileInGuest', self.vmx_file, original_name, new_name)

    def typeKeystrokesInGuest(self, keystroke):
        '''Type Keystrokes in Guest OS'''
        return self.vmrun('typeKeystrokesInGuest', self.vmx_file, keystroke)

    def connectNamedDevice(self, device_name):
        '''Disconnect the named device in the Guest OS'''
        return self.vmrun('connectNamedDevice', self.vmx_file, device_name)

    def disconnectNamedDevice(self, device_name):
        '''Disconnect the named device in the Guest OS'''
        return self.vmrun('disconnectNamedDevice', self.vmx_file, device_name)

    def captureScreen(self, path_on_host):
        '''Capture the screen of the VM to a local file'''
        return self.vmrun('captureScreen', self.vmx_file, path_on_host)

    def writeVariable(self, var_name, var_value, mode=None):
        '''Write a variable in the VM state'''
        return self.vmrun('writeVariable', self.vmx_file, mode, var_name, var_value)

    def readVariable(self, var_name, mode=None):
        '''Read a variable in the VM state'''
        return self.vmrun('readVariable', self.vmx_file, mode, var_name)

    def getGuestIPAddress(self, wait=True):
        '''Gets the IP address of the guest'''
        return self.vmrun('getGuestIPAddress', self.vmx_file, '-wait' if wait else None)

    ############################################################################
    # GENERAL COMMANDS         PARAMETERS           DESCRIPTION
    # ----------------         ----------           -----------
    # list                                          List all running VMs
    #
    # upgradevm                Path to vmx file     Upgrade VM file format, virtual hw
    #
    # installTools             Path to vmx file     Install Tools in Guest
    #
    # checkToolsState          Path to vmx file     Check the current Tools state
    #
    # deleteVM                 Path to vmx file     Delete a VM
    #
    # clone                    Path to vmx file     Create a copy of the VM
    #                          Path to destination vmx file
    #                          full|linked
    #                          [-snapshot=Snapshot Name]
    #                          [-cloneName=Name]

    def list(self):
        '''List all running VMs'''
        return self.vmrun('list', self.vmx_file)

    def upgradevm(self):
        '''Upgrade VM file format, virtual hw'''
        return self.vmrun('upgradevm', self.vmx_file)

    def installTools(self):
        '''Install Tools in Guest OS'''
        return self.vmrun('installTools', self.vmx_file)

    def checkToolsState(self):
        '''Check the current Tools state'''
        return self.vmrun('checkToolsState', self.vmx_file)

    def register(self):
        # unavailable in VMware Fusion 10 (OS X)?
        '''Register a VM'''
        return self.vmrun('register', self.vmx_file)

    def unregister(self):
        # unavailable in VMware Fusion 10 (OS X)?
        '''Unregister a VM'''
        return self.vmrun('unregister', self.vmx_file)

    def listRegisteredVM(self):
        # unavailable in VMware Fusion 10 (OS X)?
        '''List registered VMs'''
        return self.vmrun('listRegisteredVM', self.vmx_file)

    def deleteVM(self):
        '''Delete a VM'''
        return self.vmrun('deleteVM', self.vmx_file)

    def clone(self, dest_vmx, mode, snap_name=None):
        '''Create a copy of the VM'''
        return self.vmrun('clone', self.vmx_file, dest_vmx, mode, snap_name)

    ############################################################################
    # RECORD/REPLAY COMMANDS   PARAMETERS           DESCRIPTION
    # ----------------------   ----------           -----------
    # beginRecording           Path to vmx file     Begin recording a VM
    #                          Snapshot name
    #
    # endRecording             Path to vmx file     End recording a VM
    #
    # beginReplay              Path to vmx file     Begin replaying a VM
    #                          Snapshot name
    #
    # endReplay                Path to vmx file     End replaying a VM

    def beginRecording(self, snap_name):
        # unavailable in VMware Fusion 10 (OS X)?
        '''Begin recording a VM'''
        return self.vmrun('beginRecording', self.vmx_file, snap_name)

    def endRecording(self):
        # unavailable in VMware Fusion 10 (OS X)?
        '''End recording a VM'''
        return self.vmrun('endRecording', self.vmx_file)

    def beginReplay(self, snap_name):
        # unavailable in VMware Fusion 10 (OS X)?
        '''Begin replaying a VM'''
        return self.vmrun('beginReplay', self.vmx_file, snap_name)

    def endReplay(self):
        # unavailable in VMware Fusion 10 (OS X)?
        '''End replaying a VM'''
        return self.vmrun('endReplay', self.vmx_file)

    ############################################################################
    # VPROBE COMMANDS          PARAMETERS           DESCRIPTION
    # ---------------          ----------           -----------
    # vprobeVersion            Path to vmx file     List VP version
    #
    # vprobeLoad               Path to vmx file     Load VP script
    #                          'VP script text'
    #
    # vprobeLoadFile           Path to vmx file     Load VP file
    #                          Path to VP file
    #
    # vprobeReset              Path to vmx file     Disable all vprobes
    #
    # vprobeListProbes         Path to vmx file     List probes
    #
    # vprobeListGlobals        Path to vmx file     List global variables

    def vprobeVersion(self):
        # unavailable in VMware Fusion 10 (OS X)?
        '''List VP version'''
        return self.vmrun('vprobeVersion', self.vmx_file)

    def vprobeLoad(self, script):
        # unavailable in VMware Fusion 10 (OS X)?
        '''Load VP script'''
        return self.vmrun('vprobeLoad', self.vmx_file, script)

    def vprobeLoadFile(self, vp):
        # unavailable in VMware Fusion 10 (OS X)?
        '''Load VP file'''
        return self.vmrun('vprobeLoadFile', self.vmx_file, vp)

    def vprobeReset(self):
        # unavailable in VMware Fusion 10 (OS X)?
        '''Disable all vprobes'''
        return self.vmrun('vprobeReset', self.vmx_file)

    def vprobeListProbes(self):
        # unavailable in VMware Fusion 10 (OS X)?
        '''List probes'''
        return self.vmrun('vprobeListProbes', self.vmx_file)

    def vprobeListGlobals(self):
        # unavailable in VMware Fusion 10 (OS X)?
        '''List global variables'''
        return self.vmrun('vprobeListGlobals', self.vmx_file)

    ############################################################################

    def installedTools(self):
        state = self.checkToolsState()
        return state == 'installed' or state == 'running'
