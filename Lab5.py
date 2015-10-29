"""
Author Hans Fredrik Skappel, 2015, NTNU

A POX controller application based using the Bellman-Ford algorithm* to find shortest path in a network.
The application will always try to use the least used nodes (based on packet counts) in the network.
It listen to link events, if a link goes down the controller will delete rules on the switches which share the link.

*The Bellman-Ford function is based on "l2_bellmanford.py", written by Dr. Chih-Heng Ke.
"""

from pox.core import core
from collections import defaultdict
from pox.lib.recoco import Timer
import pox.openflow.libopenflow_01 as of
import operator

log = core.getLogger()
adjacency = defaultdict(lambda:defaultdict(lambda:None))
adjpolicy = defaultdict(lambda:defaultdict(lambda:None))
link_list, switches, sw_con, routes = [],[],[],[]
table, mactable, path = {},{},{}


def bellman(src_dpid, dst_dpid):
    # Bellman is used to find the shortest path between switches.
    distance = {}
    previous = {}

    for dpid in switches:
        distance[dpid] = 9999
        previous[dpid] = None

    distance[src_dpid] = 0
    for m in range(len(switches) - 1):
        for p in switches:
            for q in switches:
                if adjpolicy[p][q] != None:
                    w = 1

                    if distance[p] + w < distance[q]:
                        distance[q] = distance[p] + w
                        previous[q] = p
    try:
        r = []
        p = dst_dpid
        r.append(p)
        q = previous[p]

        while q is not None:
            if q == src_dpid:
                r.append(q)
                break
            p = q
            r.append(p)
            q = previous[p]
        r.reverse()
        print "Bellman-Ford found shortest path: ",r
        return r

    except KeyError:
        print "Error! Invalid path. Check policy"
        return False


def generate_Flows(path, src_adr, dst_adr):

    for m in range(len(path)):
    #Iterate over total path

        for switch in sw_con:

            if len(path) == 1:

                if switch.dpid == table.get(src_adr):
                #Applying local switch rules on initiating (if hosts located at same switch)
                    msg = of.ofp_flow_mod()
                    msg.match.dl_dst = src_adr
                    msg.match.dl_src = dst_adr
                    msg.actions.append(of.ofp_action_output(port=mactable.get(src_adr)))
                    switch.connection.send(msg)

                if switch.dpid == table.get(dst_adr):
                #Applying local switch rules on initiating switch (if hosts located at same switch)
                    msg = of.ofp_flow_mod()
                    msg.match.dl_dst = dst_adr
                    msg.match.dl_src = src_adr
                    msg.actions.append(of.ofp_action_output(port=mactable.get(dst_adr)))
                    switch.connection.send(msg)
                    return

            else:
                try:
                    if switch.dpid == path[m+1]:
                        swobj1 = switch
                    if switch.dpid == path[m]:
                        swobj2 = switch
                except IndexError:
                    break


        try:
            if swobj1.dpid == table.get(src_adr):
            #Applying local switch rules on initiating
                msg = of.ofp_flow_mod()
                msg.match.dl_dst = src_adr
                msg.match.dl_src = dst_adr
                msg.actions.append(of.ofp_action_output(port=mactable.get(src_adr)))
                swobj1.connection.send(msg)

            if swobj2.dpid == table.get(dst_adr):
            #Applying local switch rules on dest switch
                msg = of.ofp_flow_mod()
                msg.match.dl_dst = dst_adr
                msg.match.dl_src = src_adr
                msg.actions.append(of.ofp_action_output(port=mactable.get(dst_adr)))
                swobj2.connection.send(msg)

            for links in link_list:
            #Finds the links
                if links.dpid1 == swobj1.dpid and links.dpid2 == swobj2.dpid:  # Finds the link for only one way
                    msg = of.ofp_flow_mod()
                    msg.match.dl_dst = dst_adr
                    msg.match.dl_src = src_adr
                    msg.actions.append(of.ofp_action_output(port=links.port1))
                    swobj1.connection.send(msg)

                    msg = of.ofp_flow_mod()
                    msg.match.dl_dst = src_adr
                    msg.match.dl_src = dst_adr
                    msg.actions.append(of.ofp_action_output(port=links.port2))
                    swobj2.connection.send(msg)

        except IndexError:
            log.debug("Error")
            return


def _handle_ConnectionUp(event):
    print "Switch with DPIPD: ", event.dpid, " connected!"
    switches.append(event.dpid)
    sw_con.append(event)


def _handle_aggregate(event):
    path[event.dpid]= event.stats.packet_count
    print "Switch: ", event.dpid, "Packet count: ", event.stats.packet_count, "Flow count: ", event.stats.flow_count


def link_event(event):
    global link_list
    link_list = core.openflow_discovery.adjacency

    if event.added:
        adjacency[event.link.dpid1][event.link.dpid2] = event.link.port1
        #Removes the rules from the switch. Forces the packet to the controller and new shortest path is generated
        msg = of.ofp_flow_mod()
        msg.command = 0x0003
        for sw in sw_con:       #Removes all rules on switch.
            if event.link.dpid1 == sw.connection.dpid:
                sw.connection.send(msg)
            elif event.link.dpid1 == sw.connection.dpid:
                sw.connection.send(msg)


    if event.removed:
    #If a link goes down
        del adjacency[event.link.dpid1][event.link.dpid2]
        #Removes the rules from the switch. Forces the packet to the controller and new shortest path is generated
        msg = of.ofp_flow_mod()
        msg.command = 0x0003
        for sw in sw_con:
            if event.link.dpid1 == sw.connection.dpid:
                sw.connection.send(msg)
            elif event.link.dpid1 == sw.connection.dpid:
                sw.connection.send(msg)


def _handle_PacketIn(event):
    packet = event.parsed
    src = table.get(packet.src)
    dst = table.get(packet.dst)

    if (src and dst) is not None:

        policy(src, dst, packet.src, packet.dst)
        return

    else:
    #If src not in table - save it (initiating switch)
        if table.get(packet.src) is None:
            table[packet.src] = event.connection.dpid
            mactable[packet.src] = event.port


    #If dst not in table - broadcast it to make it respond to ARP
        elif table.get(packet.dst) is None:
            msg = of.ofp_packet_out(data = event.ofp)
            msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))      #flood to all except input port
            event.connection.send(msg)
            #print "Broadcast from: ", packet.src, " on port: ", event.port, "want to connect to: ", packet.dst



def policy(src_dpid, dst_dpid, src_adr, dst_adr):
#Get statistics from all intermeadiate swiches. Use the switch with least packet counts and feed it to Bellman Ford.
# #If not the total path is found, add another switch to the list and try again.

    del routes[:]
    adjpolicy.clear()
    sorted_path = sorted(path.items(), key=operator.itemgetter(1))  #Sorts the nodes acourding to least used
    routes.append(src_dpid)
    routes.append(dst_dpid)

    for key, value in sorted_path:                                  #Adds the least used nodes in a list. Tries BF to final path is found
        if key != src_dpid and key != dst_dpid:
            #print "Swich added to path:", key
            routes.append(key)
            for m in routes:
                for n in routes:
                    if adjacency[m][n] != None:
                        adjpolicy[m][n] = adjacency[m][n]

        r = bellman(src_dpid,dst_dpid)
        #First when BF returns a full path, then we create the rules
        if src_dpid in r and dst_dpid in r:
            #Sort path, rules should be installed backwards on the switches in path
            if r[0] == src_dpid:
                r = r[::-1]
            generate_Flows(r, src_adr, dst_adr)
            print "Flow path generated: ", r
            return


    else:
        print "No path between switch: ", dst_dpid, " and switch: ", src_dpid


def _on_timer():
    path.clear()
    for n in sw_con:
        n.connection.send(of.ofp_stats_request(body=of.ofp_aggregate_stats_request()))


def launch():
    from pox.openflow.discovery import launch
    launch()

    from pox.openflow.spanning_tree import launch
    launch()

    core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
    core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
    core.openflow_discovery.addListenerByName("LinkEvent", link_event)
    core.openflow.addListenerByName("AggregateFlowStatsReceived", _handle_aggregate)
    Timer(10, _on_timer, recurring=True)