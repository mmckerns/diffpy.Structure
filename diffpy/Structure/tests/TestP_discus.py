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
# See LICENSE_DANSE.txt for license information.
#
##############################################################################

"""Unit tests for diffpy.Structure.Parsers.P_discus module
"""

import unittest
import os
import re

from diffpy.Structure.tests.testutils import datafile
from diffpy.Structure import Structure, StructureFormatError


def assertListAlmostEqual(self, l1, l2, places=None):
    """wrapper for list comparison"""
    if places is None: places = self.places
    self.assertEqual(len(l1), len(l2))
    for i in range(len(l1)):
        self.assertAlmostEqual(l1[i], l2[i], places)


##############################################################################
class TestP_discus(unittest.TestCase):
    """test Parser for PDFFit file format"""

    assertListAlmostEqual = assertListAlmostEqual


    def setUp(self):
        self.stru = Structure()
        self.format = "discus"
        self.places = 8


    def test_read_discus_Ni(self):
        """check reading of Ni structure in discus format"""
        stru = self.stru
        stru.read(datafile('Ni-discus.stru'), self.format)
        f_title = 'structure Ni  FCC'
        self.assertEqual(f_title, stru.title)
        self.assertEqual('Fm-3m', stru.pdffit['spcgr'])
        # cell record
        abcABG = (3.52, 3.52, 3.52, 90.0, 90.0, 90.0)
        self.assertEqual(abcABG, stru.lattice.abcABG())
        # ncell
        self.assertEqual([1, 1, 1, 4], stru.pdffit['ncell'])
        self.assertEqual(4, len(stru))
        # first atom
        a0 = stru[0]
        self.assertEqual((0.0, 0.0, 0.0), tuple(a0.xyz))
        self.failUnless(not a0.anisotropy)
        Biso0 = 0.1
        self.assertAlmostEqual(Biso0, a0.Bisoequiv, self.places)
        return


    def test_except_other_formats(self):
        """check exceptions when reading files in other formats"""
        badfiles = [
                'LiCl-bad.cif',
                'PbTe.cif',
                'arginine.pdb',
                'ZnSb_RT_Q28X_VM_20_fxiso.rstr',
                'Ni-bad.stru',
                'Ni.stru',
                'BubbleRaftShort.xcfg',
                'bucky-bad1.xyz',
                'bucky-bad2.xyz',
                'bucky-plain-bad.xyz',
                'bucky-plain.xyz',
                'bucky-raw.xyz',
                'bucky.xyz',
                'hexagon-raw-bad.xyz',
                'hexagon-raw.xyz',
        ]
        for ft in badfiles:
            ff = datafile(ft)
            self.assertRaises(StructureFormatError,
                    self.stru.read, ff, format=self.format)
        return


    def test_ignored_lines(self):
        """check skipping of ignored lines in the header
        """
        r1 = 'ignored record 1\n'
        r2 = 'ignored record 2\n'
        ni_lines = open(datafile('Ni-discus.stru')).readlines()
        ni_lines.insert(2, r1)
        ni_lines.insert(4, r2)
        s_s1 = "".join(ni_lines)
        p = self.stru.readStr(s_s1, self.format)
        self.assertEqual([r1.rstrip(), r2.rstrip()], p.ignored_lines)
        ni_lines.append(r1)
        s_s2 = "".join(ni_lines)
        self.assertRaises(StructureFormatError, self.stru.readStr,
                s_s2, self.format)
        return


    def test_spdiameter_parsing(self):
        """check parsing of spdiameter record from a file.
        """
        stru = self.stru
        stru.read(datafile('Ni-discus.stru'), self.format)
        self.assertEqual(0, stru.pdffit['spdiameter'])
        snoshape = stru.writeStr(format=self.format)
        self.failUnless(not re.search('(?m)^shape', snoshape))
        # produce a string with non-zero spdiameter
        stru.pdffit['spdiameter'] = 13
        s13 = stru.writeStr(format=self.format)
        self.failUnless(re.search('(?m)^shape +sphere, ', s13))
        stru13 = Structure()
        stru13.readStr(s13)
        self.assertEqual(13, stru13.pdffit['spdiameter'])
        ni_lines = open(datafile('Ni.stru')).readlines()
        ni_lines.insert(3, 'shape invalid, 7\n')
        sbad = ''.join(ni_lines)
        self.assertRaises(StructureFormatError, self.stru.readStr,
                sbad, format=self.format)
        return


    def test_stepcut_parsing(self):
        """check parsing of stepcut record from a file.
        """
        stru = self.stru
        stru.read(datafile('Ni-discus.stru'), self.format)
        self.assertEqual(0, stru.pdffit['stepcut'])
        snoshape = stru.writeStr(format=self.format)
        self.failUnless(not re.search('(?m)^shape', snoshape))
        # produce a string with non-zero stepcut
        stru.pdffit['stepcut'] = 13
        s13 = stru.writeStr(format=self.format)
        self.failUnless(re.search('(?m)^shape +stepcut, ', s13))
        stru13 = Structure()
        stru13.readStr(s13)
        self.assertEqual(13, stru13.pdffit['stepcut'])
        ni_lines = open(datafile('Ni.stru')).readlines()
        ni_lines.insert(3, 'shape invalid, 7\n')
        sbad = ''.join(ni_lines)
        self.assertRaises(StructureFormatError, self.stru.readStr,
                sbad, format=self.format)
        return


# End of TestP_discus


if __name__ == '__main__':
    unittest.main()

# End of file
