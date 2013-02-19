#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path
import argparse
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
import common
import backend
import config

from common_functions import *

parser = argparse.ArgumentParser(description="Preprocess SNMP data")
parser.add_argument(
	"file", nargs="*", help="File to parse")
parser.add_argument(
	"--dst-host", nargs="?", default=config.data_backend_host,
	help="Backend database host")
parser.add_argument(
	"--dst-port", nargs="?", default=config.data_backend_port,
	type=int, help="Backend database port")
parser.add_argument(
	"--dst-user", nargs="?", default=config.data_backend_user,
	help="Backend database user")
parser.add_argument(
	"--dst-password", nargs="?",
	default=config.data_backend_password, help="Backend database password")
parser.add_argument(
	"--dst-database", nargs="?",
	default=config.data_backend_snmp_name, help="Backend database name")
parser.add_argument(
	"--clear-database", nargs="?", type=bool, default=False, const=True,
	help="Whether to clear the whole databse before importing any flows.")
parser.add_argument(
	"--backend", nargs="?", default=config.data_backend, const=True,
	help="Selects the backend type that is used to store the data")

args = parser.parse_args()

dst_db = backend.databackend.getBackendObject(
	args.backend, args.dst_host, args.dst_port,
	args.dst_user, args.dst_password, args.dst_database)

if args.clear_database:
	dst_db.clearDatabase()

# dictionary which maps oid -> name and fct to parse oid value
oidmap = {
	".1.3.6.1.2.1.2.2.1.1":
	{"name": "ifIndex", "fct": plain},
	".1.3.6.1.2.1.2.2.1.2":
	{"name": "ifDescr", "fct": plain},
	".1.3.6.1.2.1.2.2.1.3":
	{"name": "ifType", "fct": plain},
	".1.3.6.1.2.1.2.2.1.4":
	{"name": "ifMtu", "fct": plain},
	".1.3.6.1.2.1.2.2.1.5":
	{"name": "ifSpeed", "fct": plain},
	".1.3.6.1.2.1.2.2.1.6":
	{"name": "ifPhysAddress", "fct": plain},
	".1.3.6.1.2.1.2.2.1.7":
	{"name": "ifAdminStatus", "fct": plain},
	".1.3.6.1.2.1.2.2.1.8":
	{"name": "ifOperStatus", "fct": plain},
	".1.3.6.1.2.1.2.2.1.9":
	{"name": "ifLastChange", "fct": plain},
	".1.3.6.1.2.1.2.2.1.10":
	{"name": "ifInOctets", "fct": plain},
	".1.3.6.1.2.1.2.2.1.11":
	{"name": "ifInUcastPkts", "fct": plain},
	".1.3.6.1.2.1.2.2.1.12":
	{"name": "ifInNUcastPkts", "fct": plain},
	".1.3.6.1.2.1.2.2.1.13":
	{"name": "ifInDiscards", "fct": plain},
	".1.3.6.1.2.1.2.2.1.14":
	{"name": "ifInErrors", "fct": plain},
	".1.3.6.1.2.1.2.2.1.15":
	{"name": "ifInUnknownProtos", "fct": plain},
	".1.3.6.1.2.1.2.2.1.16":
	{"name": "ifOutOctets", "fct": plain},
	".1.3.6.1.2.1.2.2.1.17":
	{"name": "ifOutUcastPkts", "fct": plain},
	".1.3.6.1.2.1.2.2.1.18":
	{"name": "ifOutNUcastPkts", "fct": plain},
	".1.3.6.1.2.1.2.2.1.19":
	{"name": "ifOutDiscards", "fct": plain},
	".1.3.6.1.2.1.2.2.1.20":
	{"name": "ifOutErrors", "fct": plain},
	".1.3.6.1.2.1.2.2.1.21":
	{"name": "ifOutQLen", "fct": plain},
	".1.3.6.1.2.1.2.2.1.22":
	{"name": "ifSpecific", "fct": plain},
	".1.3.6.1.2.1.4.20.1.1":
	{"name": "ipAdEntAddr", "fct": ip2int},
	".1.3.6.1.2.1.4.20.1.2":
	{"name": "ipAdEntIfIndex", "fct": plain},
	".1.3.6.1.2.1.4.20.1.3":
	{"name": "ipAdEntNetMask", "fct": netmask2int},
	".1.3.6.1.2.1.4.20.1.4":
	{"name": "ipAdEntBcastAddr", "fct": plain},
	".1.3.6.1.2.1.4.20.1.5":
	{"name": "ipAdEntReasmMaxSize", "fct": plain},
	".1.3.6.1.2.1.4.21.1.1":
	{"name": "ipRouteDest", "fct": ip2int},
	".1.3.6.1.2.1.4.21.1.2":
	{"name": "ipRouteIfIndex", "fct": plain},
	".1.3.6.1.2.1.4.21.1.3":
	{"name": "ipRouteMetric1", "fct": plain},
	".1.3.6.1.2.1.4.21.1.4":
	{"name": "ipRouteMetric2", "fct": plain},
	".1.3.6.1.2.1.4.21.1.5":
	{"name": "ipRouteMetric3", "fct": plain},
	".1.3.6.1.2.1.4.21.1.6":
	{"name": "ipRouteMetric4", "fct": plain},
	".1.3.6.1.2.1.4.21.1.7":
	{"name": "ipRouteNextHop", "fct": ip2int},
	".1.3.6.1.2.1.4.21.1.8":
	{"name": "ipRouteType", "fct": plain},
	".1.3.6.1.2.1.4.21.1.9":
	{"name": "ipRouteProto", "fct": plain},
	".1.3.6.1.2.1.4.21.1.10":
	{"name": "ipRouteAge", "fct": plain},
	".1.3.6.1.2.1.4.21.1.11":
	{"name": "ipRouteMask", "fct": netmask2int},
	".1.3.6.1.2.1.4.21.1.12":
	{"name": "ipRouteMetric5", "fct": plain},
	".1.3.6.1.2.1.4.21.1.13":
	{"name": "ipRouteInfo", "fct": plain},
	".1.3.6.1.4.1.9.9.449.1.3.1.1.1":
	{"name": "cEigrpDestNetType", "fct": plain},
	".1.3.6.1.4.1.9.9.449.1.3.1.1.2":
	{"name": "cEigrpDestNet", "fct": ip2int},
	".1.3.6.1.4.1.9.9.449.1.3.1.1.3":
	{"name": "cEigrpDestNetPrefixLen", "fct": plain},
	".1.3.6.1.4.1.9.9.449.1.3.1.1.4":
	{"name": "cEigrpDestNetPrefixLen", "fct": plain},
	".1.3.6.1.4.1.9.9.449.1.3.1.1.5":
	{"name": "cEigrpActive", "fct": plain},
	".1.3.6.1.4.1.9.9.449.1.3.1.1.6":
	{"name": "cEigrpStuckInActive", "fct": plain},
	".1.3.6.1.4.1.9.9.449.1.3.1.1.7":
	{"name": "cEigrpDestSuccessors", "fct": plain},
	".1.3.6.1.4.1.9.9.449.1.3.1.1.8":
	{"name": "cEigrpFdistance", "fct": plain},
	".1.3.6.1.4.1.9.9.449.1.3.1.1.9":
	{"name": "cEigrpRouteOriginType", "fct": plain},
	".1.3.6.1.4.1.9.9.449.1.3.1.1.10":
	{"name": "cEigrpRouteOriginAddrType", "fct": plain},
	".1.3.6.1.4.1.9.9.449.1.3.1.1.11":
	{"name": "cEigrpRouteOriginAddr", "fct": hex2ip2int},
	".1.3.6.1.4.1.9.9.449.1.3.1.1.12":
	{"name": "cEigrpNextHopAddressType", "fct": plain},
	".1.3.6.1.4.1.9.9.449.1.3.1.1.13":
	{"name": "cEigrpNextHopAddress", "fct": hex2ip2int},
	".1.3.6.1.4.1.9.9.449.1.3.1.1.14":
	{"name": "cEigrpNextHopInterface", "fct": plain},
	".1.3.6.1.4.1.9.9.449.1.3.1.1.15":
	{"name": "cEigrpDistance", "fct": plain},
	".1.3.6.1.4.1.9.9.449.1.3.1.1.16":
	{"name": "cEigrpReportDistance", "fct": plain},
	".1.3.6.1.2.1.4.24.4.1.1":
	{"name": "ipCidrRouteDest", "fct": ip2int},
	".1.3.6.1.2.1.4.24.4.1.2":
	{"name": "ipCidrRouteMask", "fct": netmask2int},
	".1.3.6.1.2.1.4.24.4.1.3":
	{"name": "ipCidrRouteTos", "fct": plain},
	".1.3.6.1.2.1.4.24.4.1.4":
	{"name": "ipCidrRouteNextHop", "fct": ip2int},
	".1.3.6.1.2.1.4.24.4.1.5":
	{"name": "ipCidrRouteIfIndex", "fct": plain},
	".1.3.6.1.2.1.4.24.4.1.6":
	{"name": "ipCidrRouteType", "fct": plain},
	".1.3.6.1.2.1.4.24.4.1.7":
	{"name": "ipCidrRouteProto", "fct": plain},
	".1.3.6.1.2.1.4.24.4.1.8":
	{"name": "ipCidrRouteAge", "fct": plain},
	".1.3.6.1.2.1.4.24.4.1.9":
	{"name": "ipCidrRouteInfo", "fct": plain},
	".1.3.6.1.2.1.4.24.4.1.10":
	{"name": "ipCidrRouteNextHopAS", "fct": plain},
	".1.3.6.1.2.1.4.24.4.1.11":
	{"name": "ipCidrRouteMetric1", "fct": plain},
	".1.3.6.1.2.1.4.24.4.1.12":
	{"name": "ipCidrRouteMetric2", "fct": plain},
	".1.3.6.1.2.1.4.24.4.1.13":
	{"name": "ipCidrRouteMetric3", "fct": plain},
	".1.3.6.1.2.1.4.24.4.1.14":
	{"name": "ipCidrRouteMetric4", "fct": plain},
	".1.3.6.1.2.1.4.24.4.1.15":
	{"name": "ipCidrRouteMetric5", "fct": plain},
	".1.3.6.1.2.1.4.24.4.1.16":
	{"name": "ipCidrRouteStatus", "fct": plain}
}

fieldDict = {
	"interface_phy": {
		"_id": ("BIGINT", "PRIMARY", "AUTO_INCREMENT"),
		"timestamp": ("BIGINT UNSIGNED", None, None),
		"router": ("VARCHAR(15)", None, None),
		"if_number": ("INT", None, None),
		"ifIndex": ("INT", None, None),
		"ifDescr": ("VARCHAR(100)", None, None),
		"ifType": ("INT", None, None),
		"ifMtu": ("INT", None, None),
		"ifSpeed": ("INT UNSIGNED", None, None),
		"ifPhysAddress": ("VARCHAR(100)", None, None),
		"ifAdminStatus": ("INT", None, None),
		"ifOperStatus": ("INT", None, None),
		"ifLastChange": ("VARCHAR(100)", None, None),
		"ifInOctets": ("INT UNSIGNED", None, None),
		"ifInUcastPkts": ("INT UNSIGNED", None, None),
		"ifInNUcastPkts": ("INT UNSIGNED", None, None),
		"ifInDiscards": ("INT", None, None),
		"ifInErrors": ("INT", None, None),
		"ifInUnknownProtos": ("INT UNSIGNED", None, None),
		"ifOutOctets": ("INT UNSIGNED", None, None),
		"ifOutUcastPkts": ("INT UNSIGNED", None, None),
		"ifOutNUcastPkts": ("INT UNSIGNED", None, None),
		"ifOutDiscards": ("BIGINT", None, None),
		"ifOutErrors": ("INT", None, None),
		"ifOutQLen": ("INT", None, None),
		"ifSpecific": ("VARCHAR(100)", None, None),
		"index_preprocess": ("UNIQUE INDEX", "router ASC, if_number ASC, timestamp ASC"),
		"table_options": "ENGINE=MyISAM ROW_FORMAT=FIXED"
	},

	"interface_log": {
		"_id": ("BIGINT", "PRIMARY", "AUTO_INCREMENT"),
		"timestamp": ("BIGINT UNSIGNED", None, None),
		"router": ("VARCHAR(15)", None, None),
		"if_ip": ("INT UNSIGNED", None, None),
		"ipAdEntAddr": ("INT UNSIGNED", None, None),
		"ipAdEntIfIndex": ("INT", None, None),
		"ipAdEntNetMask": ("TINYINT", None, None),
		"ipAdEntBcastAddr": ("INT", None, None),
		"ipAdEntReasmMaxSize": ("INT", None, None),
		"index_preprocess": ("UNIQUE INDEX", "router ASC, if_ip ASC, timestamp ASC"),
		"index_findRoute": ("INDEX", "timestamp, ipAdEntAddr"),
		"table_options": "ENGINE=MyISAM ROW_FORMAT=FIXED"
	},
		
	"ipRoute": {
		"_id": ("BIGINT", "PRIMARY", "AUTO_INCREMENT"),
		"timestamp": ("VARCHAR(100)", None, None),
		"ip_src": ("VARCHAR(100)", None, None),
		"ip_dst": ("VARCHAR(100)", None, None),
		"low_ip": ("VARCHAR(100)", None, None),
		"high_ip": ("VARCHAR(100)", None, None),
		"ipRouteDest": ("VARCHAR(100)", None, None),
		"ipRouteIfIndex": ("VARCHAR(100)", None, None),
		"ipRouteMetric1": ("VARCHAR(100)", None, None),
		"ipRouteMetric2": ("VARCHAR(100)", None, None),
		"ipRouteMetric3": ("VARCHAR(100)", None, None),
		"ipRouteMetric4": ("VARCHAR(100)", None, None),
		"ipRouteMetric5": ("VARCHAR(100)", None, None),
		"ipRouteNextHop": ("VARCHAR(100)", None, None),
		"ipRouteProto": ("VARCHAR(100)", None, None),
		"ipRouteAge": ("VARCHAR(100)", None, None),
		"ipRouteMask": ("VARCHAR(100)", None, None),
		"ipRouteInfo": ("VARCHAR(100)", None, None),
		"index_preprocess": ("UNIQUE INDEX", "ip_src ASC, ip_dst ASC, timestamp ASC"),
		"table_options": "ENGINE=MyISAM ROW_FORMAT=FIXED"
	},
		
	"cEigrp": {
		"_id": ("BIGINT", "PRIMARY", "AUTO_INCREMENT"),
		"timestamp": ("BIGINT UNSIGNED", None, None),
		"ip_src": ("INT UNSIGNED", None, None),
		"ip_dst": ("INT UNSIGNED", None, None),
		"mask_dst": ("TINYINT", None, None),
		"low_ip": ("INT UNSIGNED", None, None),
        "high_ip": ("INT UNSIGNED", None, None),
		"cEigrpDestNetType": ("VARCHAR(100)", None, None),
		"cEigrpDestNet": ("VARCHAR(100)", None, None),
		"cEigrpDestNetPrefixLen": ("VARCHAR(100)", None, None),
		"cEigrpActive": ("VARCHAR(100)", None, None),
		"cEigrpStuckInActive": ("VARCHAR(100)", None, None),
		"cEigrpDestSuccessors": ("VARCHAR(100)", None, None),
		"cEigrpFdistance": ("VARCHAR(100)", None, None),
		"cEigrpRouteOriginType": ("VARCHAR(100)", None, None),
		"cEigrpRouteOriginAddrType": ("VARCHAR(100)", None, None),
		"cEigrpRouteOriginAddr": ("VARCHAR(100)", None, None),
		"cEigrpNextHopAddressType": ("VARCHAR(100)", None, None),
		"cEigrpNextHopAddress": ("VARCHAR(100)", None, None),
		"cEigrpNextHopInterface": ("VARCHAR(100)", None, None),
		"cEigrpDistance": ("VARCHAR(100)", None, None),
		"cEigrpReportDistance": ("VARCHAR(100)", None, None),
		"index_preprocess": ("UNIQUE INDEX", "ip_src ASC, ip_dst ASC, mask_dst ASC, timestamp ASC"),
		"table_options": "ENGINE=MyISAM ROW_FORMAT=FIXED"
	},
		
	"ipCidrRoute": {
		"_id": ("BIGINT", "PRIMARY", "AUTO_INCREMENT"),
		"timestamp": ("BIGINT UNSIGNED", None, None),
		"ip_src": ("INT UNSIGNED", None, None),
		"ip_dst": ("INT UNSIGNED", None, None),
		"mask_dst": ("TINYINT", None, None),
		"ip_gtw": ("INT UNSIGNED", None, None),
		"low_ip": ("INT UNSIGNED", None, None),
        "high_ip": ("INT UNSIGNED", None, None),
		"ipCidrRouteDest": ("VARCHAR(100)", None, None),
		"ipCidrRouteMask": ("VARCHAR(100)", None, None),
		"ipCidrRouteTos": ("VARCHAR(100)", None, None),
		"ipCidrRouteNextHop": ("VARCHAR(100)", None, None),
		"ipCidrRouteIfIndex": ("VARCHAR(100)", None, None),
		"ipCidrRouteType": ("VARCHAR(100)", None, None),
		"ipCidrRouteProto": ("VARCHAR(100)", None, None),
		"ipCidrRouteAge": ("VARCHAR(100)", None, None),
		"ipCidrRouteInfo": ("VARCHAR(100)", None, None),
		"ipCidrRouteNextHopAS": ("VARCHAR(100)", None, None),
		"ipCidrRouteMetric1": ("VARCHAR(100)", None, None),
		"ipCidrRouteMetric2": ("VARCHAR(100)", None, None),
		"ipCidrRouteMetric3": ("VARCHAR(100)", None, None),
		"ipCidrRouteMetric4": ("VARCHAR(100)", None, None),
		"ipCidrRouteMetric5": ("VARCHAR(100)", None, None),
		"ipCidrRouteStatus": ("VARCHAR(100)", None, None),
		"index_preprocess": ("UNIQUE INDEX", "ip_src ASC, ip_dst ASC, ip_gtw ASC, mask_dst ASC, timestamp ASC"),
		"index_findRoute1": ("INDEX", "ipCidrRouteProto, timestamp, low_ip, high_ip"),
		"index_findRoute2": ("INDEX", "timestamp, ip_src, low_ip, high_ip"),
		"table_options": "ENGINE=MyISAM ROW_FORMAT=FIXED"
	}
}

def getFieldDict():
	if args.backend == "mysql":
		return fieldDict
	elif args.backend == "oracle":
		raise Exception("Not yet implemeneted!")
	elif args.backend == "mongo":
		return None
	else:
		raise Exception("Unknown data backend: " + args.backend);

collections = dict()
for name, fields in getFieldDict().items():
	dst_db.prepareCollection(name, fields)
	collections[name] = dst_db.getCollection(name)

# TODO: hacky ... make something more general ...
if backend == "mongo":
	db = pymongo.Connection(args.dst_host, args.dst_port)[args.dst_database]
	collection = db["snmp_raw"]
	collection.ensure_index([("router", pymongo.ASCENDING), ("if_number", pymongo.ASCENDING), ("timestamp", pymongo.ASCENDING), ("type", pymongo.ASCENDING)])
	collection.ensure_index([("router", pymongo.ASCENDING), ("if_ip", pymongo.ASCENDING), ("timestamp", pymongo.ASCENDING), ("type", pymongo.ASCENDING)])
	collection.ensure_index([("ip_src", pymongo.ASCENDING), ("ip_dst", pymongo.ASCENDING), ("timestamp", pymongo.ASCENDING), ("type", pymongo.ASCENDING)])
	collection.ensure_index([("ip_src", pymongo.ASCENDING), ("ip_dst", pymongo.ASCENDING), ("mask_dst", pymongo.ASCENDING), ("ip_gtw", pymongo.ASCENDING), ("timestamp", pymongo.ASCENDING), ("type", pymongo.ASCENDING)])

	# restore generic backend collection
	collection = dst_db.getCollection("snmp_raw")
else: 
#	collection.createIndex("router")
#	collection.createIndex("if_number")
#	collection.createIndex("timestamp")
#	collection.createIndex("type")
#	collection.createIndex("ip_src")
#	collection.createIndex("ip_dst")
	pass

def update_doc(table, table_key, db_key, db_values):
	""" update local document before comitting to databackend """
	if not table in doc:
		doc[table] = dict()
	if table_key in doc[table]:
		doc[table][table_key][1]["$set"].update(db_values)
	else:
		doc[table][table_key] = (db_key, {"$set": db_values})

def commit_doc():
	global doc
	
	time_begin = time.time()
	time_last = time_begin
	time_current = 0
	counter = 0
	total = sum(len(doc[table]) for table in doc)

	print "Commiting %s entries to databackend" % total
	
	for name, table in doc.items():
		for value in table.itervalues():
			collections[name].update(value[0], value[1], True)
			counter = counter + 1
		time_current = time.time()
		if (time_current - time_last > 5):
			print "Processed {0} entries in {1} seconds ({2} entries per second, {3}% done)".format(
				counter, time_current - time_begin,
				counter / (time_current - time_begin), 100.0 * counter / total)
			time_last = time_current 
	doc = {}

# enviromental settings
cache_treshold = 999999

# statistical counters
time_begin = time.time()
time_last = time_begin
counter = 0

# local document storage
doc = {}
lines_since_commit = 0
timestamps = set()

for file in args.file:
	
	# parse file name
	params = os.path.basename(file).rstrip(".txt").split("-")
	source_type = params[0]
	ip_src = params[1]
	timestamp = params[2]
	timestamps.add(timestamp)

#	print "file: %s" % file

	# read and process file contents
	file = open(file, "r")
	for line in file:
		index = line.find(" ")
		value = line[index + 1:]
		value = value.strip("\n")
		value = value.strip('"')
		line = line[0:index]

		# parse interface_phy oid
		if line.startswith(".1.3.6.1.2.1.2.2.1"):
			line = line.split(".")
			oid = '.'.join(line[0:11])
			interface = line[11]

			if oid in oidmap:
				update_doc(
					"interface_phy",
					ip_src + interface + timestamp,
					{"router": ip_src, "if_number": interface,
						"timestamp": timestamp},
					{oidmap[oid]["name"]: oidmap[oid]["fct"](value)}
				)

		# parse interface_log oid
		elif line.startswith(".1.3.6.1.2.1.4.20.1"):
			line = line.split(".")
			oid = '.'.join(line[0:11])
			ip = '.'.join(line[11:15])

			if oid in oidmap:
				update_doc(
					"interface_log",
					ip_src + ip + timestamp,
					{"router": ip_src, "if_ip": ip2int(ip),
						"timestamp": timestamp},
					{oidmap[oid]["name"]: oidmap[oid]["fct"](value)}
				)

		# parse ip route oid
		elif line.startswith(".1.3.6.1.2.1.4.21.1"):
			line = line.split(".")
			oid = '.'.join(line[0:11])
			ip = '.'.join(line[11:15])

			if oid in oidmap:
				update_doc(
					"ipRoute",
					ip_src + ip + timestamp,
					{"ip_src": ip2int(ip_src), "timestamp": timestamp,
						"ip_dst": ip2int(ip)},
					{oidmap[oid]["name"]: oidmap[oid]["fct"](value)}
				)

		# parse eigrp oid
		elif line.startswith(".1.3.6.1.4.1.9.9.449.1.3.1.1"):
			line = line.split(".")
			oid = '.'.join(line[0:15])
			ip = '.'.join(line[19:23])

			if oid in oidmap:
				update_doc(
					"cEigrp",
					ip_src + ip + line[23] + timestamp,
					{"ip_src": ip2int(ip_src), "timestamp": timestamp,
						"ip_dst": ip2int(ip), "mask_dst": line[23]},
					{oidmap[oid]["name"]: oidmap[oid]["fct"](value)}
				)

		# parse ipcidrroute oid
		elif line.startswith(".1.3.6.1.2.1.4.24.4.1"):
			line = line.split(".")
			oid = '.'.join(line[0:12])
			ip_dst = '.'.join(line[12:16])
			mask_dst = '.'.join(line[16:20])
			ip_gtw = '.'.join(line[21:25])

			if oid in oidmap:
				update_doc(
					"ipCidrRoute",
					ip_src + ip_dst + mask_dst + ip_gtw + timestamp,
					{"ip_src": ip2int(ip_src), "timestamp": timestamp, "ip_dst": ip2int(ip_dst),
						"mask_dst": netmask2int(mask_dst), "ip_gtw": ip2int(ip_gtw)},
					{oidmap[oid]["name"]: oidmap[oid]["fct"](value)}
				)

		# increment counter for processed lines
		counter += 1
		lines_since_commit += 1

		# do statistical calculation
		time_current = time.time()
		if (time_current - time_last > 5):
			print "Processed %s lines in %s seconds (%s lines per second)" % (
				counter, time_current - time_begin, counter / (time_current - time_begin))
			time_last = time_current

		if lines_since_commit > cache_treshold:
			commit_doc()
			lines_since_commit = 0

#	print "counter: %s" % counter


# commit local doc to databackend in the end

commit_doc()

for collection in collections.itervalues():
	collection.flushCache()

print "Calculating IP ranges"

# calculate ip network ranges
for timestamp in timestamps:
	for row in collections["ipCidrRoute"].find({"timestamp": timestamp}):
		(low_ip, high_ip) = calc_ip_range(row["ip_dst"], row["mask_dst"])
		collections["ipCidrRoute"].update({"_id": row["_id"]}, {"$set": {"low_ip": low_ip, "high_ip": high_ip}}, True)

	for row in collections["cEigrp"].find({"timestamp": timestamp}):
		(low_ip, high_ip) = calc_ip_range(row["ip_dst"], int(row["mask_dst"]))
		collections["cEigrp"].update({"_id": row["_id"]}, {"$set": {"low_ip": low_ip, "high_ip": high_ip}}, True)

for collection in collections.itervalues():
	collection.flushCache()

# do some statistics in the end
time_current = time.time()
print "Processed %s lines in %s seconds (%s lines per second)" % (
		counter, time_current - time_begin, counter / (time_current - time_begin))
