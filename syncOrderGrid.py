#!/usr/bin/python
# -*- coding: utf-8 -*-

''' Cron script to fix the grid problem with status not correctly updated in 
the grid after a change in the order table
'''

import datetime
from pylib.DB import Database

sql = '''create temporary table if not exists sync_temp_order_id ( INDEX(entity_id) ) AS ( select o2.entity_id, o2.status from PREFIX_sales_flat_order as o2, PREFIX_sales_flat_order_grid as g2 where g2.entity_id = o2.entity_id and o2.status <> g2.status );
update PREFIX_sales_flat_order_grid as g join sync_temp_order_id as o ON g.entity_id = o.entity_id set g.status = o.status;
drop table sync_temp_order_id;'''

print datetime.datetime.now().isoformat(' '),
DB = Database()

for s in sql.split('\n'):
  print s
  DB.query(s)

print datetime.datetime.now().isoformat(' '), '[END]'