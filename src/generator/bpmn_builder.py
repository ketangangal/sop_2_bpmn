from src.models.bpmn import BPMNNode, BPMNNodeType, BPMNProcess, BPMNSequenceFlow
from src.models.sop import SOPDocument, SOPElement, SOPElementType


class BPMNBuilder:
    """Converts a parsed SOPDocument into a BPMNProcess graph."""

    def __init__(self) -> None:
        self._node_counter: int = 0
        self._flow_counter: int = 0

    def build(self, sop: SOPDocument) -> BPMNProcess:
        process = BPMNProcess(name=sop.title)

        start_node = self._make_node(BPMNNodeType.START_EVENT, f"{sop.title} Started")
        process.nodes.append(start_node)

        last_node_id = self._process_elements(sop.elements, process, start_node.id)

        end_node = self._make_node(BPMNNodeType.END_EVENT, f"{sop.title} Completed")
        process.nodes.append(end_node)
        self._add_flow(process, last_node_id, end_node.id)

        return process

    def _process_elements(
        self,
        elements: list[SOPElement],
        process: BPMNProcess,
        last_node_id: str,
    ) -> str:
        """Process a list of SOP elements, returning the ID of the last node."""
        for element in elements:
            if element.element_type == SOPElementType.STEP:
                task = self._make_node(BPMNNodeType.TASK, element.text)
                process.nodes.append(task)
                self._add_flow(process, last_node_id, task.id)
                last_node_id = task.id

            elif element.element_type == SOPElementType.DECISION:
                last_node_id = self._process_decision(element, process, last_node_id)

        return last_node_id

    def _process_decision(
        self,
        element: SOPElement,
        process: BPMNProcess,
        last_node_id: str,
    ) -> str:
        """Build diverging gateway -> branch tasks -> converging gateway."""
        decision = element.decision

        # Diverging gateway
        div_gateway = self._make_node(
            BPMNNodeType.EXCLUSIVE_GATEWAY,
            decision.question if decision else element.text,
        )
        process.nodes.append(div_gateway)
        self._add_flow(process, last_node_id, div_gateway.id)

        # Converging gateway
        conv_gateway = self._make_node(BPMNNodeType.CONVERGING_GATEWAY, "")
        process.nodes.append(conv_gateway)

        if not decision or not decision.branches:
            # No branches — direct flow through
            self._add_flow(process, div_gateway.id, conv_gateway.id)
            return conv_gateway.id

        for branch in decision.branches:
            if branch.steps:
                branch_last_id = div_gateway.id
                is_first = True
                for step in branch.steps:
                    if step.element_type == SOPElementType.STEP:
                        task = self._make_node(BPMNNodeType.TASK, step.text)
                        process.nodes.append(task)
                        flow_name = branch.condition_label if is_first else ""
                        self._add_flow(process, branch_last_id, task.id, name=flow_name)
                        branch_last_id = task.id
                        is_first = False
                    elif step.element_type == SOPElementType.DECISION:
                        if is_first:
                            # Label the flow from gateway to nested decision
                            self._add_flow(
                                process,
                                branch_last_id,
                                "",  # placeholder, will be set by recursive call
                                name=branch.condition_label,
                            )
                        branch_last_id = self._process_decision(step, process, branch_last_id)
                        is_first = False

                self._add_flow(process, branch_last_id, conv_gateway.id)
            else:
                # Empty branch — direct flow
                self._add_flow(
                    process,
                    div_gateway.id,
                    conv_gateway.id,
                    name=branch.condition_label,
                )

        return conv_gateway.id

    def _make_node(self, node_type: BPMNNodeType, name: str) -> BPMNNode:
        self._node_counter += 1
        prefix_map = {
            BPMNNodeType.START_EVENT: "StartEvent",
            BPMNNodeType.END_EVENT: "EndEvent",
            BPMNNodeType.TASK: "Task",
            BPMNNodeType.EXCLUSIVE_GATEWAY: "Gateway",
            BPMNNodeType.CONVERGING_GATEWAY: "Gateway",
        }
        prefix = prefix_map[node_type]
        return BPMNNode(id=f"{prefix}_{self._node_counter}", node_type=node_type, name=name)

    def _add_flow(
        self,
        process: BPMNProcess,
        source_ref: str,
        target_ref: str,
        name: str = "",
    ) -> BPMNSequenceFlow:
        self._flow_counter += 1
        flow = BPMNSequenceFlow(
            id=f"Flow_{self._flow_counter}",
            source_ref=source_ref,
            target_ref=target_ref,
            name=name,
        )
        process.sequence_flows.append(flow)
        return flow
