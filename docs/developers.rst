For Developers
==============

If you wish to browse or extend the code, go to `git hub page <https://github.com/ben-wilson-github/bw_tools>`_

There is also an :doc:`api_reference`

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

Adding Actions To Menu Bar
--------------------------
You should add a new action to the BW Tool menu bar, accessed through the api tool, in the on_initialize function.

.. code-block:: python
    
    def on_initialize(api: BWAPITool):
        action = api.menu.addAction("My Action")
        action.triggered.connect(func_to_run)

Adding Actions To The Graph View Toolbar
----------------------------------------
The plugin will handle creating and managing the graphview toolbar itself,
but you must add your actions to it in the on_initialize function.

Use the api tool to register a new graph view created callback to add your new actions to the graph view toolbar,
also accessed through the api tool.

The toobar must also be added to the new graphview to correctly update the UI.

.. code-block:: python
    
    def on_graph_view_created(graph_view_id, api: BWAPITool):
        # Move the toolbar to the new graph view
        api.add_toolbar_to_graph_view(graph_view_id)

        # Create a new action
        action = QAction()
        action.triggered.connect(func_to_run)

        # Add action to graph view toolbar
        api.graph_view_toolbar.add_action("my_tool_name", action)


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
            ├── my_new_module_settings.py

The json file must follow a specific format in order for the plugin to automatically generate UI for your module.

You define the settings name with the key of a dictionary, the values of which then define the properties for the setting.

.. code-block:: json

    {
        "Hotkey": {
            "widget": 1,
            "value": "Alt+C"
        }
    }

Setting properties
^^^^^^^^^^^^^^^^^^
Properties are defined by dictionary keys and value pairs.

* widget - Enum int to define which widget the UI should use. Referrs to the ``WidgetTypes`` Enum inside ``bw_tools/modules/bw_settings/settings_loader.py``.

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

How settings work
    settings files
    defualt settings
    settings module

common module usage
    nodes
    node selections
    chain dimension

