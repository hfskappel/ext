    # If dst not in table - broadcast it to make it respond to ARP
        #elif table.get(packet.dst) is None:
        #    msg = of.ofp_packet_out(data = event.ofp)
        #    msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))      #flood to all except input port
        #    event.connection.send(msg)
            #print "Broadcast from: ", packet.src, " on port: ", event.port, "want to connect to: ", packet.dst

        #Testing new way to ARP
        elif table.get(packet.dst) is None:
            switchports = []
            for m in sw_con:
                for n in m.connection.features.ports:
                    for link in link_list:
                        if link.dpid1 == m.connection.dpid:
                            switchports.append(link.port1)

                    if n.port_no not in switchports and n.port_no != 65534:
                        print "FUNNET LINKPORT: ", n.port_no
                        print "EVENT:", event.ofp
                        msg = of.ofp_packet_out(data = event.ofp)
                        msg.buffer_id = 1
                        msg.actions.append(of.ofp_action_output(port = n.port_no))      #Send out port
                        m.connection.send(msg)
                del switchports[:]


# Works with iterating over every switches in the network and removing switchlinks.
#Tries to send out the broadcast on single ports, linkports, but it seems to be a problem with the buffer
#Use this in master theisis


    adjpolicy.clear()
    chosenports = {}

    #Shortest path over least loaded links
    #rangere etter korteste links
    #pr0ve BF nedover til det gAr

    #sjekke mot link list

    for e in ports:
        #Find least used port on first node
        for p in e.stats:
            if e.connection.dpid == src_dpid:
                for link in link_list:
                   if e.connection.dpid == link.dpid1 and p.port_no == link.port1:
                       print "Switchlink funnet"
                        chosenports =





                print p.port_no, p.tx_packets, p.rx_packets


#Metric reguleres ihht delay eller tap







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
















