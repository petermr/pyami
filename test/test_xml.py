import lxml.etree
from py4ami.xml_lib import XmlLib
from test.test_all import AmiAnyTest

class TextXml(AmiAnyTest):

    def test_is_integer(self):
        span = lxml.etree.Element("span")
        span.text = "12"
        assert XmlLib.is_integer(span), f"an integer {span}"

        span.text = "+12"
        assert XmlLib.is_integer(span), f"an integer {span}"

        span.text = "-12"
        assert XmlLib.is_integer(span), f"integer {span.text}"

        span.text = "b12"
        assert not XmlLib.is_integer(span), f"not an integer {span.text}"

        span.text = "-12.0"
        assert not XmlLib.is_integer(span), f"not an integer {span.text}"

