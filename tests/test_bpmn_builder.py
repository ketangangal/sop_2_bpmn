from src.generator.bpmn_builder import BPMNBuilder
from src.models.bpmn import BPMNNodeType


class TestBPMNBuilderLinear:
    """Test BPMN graph construction for linear SOPs (no decisions)."""

    def test_linear_has_start_and_end(self, linear_sop_document):
        builder = BPMNBuilder()
        process = builder.build(linear_sop_document)

        types = [n.node_type for n in process.nodes]
        assert BPMNNodeType.START_EVENT in types
        assert BPMNNodeType.END_EVENT in types

    def test_linear_node_count(self, linear_sop_document):
        builder = BPMNBuilder()
        process = builder.build(linear_sop_document)

        # start + 3 tasks + end = 5
        assert len(process.nodes) == 5

    def test_linear_flow_count(self, linear_sop_document):
        builder = BPMNBuilder()
        process = builder.build(linear_sop_document)

        # start->A, A->B, B->C, C->end = 4
        assert len(process.sequence_flows) == 4

    def test_linear_flow_chain(self, linear_sop_document):
        builder = BPMNBuilder()
        process = builder.build(linear_sop_document)

        # Verify the chain: each flow's target is the next flow's source
        for i in range(len(process.sequence_flows) - 1):
            assert process.sequence_flows[i].target_ref == process.sequence_flows[i + 1].source_ref


class TestBPMNBuilderDecision:
    """Test BPMN graph construction for SOPs with decisions."""

    def test_decision_creates_gateways(self, sample_sop_document):
        builder = BPMNBuilder()
        process = builder.build(sample_sop_document)

        gateway_types = [
            n.node_type
            for n in process.nodes
            if n.node_type in (BPMNNodeType.EXCLUSIVE_GATEWAY, BPMNNodeType.CONVERGING_GATEWAY)
        ]
        assert BPMNNodeType.EXCLUSIVE_GATEWAY in gateway_types
        assert BPMNNodeType.CONVERGING_GATEWAY in gateway_types

    def test_decision_node_count(self, sample_sop_document):
        builder = BPMNBuilder()
        process = builder.build(sample_sop_document)

        # start + task(receive) + gateway(div) + task(billing) + task(general) +
        # gateway(conv) + task(send) + task(close) + end = 9
        assert len(process.nodes) == 9

    def test_all_ids_unique(self, sample_sop_document):
        builder = BPMNBuilder()
        process = builder.build(sample_sop_document)

        node_ids = [n.id for n in process.nodes]
        assert len(node_ids) == len(set(node_ids))

        flow_ids = [f.id for f in process.sequence_flows]
        assert len(flow_ids) == len(set(flow_ids))

    def test_branch_flows_have_labels(self, sample_sop_document):
        builder = BPMNBuilder()
        process = builder.build(sample_sop_document)

        labeled_flows = [f for f in process.sequence_flows if f.name]
        labels = {f.name for f in labeled_flows}
        assert "Yes" in labels
        assert "No" in labels

    def test_sequence_flow_refs_valid(self, sample_sop_document):
        builder = BPMNBuilder()
        process = builder.build(sample_sop_document)

        node_ids = {n.id for n in process.nodes}
        for flow in process.sequence_flows:
            assert flow.source_ref in node_ids, f"Invalid source_ref: {flow.source_ref}"
            assert flow.target_ref in node_ids, f"Invalid target_ref: {flow.target_ref}"
