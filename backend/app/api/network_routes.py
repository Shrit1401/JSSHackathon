from fastapi import APIRouter

from app.database import service as db
from app.database.seed_data import (
    DEVICE_FLEET,
    TOPOLOGY_EDGES,
    INITIAL_TRUST_PROFILES,
    _name_to_uuid,
)
from app.api.telemetry_routes import generator
from app.api.trust_routes import trust_engine

router = APIRouter(prefix="/network-map", tags=["Network Graph"])


def _build_in_memory_nodes() -> list[dict]:
    nodes = []
    name_to_uuid = {d["name"]: _name_to_uuid(d["name"]) for d in DEVICE_FLEET}
    for d in DEVICE_FLEET:
        tp = INITIAL_TRUST_PROFILES[d["name"]]

        live_trust = None
        live_device = generator.get_device_by_id(d["name"])
        if live_device:
            live_trust = trust_engine.get_device_trust(d["name"])

        trust_score = live_trust.trust_score if live_trust else tp["trust"]
        risk_level = live_trust.risk_level.value if live_trust else tp["risk"]
        status = "safe"
        if trust_score < 40:
            status = "compromised"
        elif trust_score < 70:
            status = "suspicious"

        parent_edge = next(
            (e for e in TOPOLOGY_EDGES if e[1] == d["name"]),
            None,
        )

        nodes.append({
            "id": name_to_uuid[d["name"]],
            "device_name": d["name"],
            "device_type": d["type"],
            "ip_address": d["ip"],
            "trust_score": trust_score,
            "risk_level": risk_level,
            "status": status,
            "parent_id": name_to_uuid.get(parent_edge[0]) if parent_edge else None,
        })
    return nodes


def _build_in_memory_edges() -> list[dict]:
    edges = []
    for src, tgt, conn_type in TOPOLOGY_EDGES:
        edges.append({
            "id": f"{_name_to_uuid(src)[:8]}-{_name_to_uuid(tgt)[:8]}",
            "source": _name_to_uuid(src),
            "target": _name_to_uuid(tgt),
            "connection_type": conn_type,
        })
    return edges


def _build_tree(nodes: list[dict], edges: list[dict]) -> list[dict]:
    node_map = {n["id"]: {**n, "children": []} for n in nodes}
    child_ids = set()

    for e in edges:
        parent = node_map.get(e["source"])
        child = node_map.get(e["target"])
        if parent and child:
            parent["children"].append(child)
            child_ids.add(e["target"])

    roots = [n for nid, n in node_map.items() if nid not in child_ids]
    return roots


@router.get("")
def get_network_map():
    db_data = db.get_network_map()
    if db_data["nodes"]:
        nodes = db_data["nodes"]
        edges_raw = db_data["edges"]
    else:
        nodes = _build_in_memory_nodes()
        edges_raw = _build_in_memory_edges()

    source = "supabase" if db_data["nodes"] else "in_memory"

    return {
        "nodes": nodes,
        "edges": edges_raw,
        "tree": _build_tree(nodes, edges_raw),
        "total_nodes": len(nodes),
        "total_edges": len(edges_raw),
        "source": source,
    }


@router.get("/flat")
def get_flat_map():
    db_data = db.get_network_map()
    if db_data["nodes"]:
        return {
            "nodes": db_data["nodes"],
            "edges": db_data["edges"],
            "source": "supabase",
        }
    return {
        "nodes": _build_in_memory_nodes(),
        "edges": _build_in_memory_edges(),
        "source": "in_memory",
    }


@router.get("/tree")
def get_tree():
    db_data = db.get_network_map()
    if db_data["nodes"]:
        nodes = db_data["nodes"]
        edges = db_data["edges"]
    else:
        nodes = _build_in_memory_nodes()
        edges = _build_in_memory_edges()

    return _build_tree(nodes, edges)


@router.get("/nodes")
def get_nodes():
    db_devices = db.get_all_devices()
    if db_devices:
        return db_devices
    return _build_in_memory_nodes()


@router.get("/edges")
def get_edges():
    db_edges = db.get_full_topology()
    if db_edges:
        return [
            {
                "id": e["id"],
                "source": e["source_device"],
                "target": e["target_device"],
                "connection_type": e["connection_type"],
                "last_active": e.get("last_active"),
            }
            for e in db_edges
        ]
    return _build_in_memory_edges()
