drop table if exists grp_core.bw_metrics cascade;
create table grp_core.bw_metrics (
metric_id text null,
created_at text null,
value text NULL
)
distributed by (metric_id);
