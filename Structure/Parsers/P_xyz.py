"""Parser for XYZ file format

first line gives number of atoms
second one has optional title
remaining lines contain element, x, y, z
"""

__id__ = "$Id$"

import sys
from Structure.structure import Structure, InvalidStructureFormat
from Structure.lattice import Lattice
from Structure.atom import Atom
from StructureParser import StructureParser

class Parser(StructureParser):
    """Parser --> StructureParser subclass for XYZ format"""

    def __init__(self):
        self.format = "xyz"
        return

    def parseLines(self, lines):
        """parse list of lines in XYZ format

        return Structure object or raise InvalidStructureFormat exception
        """
        linefields = [l.split() for l in lines]
        # prepare output structure
        stru = Structure()
        # find first valid record
        start = 0
        for field in linefields:
            if len(field) == 0 or field[0] == "#":
                start += 1
            else:
                break
        # first valid line gives number of atoms
        try:
            lfs = linefields[start]
            w1 = linefields[start][0]
            if len(lfs) == 1 and str(int(w1)) == w1:
                p_natoms = int(w1)
                stru.title = lines[start+1].strip()
                start += 2
            else:
                raise InvalidStructureFormat, ("%d: invalid XYZ format, " +
                        "missing number of atoms") % (start+1)
        except (IndexError, ValueError):
            exc_type, exc_value, exc_traceback = sys.exc_info()
            raise InvalidStructureFormat, ("%d: invalid XYZ format, " +
                    "missing number of atoms") % (start+1), exc_traceback
        # find the last valid record
        stop = len(lines)
        while stop > start and len(linefields[stop-1]) == 0:
            stop -= 1
        # get out for empty structure
        if p_natoms == 0 or start >= stop:
            return stru
        # here we have at least one valid record line
        nfields = len(linefields[start])
        if nfields != 4:
            raise InvalidStructureFormat, ("%d: invalid XYZ format, " +
                    "expected 4 columns") % (start+1)
        # now try to read all record lines
        try:
            p_nl = start
            for fields in linefields[start:] :
                p_nl += 1
                if fields == []:
                    continue
                elif len(fields) != nfields:
                    raise InvalidStructureFormat, ('%d: all lines must have ' +
                            'the same number of columns') % p_nl
                element = fields[0]
                element = element[0].upper() + element[1:].lower()
                xyz = [ float(f) for f in fields[1:4] ]
                stru.append(Atom(element, xyz=xyz))
        except ValueError:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            raise InvalidStructureFormat, \
                    "%d: invalid number format" % p_nl, exc_traceback
        # finally check if all the atoms have been read
        if p_natoms is not None and len(stru) != p_natoms:
            raise InvalidStructureFormat, \
                    "expected %d atoms, read %d" % (p_natoms, len(stru))
        return stru
    # End of parseLines

    def toLines(self, stru):
        """convert Structure stru to a list of lines in XYZ format"""
        lines = []
        lines.append( str(len(stru)) )
        lines.append( stru.title )
        for a in stru:
            rc = stru.cartesian(a)
            s = "%-3s %g %g %g" % (a.element, rc[0], rc[1], rc[2])
            lines.append(s)
        return lines
    # End of toLines

# End of Parser