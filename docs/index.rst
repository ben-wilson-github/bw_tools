.. bw_tools documentation master file, created by
   sphinx-quickstart on Sat Sep 25 20:59:12 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.
   

Welcome to BW_Tools documentation!
====================================

Download here
unsupport graph types

To get the tools installed, follow this guide
:doc:`install`


general guide to using the tools
    as helpers to layout yourself
    layout in small groups
    little by little
    fix uniform nodes as you go
ref to using the tools
    with page for each tool
        pictures
        settings

support

license

developers
adding modules
    required functions and folder structure
    add to toolbar
    callbacks
    settings
        structure

common module usage
    nodes
    node selections
    chain dimension

go read api Reference
:doc:`api_reference`

change list:
2.0.0
rewrite

2.0.1
added default description to framer tool
Can no longer run graph tools on unsupported graph types

2.0.2
Updated tooltip for framer
Fixed alignment behavior on layout graph not working

2.0.3
Fixed toolbar sometimes not loading correctly
Fixed toolbar returning null pointer after a package has been unloaded
Updated tooltips
Fixed on hover for icons
layout graph mainline min threshold is now correctly calculated
optimize graph no longer deleted nodes connected to the same input node, but different properties
optimize graph no longer throws error when optimising uniform color nodes directly connected to an output node

2.0.4
layout graph setting names updates
layout graph when mainline is enabled, will revert to center alignment when a mainline failed threshold test

2.0.5
setting window now saves settings when pressing ok immediately after changing a value

.. toctree::
    :maxdepth: 1

    install
    usage
    support
    api_reference