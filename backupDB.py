#!/usr/bin/python
# -*- coding: utf-8 -*-

from sys import argv, exit
from os.path import isdir
from os import mkdir
import commands
from datetime import datetime
from glob import glob
from pylib.DB import Database
from pylib import totty, ask, isHuman

DB = Database()

# Dump multilines + Dump monoline (= 2 dumps for each table)
dumpCmd = [ '/usr/bin/mysqldump --skip-opt -F -C -K --no-autocommit -u ' + DB.user + ' -h ' + DB.server + ' --password=' + DB.password + " " + DB.dbname + " %s > %s-LINES_DUMP-%s.sql", '/usr/bin/mysqldump --no-autocommit -u ' + DB.user + ' -h ' + DB.server + ' --password=' + DB.password + " " + DB.dbname + " %s > %s-QUICK_DUMP-%s.sql" ]

reloadCmd = '/usr/bin/mysql -u ' + DB.user + ' -h ' + DB.server + ' --password=' + DB.password + ' ' + DB.dbname

tablesTest = [ DB.prefix + 'widget_instance', DB.prefix + 'eav_entity_store', DB.prefix + 'widget_instance_page', DB.prefix + 'widget_instance_page_layout']

def dumpTables(tables, to_dir, gzip = False, mode = 'quick'):
  # trick to get 'eav_entity_store' at the end of the dump to get the latest order increment_ids
  keep = 0
  for t in tables:
    if 'eav_entity_store' in t:
      keep = t
      break
  if keep:
    tables.remove(keep)
    tables.append(keep)
  
  nows = to_dir + datetime.now().isoformat().split('T')[0]
  if gzip:
    print 'Gzip', totty('[Enabled]', 'green')
  nb = len(tables)
  if mode == 'both':
    nb = nb * 2.0
    print 'Quick and Lines(1 by 1)', totty('[Enabled]', 'green')
  i = 0
  print 
  for t in tables:
    for dc in dumpCmd:
      if mode == 'quick' and '--skip-opt' in dc:  continue
      if mode == 'lines' and 'QUICK_DUMP' in dc:  continue
      dc = dc % ( t, nows, t )
      if gzip:
        dc = dc.replace(' >', ' | gzip >') + '.gz'
      ret = commands.getstatusoutput( dc )
      #print ret
      if ret[0] != 0 or ret[1] != '':
        print totty('Error Dump Table :', 'red', 1), t
        print ret[1]
        exit(1)
      print 'QUICK' if 'quick' in dc.lower() else 'LINES', 'DUMP', t, ':', totty('SUCCESS', 'green')
      i += 1
      print totty('%0.1f%%' %  ( i*100.0/(nb) ) , 'green'), 'Done =', '%d/%d' % (i, int(nb)), 'dumps'

def getQuickFiles(directory):
  files = glob(directory + '/*QUICK_DUMP*')
  for f in files:
    if not f.endswith('.gz'):
      if f + '.gz' in files:
        print totty('Error: Ambiguous', 'red', 1)
        print 'Beware, gzipped files and plain-text files of same tables such as :\n%s are present in the directory\nPlease delete either plaintext or .gz file for each table' % f
        exit(1)
  return files

def getTableFile(fileName):
  return f.split('QUICK_DUMP')[1][1:].split('.gz')[0]

def reloadTableFiles(files):
  nb = len( files )
  i = 0

  for f in files:
    t = getTableFile(f)
    if f.endswith('gz'):
      ret = commands.getstatusoutput( '/bin/gunzip -c ' + f + ' | ' + reloadCmd )
    else:
      ret = commands.getstatusoutput( reloadCmd + ' < ' + f )
    #print ret
    if ret[0] != 0 or ret[1] != '':
      print totty('Error Loading Table :', 'red', 1), t
      print ret[1]
      exit(1)
    print 'Load', t, ':', totty('SUCCESS', 'green')
    i += 1
    print totty('%0.1f%%' %  ( i*100.0/(nb) ) , 'green'), 'Done =', '%d/%d' % (i, int(nb)), 'dumps'

def getAllTables():
  tables = DB.run('show tables;')
  return [ t[0] for t in tables ]

if __name__ == "__main__":
  progName = argv[0]
  del argv[0]

  # Reload
  if '--reload' in argv:
    argv.remove('--reload')
    files = getQuickFiles(argv[0] if len(argv) else '.')
    print 'Reload tables :'
    if not files:
      quit(totty('No files *QUICK_DUMP* found', 'red', 1))
    else:
      nb_files = len(files)
      if nb_files < 10:
        tab = files
      else:
        print nb_files, 'dumps to load, starting with:'
        tab = files[0:3]
      for f in tab:
        print getTableFile(f), '<', f
      if len(tab) < nb_files:
        print '... (', nb_files - 3, 'left )'
    print
    c = 'y'
    if isHuman():
      c = ask('Do you want to load these tables')
    if c == 'y':
      reloadTableFiles(files)
    exit(0)

  # Dump
  gzip = False
  mode = 'quick'
  tables = []

  to_dir = './'
  for a in argv:
    if '/' in a:
      to_dir = a
      if not isdir(to_dir):
        mkdir(to_dir)
      argv.remove(a)
  if '--gzip' in argv:
    gzip = True
    argv.remove('--gzip')
  if '--onlylines' in argv:
    mode = 'lines'
    argv.remove('--onlylines')
  if '--lines' in argv:
    mode = 'lines'
    argv.remove('--lines')
  if '--twodumps' in argv:
    mode = 'both'
    argv.remove('--twodumps')
  if '--two' in argv:
    mode = 'both'
    argv.remove('--two')
  if '--both' in argv:
    mode = 'both'
    argv.remove('--both')
  if '--test' in argv:
    tables = tablesTest
  if '--all' in argv:
    tables = getAllTables()
  # search in argv the table names
  if not tables:
    tables = argv
  dumpTables(tables, to_dir, gzip, mode)
  if not tables:
    print 'Usage to', totty('Backup', 'green', 1), ':'
    print progName, 'table1|--all [table2 table3] [TO_PATH/] [--gzip] [--twodumps|--two] --onlylines'
    print '  --all instead of table1 to get all tables automatically'
    print '  --twodumps or --two or --both: make 2 dumps, one as Quick and one as "Lines" = line per line'
    print '  --onlylines or --lines: make only 1 dump but as "Lines" = line per line, no QUICK'
    print '  --gzip : sql files are gzipped instead of plain text'
    print '  by default it will save dumps into current directory unless a TO_PATH with a "/" is provided'
    print
    print 'Usage to', totty('Reload', 'yellow', 1), ':'
    print progName, '--reload [FROM_PATH/]'
    print '  by default it will look for QUICK_DUMP files in current directory'
