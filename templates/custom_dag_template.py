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

    dag_id = '',

    default_args = default_args,

    schedule_interval = None

    catchup = False,

    tags = []

)

def load_core(): 

 

    path_file1 = '/opt/airflow/dags/models/{stream}/{model}.sql'
    path_file1 = '/opt/airflow/dags/models/{stream}/{loader}.sql'

    conn_id = 'greenplum'

 

  

    sql = """



      """

     

    def read_text(path_file):

        with open(path_file, "r") as f:

            sql = f.read()

        print(sql)

        return sql     

      

    sensor = SqlSensor(       

        task_id='sql_sensor',

        conn_id=conn_id,

        sql=sql,

        poke_interval=60*5,         # time in sec that sensor waits before checking the condition again.

        timeout=64800,              # if the criteria is not met reschedule the next check for a later time

        mode='reschedule',          # для высвобождения слота после каждой отрицательной проверки

        on_failure_callback=task_failure_callback  # для вывода информации что датчик вышел за таймаут не дождавшись положительного ответа в период жизни

    )

 

    {{model}} = PostgresOperator(

        task_id='{{model}}',

        postgres_conn_id=conn_id,

        sql=read_text(path_file1),

    )

   

    {{loader}} = PostgresOperator(

        task_id='{{loader}}',

        postgres_conn_id=conn_id,

        sql=read_text(path_file2),

    )



 

    @task

    def log_status(schema, table, dag_id):

 

        query = f"insert into grp_sys.log_status values('{schema}.{table}', now(), now(), 'FINISH','{dag_id}');"

        print (query)

 

        postgres = PostgresHook(postgres_conn_id=conn_id)

        conn = postgres.get_conn()

        cursor = conn.cursor()

        cursor.execute(query)

        conn.commit()

       

 

    schema = {{schema}}

    dag_id = "{{ dag.dag_id }}"

   

    chain(

        sensor,

        [

            {{model}}

        ],

        [

            {{loader}}

        ],

        [

            log_status({{schema}}, '{{object_name}}', dag_id)

        ]

    )

dag = load_core()