from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.recoco import Timer
nodes = []

def _handle_ConnectionUp(event):
    print "Switch with DPIPD: ", event.dpid, " connected!"
    nodes.append(event)
    for m in event.connection.features.ports:
        port_speed(event, m.port_no, m.hw_addr)


def timer_func():
    for n in nodes:
        core.openflow.getConnection(n.connection.dpid).send(of.ofp_features_request())


def _handle_features_reply(event):
    for m in event.connection.features.ports:
        print "Features request: ", m.name,m.port_no,m.hw_addr,m.curr,m.advertised,m.supported,m.peer,m.config,m.state


def port_speed(event, port, hw):
    msg = of.ofp_port_mod()
    msg.port_no = port
    msg.hw_addr = hw
    msg.advertise = of.OFPPF_10GB_FD
    event.connection.send(msg)
    print "Modified!"


core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
core.openflow.addListenerByName("FeaturesReceived", _handle_features_reply)
Timer(10, timer_func, recurring=True)


#Does not work!