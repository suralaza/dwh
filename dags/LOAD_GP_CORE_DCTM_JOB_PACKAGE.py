from airflow.decorators import dag,task

from airflow.exceptions import AirflowSensorTimeout, AirflowFailException

from airflow.providers.postgres.operators.postgres import PostgresOperator

from airflow.providers.postgres.hooks.postgres import PostgresHook

from datetime import datetime, timedelta

from airflow.sensors.sql import SqlSensor

from airflow.models.baseoperator import chain

 

# Создаем DAG в Airflow

default_args = {

    'owner': 'airflow',

    'depends_on_past': False,

    'start_date': datetime(2024, 10, 17),

    'email_on_failure': False,

    'email_on_retry': False,

    'retries': 3, #the number of retries when the task failed

    'retry_delay': timedelta(seconds=30), #deceleration time between retries

    'execution_timeout': timedelta(minutes=5), #spresify the maximum working time of the task

}

def task_failure_callback(context):

    print(f"sensor failed due to timeout, task_instance_key_str: {context['task_instance_key_str']}")

   

@dag(

    dag_id = 'LOAD_GP_CORE_DCTM_JOB_PACKAGE',

    default_args = default_args,

    schedule_interval = '30 2 * * *', # '30 2 * * *' daily at 5.30 am moscow time

    catchup = False,

    tags = ["dctm", "core"]

)

def load_core(): 

 

    path_file1 = '/opt/airflow/dags/sql/directum/create_wrk_v_dctm_job_package.sql'

    path_file2 = '/opt/airflow/dags/sql/directum/load_core_dctm_job_package.sql'

    path_file3 = '/opt/airflow/dags/sql/directum/create_wrk_v_dctm_packages.sql'

    path_file4 = '/opt/airflow/dags/sql/directum/load_core_dctm_packages.sql'

 

  

    sql = """

    with res as (

        select object_name

        from grp_sys.etl_log_status  

        where object_name in ('grp_ods_dctm.job_package_im','grp_ods_dctm.packages_im')

            and upd_dttm::date = current_date

            and status = 'FINISH'

        group by object_name

    )

    select case when count(object_name) = 2 then 1 else null end as req from res

      """

     

    def read_text(path_file):

        with open(path_file, "r") as f:

            sql = f.read()

        print(sql)

        return sql     

      

    sensor2 = SqlSensor(       

        task_id='sql_sensor',

        conn_id='greenplum',

        sql=sql,

        poke_interval=60*5,         # time in sec that sensor waits before checking the condition again.

        timeout=64800,              # if the criteria is not met reschedule the next check for a later time

        mode='reschedule',          # для высвобождения слота после каждой отрицательной проверки

        on_failure_callback=task_failure_callback  # для вывода информации что датчик вышел за таймаут не дождавшись положительного ответа в период жизни

    )

 

    create_wrk_v_dctm_job_package = PostgresOperator(

        task_id='create_wrk_v_dctm_job_package',

        postgres_conn_id='greenplum',

        sql=read_text(path_file1),

    )

   

    create_wrk_v_dctm_packages = PostgresOperator(

        task_id='create_wrk_v_dctm_packages',

        postgres_conn_id='greenplum',

        sql=read_text(path_file3),

    )

 

  

    load_core_dctm_job_package = PostgresOperator(

        task_id='load_core_dctm_job_package',

        postgres_conn_id='greenplum',

        sql=read_text(path_file2),

    )

   

    load_core_dctm_packages = PostgresOperator(

        task_id='load_core_dctm_packages',

        postgres_conn_id='greenplum',

        sql=read_text(path_file4),

    )

 

    @task

    def log_status(schema, table, dag_id):

 

        query = f"insert into grp_sys.log_status values('{schema}.{table}', now(), now(), 'FINISH','{dag_id}');"

        print (query)

 

        postgres = PostgresHook(postgres_conn_id='greenplum')

        conn = postgres.get_conn()

        cursor = conn.cursor()

        cursor.execute(query)

        conn.commit()

       

 

    schema = 'grp_core'

    dag_id = "{{ dag.dag_id }}"

   

    chain(

        sensor2,

        [

            create_wrk_v_dctm_job_package,

            create_wrk_v_dctm_packages

        ],

        [

            load_core_dctm_job_package,

            load_core_dctm_packages

        ],

        [

            log_status(schema, 'dctm_job_package', dag_id),

            log_status(schema, 'dctm_packages', dag_id),

        ]

    )

dag = load_core()