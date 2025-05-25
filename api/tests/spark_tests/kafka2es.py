from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Kafka to Elasticsearch").getOrCreate()
kafka_df = spark.readStream.format("kafka").option("kafka.bootstrap.servers", "10.0.4.17:9092").option("subscribe", "test").load()
parsed_df = kafka_df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")
elastic_config = {
    "es.nodes": "10.0.4.16",
    "es.port": "9200",
    "es.resource": "test/type",
    "es.net.http.auth.user": "",
    "es.net.http.auth.pass": ""
}
parsed_df.writeStream.format("org.elasticsearch.spark.sql").option("checkpointLocation", "/tmp/checkpoint").options(**elastic_config).start().awaitTermination()