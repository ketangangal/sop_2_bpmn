import xml.etree.ElementTree as ET

from src.generator.bpmn_builder import BPMNBuilder
from src.generator.bpmn_xml_writer import BPMNXMLWriter
from src.generator.layout import LayoutEngine


def _generate_xml(sop_document) -> str:
    builder = BPMNBuilder()
    process = builder.build(sop_document)
    LayoutEngine().apply_layout(process)
    return BPMNXMLWriter().write(process)


class TestBPMNXMLWriter:

    def test_xml_is_well_formed(self, sample_sop_document):
        xml_str = _generate_xml(sample_sop_document)
        # Should parse without error
        ET.fromstring(xml_str)

    def test_xml_has_correct_namespaces(self, sample_sop_document):
        xml_str = _generate_xml(sample_sop_document)
        assert "http://www.omg.org/spec/BPMN/20100524/MODEL" in xml_str
        assert "http://www.omg.org/spec/BPMN/20100524/DI" in xml_str
        assert "http://www.omg.org/spec/DD/20100524/DC" in xml_str
        assert "http://www.omg.org/spec/DD/20100524/DI" in xml_str

    def test_xml_has_process(self, sample_sop_document):
        xml_str = _generate_xml(sample_sop_document)
        root = ET.fromstring(xml_str)
        ns = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
        processes = root.findall("bpmn:process", ns)
        assert len(processes) == 1

    def test_xml_has_diagram_section(self, sample_sop_document):
        xml_str = _generate_xml(sample_sop_document)
        assert "BPMNDiagram" in xml_str
        assert "BPMNPlane" in xml_str
        assert "BPMNShape" in xml_str
        assert "BPMNEdge" in xml_str

    def test_xml_has_start_and_end_events(self, sample_sop_document):
        xml_str = _generate_xml(sample_sop_document)
        root = ET.fromstring(xml_str)
        ns = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
        proc = root.find("bpmn:process", ns)

        starts = proc.findall("bpmn:startEvent", ns)
        ends = proc.findall("bpmn:endEvent", ns)
        assert len(starts) == 1
        assert len(ends) == 1

    def test_xml_has_gateways(self, sample_sop_document):
        xml_str = _generate_xml(sample_sop_document)
        root = ET.fromstring(xml_str)
        ns = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
        proc = root.find("bpmn:process", ns)

        gateways = proc.findall("bpmn:exclusiveGateway", ns)
        assert len(gateways) >= 2  # at least diverging + converging

    def test_xml_sequence_flows_have_refs(self, sample_sop_document):
        xml_str = _generate_xml(sample_sop_document)
        root = ET.fromstring(xml_str)
        ns = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
        proc = root.find("bpmn:process", ns)

        flows = proc.findall("bpmn:sequenceFlow", ns)
        for flow in flows:
            assert flow.get("sourceRef") is not None
            assert flow.get("targetRef") is not None

    def test_linear_xml(self, linear_sop_document):
        xml_str = _generate_xml(linear_sop_document)
        root = ET.fromstring(xml_str)
        ns = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
        proc = root.find("bpmn:process", ns)

        # No gateways in linear SOP
        gateways = proc.findall("bpmn:exclusiveGateway", ns)
        assert len(gateways) == 0

        tasks = proc.findall("bpmn:task", ns)
        assert len(tasks) == 3

    def test_xml_has_bounds_on_shapes(self, sample_sop_document):
        xml_str = _generate_xml(sample_sop_document)
        root = ET.fromstring(xml_str)
        ns = {
            "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
            "dc": "http://www.omg.org/spec/DD/20100524/DC",
        }
        shapes = root.findall(".//bpmndi:BPMNShape", ns)
        assert len(shapes) > 0
        for shape in shapes:
            bounds = shape.find("dc:Bounds", ns)
            assert bounds is not None
            assert bounds.get("x") is not None
            assert bounds.get("y") is not None
