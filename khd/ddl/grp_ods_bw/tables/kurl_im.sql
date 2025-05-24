drop table if exists grp_ods_bw.kurl_im;
create table grp_ods_bw.kurl_im (
guid text null,
created_at text null,
value text NULL
)
distributed randomly;
