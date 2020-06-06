# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2009-2013 Stephan Raue (stephan@openelec.tv)
# Copyright (C) 2013 Lutz Fiebach (lufie@openelec.tv)
# Copyright (C) 2018-present Team CoreELEC (https://coreelec.org)

################################# variables ##################################

import xbmc
import xbmcaddon
import xbmcgui
import os
import re
import locale
import sys
import urllib2
import time
import tarfile
import traceback
import subprocess
import dbus
import dbus.mainloop.glib
import defaults
import shutil
import hashlib, binascii

from xml.dom import minidom

__author__ = 'CoreELEC'
__scriptid__ = 'service.coreelec.settings'
__addon__ = xbmcaddon.Addon(id=__scriptid__)
__cwd__ = __addon__.getAddonInfo('path')
__oe__ = sys.modules[globals()['__name__']]
__media__ = '%s/resources/skins/Default/media' % __cwd__
xbmcDialog = xbmcgui.Dialog()

is_service = False
conf_lock = False
__busy__ = 0
xbmcIsPlaying = 0
input_request = False
dictModules = {}
listObject = {
    'list': 1100,
    'netlist': 1200,
    'btlist': 1300,
    'other': 1900,
    'test': 900,
    }
CANCEL = (
    9,
    10,
    216,
    247,
    257,
    275,
    61467,
    92,
    61448,
    )

try:
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
except:
    pass

dbusSystemBus = dbus.SystemBus()

###############################################################################
########################## initialize module ##################################
## append resource subfolders to path

sys.path.append(xbmc.translatePath(os.path.join(__cwd__, 'resources', 'lib')))
sys.path.append(xbmc.translatePath(os.path.join(__cwd__, 'resources', 'lib', 'modules')))

## set default encoding

encoding = locale.getpreferredencoding(do_setlocale=True)
reload(sys)
sys.setdefaultencoding(encoding)

## load oeSettings modules

import oeWindows
xbmc.log('## CoreELEC Addon ## ' + unicode(__addon__.getAddonInfo('version')))

class ProgressDialog:
    def __init__(self, label1=32181, label2=32182, label3=32183, minSampleInterval=1.0, maxUpdatesPerSecond=5):
        self.label1 = _(label1).encode('utf-8')
        self.label2 = _(label2).encode('utf-8')
        self.label3 = _(label3).encode('utf-8')
        self.minSampleInterval = minSampleInterval
        self.maxUpdatesPerSecond = 1 / maxUpdatesPerSecond

        self.dialog = None

        self.source = None
        self.total_size = 0

        self.reset()

    def reset(self):
        self.percent = 0
        self.speed = 0

        self.partial_size = 0
        self.prev_size = 0

        self.start = 0
        self.last_update = 0
        self.minutes = 0
        self.seconds = 0

        self.cancelled = False

    def setSource(self, source):
        self.source = source

    def setSize(self, total_size):
        self.total_size = total_size

    def getPercent(self):
        return self.percent

    def getSpeed(self):
        return self.speed

    def open(self, heading='CoreELEC', line1='', line2='', line3=''):
        self.dialog = xbmcgui.DialogProgress()
        self.dialog.create(heading, line1, line2, line3)
        self.reset()

    def update(self, chunk):
        if self.dialog and self.needsUpdate(chunk):
            line1 = '%s: %s' % (self.label1, self.source.rsplit('/', 1)[1])
            line2 = '%s: %s KB/s' % (self.label2, '{:,}'.format(self.speed))
            line3 = '%s: %d m %d s' % (self.label3, self.minutes, self.seconds)
            self.dialog.update(self.percent, line1, line2, line3)
            self.last_update = time.time()

    def close(self):
        if self.dialog:
            self.dialog.close()
        self.dialog = None

    # Calculate current speed at regular intervals, or upon completion
    def sample(self, chunk):
        self.partial_size += len(chunk)

        now = time.time()
        if self.start == 0:
            self.start = now

        if (now - self.start) >= self.minSampleInterval or not chunk:
            self.speed = max(int((self.partial_size - self.prev_size) / (now - self.start) / 1024), 1)
            remain = self.total_size - self.partial_size
            self.minutes = int(remain / 1024 / self.speed / 60)
            self.seconds = int(remain / 1024 / self.speed) % 60
            self.prev_size = self.partial_size
            self.start = now

        if self.total_size != 0:
            self.percent = int(self.partial_size * 100.0 / self.total_size)

    # Update the progress dialog when required, or upon completion
    def needsUpdate(self, chunk):
        if not chunk:
            return True
        else:
            return ((time.time() - self.last_update) >= self.maxUpdatesPerSecond)

    def iscanceled(self):
        if self.dialog:
            self.cancelled = self.dialog.iscanceled()
        return self.cancelled

def _(code):
    wizardComp = read_setting('coreelec', 'wizard_completed')
    if wizardComp == "True":
        codeNew = __addon__.getLocalizedString(code)
    else:
        curLang = read_setting("system", "language")
        if curLang is not None:
            lang_file = os.path.join(__cwd__, 'resources', 'language', str(curLang), 'strings.po')
            with open(lang_file) as fp:
                contents = fp.read().decode('utf-8').split('\n\n')
                for strings in contents:
                    if str(code) in strings:
                        subString = strings.split('msgstr ')[1]
                        subStringClean = re.sub('"', '', subString)
                        codeNew = subStringClean
                        break
                    else:
                        codeNew = __addon__.getLocalizedString(code)
        else:
            codeNew = __addon__.getLocalizedString(code)
    return codeNew


def dbg_log(source, text, level=3):
    if level == 0 and os.environ.get('DEBUG', 'no') == 'no':
        return
    xbmc.log('## CoreELEC Addon ## ' + source + ' ## ' + text, level)
    if level == 4:
        tracedata = traceback.format_exc()
        if tracedata != "None\n":
            xbmc.log(tracedata, level)

def notify(title, message, icon='icon'):
    try:
        dbg_log('oe::notify', 'enter_function', 0)
        msg = 'Notification("%s", "%s", 5000, "%s/%s.png")' % (
            title,
            message[0:64],
            __media__,
            icon,
            )
        xbmc.executebuiltin(msg)
        dbg_log('oe::notify', 'exit_function', 0)
    except Exception, e:
        dbg_log('oe::notify', 'ERROR: (' + repr(e) + ')')


def execute(command_line, get_result=0):
    try:
        dbg_log('oe::execute', 'enter_function', 0)
        dbg_log('oe::execute::command', command_line, 0)
        if get_result == 0:
            process = subprocess.Popen(command_line, shell=True, close_fds=True)
            process.wait()
        else:
            result = ''
            process = subprocess.Popen(command_line, shell=True, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            process.wait()
            for line in process.stdout.readlines():
                result = result + line
            return result
        dbg_log('oe::execute', 'exit_function', 0)
    except Exception, e:
        dbg_log('oe::execute', 'ERROR: (' + repr(e) + ')')


def enable_service(service):
    try:
        if os.path.exists('%s/services/%s' % (CONFIG_CACHE, service)):
            pass
        if os.path.exists('%s/services/%s.disabled' % (CONFIG_CACHE, service)):
            pass
        service_file = '%s/services/%s' % (CONFIG_CACHE, service)
    except Exception, e:
        dbg_log('oe::enable_service', 'ERROR: (' + repr(e) + ')')


def set_service_option(service, option, value):
    try:
        lines = []
        changed = False
        conf_file_name = '%s/services/%s.conf' % (CONFIG_CACHE, service)
        if os.path.isfile(conf_file_name):
            with open(conf_file_name, 'r') as conf_file:
                for line in conf_file:
                    if option in line:
                        line = '%s=%s' % (option, value)
                        changed = True
                    lines.append(line.strip())
        if changed == False:
            lines.append('%s=%s' % (option, value))
        with open(conf_file_name, 'w') as conf_file:
            conf_file.write('\n'.join(lines) + '\n')
    except Exception, e:
        dbg_log('oe::set_service_option', 'ERROR: (' + repr(e) + ')')


def get_service_option(service, option, default=None):
    try:
        lines = []
        conf_file_name = ''
        if os.path.exists('%s/services/%s.conf' % (CONFIG_CACHE, service)):
            conf_file_name = '%s/services/%s.conf' % (CONFIG_CACHE, service)
        if os.path.exists('%s/services/%s.disabled' % (CONFIG_CACHE, service)):
            conf_file_name = '%s/services/%s.disabled' % (CONFIG_CACHE, service)
        if os.path.exists(conf_file_name):
            with open(conf_file_name, 'r') as conf_file:
                for line in conf_file:
                    if option in line:
                        if '=' in line:
                            default = line.strip().split('=')[-1]
        return default
    except Exception, e:
        dbg_log('oe::get_service_option', 'ERROR: (' + repr(e) + ')')


def get_service_state(service):
    try:
        if os.path.exists('%s/services/%s.conf' % (CONFIG_CACHE, service)):
            return '1'
        else:
            return '0'
    except Exception, e:
        dbg_log('oe::get_service_state', 'ERROR: (' + repr(e) + ')')


def set_service(service, options, state):
    try:
        dbg_log('oe::set_service', 'enter_function', 0)
        dbg_log('oe::set_service::service', repr(service), 0)
        dbg_log('oe::set_service::options', repr(options), 0)
        dbg_log('oe::set_service::state', repr(state), 0)
        config = {}
        changed = False

        # Service Enabled

        if state == 1:

            # Is Service alwys enabled ?

            if get_service_state(service) == '1':
                cfn = '%s/services/%s.conf' % (CONFIG_CACHE, service)
                cfo = cfn
            else:
                cfn = '%s/services/%s.conf' % (CONFIG_CACHE, service)
                cfo = '%s/services/%s.disabled' % (CONFIG_CACHE, service)
            if os.path.exists(cfo) and not cfo == cfn:
                os.remove(cfo)
            with open(cfn, 'w') as cf:
                for option in options:
                    cf.write('%s=%s\n' % (option, options[option]))
        else:

        # Service Disabled

            cfo = '%s/services/%s.conf' % (CONFIG_CACHE, service)
            cfn = '%s/services/%s.disabled' % (CONFIG_CACHE, service)
            if os.path.exists(cfo):
                os.rename(cfo, cfn)
        if not __oe__.is_service:
            if service in defaults._services:
                for svc in defaults._services[service]:
                    execute('systemctl restart %s' % svc)
        dbg_log('oe::set_service', 'exit_function', 0)
    except Exception, e:
        dbg_log('oe::set_service', 'ERROR: (' + repr(e) + ')')


def load_file(filename):
    try:
        if os.path.isfile(filename):
            objFile = open(filename, 'r')
            content = objFile.read()
            objFile.close()
        else:
            content = ''
        return content.strip()
    except Exception, e:
        dbg_log('oe::load_file(' + filename + ')', 'ERROR: (' + repr(e) + ')')

def get_dtname():
    try:
        dtname = 'unknown'
        if os.path.isfile("/proc/device-tree/le-dt-id"):
            dtname = load_file("/proc/device-tree/le-dt-id")
        if os.path.isfile("/proc/device-tree/coreelec-dt-id"):
            dtname = load_file("/proc/device-tree/coreelec-dt-id")

        return dtname.rstrip('\x00\n')
    except Exception, e:
        dbg_log('oe::get_dtname', 'ERROR: (' + repr(e) + ')')

def get_config_ini(var, def_no_value=""):
    found = def_no_value
    if os.path.isfile(configini):
      f = open(configini)
      fl = f.readlines()
      f.close()
      for i, line in enumerate(fl):
        regex = r"^[^#]*\b%s=([^#]*)#*" % (var)
        match = re.search(regex, line)
        if match:
          found = match.group(1).strip()
          regex = r"^[\'\"].*[\'\"]$"
          if re.search(regex, found):
            found = found[1:-1]
    return found

def set_config_ini(var, val="\'\'"):
    mlist = []
    if os.path.isfile(configini):
      f = open(configini)
      fl = f.readlines()
      f.close()
    else:
      fl = []

    for i, line in enumerate(fl):
      regex = r"\b%s=" % (var)
      match = re.search(regex, line)
      if match:
        mlist.append(i)

    matches = len(mlist)

    if matches:
      for i, m in enumerate(mlist):
        if matches == (i + 1):
          last = 1
        else:
          last = 0
        if not last:
          line = re.sub("^(.*)(?=%s)" % regex,"", fl[m])
          fl[m] = "# %s" % (line)
        else:
          fl[m] = "%s=%s\n" % (var, val)

    if not matches:
      fl.append("\n%s=%s\n" % (var, val))

    ret = subprocess.call("mount -o remount,rw /flash", shell=True)
    f = open(configini,'w')
    f.writelines(fl)
    f.close()
    ret = subprocess.call("mount -o remount,ro /flash", shell=True)

def url_quote(var):
    return urllib2.quote(var, safe="")

def load_url(url):
    try:
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        content = response.read()
        return content.strip()
    except Exception, e:
        dbg_log('oe::load_url(' + url + ')', 'ERROR: (' + repr(e) + ')')


def download_file(source, destination, silent=False):
    try:
        local_file = open(destination, 'wb')

        response = urllib2.urlopen(urllib2.quote(source, safe=':/'))

        progress = ProgressDialog()
        if not silent:
            progress.open()

        progress.setSource(source)
        progress.setSize(int(response.info().getheader('Content-Length').strip()))

        last_percent = 0

        while not (xbmc.abortRequested or progress.iscanceled()):
            part = response.read(32768)

            progress.sample(part)

            if not silent:
                progress.update(part)
            else:
                if progress.getPercent() - last_percent > 5 or not part:
                    dbg_log('oe::download_file(%s)' % destination, '%d%% with %d KB/s' % (progress.getPercent(), progress.getSpeed()))
                    last_percent = progress.getPercent()

            if part:
                local_file.write(part)
            else:
                break

        progress.close()
        local_file.close()
        response.close()

        if progress.iscanceled() or xbmc.abortRequested:
            os.remove(destination)
            return None

        return destination

    except Exception, e:
        dbg_log('oe::download_file(' + source + ', ' + destination + ')', 'ERROR: (' + repr(e) + ')')


def copy_file(source, destination, silent=False):
    try:
        dbg_log('oe::copy_file', 'SOURCE: %s, DEST: %s' % (source, destination))

        source_file = open(source, 'rb')
        destination_file = open(destination, 'wb')

        progress = ProgressDialog()
        if not silent:
            progress.open()

        progress.setSource(source)
        progress.setSize(os.path.getsize(source))

        last_percent = 0

        while not (xbmc.abortRequested or progress.iscanceled()):
            part = source_file.read(32768)

            progress.sample(part)

            if not silent:
                progress.update(part)
            else:
                if progress.getPercent() - last_percent > 5 or not part:
                    dbg_log('oe::copy_file(%s)' % destination, '%d%% with %d KB/s' % (progress.getPercent(), progress.getSpeed()))
                    last_percent = progress.getPercent()

            if part:
                destination_file.write(part)
            else:
                break

        progress.close()
        source_file.close()
        destination_file.close()

        if progress.iscanceled() or xbmc.abortRequested:
            os.remove(destination)
            return None

        return destination

    except Exception as e:
        dbg_log('oe::copy_file(' + source + ', ' + destination + ')', 'ERROR: (' + repr(e) + ')')


def is_busy():
    global __busy__
    return __busy__ > 0


def set_busy(state):
    global __busy__, __oe__, input_request, is_service
    try:
        if not is_service:
            if state == 1:
                __busy__ = __busy__ + 1
            else:
                __busy__ = __busy__ - 1
            dbg_log('oe::set_busy', '__busy__ = ' + unicode(__busy__), 0)
    except Exception, e:
        dbg_log('oe::set_busy', 'ERROR: (' + repr(e) + ')', 4)


def start_service():
    global dictModules, __oe__
    try:
        __oe__.is_service = True
        for strModule in sorted(dictModules, key=lambda x: dictModules[x].menu.keys()):
            module = dictModules[strModule]
            if hasattr(module, 'start_service') and module.ENABLED:
                module.start_service()
        __oe__.is_service = False
    except Exception, e:
        dbg_log('oe::start_service', 'ERROR: (' + repr(e) + ')')


def stop_service():
    global dictModules
    try:
        for strModule in dictModules:
            module = dictModules[strModule]
            if hasattr(module, 'stop_service') and module.ENABLED:
                module.stop_service()
        xbmc.log('## CoreELEC Addon ## STOP SERVICE DONE !')
    except Exception, e:
        dbg_log('oe::stop_service', 'ERROR: (' + repr(e) + ')')


def openWizard():
    global winOeMain, __cwd__, __oe__
    try:
        winOeMain = oeWindows.wizard('service-CoreELEC-Settings-wizard.xml', __cwd__, 'Default', oeMain=__oe__)
        winOeMain.doModal()
        winOeMain = oeWindows.mainWindow('service-CoreELEC-Settings-mainWindow.xml', __cwd__, 'Default', oeMain=__oe__)  # None
    except Exception, e:
        dbg_log('oe::openWizard', 'ERROR: (' + repr(e) + ')')

def openReleaseNotes():
    global winOeMain, __cwd__, __oe__
    try:
        RNOTES = load_file('/etc/release-notes')
        RNOTES_TITLE = 'Release Notes: CoreELEC %s' % VERSION

        #TODO: fix so this can be done in a way that doesn't leave blank line
        regex = '\[TITLE\](.*?)\[\/TITLE\]'
        match = re.search(regex, RNOTES, re.IGNORECASE)
        if match:
          RNOTES_TITLE = match.group(1)
          RNOTES = re.sub(regex, "", RNOTES)

        CLdialog = xbmcgui.Dialog()
        CLdialog.textviewer(RNOTES_TITLE, RNOTES, 1)
    except Exception, e:
        dbg_log('oe::openChangeLog', 'ERROR: (' + repr(e) + ')')


def openConfigurationWindow():
    global winOeMain, __cwd__, __oe__, dictModules
    try:
        PINmatch = False
        PINnext = 1000
        PINenable = read_setting('system', 'pinlock_enable')
        if PINenable == "0" or PINenable == None:
            PINmatch = True
        if PINenable == "1":
            PINfail = read_setting('system', 'pinlock_timeFail')
            if PINfail:
                nowTime = time.time()
                PINnext = (nowTime - float(PINfail))
            if PINnext >= 300:
                PINtry = 4
                while PINmatch == False:
                    if PINtry > 0:
                        PINlock = xbmcDialog.input(_(32233), type=xbmcgui.INPUT_NUMERIC)
                        if PINlock == '':
                            break
                        else:
                            storedPIN = read_setting('system', 'pinlock_pin')
                            PINmatch = verify_password(storedPIN, PINlock)
                            if PINmatch == False:
                                PINtry -= 1
                                if PINtry > 0:
                                    xbmcDialog.ok(_(32234), str(PINtry) + _(32235))
                    else:
                        timeFail = time.time()
                        write_setting('system', 'pinlock_timeFail', str(timeFail))
                        xbmcDialog.ok(_(32234), _(32236))
                        break
            else:
                timeLeft = "{0:.2f}".format((300 - PINnext)/60)
                xbmcDialog.ok(_(32237), timeLeft + _(32238))
        if PINmatch == True:
            winOeMain = oeWindows.mainWindow('service-CoreELEC-Settings-mainWindow.xml', __cwd__, 'Default', oeMain=__oe__)
            winOeMain.doModal()
            for strModule in dictModules:
                dictModules[strModule].exit()
            winOeMain = None
            del winOeMain
        else:
            pass

    except Exception, e:
        dbg_log('oe::openConfigurationWindow', 'ERROR: (' + repr(e) + ')')

def standby_devices():
    global dictModules
    try:
        if 'bluetooth' in dictModules:
            dictModules['bluetooth'].standby_devices()
    except Exception, e:
        dbg_log('oe::standby_devices', 'ERROR: (' + repr(e) + ')')

def load_config():
    try:
        global conf_lock
        while conf_lock:
            time.sleep(0.2)
        conf_lock = True
        if os.path.exists(configFile):
            config_file = open(configFile, 'r')
            config_text = config_file.read()
            config_file.close()
        else:
            config_text = ''
        if config_text == '':
            xml_conf = minidom.Document()
            xml_main = xml_conf.createElement('coreelec')
            xml_conf.appendChild(xml_main)
            xml_sub = xml_conf.createElement('addon_config')
            xml_main.appendChild(xml_sub)
            xml_sub = xml_conf.createElement('settings')
            xml_main.appendChild(xml_sub)
            config_text = xml_conf.toprettyxml()
        else:
            xml_conf = minidom.parseString(config_text)
        conf_lock = False
        return xml_conf
    except Exception, e:
        dbg_log('oe::load_config', 'ERROR: (' + repr(e) + ')')


def save_config(xml_conf):
    try:
        global configFile, conf_lock
        while conf_lock:
            time.sleep(0.2)
        conf_lock = True
        config_file = open(configFile, 'w')
        config_file.write(xml_conf.toprettyxml())
        config_file.close()
        conf_lock = False
    except Exception, e:
        dbg_log('oe::save_config', 'ERROR: (' + repr(e) + ')')


def read_module(module):
    try:
        xml_conf = load_config()
        xml_settings = xml_conf.getElementsByTagName('settings')
        for xml_setting in xml_settings:
            for xml_modul in xml_setting.getElementsByTagName(module):
                return xml_modul
    except Exception, e:
        dbg_log('oe::read_module', 'ERROR: (' + repr(e) + ')')


def read_node(node_name):
    try:
        xml_conf = load_config()
        xml_node = xml_conf.getElementsByTagName(node_name)
        value = {}
        for xml_main_node in xml_node:
            value[xml_main_node.nodeName] = {}
            for xml_sub_node in xml_main_node.childNodes:
                if len(xml_sub_node.childNodes) == 0:
                    continue
                value[xml_main_node.nodeName][xml_sub_node.nodeName] = {}
                for xml_value in xml_sub_node.childNodes:
                    if hasattr(xml_value.firstChild, 'nodeValue'):
                        value[xml_main_node.nodeName][xml_sub_node.nodeName][xml_value.nodeName] = xml_value.firstChild.nodeValue
                    else:
                        value[xml_main_node.nodeName][xml_sub_node.nodeName][xml_value.nodeName] = ''
        return value
    except Exception, e:
        dbg_log('oe::read_node', 'ERROR: (' + repr(e) + ')')


def remove_node(node_name):
    try:
        xml_conf = load_config()
        xml_node = xml_conf.getElementsByTagName(node_name)
        for xml_main_node in xml_node:
            xml_main_node.parentNode.removeChild(xml_main_node)
        save_config(xml_conf)
    except Exception, e:
        dbg_log('oe::remove_node', 'ERROR: (' + repr(e) + ')')


def read_setting(module, setting, default=None):
    try:
        xml_conf = load_config()
        xml_settings = xml_conf.getElementsByTagName('settings')
        value = default
        for xml_setting in xml_settings:
            for xml_modul in xml_setting.getElementsByTagName(module):
                for xml_modul_setting in xml_modul.getElementsByTagName(setting):
                    if hasattr(xml_modul_setting.firstChild, 'nodeValue'):
                        value = xml_modul_setting.firstChild.nodeValue
        return value
    except Exception, e:
        dbg_log('oe::read_setting', 'ERROR: (' + repr(e) + ')')


def write_setting(module, setting, value, main_node='settings'):
    try:
        xml_conf = load_config()
        xml_settings = xml_conf.getElementsByTagName(main_node)
        if len(xml_settings) == 0:
            for xml_main in xml_conf.getElementsByTagName('coreelec'):
                xml_sub = xml_conf.createElement(main_node)
                xml_main.appendChild(xml_sub)
                xml_settings = xml_conf.getElementsByTagName(main_node)
        module_found = 0
        setting_found = 0
        for xml_setting in xml_settings:
            for xml_modul in xml_setting.getElementsByTagName(module):
                module_found = 1
                for xml_modul_setting in xml_modul.getElementsByTagName(setting):
                    setting_found = 1
        if setting_found == 1:
            if hasattr(xml_modul_setting.firstChild, 'nodeValue'):
                xml_modul_setting.firstChild.nodeValue = value
            else:
                xml_value = xml_conf.createTextNode(value)
                xml_modul_setting.appendChild(xml_value)
        else:
            if module_found == 0:
                xml_modul = xml_conf.createElement(module)
                xml_setting.appendChild(xml_modul)
            xml_setting = xml_conf.createElement(setting)
            xml_modul.appendChild(xml_setting)
            xml_value = xml_conf.createTextNode(value)
            xml_setting.appendChild(xml_value)
        save_config(xml_conf)
    except Exception, e:
        dbg_log('oe::write_setting', 'ERROR: (' + repr(e) + ')')


def load_modules():

  # # load coreelec configuration modules

    try:
        global dictModules, __oe__, __cwd__, init_done
        for strModule in dictModules:
            dictModules[strModule] = None
        dict_names = {}
        dictModules = {}
        for file_name in sorted(os.listdir(__cwd__ + '/resources/lib/modules')):
            if not file_name.startswith('__') and (file_name.endswith('.py') or file_name.endswith('.pyo')):
                (name, ext) = file_name.split('.')
                dict_names[name] = None
        for module_name in dict_names:
            try:
                if not module_name in dictModules:
                    dictModules[module_name] = getattr(__import__(module_name), module_name)(__oe__)
                    if hasattr(defaults, module_name):
                        for key in getattr(defaults, module_name):
                            setattr(dictModules[module_name], key, getattr(defaults, module_name)[key])
            except Exception, e:
                dbg_log('oe::MAIN(loadingModules)(strModule)', 'ERROR: (' + repr(e) + ')')
    except Exception, e:
        dbg_log('oe::MAIN(loadingModules)', 'ERROR: (' + repr(e) + ')')


def timestamp():
    now = time.time()
    localtime = time.localtime(now)
    return time.strftime('%Y%m%d%H%M%S', localtime)


def split_dialog_text(text):
    ret = [''] * 3
    txt = re.findall('.{1,60}(?:\W|$)', text)
    for x in range(0, 2):
        if len(txt) > x:
            ret[x] = txt[x]
    return ret


def reboot_counter(seconds=10, title=' '):
    reboot_dlg = xbmcgui.DialogProgress()
    reboot_dlg.create('CoreELEC %s' % title, ' ', ' ', ' ')
    reboot_dlg.update(0)
    wait_time = seconds
    while seconds >= 0 and not reboot_dlg.iscanceled():
        progress = round(1.0 * seconds / wait_time * 100)
        reboot_dlg.update(int(progress), _(32329) % seconds)
        time.sleep(1)
        seconds = seconds - 1
    if not reboot_dlg.iscanceled():
        return 1
    else:
        return 0


def exit():
    global WinOeSelect, winOeMain, __addon__, __cwd__, __oe__, _, dbusSystemBus, dictModules
    dbusSystemBus.close()
    dbusSystemBus = None

    # del winOeMain

    del dbusSystemBus
    del dictModules
    del __addon__
    del __oe__
    del _


# fix for xml printout

def fixed_writexml(self, writer, indent='', addindent='', newl=''):
    writer.write(indent + '<' + self.tagName)
    attrs = self._get_attributes()
    a_names = attrs.keys()
    a_names.sort()
    for a_name in a_names:
        writer.write(' %s="' % a_name)
        minidom._write_data(writer, attrs[a_name].value)
        writer.write('"')
    if self.childNodes:
        if len(self.childNodes) == 1 and self.childNodes[0].nodeType == minidom.Node.TEXT_NODE:
            writer.write('>')
            self.childNodes[0].writexml(writer, '', '', '')
            writer.write('</%s>%s' % (self.tagName, newl))
            return
        writer.write('>%s' % newl)
        for node in self.childNodes:
            if node.nodeType is not minidom.Node.TEXT_NODE:
                node.writexml(writer, indent + addindent, addindent, newl)
        writer.write('%s</%s>%s' % (
            indent,
            self.tagName,
            newl,
            ))
    else:
        writer.write('/>%s' % newl)


def parse_os_release():
    os_release_fields = re.compile(r'(?!#)(?P<key>.+)=(?P<quote>[\'\"]?)(?P<value>.+)(?P=quote)$')
    os_release_unescape = re.compile(r'\\(?P<escaped>[\'\"\\])')
    try:
        with open('/etc/os-release') as f:
            info = {}
            for line in f:
                m = re.match(os_release_fields, line)
                if m is not None:
                    key = m.group('key')
                    value = re.sub(os_release_unescape, r'\g<escaped>', m.group('value'))
                    info[key] = value
            return info
    except OSError:
        return None


def get_os_release():
    distribution = version = architecture = build = project = device = builder_name = builder_version = ''
    os_release_info = parse_os_release()
    if os_release_info is not None:
        if 'NAME' in os_release_info:
            distribution = os_release_info['NAME']
        if 'VERSION_ID' in os_release_info:
            version = os_release_info['VERSION_ID']
        if 'VERSION' in os_release_info:
            version = os_release_info['VERSION']
        if 'COREELEC_ARCH' in os_release_info:
            architecture = os_release_info['COREELEC_ARCH']
        if 'COREELEC_BUILD' in os_release_info:
            build = os_release_info['COREELEC_BUILD']
        if 'COREELEC_PROJECT' in os_release_info:
            project = os_release_info['COREELEC_PROJECT']
        if 'COREELEC_DEVICE' in os_release_info:
            device = os_release_info['COREELEC_DEVICE']
        if 'BUILDER_NAME' in os_release_info:
            builder_name = os_release_info['BUILDER_NAME']
        if 'BUILDER_VERSION' in os_release_info:
            builder_version = os_release_info['BUILDER_VERSION']
        return (
            distribution,
            version,
            architecture,
            build,
            project,
            device,
            builder_name,
            builder_version
            )

def hash_password(password):
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

def verify_password(stored_password, provided_password):
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512',
                                  provided_password.encode('utf-8'),
                                  salt.encode('ascii'),
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password


minidom.Element.writexml = fixed_writexml

############################################################################################
# Base Environment
############################################################################################

os_release_data = get_os_release()
DISTRIBUTION = os_release_data[0]
VERSION = os_release_data[1]
ARCHITECTURE = os_release_data[2]
BUILD = os_release_data[3]
PROJECT = os_release_data[4]
DEVICE = os_release_data[5]
BUILDER_NAME = os_release_data[6]
BUILDER_VERSION = os_release_data[7]
DOWNLOAD_DIR = '/storage/downloads'
XBMC_USER_HOME = os.environ.get('XBMC_USER_HOME', '/storage/.kodi')
CONFIG_CACHE = os.environ.get('CONFIG_CACHE', '/storage/.cache')
USER_CONFIG = os.environ.get('USER_CONFIG', '/storage/.config')
TEMP = '%s/temp/' % XBMC_USER_HOME
winOeMain = oeWindows.mainWindow('service-CoreELEC-Settings-mainWindow.xml', __cwd__, 'Default', oeMain=__oe__)
if os.path.exists('/etc/machine-id'):
    SYSTEMID = load_file('/etc/machine-id')
else:
    SYSTEMID = os.environ.get('SYSTEMID', '')

if PROJECT == 'RPi':
  RPI_CPU_VER = execute('vcgencmd otp_dump 2>/dev/null | grep 30: | cut -c8', get_result=1).replace('\n','')
else:
  RPI_CPU_VER = ''

configini = '/flash/config.ini'
BOOT_STATUS = load_file('/storage/.config/boot.status')
BOOT_HINT = load_file('/storage/.config/boot.hint')

if os.path.getsize('/etc/release-notes') > 1:
  HAS_RNOTES = 1
else:
  HAS_RNOTES = 0

############################################################################################

try:
    configFile = '%s/userdata/addon_data/service.coreelec.settings/oe_settings.xml' % XBMC_USER_HOME
    if not os.path.exists('%s/userdata/addon_data/service.coreelec.settings' % XBMC_USER_HOME):
        if os.path.exists('%s/userdata/addon_data/service.libreelec.settings' % XBMC_USER_HOME):
            shutil.copytree(('%s/userdata/addon_data/service.libreelec.settings' % XBMC_USER_HOME),
                    ('%s/userdata/addon_data/service.coreelec.settings' % XBMC_USER_HOME))
            with open(configFile,'r+') as f:
                xml = f.read()
                xml = xml.replace("<libreelec>","<coreelec>")
                xml = xml.replace("</libreelec>","</coreelec>")
                f.seek(0)
                f.write(xml)
                f.truncate()
        else:
            os.makedirs('%s/userdata/addon_data/service.coreelec.settings' % XBMC_USER_HOME)
    if not os.path.exists('%s/services' % CONFIG_CACHE):
        os.makedirs('%s/services' % CONFIG_CACHE)
except:
    pass
