#!/usr/bin/python
# -*- coding: utf-8 -*-

try:
  import _mysql, MySQLdb
except:
  raise ImportError, 'MySQLdb python package is not installed, please install it with :\nsudo yum install MySQL-python'
from datetime import datetime
from sys import argv
from socket import gethostbyname
from __init__ import totty, MagentoConfig, environments

class Database():
  # constants for run()
  MODE_ITER = 0
  MODE_ASSOC = 1
  MODE_FULL = 2
	
  now = datetime.now().isoformat().split('.')[0].replace('T', ' ')
  
  def __init__(self, utf8 = False, localxml = None, silent = False):
    # Find PROD / PreProd database
    mag = MagentoConfig(localxml, silent)
    
    self.server = mag.get('host')
    if self.server == 'mydb':
      self.server = gethostbyname('mydb')
    if environments['database'].has_key(self.server):
      self.serverDisplay = totty(environments['database'][self.server], 'red', 1)
    else:
      self.serverDisplay = self.server

    self.user = mag.get('username')
    self.password = mag.get('password')
    self.dbname = mag.get('dbname')
    self.prefix = mag.get('table_prefix')
    if not silent:
      print 'Using Database:', self.serverDisplay, 'with user:', self.user

    self.utf8 = utf8
    self.connect()
    self.result = None
    self.lastSql = None

  def connect(self):
    self.con = _mysql.connect(self.server, self.user, self.password, self.dbname)
    if self.utf8:  self.con.query('SET NAMES UTF8')

  def run(self, sql, mode = 0):
    ''' mode = 0 is standard array 0..n
        mode = 1 is dict with maybe the table name if collision
        mode = 2 is always table.column'''
    #print sql
    self.query( sql )
    self.result = self.con.store_result()
    return self.result.fetch_row(0, mode)

  def columns(self):
    if not self.result:  return []
    return [ r[0] for r in self.result.describe() ]

  def hash(self, sql, removeKey = False, key = 0, mode = 0):
    res = self.run(sql, mode)
    dic = {}
    for r in res:
      if removeKey:
        if key == 0 and len(r) == 2:
          dic[ r[key] ] = r[1]
        elif key == 0:
          dic[ r[key] ] = r[1:]
        else:
          l = list(r)
          del l[key]
          dic[ r[key] ] = l
      else:
        dic[ r[key] ] = r
    return dic

  def dict(self, sql, where = None):
    if where:
      if type(where) is dict:
        where = where.keys()
        
      if type(where) is str:
        if where.isdigit():
          sql = sql % where
        else:
          sql = sql % ( "'" + where + "'" )
      elif type(where) is int or type(where) is float:
        sql = sql % str(where)
      elif type(where) is list:
        if len(where) == 0:
          return {}
        if type(where[0]) is str:
          if where[0].isdigit():
            sql = sql % ','.join(where)
          else:
            sql = sql % ( "'" + "','".join(where) + "'" )
        elif type(where[0]) is int or type(where[0]) is float:
          sql = sql % ', '.join(str(x) for x in where)
      else:
        raise ValueError, 'Unsupported type'
   
    #print sql
    res = self.run(sql, 1)
    dic = {}
    key = self.columns()[0]
    for r in res:
      dic[ r[key] ] = r
    return dic

  def map(self, sql): 
    result = self.run(sql, 1)
    cols = self.columns()
    key = cols[0]
    value = cols[1]
    
    ret = {}
    for l in result:
      p = l[key]
      if ret.has_key(p):
        raise ValueError, 'Your SQL %s could not map results, multiple keys %s' % (sql, p)
      else:
        ret[p] = l[value]
    return ret 
  
  def junction(self, sql): 
    result = self.run(sql, 1)
    cols = self.columns()
    key = cols[0]
    value = cols[1]
    
    ret = {}
    for l in result:
      p = l[key]
      if ret.has_key(p):
        ret[p].append(l[value])
      else:
        ret[p] = [ l[value] ]
    return ret
  
  def query(self, sql):
    self.lastSql = sql
    if isinstance(sql, unicode):
      sql = sql.encode('utf-8')
      if not self.utf8:
        print totty('Your DB connection is not in UTF-8 but one of your SQL commande was unicode', 'yellow', 1)
    try:
      return self.con.query(sql)
    except MySQLdb.OperationalError as e:
      if 'MySQL server has gone away' in str(e):
        # print 'MySQL Reconnecting'
        self.connect()
        return self.con.query(sql)
      else:
        raise e
    return false

  def getEAV(self, search, entity_type_id = None):
    sql = "select attribute_id, attribute_code from " + self.prefix + "eav_attribute where attribute_code LIKE '" + search + "'"
    if entity_type_id:
      sql += ' and entity_type_id = ' + str(entity_type_id)
    return self.run( sql + ' limit 1;')[0]

  def getConfig(self, path, scope_id = 0):
    return self.run("select value from %score_config_data where path = '%s' and scope_id = %d limit 1;" % (self.prefix, path, scope_id) )[0][0]
  
  def getConfigs(self, path):
    return [ d[0] for d in self.run("select value from %score_config_data where path = '%s';" % (self.prefix, path) )]
  
  def getBO(self):
    return self.getConfig('web/secure/base_url')

  def doSqlFile(self, fileName, run = False):
    if not run:
      print totty('Data has NOT BEEN PROCESSED', 'red', 1)
      print 'find the mysql password first, you will need it'
      print '=> to UPDATE data please run using mysql the following SQL script :', fileName    
      print 'time mysql -u ' + self.user + ' -h ' + self.server + ' -p ' + self.dbname + ' <', fileName
    else:
      print 'Executing file', fileName
      print 'time mysql -u ' + self.user + ' -h ' + self.server + ' -p ' + self.dbname + ' <', fileName
      loadCmd = '/usr/bin/mysql -u ' + self.user + ' -h ' + self.server + ' --password=' + self.password + ' ' + self.dbname
      import commands
      ret = commands.getstatusoutput( loadCmd + ' < ' + fileName )
      #print ret
      if ret[0] != 0 or ret[1] != '':
        print totty('Error loading :', 'red', 1), fileName
        print ret[1]
        raise Exception, ret[1]
      print 'mysql load', fileName, ':', totty('SUCCESS', 'green')

def sqlFileHeader(f, charset):
  f.write( '''/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = ''' + charset + '''*/;

SET AUTOCOMMIT = 0;
''' )

def sqlFileFooter(f):
  f.write( '''commit;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
''' )
