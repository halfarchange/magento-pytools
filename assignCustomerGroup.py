#!/usr/bin/python
# -*- coding: utf-8 -*-

from sys import argv
from pylib.DB import Database
from pylib import slice

'''script to batch assign customers to a customer group
needs a csv file which is simply a list of entity_ids or increment_ids
one per line such as :
125
147
190
'''

batchAmount = 90000

DB = Database()

def getCounts():
  counts = DB.hash('select group_id, count(*) from PREFIX_customer_entity group by group_id;', 1)
  print 'group_id group_name        count_customers'
  for l in DB.run('select * from PREFIX_customer_group'):
    print l[0] + ' '*(8 - len(l[0])), l[1] + ' '*(17 - len(l[1])), counts[l[0]] if counts.has_key(l[0]) else 0

getCounts()
print 

# get list of customers in csv
try:
  customers_csv = open(argv[1]).read().split()
except:
  print 'Usage =\n' + argv[0] + ' file.csv group_id [--inc] [--run]'
  print '    file.csv is a list of ids one per line'
  print '    group_id is the id of the group to assign the customers to'
  print '    --inc means that the ids are customer increment_id instead of ids'
  print '    without --run modifications are not implemented'
  quit()

# remove titles line(s) if any
while not customers_csv[0].isdigit():  customers_csv.pop(0)

# increment_id or id ?
if '--inc' in argv:
  column = 'increment_id'
else:
  column = 'entity_id'

# find the right group
group_id = int(argv[2])
group_name = DB.run('select customer_group_code from PREFIX_customer_group where customer_group_id = %d' % group_id )[0][0]
print 'Preparing to assign customers to group', group_name
print
print 'Members that do not exist or are not active :'
customers_db = DB.hash('select %s from PREFIX_customer_entity where is_active = 1;' % column)
customers_left = []
for c in customers_csv:
  if not customers_db.has_key(c):
    print c
  else:
    customers_left.append(c)
print 

sql_update = 'update PREFIX_customer_entity set group_id = ' + str(group_id) + ', disable_auto_group_change = 1 where ' + column + ' in ( %s );'
slices = slice(customers_left, batchAmount)
for s in slices:
  tmp = ", ".join(s)
  if not '--run' in argv:
    sql = sql_update % tmp
    print 'SQL string size =', len(sql), ':', sql.split(' (')[0], '...'
  else:
    DB.query(sql_update % tmp)

print 
print len(customers_left), 'members processed in', len(slices), 'sql requests'
print

getCounts()
