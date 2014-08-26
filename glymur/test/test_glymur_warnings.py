"""
Test suite for warnings issued by glymur.
"""

# unittest doesn't work well with R0904.
# pylint: disable=R0904

import os
import re
import struct
import sys
import tempfile
import unittest
import warnings

from glymur import Jp2k
import glymur

from .fixtures import opj_data_file, OPJ_DATA_ROOT

@unittest.skipIf(sys.hexversion < 0x03030000,
                 "assertWarn methods introduced in 3.x")
@unittest.skipIf(OPJ_DATA_ROOT is None,
                 "OPJ_DATA_ROOT environment variable not set")
class TestWarnings(unittest.TestCase):
    """Test suite for warnings issued by glymur."""

    def test_exceeded_box_length(self):
        """
        should warn if reading past end of a box

        Verify that a warning is issued if we read past the end of a box
        This file has a palette (pclr) box whose length is impossibly
        short.
        """
        infile = os.path.join(OPJ_DATA_ROOT,
                              'input/nonregression/mem-b2ace68c-1381.jp2')
        regex = re.compile(r'''Encountered\san\sunrecoverable\sValueError\s
                               while\sparsing\sa\spclr\sbox\sat\sbyte\soffset\s
                               \d+\.\s+The\soriginal\serror\smessage\swas\s
                               "total\ssize\sof\snew\sarray\smust\sbe\s
                               unchanged"''',
                           re.VERBOSE)
        with self.assertWarnsRegex(UserWarning, regex):
            Jp2k(infile)

    def test_NR_DEC_issue188_beach_64bitsbox_jp2_41_decode(self):
        """
        Has an 'XML ' box instead of 'xml '.  Yes that is pedantic, but it
        really does deserve a warning.
        """
        relpath = 'input/nonregression/issue188_beach_64bitsbox.jp2'
        jfile = opj_data_file(relpath)
        regex = re.compile(r"""Unrecognized\sbox\s\(b'XML\s'\)\sencountered.""",
                           re.VERBOSE)
        with self.assertWarnsRegex(UserWarning, regex):
            Jp2k(jfile)


    def test_NR_gdal_fuzzer_unchecked_numresolutions_dump(self):
        """
        Has an invalid number of resolutions.
        """
        lst = ['input', 'nonregression',
               'gdal_fuzzer_unchecked_numresolutions.jp2']
        jfile = opj_data_file('/'.join(lst))
        regex = re.compile(r"""Invalid\snumber\sof\sresolutions\s
                               \(\d+\)\.""",
                           re.VERBOSE)
        with self.assertWarnsRegex(UserWarning, regex):
            Jp2k(jfile)

    @unittest.skipIf(re.match("1.5|2.0.0", glymur.version.openjpeg_version),
                     "Test not passing on 1.5.x, not introduced until 2.x")
    def test_NR_gdal_fuzzer_check_number_of_tiles(self):
        """
        Has an impossible tiling setup.
        """
        lst = ['input', 'nonregression',
               'gdal_fuzzer_check_number_of_tiles.jp2']
        jfile = opj_data_file('/'.join(lst))
        regex = re.compile(r"""Invalid\snumber\sof\stiles\s
                               \(\d+\)\.""",
                           re.VERBOSE)
        with self.assertWarnsRegex(UserWarning, regex):
            Jp2k(jfile)

    def test_NR_gdal_fuzzer_check_comp_dx_dy_jp2_dump(self):
        """
        Invalid subsampling value.
        """
        lst = ['input', 'nonregression', 'gdal_fuzzer_check_comp_dx_dy.jp2']
        jfile = opj_data_file('/'.join(lst))
        regex = re.compile(r"""Invalid\ssubsampling\svalue\sfor\scomponent\s
                               \d+:\s+
                               dx=\d+,\s*dy=\d+""",
                           re.VERBOSE)
        with self.assertWarnsRegex(UserWarning, regex):
            Jp2k(jfile)

    def test_NR_gdal_fuzzer_assert_in_opj_j2k_read_SQcd_SQcc_patch_jp2(self):
        lst = ['input', 'nonregression',
               'gdal_fuzzer_assert_in_opj_j2k_read_SQcd_SQcc.patch.jp2']
        jfile = opj_data_file('/'.join(lst))
        regex = re.compile(r"""Invalid\scomponent\snumber\s\(\d+\),\s
                               number\sof\scomponents\sis\sonly\s\d+""",
                           re.VERBOSE)
        with self.assertWarnsRegex(UserWarning, regex):
            Jp2k(jfile)

    def test_NR_broken_jp2_dump(self):
        """
        The colr box has a ridiculously incorrect box length.
        """
        jfile = opj_data_file('input/nonregression/broken.jp2')
        regex = re.compile(r'''b'colr'\sbox\shas\sincorrect\sbox\slength\s
                               \(\d+\)''',
                           re.VERBOSE)
        with self.assertWarnsRegex(UserWarning, regex):
            jp2 = Jp2k(jfile)

    def test_NR_broken2_jp2_dump(self):
        """
        Invalid marker ID on codestream.
        """
        jfile = opj_data_file('input/nonregression/broken2.jp2')
        regex = re.compile(r'''Invalid\smarker\sid\sencountered\sat\sbyte\s
                               \d+\sin\scodestream:\s*"0x[a-fA-F0-9]{4}"''', 
                           re.VERBOSE)
        with self.assertWarnsRegex(UserWarning, regex):
            Jp2k(jfile)

    def test_NR_broken4_jp2_dump(self):
        """
        Has an invalid marker in the main header
        """
        jfile = opj_data_file('input/nonregression/broken4.jp2')
        regex = r'Invalid marker id encountered at byte \d+ in codestream'
        with self.assertWarnsRegex(UserWarning, regex):
            jp2 = Jp2k(jfile)

    @unittest.skipIf(sys.maxsize < 2**32, 'Do not run on 32-bit platforms')
    def test_NR_broken3_jp2_dump(self):
        """
        Has an impossibly large box length.

        The file in question here has a colr box with an erroneous box
        length of over 1GB.  Don't run it on 32-bit platforms.
        """
        jfile = opj_data_file('input/nonregression/broken3.jp2')
        regex = re.compile(r'''b'colr'\sbox\shas\sincorrect\sbox\slength\s
                               \(\d+\)''', re.VERBOSE)
        with self.assertWarnsRegex(UserWarning, regex):
            Jp2k(jfile)

    def test_bad_rsiz(self):
        """Should warn if RSIZ is bad.  Issue196"""
        filename = opj_data_file('input/nonregression/edf_c2_1002767.jp2')
        with self.assertWarnsRegex(UserWarning, 'Invalid profile'):
            Jp2k(filename)

    def test_bad_wavelet_transform(self):
        """Should warn if wavelet transform is bad.  Issue195"""
        filename = opj_data_file('input/nonregression/edf_c2_10025.jp2')
        with self.assertWarnsRegex(UserWarning, 'Invalid wavelet transform'):
            Jp2k(filename)

    def test_invalid_progression_order(self):
        """Should still be able to parse even if prog order is invalid."""
        jfile = opj_data_file('input/nonregression/2977.pdf.asan.67.2198.jp2')
        with self.assertWarnsRegex(UserWarning, 'Invalid progression order'):
            Jp2k(jfile)

    def test_tile_height_is_zero(self):
        """Zero tile height should not cause an exception."""
        filename = opj_data_file('input/nonregression/2539.pdf.SIGFPE.706.1712.jp2')
        with self.assertWarnsRegex(UserWarning, 'Invalid tile dimensions'):
            Jp2k(filename)

    @unittest.skipIf(os.name == "nt", "Temporary file issue on window.")
    def test_unknown_marker_segment(self):
        """Should warn for an unknown marker."""
        # Let's inject a marker segment whose marker does not appear to
        # be valid.  We still parse the file, but warn about the offending
        # marker.
        filename = os.path.join(OPJ_DATA_ROOT, 'input/conformance/p0_01.j2k')
        with tempfile.NamedTemporaryFile(suffix='.j2k') as tfile:
            with open(filename, 'rb') as ifile:
                # Everything up until the first QCD marker.
                read_buffer = ifile.read(45)
                tfile.write(read_buffer)

                # Write the new marker segment, 0xff79 = 65401
                read_buffer = struct.pack('>HHB', int(65401), int(3), int(0))
                tfile.write(read_buffer)

                # Get the rest of the input file.
                read_buffer = ifile.read()
                tfile.write(read_buffer)
                tfile.flush()
 
                with self.assertWarnsRegex(UserWarning, 'Unrecognized marker'):
                    codestream = Jp2k(tfile.name).get_codestream()


if __name__ == "__main__":
    unittest.main()
