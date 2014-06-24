#! /usr/bin/env python
#  -*- coding: utf-8 -*-

'''
Copyright 2014 Stathis Aliprantis

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License version 3 as published
by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with This program. If not, see http://www.gnu.org/licenses/.
'''

'''
This program is intended to restore text which was accidently saved in a wrong
charset.
It calls iconv to make the conversion.
'''


import pygtk
pygtk.require('2.0')
import gtk 
import sys
import subprocess
import fileinput
import os


# ensure iconv is installed
try:
    subprocess.check_call(["whatis", "iconv"], stdout=open('/dev/null'))
except subprocess.CalledProcessError:
    # show error and exit
    print("Could not find iconv. Please install iconv")
    errorMsg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE,
                  message_format="Could not find iconv. Please install iconv")
    errorMsg.set_modal(True)
    errorMsg.set_title("Fatal Error")
    def callback(dialog, response_id): sys.exit(1)
    errorMsg.connect("response", callback)
    errorMsg.show()
    


class CharSet:
    def __init__(self, name, lang, intermediate, alterns=[]):
        self.name = name # name of the charset
        self.lang = lang # language that supports
        self.intermediate = intermediate # intermediate charset to convert to
        self.alterns = alterns # alternative charsets for the same language
        
        
class ConversionResult:
    def __init__(self, text, errmsg):
        self.text = text # restored text
        self.errmsg = errmsg # error message if conversion failed


# Supported charsets
#   (not all are tested since I don't know all these languages...)
CHARSETS = [
    CharSet("ISO8859-1", "Western Europe", "ISO8859-1", ["WINDOWS-1252"]),
    CharSet("ISO8859-2", "Western and Central Europe", "ISO8859-1"),
    CharSet("ISO8859-3", "Western Europe and South European", "ISO8859-1"),
    CharSet("ISO8859-4", "Western Europe and Baltic countries", "ISO8859-1"),
    CharSet("ISO8859-5", "Cyrillic", "ISO8859-1", ["WINDOWS-1251"]),
    CharSet("ISO8859-6", "Arabic", "ISO8859-1", ["WINDOWS-1256"]),
    CharSet("ISO8859-7", "Greek", "ISO8859-1", ["WINDOWS-1253"]),
    CharSet("ISO8859-8", "Hebrew", "ISO8859-1", ["WINDOWS-1255"]),
    CharSet("ISO8859-9", "Turkish", "ISO8859-1", ["WINDOWS-1254"]),
    CharSet("ISO8859-10", "Nordic", "ISO8859-1"),
    CharSet("ISO8859-11", "Thai", "ISO8859-1", ["WINDOWS-874"]),
    CharSet("ISO8859-13", "Baltic + Polish", "ISO8859-1", ["WINDOWS-1257"]),
    CharSet("ISO8859-14", "Celtic", "ISO8859-1"),
    CharSet("ISO8859-15", "ISO 8859-1 plus euro sing and others", "ISO8859-1"),
    CharSet("ISO8859-16", "Central, Eastern and Southern European", "ISO8859-1"),
    CharSet("WINDOWS-874", "Thai", "ISO8859-1", ["ISO8859-11"]),
    CharSet("WINDOWS-1250", "Central European", "WINDOWS-1252"),
    CharSet("WINDOWS-1251", "Cyrillic", "WINDOWS-1252", ["ISO8859-5"]),
    CharSet("WINDOWS-1252", "Western", "WINDOWS-1252", ["ISO8859-1"]),
    CharSet("WINDOWS-1253", "Greek", "WINDOWS-1252", ["ISO8859-7"]),
    CharSet("WINDOWS-1254", "Turkish", "WINDOWS-1252", ["ISO8859-9"]),
    CharSet("WINDOWS-1255", "Hebrew", "WINDOWS-1252", ["ISO8859-8"]),
    CharSet("WINDOWS-1256", "Arabic", "WINDOWS-1252", ["ISO8859-6"]),
    CharSet("WINDOWS-1257", "Baltic", "WINDOWS-1252", ["ISO8859-13"]),
    CharSet("WINDOWS-1258", "Vietnamese", "WINDOWS-1252")
]
DEFAULT_CHARSET = 19   # WINDOWS-1253


# tries to convert the given text to the given charset
# returns a ConversionResult
def convert(text, charset):
    text = text.replace("'", "'\\''") # escape the text
    err = os.pipe()
    restored = subprocess.check_output(["sh", "-c", 
        "echo "
        + "'" + text + "'"
        + " |iconv -f UTF-8 -t " + charset.intermediate
        + " |iconv -f " + charset.name + " -t UTF-8"],
        stderr=err[1])[0:-1]
    os.close(err[1])
    errF = os.fdopen(err[0])
    errmsg = errF.readline()
    errF.close()
    return ConversionResult(restored, errmsg)


# handles errors during conversion
def show_conversion_error(errormsg, charset):
    msg = ("Could not convert to specified charset.\n"
          + "  Reason: " + errormsg + "\n"
          + "Alternative " + charset.lang + " charsets:\n"
          + reduce(lambda x, y: x+y, map(lambda a: a+"  ", charset.alterns), ""))
    print(msg)
    errorDialog = gtk.MessageDialog(type=gtk.MESSAGE_ERROR,
                 buttons=gtk.BUTTONS_CLOSE,
                 message_format=msg)
    errorDialog.set_modal(True)
    errorDialog.set_title("Conversion Error")
    def callback(dialog, response_id): dialog.destroy()
    errorDialog.connect("response", callback)
    errorDialog.show()


# Main Window
class CharRest:

    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()
        
    def canClick(self, widget, data=None):
        gtk.main_quit()

    # on original text changed in the textfield
    def textToRestoreChanged(self, editable):
        charset = CHARSETS[self.encodings.get_active()]
        toBeRestored = self.toBeRestored.get_text()
        result = convert(toBeRestored, charset)
        self.restored.set_text(result.text)
        if  result.errmsg != "":
            show_conversion_error(result.errmsg, charset)
    
    # on paste button clicked
    def onClickPaste(self, widget, data=None):
        self.toBeRestored.set_text(gtk.Clipboard().wait_for_text())
    
    # on copy button clicked
    def onClickCopy(self, widget, data=None):
        gtk.Clipboard().set_text(self.restored.get_text())

    def __init__(self):
        # create the components
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.verBox = gtk.VBox(False, 4)
        self.toBeRestored = gtk.Entry()
        self.restored     = gtk.Entry()
        self.encodings = gtk.combo_box_new_text()
        self.buttonBox = gtk.HButtonBox()
        self.close     = gtk.Button("Close")
        self.paste = gtk.Button("Paste")
        self.copy  = gtk.Button("Copy")
        
        # set tooltips
        self.window.set_title("CharRest")
        self.toBeRestored.set_tooltip_text("Corrupted text here")
        self.restored.set_tooltip_text("Restored text")
        self.paste.set_tooltip_text("Paste from clipboard")
        self.copy.set_tooltip_text("Copy to clipboard")
        self.close.set_tooltip_text("Close")      

        # pack
        self.buttonBox.pack_end(self.paste)
        self.buttonBox.pack_end(self.copy)
        self.buttonBox.pack_end(self.close)
        
        self.verBox.pack_start(self.toBeRestored)
        self.verBox.pack_start(self.restored)
        self.verBox.pack_start(self.encodings)
        self.verBox.pack_start(self.buttonBox)
        
        self.window.add(self.verBox)
        self.buttonBox.set_layout(gtk.BUTTONBOX_START)
        
        self.restored.set_editable(False)
        # add charsets
        for charset in CHARSETS:
            self.encodings.append_text(charset.name + "  -  " + charset.lang)
        self.encodings.set_active(DEFAULT_CHARSET)
        
        # connect signals
        self.window.connect("delete_event", self.delete_event)
        self.paste.connect("clicked", self.onClickPaste)
        self.copy.connect("clicked", self.onClickCopy)
        self.close.connect("clicked", self.canClick)
        self.toBeRestored.connect("changed", self.textToRestoreChanged)
        
        # show everything
        self.toBeRestored.show()
        self.restored.show()
        self.encodings.show()
        self.paste.show()
        self.copy.show()
        self.close.show()
        self.buttonBox.show()
        self.verBox.show()
        self.window.show()

    def main(self):
        gtk.main()


if __name__ == "__main__":
    mainWindow = CharRest()
    mainWindow.main()
