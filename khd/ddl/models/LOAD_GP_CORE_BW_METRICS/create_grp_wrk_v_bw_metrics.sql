drop view if exists grp_wrk.v_bw_metrics;
create view grp_wrk.v_bw_metrics
AS
select 
guid as metric_id,
created_at,
value
from grp_ods_bw.kurl_im
where created_at> {{Param_in}}::date;
