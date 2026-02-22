import xml.etree.ElementTree as ET

from src.models.bpmn import BPMNNodeType, BPMNProcess

# BPMN 2.0 Namespaces (compatible with bpmn.io)
NS_BPMN = "http://www.omg.org/spec/BPMN/20100524/MODEL"
NS_BPMNDI = "http://www.omg.org/spec/BPMN/20100524/DI"
NS_DC = "http://www.omg.org/spec/DD/20100524/DC"
NS_DI = "http://www.omg.org/spec/DD/20100524/DI"
TARGET_NAMESPACE = "http://bpmn.io/schema/bpmn"


class BPMNXMLWriter:
    """Serializes a BPMNProcess to BPMN 2.0 XML."""

    def write(self, process: BPMNProcess) -> str:
        ET.register_namespace("bpmn", NS_BPMN)
        ET.register_namespace("bpmndi", NS_BPMNDI)
        ET.register_namespace("dc", NS_DC)
        ET.register_namespace("di", NS_DI)

        definitions = ET.Element(f"{{{NS_BPMN}}}definitions")
        definitions.set("id", "Definitions_1")
        definitions.set("targetNamespace", TARGET_NAMESPACE)
        definitions.set("exporter", "SOP to BPMN Converter")
        definitions.set("exporterVersion", "1.0.0")

        # <bpmn:process>
        proc_elem = ET.SubElement(definitions, f"{{{NS_BPMN}}}process")
        proc_elem.set("id", process.id)
        proc_elem.set("name", process.name)
        proc_elem.set("isExecutable", "true")

        for node in process.nodes:
            self._write_node(proc_elem, node, process)

        for flow in process.sequence_flows:
            self._write_sequence_flow(proc_elem, flow)

        # <bpmndi:BPMNDiagram>
        diagram = ET.SubElement(definitions, f"{{{NS_BPMNDI}}}BPMNDiagram")
        diagram.set("id", "BPMNDiagram_1")

        plane = ET.SubElement(diagram, f"{{{NS_BPMNDI}}}BPMNPlane")
        plane.set("id", "BPMNPlane_1")
        plane.set("bpmnElement", process.id)

        for node in process.nodes:
            self._write_shape(plane, node)

        for flow in process.sequence_flows:
            self._write_edge(plane, flow)

        ET.indent(definitions, space="  ")
        xml_str = ET.tostring(definitions, encoding="unicode", xml_declaration=False)
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str

    def _write_node(self, parent: ET.Element, node, process: BPMNProcess) -> None:
        xml_tag_map = {
            BPMNNodeType.START_EVENT: "startEvent",
            BPMNNodeType.END_EVENT: "endEvent",
            BPMNNodeType.TASK: "task",
            BPMNNodeType.EXCLUSIVE_GATEWAY: "exclusiveGateway",
            BPMNNodeType.CONVERGING_GATEWAY: "exclusiveGateway",
        }
        tag = xml_tag_map[node.node_type]
        elem = ET.SubElement(parent, f"{{{NS_BPMN}}}{tag}")
        elem.set("id", node.id)
        if node.name:
            elem.set("name", node.name)

        # Add incoming/outgoing references
        for flow in process.sequence_flows:
            if flow.target_ref == node.id:
                inc = ET.SubElement(elem, f"{{{NS_BPMN}}}incoming")
                inc.text = flow.id
        for flow in process.sequence_flows:
            if flow.source_ref == node.id:
                out = ET.SubElement(elem, f"{{{NS_BPMN}}}outgoing")
                out.text = flow.id

    def _write_sequence_flow(self, parent: ET.Element, flow) -> None:
        elem = ET.SubElement(parent, f"{{{NS_BPMN}}}sequenceFlow")
        elem.set("id", flow.id)
        elem.set("sourceRef", flow.source_ref)
        elem.set("targetRef", flow.target_ref)
        if flow.name:
            elem.set("name", flow.name)

    def _write_shape(self, plane: ET.Element, node) -> None:
        shape = ET.SubElement(plane, f"{{{NS_BPMNDI}}}BPMNShape")
        shape.set("id", f"{node.id}_di")
        shape.set("bpmnElement", node.id)

        bounds = ET.SubElement(shape, f"{{{NS_DC}}}Bounds")
        bounds.set("x", str(int(node.x)))
        bounds.set("y", str(int(node.y)))
        bounds.set("width", str(int(node.width)))
        bounds.set("height", str(int(node.height)))

    def _write_edge(self, plane: ET.Element, flow) -> None:
        edge = ET.SubElement(plane, f"{{{NS_BPMNDI}}}BPMNEdge")
        edge.set("id", f"{flow.id}_di")
        edge.set("bpmnElement", flow.id)

        for wp in flow.waypoints:
            waypoint = ET.SubElement(edge, f"{{{NS_DI}}}waypoint")
            waypoint.set("x", str(int(wp.x)))
            waypoint.set("y", str(int(wp.y)))
