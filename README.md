# Network policy lab using POX

A POX controller application based using the Bellman-Ford algorithm* to find shortest path in a network.
The application will always try to use the least used nodes (based on byte counts) in the network.
If a nodes' bandwidth exceeds a limit, the node is considered unavailable and is excluded.
It listen to link events, if a link goes down the controller will delete flow rules which use the link, in order to start a new forwarding calculation. If a node tries to communicate when no path is available, a drop rule will be installed.

# Run the script
- Install POX and Mininet
- Add script to the ext-folder in pox
- Start up a mininet network with connection to pox controller
- Run application by: ./pox.py ext.Lab5
