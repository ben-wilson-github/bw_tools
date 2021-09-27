BW Layout Graph
===============
Automatically align selected nodes based on their hierarchy and are arranged such to minimise overlapping.
It is possible to align a given nodes inputs about their center point, stack them on top of each other or align them by their mainline. See Mainline

Node Placement Behavior
-----------------------

Simple Chain
^^^^^^^^^^^^
in line

Simple Hierarchy
^^^^^^^^^^^^^^^^
branching inputs
alignment Behavior
node heights

Looping Networks
^^^^^^^^^^^^^^^^^^^^^^^
placing behind closest output
y align to farthest
test_chain_8 sibling above moved above branching output sibling to minimise connection crossing over
    ddoesnt do it when under mainline


Network Chain Behavior
----------------
moved above / below sibling
without mainline / with mainline comparsion in x and y
if mainline then sibling is center

Root Nodes
^^^^^^^^^^
is a top parent node
multiple output roots
roots considered serarate Chains
make room for expanding network

Mainline
--------
largest network, where branch is considered a new Chain
moved back behind

Settings
--------