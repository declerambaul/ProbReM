'''
Student Professor example from Pasula/Stuart paper
'''


import sys,os

import sqlite3

import numpy as N


# simple model
nstudents = 1
nprofs = 10



def createSkeleton(database_fn):
	''' Creating empty SQLite database'''
	
	#os.system('rm ./sqlite/'+database_fn)
	con = sqlite3.connect('./sqlite/'+database_fn)

	con.isolation_level = "DEFERRED"
	cur = con.cursor()

	cur.executescript(open("./createSQL_DB.sql").read())





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

	return con


if __name__ == '__main__':
	createSkeleton('studentprof.sqlite')











