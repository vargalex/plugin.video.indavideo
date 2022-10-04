from time import sleep
try:
    from sqlite3 import dbapi2 as database
except:
    from pysqlite2 import dbapi2 as database

import json

from resources.lib import control
from resources.lib.utils import py2_encode, py2_decode


def getHistory():
    try:
        dbcon = database.connect(control.historyFile)
        dbcur = dbcon.cursor()
        dbcur.execute("SELECT * FROM history")
        items = dbcur.fetchall()
        items = [(py2_encode(i[0]), eval(py2_encode(i[1]))) for i in items]
    except:
        items = []

    return items


def addHistory(name):
    try:
        control.makeFile(control.dataPath)
        dbcon = database.connect(control.historyFile)
        dbcur = dbcon.cursor()
        dbcur.execute("CREATE TABLE IF NOT EXISTS history (""id TEXT, ""items TEXT, ""UNIQUE(id)"");")
        dbcur.execute("DELETE FROM history WHERE id = '%s'" %  py2_decode(name))
        dbcur.execute("INSERT INTO history Values (?, ?)", (py2_decode(name), '0'))
        dbcon.commit()

        control.refresh()
    except:
        return


def deleteHistory(name):
    try:
        try:
            dbcon = database.connect(control.historyFile)
            dbcur = dbcon.cursor()
            dbcur.execute("DELETE FROM history WHERE id = '%s'" % py2_decode(name))
            dbcon.commit()
        except:
            pass

        control.refresh()
    except:
        return
    
def clear(table='history'):
    try:
        control.idle()

        if table == None: table = ['rel_list', 'rel_lib']
        elif not type(table) == list: table = [table]

        yes = control.yesnoDialog(u'\u00D6sszes el\u0151zm\u00E9ny t\u00F6rl\u00E9se', u'Biztos benne?', '')
        if not yes: return

        dbcon = database.connect(control.historyFile)
        dbcur = dbcon.cursor()

        for t in table:
            try:
                dbcur.execute("DROP TABLE IF EXISTS %s" % t)
                dbcur.execute("VACUUM")
                dbcon.commit()
            except:
                pass
        control.refresh()
    except:
        pass