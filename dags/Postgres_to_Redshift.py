from airflow import DAG
from airflow.macros import *
from airflow.models import Variable
from plugins.postgres_to_s3_operator import PostgresToS3Operator
from plugins.s3_to_redshift_operator import S3ToRedshiftOperator


DAG_ID = "Postgres_to_Redshift"
dag = DAG(
    DAG_ID,
    schedule_interval="@once",
    max_active_runs=1,
    concurrency=2,
    start_date=datetime(2020, 8, 10),
    catchup=False
)

tables = [
    "customer_features",
    "customer_variants"
]


# s3_bucket, local_dir
s3_bucket = 'grepp-data-engineering'
local_dir = ''
s3_key_prefix = 'keeyong'
schema = 'raw_data'
prev_task = None

for table in tables:
    s3_key=s3_key_prefix+'/'+table+'.tsv'

    postgrestos3 = PostgresToS3Operator(
        table="public."+table,
        s3_bucket=s3_bucket,
        s3_key=s3_key,
        data_dir=local_dir,
        dag=dag,
        task_id="Postgres_to_S3"+"_"+table
    )

    s3toredshift = S3ToRedshiftOperator(
        schema=schema,
        table=table,
        s3_bucket=s3_bucket,
        s3_key=s3_key,
        copy_options="delimiter '\\t' COMPUPDATE ON",
        aws_conn_id='aws_s3_default',
        task_id='S3_to_Redshift'+"_"+table,
        dag=dag
    )
    if prev_task is not None:
        prev_task >> postgrestos3 >> s3toredshift
    else:
        postgrestos3 >> s3toredshift
    prev_task = s3toredshift
