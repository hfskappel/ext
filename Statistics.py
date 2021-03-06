"""
Author Hans Fredrik Skappel, 2015, NTNU

A simple POX controller application used to gather different parameters from the network topology.
"""
from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.recoco import Timer
nodes = []

def _handle_ConnectionUp(event):
    nodes.append(event)
    print "Switch discovered with DIPID: ", event.connection.dpid

def _handle_linkevent(event):
    link_list = core.openflow_discovery.adjacency
    print "Link discovered: ", event.link

def _handle_features(event):
    print event.connection.features.datapath_id, event.connection.features.n_buffers, event.connection.features.n_tables, event.connection.features.capabilities, event.connection.features.actions
    for m in event.connection.features.ports:
        print "Features: ", m.name,m.port_no,m.hw_addr,m.curr,m.advertised,m.supported,m.peer,m.config,m.state

def _handle_portstats(event):
    for f in event.stats:
        print "Switch: ", event.connection.dpid, " PortNo:", f.port_no, " Fwd's Pkts:", f.tx_packets, " Rc'd Pkts:", f.rx_packets

def _handle_flowstats(event):
    for n in event.stats:
        print "FLOWSTATUS: TableID: ", n.table_id, " Packet count: ", n.packet_count, " Byte count :", n.byte_count
        for o in n.actions:
            print "FLOWSTATUS: Switch: ", event.connection.dpid, " Port: ", o.port, "Packet count: ", n.packet_count

def _handle_aggregate(event):
        print "Total counts for switch:", event.dpid, " Packet count: ", event.stats.packet_count, " Byte count: ", event.stats.byte_count, "Flow count: ", event.stats.flow_count


def _on_timer():

    for n in nodes:
        #Sends out requests to the network nodes
        core.openflow.getConnection(n.connection.dpid).send(of.ofp_features_request())
        n.connection.send(of.ofp_stats_request(body=of.ofp_port_stats_request()))
        n.connection.send(of.ofp_stats_request(body=of.ofp_aggregate_stats_request()))
        n.connection.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))


def launch():
    from pox.openflow.discovery import launch
    launch()

    core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
    core.openflow_discovery.addListenerByName("LinkEvent", _handle_linkevent)
    core.openflow.addListenerByName("FeaturesReceived", _handle_features)
    core.openflow.addListenerByName("PortStatsReceived",_handle_portstats)
    core.openflow.addListenerByName("FlowStatsReceived",_handle_flowstats)
    core.openflow.addListenerByName("AggregateFlowStatsReceived", _handle_aggregate)

    Timer(10, _on_timer, recurring=True)

