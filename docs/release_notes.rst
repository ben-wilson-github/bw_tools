Relase Notes
============

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