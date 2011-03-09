#!/usr/bin/env python
##############################################################################
#
# diffpy.Structure  by DANSE Diffraction group
#                   Simon J. L. Billinge
#                   (c) 2006 trustees of the Michigan State University.
#                   All rights reserved.
#
# File coded by:    Pavol Juhas
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################

"""anyeye    view structure file in atomeye
Usage: anyeye [options] strufile

anyeye understands more structure formats than atomeye.  It converts strufile
to a temporary XCFG file which is opened in atomeye.  Supported file formats:
    inputFormats

Options:
  -f, --formula   override chemical formula in strufile, formula defines
                  elements in the same order as in strufile, e.g, Na4Cl4
  -w, --watch     watch input file for changes
  -h, --help      display this message
  -V, --version   show script version
"""

__id__ = "$Id$"

import sys
import os, os.path
import re
import signal
from diffpy.Structure import StructureFormatError

def usage(style = None):
    """show usage info, for style=="brief" show only first 2 lines"""
    import os.path
    myname = os.path.basename(sys.argv[0])
    msg = __doc__.replace("anyeye", myname)
    if style == 'brief':
        msg = msg.split("\n")[1] + "\n" + \
                "Try `%s --help' for more information." % myname
    else:
        from diffpy.Structure.Parsers import inputFormats
        fmts = [ f for f in inputFormats() if f != 'auto' ]
        msg = msg.replace("inputFormats", " ".join(fmts))
    print msg
    return

def version():
    from diffpy.Structure import __version__
    print __id__
    print "diffpy.Structure", __version__

def loadStructureFile(filename, format="auto"):
    """Load structure from specified file.

    Return a tuple of (Structure, fileformat).
    """
    from diffpy.Structure import Structure
    stru = Structure()
    p = stru.read(filename, format)
    fileformat = p.format
    return (stru, fileformat)

def convertStructureFile(pd):
    # make temporary directory on the first pass
    if 'tmpdir' not in pd:
        from tempfile import mkdtemp
        pd['tmpdir'] = mkdtemp()
    strufile = pd['strufile']
    tmpfile = os.path.join(pd['tmpdir'], os.path.basename(strufile))
    format  = pd.get('format', 'auto')
    stru = None
    if format == 'auto':
        stru, format = loadStructureFile(strufile, format)
        pd['format'] = format
    # format is detected here
    if format in ('pdb', 'xcfg') and 'formula' not in pd:
        import shutil
        shutil.copyfile(strufile, tmpfile+'.tmp')
        os.rename(tmpfile+'.tmp', tmpfile)
    else:
        if stru is None:
            stru, ignore = loadStructureFile(strufile, format)
        if 'formula' in pd:
            formula = pd['formula']
            if len(formula) != len(stru):
                raise RuntimeError, \
                        "Formula has %i atoms while structure %i" % (
                                len(formula), len(stru) )
            for i in range(len(stru)):
                stru[i].element = formula[i]
        elif format == "rawxyz":
            for a in stru:
                if a.element == "": a.element = "C"
        stru.write(tmpfile+'.tmp', 'xcfg')
        os.rename(tmpfile+'.tmp', tmpfile)
    pd['tmpfile'] = tmpfile

def watchStructureFile(pd):
    from time import sleep
    strufile = pd['strufile']
    tmpfile  = pd['tmpfile']
    format  = pd['format']
    while pd['watch']:
        if os.path.getmtime(tmpfile) < os.path.getmtime(strufile):
            convertStructureFile(pd)
        sleep(1)

def cleanUp(pd):
    if 'tmpfile' in pd:
        os.remove(pd['tmpfile'])
        del pd['tmpfile']
    if 'tmpdir' in pd:
        os.rmdir(pd['tmpdir'])
        del pd['tmpdir']

def parseFormula(formula):
    """parse chemical formula and return a list of elements"""
    # remove all blanks
    formula = re.sub('\s', '', formula)
    if not re.match('^[A-Z]', formula):
        raise RuntimeError, "InvalidFormula '%s'" % formula
    elcnt = re.split('([A-Z][a-z]?)', formula)[1:]
    ellst = []
    try:
        for i in range(0, len(elcnt), 2):
            el = elcnt[i]
            cnt = elcnt[i+1]
            cnt = (cnt == "") and 1 or int(cnt)
            ellst.extend(cnt*[el])
    except ValueError:
        raise RuntimeError, \
            "Invalid formula, %r is not valid count" % elcnt[i+1]
    return ellst

def die(exit_status=0, pd={}):
    cleanUp(pd)
    sys.exit(exit_status)

# parameter dictionary
pd = {}

def signalHandler(signum, stackframe):
    # revert to default handler
    signal.signal(signum, signal.SIG_DFL)
    if signum == signal.SIGCLD:
        pid, exit_status = os.wait()
        exit_status = (exit_status >> 8) + (exit_status & 0x00ff)
        die(exit_status, pd)
    else:
        die(1, pd)

def main():
    import getopt
    # default parameters
    pd['watch'] = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:whV", \
                ["formula=", "watch", "help", "version"])
    except getopt.GetoptError, errmsg:
        print >> sys.stderr, errmsg
        die(2)
    # process options
    for o, a in opts:
        if o in ("-f", "--formula"):
            try:
                pd['formula'] = parseFormula(a)
            except RuntimeError, msg:
                print >> sys.stderr, msg
                die(2)
        elif o in ("-w", "--watch"):
            pd['watch'] = True
        elif o in ("-h", "--help"):
            usage()
            die()
        elif o in ("-V", "--version"):
            version()
            die()
    if len(args) < 1:
        usage('brief')
        die()
    elif len(args) > 1:
        print >> sys.stderr, "too many structure files"
        die(2)
    pd['strufile'] = args[0]
    # trap the following signals
    signal.signal(signal.SIGHUP, signalHandler)
    signal.signal(signal.SIGQUIT, signalHandler)
    signal.signal(signal.SIGSEGV, signalHandler)
    signal.signal(signal.SIGTERM, signalHandler)
    signal.signal(signal.SIGINT, signalHandler)
    # try to run the thing:
    try:
        convertStructureFile(pd)
        # load strufile in atomeye
        if pd['watch']:
            signal.signal(signal.SIGCLD, signalHandler)
            os.spawnlp(os.P_NOWAIT, 'atomeye', 'atomeye', pd['tmpfile'])
            watchStructureFile(pd)
        else:
            status = os.spawnlp(os.P_WAIT, 'atomeye', 'atomeye', pd['tmpfile'])
            die(status, pd)
    except IOError, (errno, errmsg):
        print >> sys.stderr, "%s: %s" % (args[0], errmsg)
        die(1, pd)
    except StructureFormatError, errmsg:
        print >> sys.stderr, "%s: %s" % (args[0], errmsg)
        die(1, pd)

if __name__ == "__main__":
    main()
