#!/usr/bin/python
# -*- coding: utf-8 -*-

from sys import argv
import re
from pylib.DB import Database
from pylib import sendMail, time2str, now, sendSlack

'''script to be executed every 28th of the month, it will disable automatically all admin users that were
 not connected since the beginning of the month and send a html report by email. The users can be reactivated 
 in Magento backend (or in the database)'''

if __name__ == "__main__":
  if len(argv) < 2 or argv[1] != '--run':
    print 'Usage :'
    print argv[0], '--run # to start the script'
    print '  this script will disable admin users who havent connected in a while'
    quit()

DB = Database(utf8 = True)

sql_users = "select user_id, firstname, lastname, email, username, logdate, lock_expires from PREFIX_admin_user where is_active = 1 and logdate < '%s' order by logdate ASC;" % ( time2str(now())[0:8] + '01' )
  
nbTotalUsers    = int(DB.run('select count(*) from PREFIX_admin_user')[0][0])
nbActiveUsers   = int(DB.run('select count(*) from PREFIX_admin_user where is_active = 1')[0][0])
nbInActiveUsers = int(DB.run('select count(*) from PREFIX_admin_user where is_active = 0')[0][0])

html = '<i>At start :</i><br>\n%d users in total<br>\n%d active users<br>\n%d disabled users<br>\n<br>\n' % ( nbTotalUsers, nbActiveUsers, nbInActiveUsers )

html += 'Here is the list of users that are going to be disabled now :<br>\n<br>\n<b>Last Login date</b><br>\n'

lateUsers = DB.run(sql_users, 1)
if len(lateUsers) < 1:
  quit('Nothing to do')
  
for u in lateUsers:
  html += u['logdate'][0:10] + ' <a href="%sindex.php/admin/permissions_user/edit/user_id/%s">%s</a>' % ( DB.getBO(), u['user_id'], u['username'] ) + ' - ' + u['firstname'] + ' ' + u['lastname'] + ' ' + u['email'] + "<br>\n"

html += '<br>\n%d users have been deactivated<br>\n' % len(lateUsers)

sqlModif = "update PREFIX_admin_user set is_active = 0 where user_id IN ( %s )" % ', '.join([ u['user_id'] for u in lateUsers ])
DB.query(sqlModif)

print re.sub('<[^<]+?>', '', html)
sendMail(html = html, subject = 'Magento Backend Users deactivation' ) # add : emails = ['me@there.com', 'other@there.com'] 
sendSlack(html)
