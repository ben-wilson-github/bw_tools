Welcome to BW Tools documentation!
====================================
.. toctree::
    :maxdepth: 1

    install
    usage
    general_guide
    support
    api_reference


Download
========

Download here

Installing The Tools
====================
To get the tools installed, follow this guide
:doc:`install`

Overview
========
BW Tools is a plugin for Substance Designer aimed at speeding up graph organisation tasks.
The plugin is split into a series of modules, each designed to solve a particular problem.
Take a look at :doc:`usage` for a more detailed look at each of the tools.

I recommend looking at :doc:`general_guide` to get the most out of the tools.

If you are looking to work with the code or want to understand more,
check out the :doc:`api_reference` and my `git hub page <https://github.com/ben-wilson-github/bw_tools>`_


Compatibility
=============
Compatible with Substance Designer 11.2.0 onwards


License
=======
MIT License

Copyright (c) 2021 ben-wilson-github

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.



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

2.0.6
Layout graph mainline logic update. Now only considers mainline nodes if input chains are not equal. Reverts to center align

