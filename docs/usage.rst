Tool Documentation
==================
.. toctree::
    :maxdepth: 1

    tool_documentation/settings
    tool_documentation/framer
    tool_documentation/layout
    tool_documentation/straighten
    tool_documentation/optimize
    tool_documentation/pbr_reference

Unsupported Graph Types
^^^^^^^^^^^^^^^^^^^^^^^
Currently, the Designer API has many bugs with the new graph types added in 11.0.0 which causes the tools to error or crash.
For this reason, I have disabled the tools from running in these unsupported graph types.
I hope to support all graph types in future when the Designer API has fixed the bugs.

Current unsupported graph types are

1. Model Graph

2. MDL Graph

3. FX Map Graph
