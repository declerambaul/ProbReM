'''
Student Professor example from Pasula/Stuart paper
'''


import sys,os

import sqlite3

import numpy as N


''' Creating empty SQLite database'''
database = 'studentprof.10.sqlite'
#os.system('rm ./sqlite/'+database)
con = sqlite3.connect('./sqlite/'+database)

con.isolation_level = "DEFERRED"
cur = con.cursor()

cur.executescript(open("./createSQL_DB.sql").read())

# simple model
nstudents = 1
nprofs = 10



# Students
objs = []
for i in range(nstudents):
    objs.append(('s%s.success'%(i+1),))
stm = 'INSERT INTO Student VALUES (null,?)'
#print objs
cur.executemany(stm,objs)


# Professor
objs = []
for i in range(nprofs):
    objs.append(('p%s.fame'%(i+1),'p%s.funding'%(i+1),))
stm = 'INSERT INTO Professor VALUES (null,?,?)'
#print objs
cur.executemany(stm,objs)

con.commit()












