import pymel.core as pm
import maya.cmds as cmds
import math


class UnitScaling(object):
    def __init__(self):
        rawLinearToM = cmds.convertUnit(1.0, toUnit="m")
        self.linearToM = float(rawLinearToM.split("m")[0])
        self.linearToCm = self.linearToM * 100.0

        self.mToCm = 100.0
        self.cmToM = 1.0 / self.mToCm

        self.mToLinear = 1.0 / self.linearToM
        self.cmToLinear = 1.0 / self.linearToCm

    def transformLinearToM(self, v):
        if len(v) == 3:
            return (
                v[0] * self.linearToM,
                v[1] * self.linearToM,
                v[2] * self.linearToM,
            )

        elif len(v) == 4:
            invW = 1 / v[3]
            return (
                v[0] * invW * self.linearToM,
                v[1] * invW * self.linearToM,
                v[2] * invW * self.linearToM,
            )

        else:
            assert False


def checkType(var, *expectedTypes, **kwargs):
    """ Check whether passed variable has the expected type.

    Args:
        var (any): Checked variable.
        expectedTypes (any): Expected type in any class, see examples.

    Examples:
        ### Simple checks:
        checkType(0, numbers.Number)
        checkType(u"any", unicode)
        checkType(u"any", str)
        # Fail, the variable needs to be number.
        #checkType(u"any", numbers.Number)
        # Ok, variable needs to be number or str.
        checkType(u"any", numbers.Number, str)

        ### List checks:
        # Ok, expected type is list.
        checkType([], list)
        # Fail, expected type is list, but not empty.
        checkType([], list, noEmptyCollection=True)
        # Ok, expected type is list with elements in any type.
        checkType([1, "any"], list)
        # Ok, elements are expected as strs.
        checkType(["any", "any"], [str])
        # Ok, elements are expected as strs and integers.
        checkType(["any", "any"], [str, int])
        # Fail, elements are expected as integers stored in list.
        #checkType(["any", "any"], [int])
        # Ok, nesting is acceptable. In the outer list, elements are
        # expected as strs or lists. In the inner list elements,
        # str needs to be used. Hard to read, do not use frequently.
        checkType(["any", ["any"]], [[str], str])

        ### Set checks:
        # Ok, expected type is a set.
        checkType(set(), set)
        # Fail, expected type is a set, but not empty.
        checkType(set(), set, noEmptyCollection=True)
        # Ok, expected type is a set with elements of any type.
        checkType(set([1, "any"]), set)
        # Ok, elements are expected as strs.
        checkType(set(["any", "any"]), set([str]))
        # Ok, elements are expected as strs and integers.
        checkType(set([1, 2, "any"]), set([str, int]))
        # Fail, elements are expected to be integers only.
        checkType(set([1, 2, "any"]), set([int]))

        # Nesting is supported even for sets. Note that noEmptyCollection applies only
        # for the root collection (lists, sets, frozensets), not for the nested ones.
        # Ok, expected list with integers and/or sets containing strs.
        checkType([1, 2, 3, set(["any", "test"])], [int, set([str])])
        # Fail, expected nested sets with strs.
        checkType([set([1])], [set([str])])
        # Ok, nested collection is empty, however, the root collection is not.
        checkType([set()], [set([str])], noEmptyCollection=True)

        ### Frozenset checks:
        # Frozensets are also supported and behave the same way as sets.
        # They are not interchangeable with sets!
        # Ok, frozenset with integer and str elements expected.
        checkType(frozenset([1, 2, "any"]), frozenset([int, str]))
        # Fail, only str elements expected.
        checkType(frozenset([1, 2, "any"]), frozenset([str]))
        # Fail, frozenset expected, got regular set.
        checkType(set([1, 2, "any"]), frozenset([int, str]))

        ### Tuple checks:
        # Ok.
        checkType(("any",), tuple)
        # Ok, it is expected a single element tuple with str element.
        checkType(("any",), (str,))
        # Ok, the 1st element needs to str and the second needs to be number.
        checkType(("any", 1), (str, numbers.Number))
        # Fail, the 1st element needs to be number.
        #checkType(("any", 1), (numbers.Number, str))
    """
    if len(expectedTypes) == 0:
        raise ValueError("At least two arguments needs to be passed.")

    # Developer's note, if you want the noEmptyCollection to apply recursively, use get() instead of pop().
    noEmptyCollection = kwargs.pop("noEmptyCollection", False)
    assert (isinstance(noEmptyCollection, bool))

    if noEmptyCollection:
        if isinstance(var, (list, set, frozenset, dict)):
            if len(var) == 0:
                raise RuntimeError("Variable is '{}'; expected non-empty collection!".format(repr(var)))

    for expectedType in expectedTypes:
        if isinstance(expectedType, type) or isinstance(expectedType, type):
            # If expected type is class 'type', check the 'type'.
            if isinstance(var, expectedType):
                return
        elif isinstance(expectedType, tuple):
            # If expected type is tuple instance, it is expected to have
            # the same element count in expectedType and in the variable.
            # All variable elements are checked with expected elements.
            if isinstance(var, tuple) and len(var) == len(expectedType):
                isOk = True
                for i in range(0, len(var)):
                    try:
                        checkType(var[i], expectedType[i], **kwargs)
                    except:
                        isOk = False
                        # Elements are not acceptable, try another expectedType.
                        break
                if isOk:
                    return

        elif isinstance(expectedType, (list, set, frozenset)):
            # If expected type is list or set instance, all variable elements
            # need to have any of the expected elements. The element counts
            # does not need to be the same.
            if not isinstance(var, type(expectedType)):
                continue

            isOk = True
            for elem in var:
                try:
                    checkType(elem, *expectedType, **kwargs)
                except:
                    isOk = False
                    break
            if isOk:
                return

    expectedTypeStr = ", ".join(str(expectedType) for expectedType in list(expectedTypes))
    raise RuntimeError("Variable is '{}'; expected '{}'.".format(repr(var), expectedTypeStr))


def _dValue(p1, p2, p3, p4):
    """ Compute and return the d value used in shortest line between lines computation.

    Args:
        p1 (pm.dt.Point)
        p2 (pm.dt.Point)
        p3 (pm.dt.Point)
        p4 (pm.dt.Point)

    Returns:
        float
    """
    checkType(p1, pm.dt.Point)
    checkType(p2, pm.dt.Point)
    checkType(p3, pm.dt.Point)
    checkType(p4, pm.dt.Point)

    return (p1.x - p2.x) * (p3.x - p4.x) + (p1.y - p2.y) * (p3.y - p4.y) + (p1.z - p2.z) * (p3.z - p4.z)


def getShortestLineSegmentBetweenTwoLines(edge1, edge2):
    checkType(edge1, pm.MeshEdge)  # Check script CHECKTYP!
    checkType(edge2, pm.MeshEdge)

    p1 = edge1.getPoint(0, "world")
    p2 = edge1.getPoint(1, "world")
    p3 = edge2.getPoint(0, "world")
    p4 = edge2.getPoint(1, "world")

    d1343 = _dValue(p1, p3, p4, p3)  # Check script _dValue!
    d4321 = _dValue(p4, p3, p2, p1)
    d4343 = _dValue(p4, p3, p4, p3)
    d1321 = _dValue(p1, p3, p2, p1)
    d2121 = _dValue(p2, p1, p2, p1)

    muaDenominator = (d2121 * d4343 - d4321 * d4321)
    mubDenominator = d4343

    if math.isclose(muaDenominator, 0.0, abs_tol=1e-5) or math.isclose(mubDenominator, 0.0, abs_tol=1e-5):
        pm.error("The lines are parallel, there are infinite possibilities for the shortest connecting line segment.")

    mua = (d1343 * d4321 - d1321 * d4343) / muaDenominator
    mub = (d1343 + mua * d4321) / mubDenominator

    sp1 = (1 - mua) * p1 + mua * p2
    sp2 = (1 - mub) * p3 + mub * p4

    return (sp1, sp2)


def mergeVerticesClosestToEdgeIntersection():
    sel = pm.selected(flatten=True)
    if len(sel) != 2 or not all([isinstance(n, pm.MeshEdge) for n in sel]):
        pm.error("Exactly two edges must be selected for this operation!")

    edge1 = sel[0]
    edge2 = sel[1]

    if edge1.node() != edge2.node():
        pm.warning("The edges belong to two different meshes, they will be aligned, but not merged!")

    sp1, sp2 = getShortestLineSegmentBetweenTwoLines(edge1, edge2)

    sp = (sp1 + sp2) / 2

    p1 = edge1.getPoint(0, "world")
    p2 = edge1.getPoint(1, "world")
    p3 = edge2.getPoint(0, "world")
    p4 = edge2.getPoint(1, "world")

    sp1p1 = pm.dt.Vector(sp1 - p1)
    sp1p2 = pm.dt.Vector(sp1 - p2)
    if sp1p1.length() < sp1p2.length():
        v1Index = 0
    else:
        v1Index = 1

    sp2p3 = pm.dt.Vector(sp2 - p3)
    sp2p4 = pm.dt.Vector(sp2 - p4)
    if sp2p3.length() < sp2p4.length():
        v2Index = 0
    else:
        v2Index = 1

    v1 = edge1.connectedVertices()[v1Index]
    v2 = edge2.connectedVertices()[v2Index]

    unitScaling = UnitScaling()
    sp = sp * unitScaling.cmToLinear

    pm.move(v1, sp)
    pm.move(v2, sp)

    if v1.node() == v2.node():
        pm.polyMergeVertex(v1, v2, alwaysMergeTwoVertices=True)


mergeVerticesClosestToEdgeIntersection()
