import maya.cmds as cmds


def _sub(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _blend(a, b, t):
    return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]


def _gap(a, b):
    d = _sub(a, b)
    return _dot(d, d)


def nearest_pair_on_lines(a_start, a_end, b_start, b_end):
    dir_a = _sub(a_end, a_start)
    dir_b = _sub(b_end, b_start)
    offset = _sub(a_start, b_start)
    aa = _dot(dir_a, dir_a)
    bb = _dot(dir_b, dir_b)
    ab = _dot(dir_a, dir_b)
    ao = _dot(dir_a, offset)
    bo = _dot(dir_b, offset)
    if aa < 1e-12 or bb < 1e-12:
        cmds.error("One of the selected edges has zero length.")
    det = aa * bb - ab * ab
    if det <= 1e-9 * aa * bb:
        cmds.error("The edges are parallel, so they have no single crossing point.")
    s = (ab * bo - bb * ao) / det
    t = (aa * bo - ab * ao) / det
    return _blend(a_start, a_end, s), _blend(b_start, b_end, t)


def _edge_ends(edge):
    verts = cmds.ls(cmds.polyListComponentConversion(edge, fromEdge=True, toVertex=True), flatten=True)
    return verts, [cmds.pointPosition(v, world=True) for v in verts]


def weld_edge_crossing():
    picked = cmds.filterExpand(selectionMask=32, expand=True) or []
    if len(picked) != 2:
        cmds.error("Select exactly two polygon edges.")

    owner_a = picked[0].split(".")[0]
    owner_b = picked[1].split(".")[0]
    same_mesh = owner_a == owner_b
    if not same_mesh:
        cmds.warning("The edges are on different meshes, so the vertices will be aligned but not merged.")

    verts_a, pos_a = _edge_ends(picked[0])
    verts_b, pos_b = _edge_ends(picked[1])

    hit_a, hit_b = nearest_pair_on_lines(pos_a[0], pos_a[1], pos_b[0], pos_b[1])
    target = _blend(hit_a, hit_b, 0.5)

    vert_a = verts_a[0] if _gap(hit_a, pos_a[0]) < _gap(hit_a, pos_a[1]) else verts_a[1]
    vert_b = verts_b[0] if _gap(hit_b, pos_b[0]) < _gap(hit_b, pos_b[1]) else verts_b[1]

    cmds.undoInfo(openChunk=True, chunkName="weldEdgeCrossing")
    try:
        for vert in {vert_a, vert_b}:
            cmds.move(target[0], target[1], target[2], vert, absolute=True, worldSpace=True)
        if same_mesh and vert_a != vert_b:
            cmds.polyMergeVertex(vert_a, vert_b, alwaysMergeTwoVertices=True)
    finally:
        cmds.undoInfo(closeChunk=True)


weld_edge_crossing()
