drop view if exists grp_rep.v_bw_metrics;
create view grp_rep.v_bw_metrics AS
select 
metric_id,
created_at,
VALUE
from grp_core.bw_metrics
where created_at>current_date - 7;

select * from dwh_meta.f_grant_default_privs('grp_rep','v_bw_metrics');
