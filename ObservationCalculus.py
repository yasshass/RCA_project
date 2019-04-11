import pyspark.sql.functions as sf


def visitduration(data):
    obs = (data
           .groupBy(['uid', 'date'])
           .agg(sf.sum("value").alias("visitduration"))
           .select('uid',"visitduration")
           ).toPandas().set_index("uid")
    return obs