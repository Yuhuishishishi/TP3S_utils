# -*- coding: utf-8 -*-
"""
Created on Mon May 16 16:28:25 2016
tp3s rehit lib json outputer

@author: yshi25
"""

import pymssql as ms
import sys
import json
import os.path

server = "fmc05609.fsillab.ford.com"
user = "tp3s"
pwd = "wwooxxnn"


def connect_db():
    conn = ms.connect(server, user, pwd, "TP3S-Safety_PROD")
    return conn


def get_lib_info(lib_id):
    conn = connect_db()
    cursor = conn.cursor(as_dict=True)
    sql = """
	select * from Libraries
	join Regions on Libraries.regionId=Regions.id
	where Libraries.id = %d
	"""
    cursor.execute(sql, (lib_id,))

    r = cursor.fetchone()
    if not r:
        print "Cannot find library with id", lib_id
        return
    platform = r['platform']
    nameplate = r['nameplate']
    comments = r['comments']
    region = r['name']

    conn.close()
    return {
        "library_id": lib_id,
        "platform": platform,
        "nameplate": nameplate,
        "comments": comments,
        "region": region
    }


def get_lib(lib_id):
    conn = connect_db()
    cursor = conn.cursor(as_dict=True)

    sql = \
        """
	select R.libraryId, R1.name as category1, R2.name as category2, C.name as position, R.speedcutoff 
	from RehitRules as R
	join RehitCategory as R1 on R.rehitCategoryId1=R1.id
	join RehitCategory as R2 on R.rehitCategoryId2=R2.id
	join rehitcategorypairpositioning as C on R.rehitCategoryPairPositioningId=C.id
	where R.libraryId = %d
	"""
    cursor.execute(sql, (lib_id,))

    r = cursor.fetchone()
    rehit_rules = []
    while r:
        first_hit = r['category1']
        second_hit = r['category2']
        position = r['position']
        speed = r['speedcutoff']

        rehit_rules.append({
            "1st_hit": first_hit,
            "2nd_hit": second_hit,
            "position": position,
            "cutoff": speed
        })

        r = cursor.fetchone()

    conn.close()
    print "Find %d rehit rules for library %d" % (len(rehit_rules), lib_id)
    return rehit_rules


def get_json(lib_id):
    lib_info = get_lib_info(lib_id)
    rules = get_lib(lib_id)

    return json.dumps({
        "lib_info": lib_info,
        "rules": rules
    })


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print "Need to provide a rehit library id"
    else:
        lib_id = int(sys.argv[1])
        output = get_json(lib_id)
        # write to file
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, "rehit_lib%d.json" % lib_id), 'wb') as f:
            f.write(output)
