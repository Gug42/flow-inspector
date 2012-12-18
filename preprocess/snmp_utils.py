#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Node(object):
    
    """ The base class for all nodes """

    def __init__(self, ip, netmask = "/32", reason_creation = ""):
        self.ip = ip
        self.netmask = netmask
        self.successors = set()
        self.reason_creation = str(reason_creation)
   
    def toGML(self):
        return '    <node id="{0}"></node>'.format(self.getID())   

    def getID(self):
        return str(self.ip) + "/" + str(self.netmask) 

    def getLabel(self):
        return str(self.ip) + "/" + str(self.netmask)


class Router(Node):

    """ This class represents a router """

    def __init__(self, ip):
        super(Router, self).__init__(ip)

    def toGML(self):
        return '\n'.join([  '    <node id="{0}">',
                            '      <data key="r">255</data>',
                            '      <data key="label">{1}</data>',
                            '      <date key="z">10</date>',
                            '    </node>']).format(self.getID(), self.getLabel())

    def getID(self):
        return "router_" + str(self.ip) + "/32"

    def getLabel(self):
        return "Router " + str(self.ip)


class Interface(Node):

    """ This class represents a router interface """

    def __init__(self, ip, netmask, ifnumber, description, router, reason_creation):
        super(Interface, self).__init__(ip)
        self.ifnumber = ifnumber
        self.netmask = netmask
        self.router = router
        self.description = description
        self.reason_creation = reason_creation

    def toGML(self):
        return '\n'.join([  '    <node id="{0}">',
                            '      <data key="g">255</data>',
                            '      <data key="label">{1}</data>',
                            '    </node>']).format(self.getID(), self.getLabel())

    def getID(self):
        return str(self.router.ip + "_" + self.ifnumber + "_" + self.ip)
   
    def getLabel(self):
        return str(self.description) + "_" + str(self.ifnumber) + "_" + str(self.ip) + "/" + str(self.netmask)

    def __str__(self):
        return "Interface " + self.router.ip + "_" + self.ifnumber + "_" + self.ip + "/" + self.netmask + "; " + reason_creation
        

class Subnet(Node):
    
    """ This class represents a subnet """ 
    
    def __init__(self, ip, netmask, reason_creation):
        super(Subnet, self).__init__(ip, netmask)
        self.reason_creation = reason_creation 

    def toGML(self):
        return '\n'.join([  '    <node id="{0}">',
                            '      <data key="b">255</data>',
                            '      <data key="label">{1}</data>',
                            '    </node>']).format(self.getID(), self.getLabel())

    def getID(self):
        return str(self.ip) + "/" + str(self.netmask)
    
    def getLabel(self):
        return str(self.ip) + "/" + str(self.netmask)


class Graph(object): 

    """ This class represents a graph containing nodes """

    def __init__(self):
        """ Instanciate new Graph object """
        self.db = {
            "Node": dict(),
            "Router": dict(),
            "Interface": dict(),
            "Subnet": dict()
        }
        self.all_nodes = list()

    def __str__(self):
        return "\n".join([
            "Node: " + str(self.db["Node"]),
            "Router: " + str(self.db["Router"]),
            "Interface: " + str(self.db["Interface"]),
            "Subnet: " + str(self.db["Subnet"]) 
        ])
    
    def isNode(self, ip, netmask = 32):
        return str(ip) + "/" + str(netmask) in self.db["Node"]

    def getNode(self, ip, netmask = 32, reason_creation = ""):
        if not self.isNode(str(ip) + "/" + str(netmask)):
            self.addNode(ip, netmask, reason_creation)
        return self.db["Node"][str(ip) + "/" + str(netmask)]

    def addNode(self, ip, netmask = 32, reason_create = ""):
        node = Node(ip, netmask, reason_create)
        self.db["Node"][str(ip) + "/" + str(netmask)] = node
        self.all_nodes.append(node)

    def isRouter(self, ip):
        return str(ip) + "/32" in self.db["Router"]

    def getRouter(self, ip):
        if not self.isRouter(ip):
            self.addRouter(ip)
        return self.db["Router"][str(ip) + "/32"]

    def addRouter(self, ip):
        router = Router(ip)
        self.db["Router"][str(ip) + "/32"] = router
        self.all_nodes.append(router)

    def isInterface(self, router_ip, interface_ip):
        return str(router_ip) + "_" + str(interface_ip) in self.db["Interface"]

    def getInterfaceByIP(self, router_ip, interface_ip, reason_creation = ""):
        if not self.isInterface(router_ip, interface_ip):
            self.addInterface(router_ip, interface_ip, "", "", "", "interface missing")
            print "!!! Interface missing !!!"
        return self.db["Interface"][str(router_ip) + "_" + str(interface_ip)]

    def getInterfaceByNumber(self, router_ip, interface_number, reason_creation = ""):
        for interface in self.db["Interface"].itervalues():
            if interface.router.ip == router_ip and interface.ifnumber == interface_number:
                return interface
        interface = self.addInterface(router_ip, "???", "???", "", interface_number)
        print "!!! Interface missing 222 !!!"
        return interface


    def addInterface(self, router_ip, interface_ip, interface_netmask, interface_number, interface_description, reason_creation):
        
        # Check whether interface already exists
        if not self.isInterface(router_ip, interface_ip):

            router = self.getRouter(router_ip)

            # Check whether a generic node with this ip exists
            if str(interface_ip) + "/32" in self.db["Node"] and (self.db["Node"][str(interface_ip) + "/32"].__class__ == Node) :
                # change existing node to type Interface
                interface = self.db["Node"][str(interface_ip) + "/32"]
                interface.__class__ = Interface
                interface.netmask = interface_netmask
                interface.ifnumber = interface_number
                interface.router = router
                interface.description = interface_description
                interface.reason_creation += "\n" + reason_creation
            else:
                # create new Interface node
                interface = Interface(interface_ip, interface_netmask, interface_number, interface_description, self.getRouter(router_ip), reason_creation)
                self.db["Node"][str(interface_ip) + "/32"] = interface
        
            self.db["Interface"][str(router_ip) + "_" + str(interface_ip)] = interface
            router.successors.add(interface)
            self.all_nodes.append(interface)
        return interface

    def isSubnet(self, ip, netmask):
        return str(ip) + "/" + str(netmask) in self.db["Subnet"]

    def addSubnet(self, ip, netmask, reason_creation = ""):
        if not self.isSubnet(ip, netmask):
            subnet = Subnet(ip, netmask, reason_creation)
            self.db["Subnet"][str(ip) + "/" + str(netmask)] = subnet
            self.db["Node"][str(ip) + "/" + str(netmask)] = subnet
            self.all_nodes.append(subnet)

    def getSubnet(self, ip, netmask, reason_creation = ""):
        if not self.isSubnet(ip, netmask):
            self.addSubnet(ip, netmask)
        return self.db["Subnet"][str(ip) + "/" + str(netmask)]

    def addConnectedSubnet(self, router_ip, interface_ip, subnet_ip, subnet_mask, reason_creation = ""):
        interface = self.getInterfaceByIP(router_ip, interface_ip, reason_creation)
        subnet = self.getSubnet(subnet_ip, subnet_mask, reason_creation)
        interface.successors.add(subnet)

    def addConnectedSubnetByNumber(self, router_ip, interface_number, subnet_ip, subnet_mask, reason_creation = ""):
        interface = self.getInterfaceByNumber(router_ip, interface_number, reason_creation)
        subnet = self.getSubnet(subnet_ip, subnet_mask, reason_creation)
        interface.successors.add(subnet)

    def addRoute_If2Node(self, router_ip, interface_number, nexthop_ip, reason_creation):
        node = self.getNode(nexthop_ip, 32, reason_creation)
        interface = self.getInterfaceByIP(router_ip, interface_number)
        interface.successors.add(node)
    
    def addRoute_Node2Node(self, ip_a, netmask_a, ip_b, netmask_b):
        node_a = self.getNode(ip_a, netmask_a)
        node_b = self.getNode(ip_b, netmask_b)
        node_a.successors.add(node_b)


        


XMLHEADER = '\n'.join([
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<graphml xmlns="http://graphml.graphdrawing.org/xmlns" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
    'xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns '
    'http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">',
    '  <graph id="g1" edgedefault="directed">',  
    '    <key attr.name="label" attr.type="string" for="node" id="label"/>',
    '    <key attr.name="Edge Label" attr.type="string" for="edge" id="edgelabel"/>',
    '    <key attr.name="weight" attr.type="double" for="edge" id="weight"/>',
    '    <key attr.name="Edge Id" attr.type="string" for="edge" id="edgeid"/>',
    '    <key attr.name="r" attr.type="int" for="node" id="r"/>',
    '    <key attr.name="g" attr.type="int" for="node" id="g"/>',
    '    <key attr.name="b" attr.type="int" for="node" id="b"/>',
    '    <key attr.name="x" attr.type="float" for="node" id="x"/>',
    '    <key attr.name="y" attr.type="float" for="node" id="y"/>',
    '    <key attr.name="z" attr.type="float" for="node" id="z"/>'
    '    <key attr.name="size" attr.type="float" for="node" id="size"/>'
])

XMLFOOTER = '\n'.join([
    '  </graph>',
    '</graphml>',
])

EDGE_TEMPLATE = '<edge id="e{0}" source="{1}" target="{2}"/>'

def graph_to_graphmlfile(graph, outputfile):
    """Export the graph into a graphml file"""
    # utf-8 encoding is default to my knowledge (see pep-3120)
    handle = open(outputfile, 'w')
    handle.write(XMLHEADER)
    handle.write('\n')
    indent = 4 * ' '

    # write nodes first (otherwise gephi complains)
    for node in graph.all_nodes:
        #handle.write(indent)
        handle.write(node.toGML())
        handle.write('\n')

    # write edges
    edge_id = 0
    for node in graph.all_nodes:
        for dst in node.successors:
            handle.write(indent)
            handle.write(EDGE_TEMPLATE.format(edge_id, node.getID(), dst.getID()))
            handle.write('\n')
            edge_id += 1
    handle.write(XMLFOOTER)
    handle.close()
