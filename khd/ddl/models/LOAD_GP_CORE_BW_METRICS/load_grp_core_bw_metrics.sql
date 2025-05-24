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
