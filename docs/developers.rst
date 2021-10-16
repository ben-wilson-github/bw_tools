For Developers
==============

If you wish to browse or extend the code, go to `git hub page <https://github.com/ben-wilson-github/bw_tools>`_

Here is some general information which will be useful to know.

Working With Modules
--------------------
You can add new modules by defining a folder and .py file with the same name inside ``./bw_tools/modules``.

For example:

.. code-block::

    bw_tools
    ├── modules
        ├── my_new_module
            ├── __init__.py
            ├── my_new_module.py

You must define a on_initialize(api: BWAPITool) function inside my_new_module.py for the plugin to automatically load your module.

.. code-block:: python
    
    def on_initialize(api: BWAPITool):
        # Do any initialization here
        ...

All logic to initialize your module must be done from this function.

Adding Actions To The Menu Bar
------------------------------
You should add new actions to the BW Tool menu bar in the on_initialize function, using the api tool.

.. code-block:: python
    
    def on_initialize(api: BWAPITool):
        action = api.menu.addAction("My Action")
        action.triggered.connect(func_to_run)

Adding Actions To The Graph View Toolbar
----------------------------------------
The plugin will handle creating and managing the graphview toolbar itself,
but you must add your actions to it in the on_initialize function.

Use the api tool to register a new graph view created callback which adds your new actions to the graph view toolbar,
also accessed through the api tool.

.. code-block:: python
    
    def on_graph_view_created(graph_view_id, api: BWAPITool):
        # Get the toolbar for the new graph view
        toolbar = api.get_graph_view_toolbar(graph_view_id)

        # Create a new action
        action = QAction()
        action.triggered.connect(func_to_run)

        # Add action to graph view toolbar
        toolbar.add_action("my_tool_name", action)


    def on_initialize(api: BWAPITool):
        api.register_on_graph_view_created_callback(
            functools.partial(on_graph_view_created, api=api)
        )

Working With Setting Files
--------------------------
Module settings are stored in json and must be named ``<module>_settings.json`` and live along side the module.py file

.. code-block::

    bw_tools
    ├── modules
        ├── my_new_module
            ├── __init__.py
            ├── my_new_module.py
            ├── my_new_module_settings.json

The json file must follow a specific format in order for the plugin to automatically generate UI for your module.

You define the settings name with the key of a dictionary, the value of which then define the properties for the setting.

.. code-block:: json

    {
        "Hotkey": {
            "widget": 1,
            "value": "Alt+C"
        }
    }

Setting properties
^^^^^^^^^^^^^^^^^^
Properties are defined with the value or a diction key.

* widget - Enum int to define which widget the UI should use. Refers to the ``WidgetTypes`` Enum inside ``bw_tools/modules/bw_settings/settings_loader.py``.

* value - The value for the setting.

* list - The list of possible values when populating a combobox. Only available for combobox widget types.

* content - The content of a groupbox widget, the value of which should be a dictionary containing the settings inside the groupbox.

.. code-block::

    {
        "My String Setting": {
            "widget": 1,
            "value": "my string value"
        },
        "My Int Setting": {
            "widget": 2,
            "value": 32
        },
        "My Float Setting": {
            "widget": 3,
            "value": 32.0
        },
        "My Bool Setting": {
            "widget": 4,
            "value": true
        },
        "My Combobox Setting": {
            "widget": 5,
            "list": [
                "Option 1",
                "Option 2",
                "Option 3"
            ],
            "value": "Option 1"
        },
        "My RGBA Setting": {
            "widget": 6,
            "value": [
                1.0,
                1.0,
                1.0,
                1.0
            ]
        },
        "My Group Box": {
            "widget": 0,
            "content": {
                "My Sub Setting": {
                    "widget": 4,
                    "value": true
                }
            }
        }
    }

Providing Default Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^
To provide default settings for a module, you must define a get_default_settings function which returns a dict inside the main module.py file.

If your module declares this function, the plugin will automatically generate a module_settings.json file
if one was not found.

.. code-block:: python

    def get_default_settings() -> Dict:
        return {
            "My Hotkey": {"widget": 1, "value": "Alt+D"},
            "My Value": {"widget": 2, "value": 32},
        }

General Helper Classes
----------------------
There are some classes inside bw_tools/common to help with general API tasks.

BWAPITool Class
^^^^^^^^^^^^^^^
This helper class is to simplify the interface with Designer's API. 
It handles the Designer application related tasks such as getting the package manager or adding UI elements to the UI,
shown in `Adding Actions To The Menu Bar`_.

.. code-block:: python

    api_tool = BWAPITool()

    # Get the current node selection
    sd_nodes = api_tool.current_node_selection
    
    # Get the current graph
    sd_graph = api_tool.current_graph

    # Get the Designer main window widget
    designer_main_window = api_tool.main_window

BWNode Class
^^^^^^^^^^^^
This node is a wrapper around the Designer API SDNode type which makes accessing properties a little easier.
Most of the modules that come with bw_tools make use for BWNode.

This class is designed to work with the `BWNodeSelection Class`_,
which handles creating these nodes, allowing you to query a nodes inputs and outputs within the selection.

.. code-block:: python

    api = BWAPITool()
    sd_nodes = api.current_node_selection

    # Create a BWNode
    node = BWNode(sd_nodes[0])

    # Print a nodes label
    print(node.label)

    # Print a nodes position
    print(node.pos)


BWNodeSelection Class
^^^^^^^^^^^^^^^^^^^^^
This node lets you define a selection of BWNode's, allowing you to query a nodes inputs and outputs.

When initializing a BWNodeSelection, the input and outputs of a given node are only added if they are in same selection.
This behavior differs from the Designer API which always returns all connected nodes, regardless of selection.

.. code-block:: python

    api = BWAPITool()

    selection = BWNodeSelection(api.current_node_selection, api.current_graph)

    # Get a particular node from the selection
    bw_node = selection.node(identifier)

    # Because we got the BWNode through BWNodeSelection Class,
    # we can now query only the connections in the selection
    output_nodes = bw_node.output_nodes

    # Confirm a node is in the selection
    selection.contains(output_nodes[0])

Running Unit Tests
------------------
The unit tests are written to be run inside Designer, using the built in Python Editor.

.. admonition:: Dependencies
   :class: important

   The unit tests depend on PIL so you must pip install Pillow into the designer install directory!

To run the tests, open run_unit_tests.py in the Designer Python Editor and run.
This will load a number of Designer graphs used by the unit tests and execute them automatically.