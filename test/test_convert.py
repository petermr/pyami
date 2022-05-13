import unittest
# local
from py4ami.ami_convert import ConvType, Converters, Svg2XmlConverter
from test.resources import Resources

class TestConvert:

    def test_list_enum_values(self):
        assert ConvType.list_values() == [
            'pdf2txt',
            'pdf2svg',
            'svg2xml',
            'txt2para',
            'txt2sent',
            'xml2html',
            'xml2sect',
            'xml2txt']

    def test_list_enum_names(self):
        assert ConvType.list_names() == [
            'PDF2TXT',
            'PDF2SVG',
            'SVG2XML',
            'TXT2PARA',
            'TXT2SENT',
            'XML2HTML',
            'XML2SECT',
            'XML2TXT']

    def test_iterate(self):
        converter_func = Converters.get_converter(ConvType.SVG2XML.value)
        svg_converter = converter_func()
        print(f"{type(svg_converter)}")
        svg_converter.iterate_cproject(cproject=Resources.CLIMATE_10_PROJ_DIR)
        # svg_converter.read_and_convert(infile=None, ctree_indir=Resources.CLIMATE_10_PROJ_DIR, outfile=None, ctree_outdir=Resources.TEMP_CLIMATE_10_PROJ_DIR)

    @unittest.skip("need to fix read_and_convert args")
    def test_get_and_run_converter(self):
        svg_converter = Converters.get_converter(ConvType.SVG2XML.value)()
        assert type(svg_converter) == Svg2XmlConverter
        svg_converter.read_and_convert(infile=None, indir_basename=Resources.CLIMATE_10_PROJ_DIR, outfile=None, outdir_basename=Resources.TEMP_CLIMATE_10_PROJ_DIR)