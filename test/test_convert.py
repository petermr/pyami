import unittest
from pathlib import Path
# local
from py4ami.ami_convert import ConvType, Converters, Svg2PageConverter
from py4ami.pyamix import PyAMI
from test.resources import Resources


class TestConvert(unittest.TestCase):

    def test_list_enum_values(self):
        assert ConvType.list_values() == [
            'pdf2txt',
            'pdf2svg',
            'svg2page',
            'txt2para',
            'txt2sent',
            'xml2html',
            'xml2sect',
            'xml2txt']

    def test_list_enum_names(self):
        assert ConvType.list_names() == [
            'PDF2TXT',
            'PDF2SVG',
            'SVG2PAGE',
            'TXT2PARA',
            'TXT2SENT',
            'XML2HTML',
            'XML2SECT',
            'XML2TXT']

    def test_iterate(self):
        """converter with implicit directories"""
        svg_converter = Converters.get_converter(ConvType.SVG2PAGE.value)()
        svg_converter.iterate_cproject(cproject=Resources.CLIMATE_10_PROJ_DIR)

    @unittest.skip("need to fix read_and_convert args")
    def test_get_and_run_converter(self):
        svg_converter = Converters.get_converter(ConvType.SVG2PAGE.value)()
        assert type(svg_converter) == Svg2PageConverter
        svg_converter.read_and_convert(infile=None, indir_basename=Resources.CLIMATE_10_PROJ_DIR, outfile=None,
                                       outdir_basename=Resources.TEMP_CLIMATE_10_PROJ_DIR)

    @unittest.skip("obsolete, args have changed")
    def test_cli_iterator_svg2xml(self):
        """PyAMI conversion with implicit directories set by converter"""
        cmd = f"-p {Resources.CLIMATE_10_PROJ_DIR} --apply svg2page"
        PyAMI().run_command(cmd)

    @unittest.skip("obsolete")
    def test_cli_iterator_(self):
        """PyAMI conversion with implicit directories set by converter"""
        assert Path(Resources.CLIMATE_10_PROJ_DIR).exists(), f"{Path(Resources.CLIMATE_10_PROJ_DIR)} should exist"
        cmd = f"-p {Resources.CLIMATE_10_PROJ_DIR} --apply svg2page"
        PyAMI().run_command(cmd)

if __name__ == '__main__':
    unittest.main()