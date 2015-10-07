from pox.core import core
from collections import defaultdict
from pox.lib.recoco import Timer
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, EthAddr

link_list = []
switches = []
sw_con = []
adjacency = defaultdict(lambda:defaultdict(lambda:None))
adjpolicy = defaultdict(lambda:defaultdict(lambda:None))
table = {}
mactable = {}
log = core.getLogger()

def bellman(src_dpid, dst_dpid):
    # Bellman is the function that finds the shortest path between switches
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
        print "Shortest path found: ",r
        return r

    except KeyError:
        print "Error! Invalid path. Check policy"
        return False


def generate_Flows(path, src_adr, dst_adr):

    for m in range(len(path)):      #Iterate over total path

        for switch in sw_con:

            if len(path) == 1:

                if switch.dpid == table.get(src_adr):  # Applying local switch rules on initiating
                    msg = of.ofp_flow_mod()
                    msg.match.dl_dst = src_adr
                    msg.match.dl_src = dst_adr
                    msg.actions.append(of.ofp_action_output(port=mactable.get(src_adr)))
                    switch.connection.send(msg)

                if switch.dpid == table.get(dst_adr):  # Applying local switch rules on initiating switch (if hosts located at same switch)
                    msg = of.ofp_flow_mod()
                    msg.match.dl_dst = dst_adr
                    msg.match.dl_src = src_adr
                    msg.actions.append(of.ofp_action_output(port=mactable.get(dst_adr)))
                    switch.connection.send(msg)
                    return

            else:

                try:
                    if switch.dpid == path[m+1]:
                        swobj2 = switch
                    if switch.dpid == path[m]:
                        swobj1 = switch
                except IndexError:
                    break


        try:
            if swobj1.dpid == table.get(src_adr): #Applying local switch rules on initiating
                msg = of.ofp_flow_mod()
                msg.match.dl_dst = src_adr
                msg.match.dl_src = dst_adr
                msg.actions.append(of.ofp_action_output(port=mactable.get(src_adr)))
                swobj1.connection.send(msg)

            if swobj2.dpid == table.get(dst_adr): #Applying local switch rules on dest switch
                msg = of.ofp_flow_mod()
                msg.match.dl_dst = dst_adr
                msg.match.dl_src = src_adr
                msg.actions.append(of.ofp_action_output(port=mactable.get(dst_adr)))
                swobj2.connection.send(msg)

            for links in link_list:
                # Finds the links
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


def link_event(event):
    global link_list
    link_list = core.openflow_discovery.adjacency
    adjacency[event.link.dpid1][event.link.dpid2] = event.link.port1


def _handle_PacketIn(event):
    packet = event.parsed
    src = table.get(packet.src)
    dst = table.get(packet.dst)

    for m in table:
        print "MAC's in table: ",m


    if (src and dst) is not None:

        policy(src, dst, packet.src, packet.dst)
        return

    else:
    # If src not in table - save it (initiating switch)
        if table.get(packet.src) is None:
            table[packet.src] = event.connection.dpid
            mactable[packet.src] = event.port


    # If dst not in table - broadcast it to make it respond to ARP
        elif table.get(packet.dst) is None:
            msg = of.ofp_packet_out(data = event.ofp)
            msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))      #flood to all except input port
            event.connection.send(msg)
            print "Broadcast from: ", packet.src, " on port: ", event.port, "want to connect to: ", packet.dst




def policy(src_dpid, dst_dpid, src_adr, dst_adr):
    #Policy to force bellman to use these links
    adjpolicy.clear()

    #Policy: Force total route
    # Add source and dest and prefered route
    ###########################################################################
    if src_adr == EthAddr("0f:12:33:2f:6a:19") and dst_adr == EthAddr("9e:2e:6b:0f:25:91"):
        route = [1, 2, 4, 5]
        if src_dpid and dst_dpid in route:
            for m in route:
                for n in route:
                    if adjacency[m][n] != None:
                        adjpolicy[m][n] = adjacency[m][n]
                        print m, n
            r = bellman(src_dpid,dst_dpid)
            generate_Flows(r, src_adr, dst_adr)
        else:
            print "Error applying rule"


    #Policy: Force through GW
    # Add source and dest and preferred switches to route the traffic through
    #Use bellman source - switch and switch - dest
    #TODO: Add for more switches
    ###########################################################################
    if src_adr == EthAddr("9e:12:33:2f:6a:19") and dst_adr == EthAddr("9e:2e:6b:0f:25:91"):
        route = [4]
        print "ROUTE[0] = ", route[0]
        if len(route) == 1:
            for m in adjacency:
                for n in adjacency:
                    adjpolicy[m][n] = adjacency[m][n]
            sw = bellman(src_dpid, route[0])
            dw = bellman(route[0], dst_dpid)
            generate_Flows((sw+dw), src_adr, dst_adr)

        else:
            print "Error appyling rule"



    else:
        adjpolicy.clear()
        for m in adjacency:
            for n in adjacency:
                adjpolicy[m][n] = adjacency[m][n]

        r = bellman(src_dpid,dst_dpid)
        try:
            generate_Flows(r, src_adr, dst_adr)
        except ReferenceError:
            print "Policy could not be applied!"
        print "No policy found, generating shortest path!"



#Use bellman not to generate rules, but to find shortest path.








    #Policy: Prefered route
    # Vertex = how much a route is worth.
    ############################################################################
    #if src_adr == EthAddr("9e:12:33:2f:6a:19") and dst_adr == EthAddr("9e:2e:6b:0f:25:91"):
        #route = [1, 2, 4, 5]





def launch():
    from pox.openflow.discovery import launch
    launch()

    from pox.openflow.spanning_tree import launch
    launch()

    core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
    core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
    core.openflow_discovery.addListenerByName("LinkEvent", link_event)

    #Include spanning-tree?