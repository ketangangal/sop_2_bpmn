from src.models.bpmn import BPMNNodeType, BPMNProcess, Waypoint

# Layout constants
HORIZONTAL_SPACING = 180
VERTICAL_SPACING = 120
START_X = 150
START_Y = 250

# Node dimensions
EVENT_SIZE = 36
GATEWAY_SIZE = 50
TASK_WIDTH = 100
TASK_HEIGHT = 80


class LayoutEngine:
    """Assigns x,y coordinates to BPMN nodes and computes sequence flow waypoints."""

    def apply_layout(self, process: BPMNProcess) -> None:
        self._set_dimensions(process)
        self._assign_coordinates(process)
        self._compute_waypoints(process)

    def _set_dimensions(self, process: BPMNProcess) -> None:
        for node in process.nodes:
            if node.node_type in (BPMNNodeType.START_EVENT, BPMNNodeType.END_EVENT):
                node.width = EVENT_SIZE
                node.height = EVENT_SIZE
            elif node.node_type in (BPMNNodeType.EXCLUSIVE_GATEWAY, BPMNNodeType.CONVERGING_GATEWAY):
                node.width = GATEWAY_SIZE
                node.height = GATEWAY_SIZE
            else:
                node.width = TASK_WIDTH
                node.height = TASK_HEIGHT

    def _assign_coordinates(self, process: BPMNProcess) -> None:
        """Traverse the graph left-to-right, handling gateway fan-out/fan-in."""
        if not process.nodes:
            return

        node_map = {n.id: n for n in process.nodes}
        outgoing: dict[str, list[str]] = {n.id: [] for n in process.nodes}
        incoming: dict[str, list[str]] = {n.id: [] for n in process.nodes}
        flow_map: dict[str, str] = {}  # flow_id -> name

        for flow in process.sequence_flows:
            outgoing[flow.source_ref].append(flow.target_ref)
            incoming[flow.target_ref].append(flow.source_ref)
            flow_map[f"{flow.source_ref}->{flow.target_ref}"] = flow.name

        placed: set[str] = set()
        converging_arrivals: dict[str, list[tuple[float, float]]] = {}

        # Find start node
        start_node = next(
            (n for n in process.nodes if n.node_type == BPMNNodeType.START_EVENT), None
        )
        if not start_node:
            return

        # BFS with (node_id, x, y)
        queue: list[tuple[str, float, float]] = [(start_node.id, START_X, START_Y)]

        while queue:
            node_id, x, y = queue.pop(0)
            node = node_map[node_id]

            # Converging gateways need all incoming branches before placement
            if node.node_type == BPMNNodeType.CONVERGING_GATEWAY:
                if node_id not in converging_arrivals:
                    converging_arrivals[node_id] = []
                converging_arrivals[node_id].append((x, y))

                incoming_count = len(incoming[node_id])
                if len(converging_arrivals[node_id]) < incoming_count:
                    continue  # Wait for all branches

                # Place at max_x + spacing, average y
                arrivals = converging_arrivals[node_id]
                max_x = max(a[0] for a in arrivals)
                avg_y = sum(a[1] for a in arrivals) / len(arrivals)
                x = max_x + HORIZONTAL_SPACING
                y = avg_y

            if node_id in placed:
                continue
            placed.add(node_id)

            # Center the node at the target position
            node.x = x - node.width / 2
            node.y = y - node.height / 2

            targets = outgoing[node_id]

            if node.node_type == BPMNNodeType.EXCLUSIVE_GATEWAY and len(targets) > 1:
                # Fan out branches vertically
                n = len(targets)
                for i, target_id in enumerate(targets):
                    branch_y = y + (i - (n - 1) / 2) * VERTICAL_SPACING
                    branch_x = x + HORIZONTAL_SPACING
                    queue.append((target_id, branch_x, branch_y))
            else:
                # Sequential: advance horizontally
                for target_id in targets:
                    queue.append((target_id, x + HORIZONTAL_SPACING, y))

    def _compute_waypoints(self, process: BPMNProcess) -> None:
        node_map = {n.id: n for n in process.nodes}

        for flow in process.sequence_flows:
            source = node_map.get(flow.source_ref)
            target = node_map.get(flow.target_ref)
            if not source or not target:
                continue

            # Source exit: right center
            src_x = source.x + source.width
            src_y = source.y + source.height / 2

            # Target entry: left center
            tgt_x = target.x
            tgt_y = target.y + target.height / 2

            if abs(src_y - tgt_y) < 1:
                # Straight horizontal
                flow.waypoints = [Waypoint(src_x, src_y), Waypoint(tgt_x, tgt_y)]
            else:
                # Z-shaped routing
                mid_x = (src_x + tgt_x) / 2
                flow.waypoints = [
                    Waypoint(src_x, src_y),
                    Waypoint(mid_x, src_y),
                    Waypoint(mid_x, tgt_y),
                    Waypoint(tgt_x, tgt_y),
                ]
