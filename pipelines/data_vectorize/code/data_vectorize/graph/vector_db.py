from pyspark.sql import *
from pyspark.sql.functions import *
from pyspark.sql.types import *
from prophecy.utils import *
from prophecy.libs import typed_lit
from data_vectorize.config.ConfigStore import *
from data_vectorize.udfs.UDFs import *

def vector_db(spark: SparkSession, web_silver_content_vectorized_1: DataFrame):
    from pyspark.sql.functions import expr, array, struct
    from spark_ai.dbs.pinecone import PineconeDB, IdVector
    from pyspark.dbutils import DBUtils
    PineconeDB(DBUtils(spark).secrets.get(scope = "pinecone", key = "token"), "us-east-1-aws").register_udfs(spark)

    if spark.catalog.tableExists("spark_catalog.default.content_vectorized_status"):
        web_silver_content_vectorized_1\
            .withColumn("_row_num", row_number().over(Window.partitionBy().orderBy(col("id"))))\
            .withColumn("_group_num", ceil(col("_row_num") / 20))\
            .withColumn("_id_vector", struct(col("id"), col("embedding").alias("vector")))\
            .groupBy(col("_group_num"))\
            .agg(collect_list(col("_id_vector")).alias("id_vectors"))\
            .withColumn("upserted", expr("pinecone_upsert(\"sumit-index\", id_vectors)"))\
            .select(col("*"), col("upserted.*"))\
            .select(col("id_vectors"), col("count"), col("error"))\
            .write\
            .format("delta")\
            .insertInto("spark_catalog.default.content_vectorized_status")
    else:
        web_silver_content_vectorized_1\
            .withColumn("_row_num", row_number().over(Window.partitionBy().orderBy(col("id"))))\
            .withColumn("_group_num", ceil(col("_row_num") / 20))\
            .withColumn("_id_vector", struct(col("id"), col("embedding").alias("vector")))\
            .groupBy(col("_group_num"))\
            .agg(collect_list(col("_id_vector")).alias("id_vectors"))\
            .withColumn("upserted", expr("pinecone_upsert(\"sumit-index\", id_vectors)"))\
            .select(col("*"), col("upserted.*"))\
            .select(col("id_vectors"), col("count"), col("error"))\
            .write\
            .format("delta")\
            .mode("overwrite")\
            .saveAsTable("spark_catalog.default.content_vectorized_status")
