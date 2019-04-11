#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This is a awesome
        python script!"""
import json
import pyspark.sql.functions as sf
#getconfig
def getconfig(config_file):
    with open(config_file, "r", encoding="ISO-8859-1") as f:
        config = json.load(f, encoding="unicode")
    return(config)

# getdata
def getdata(sdate, edate, testid, query_file, sqlCon):
    with open(query_file) as input_query:
        query = input_query.read()
        data = sqlCon.sql(query.format(sd=sdate, ed=edate, testid=testid))
    return(data)

