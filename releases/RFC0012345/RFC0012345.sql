
--dml
create schema if not exists grp_ods_bw authorization by w_alrdt;
grant all on schema grp_ods_bw to w_alrdt;
grant usage on schema grp_ods_bw to gp_develop_raw_read,gp_develop_raw_read_write;
--dml

set role w_alrdt;

--dml
delete from dwh_meta.cut_param where table_nm ilike '%grp_ods_bw.kurl_im%';
insert into dwh_meta.cut_param values('LOAD_GP_OBW_KURL_IM','grp_ods_bw.kurl_im','created_at','timestamp','1960-01-01',now());
--dml


--dml
alter table dwh_meta.cut_param drop column if exists test_column;
alter table grp_sys.etl_log_status rename to etl_log_status_old;
--dml


--ddl
drop table if exists grp_ods_bw.kurl_im;
create table grp_ods_bw.kurl_im (
guid text null,
created_at text null,
value text NULL
)
distributed randomly;

select * from dwh_meta.f_grant_default_privs('grp_ods_bw','kurl_im');
--ddl


--ddl
drop table if exists grp_core.bw_metrics cascade;
create table grp_core.bw_metrics (
metric_id text null,
created_at text null,
value text NULL
)
distributed by (metric_id);

select * from dwh_meta.f_grant_default_privs('grp_core','bw_metrics');
--ddl


--dag LOAD_GP_CORE_BW_METRICS
--model
drop view if exists grp_wrk.v_bw_metrics;
create view grp_wrk.v_bw_metrics
AS
select 
guid as metric_id,
created_at,
value
from grp_ods_bw.kurl_im;


--loader
select * from dwh_meta.f_scd1_load(
'grp_wrk.v_bw_metrics',
'grp_core.bw_metrics',
'metric_id',
'A',
'',
true,
false,
false,
'',
FALSE
'',
2);
--dag

--ddl
drop view if exists grp_rep.v_bw_metrics;
create view grp_rep.v_bw_metrics AS
select 
metric_id,
created_at,
VALUE
from grp_core.bw_metrics
where created_at>current_date - 7;

select * from dwh_meta.f_grant_default_privs('grp_rep','v_bw_metrics');
--ddl



