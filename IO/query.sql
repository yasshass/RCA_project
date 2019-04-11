SELECT
uid,
date,
variant,
platform,
format,
value,
age,
gender,
since_creation,
loginprovider
FROM
    (SELECT
        d_date as date,
        ab_variantdescription('gigya', gigyaId, {testid}) as variant,
        gigyaId as uid,
        platformcode AS platform,
        format,
        cast(SUM(secondview) as BIGINT) as value
        --count(*) as count
    FROM event_collector_prod.video_view
    WHERE
        customer='m6web'
        AND d_date BETWEEN '{sd}' AND '{ed}'
        AND secondview > 0
        AND gigyaId IS NOT NULL
    GROUP BY gigyaId, d_date, platformcode, format) as conso
inner join
    (select
        uid as gigya,
        max(floor(
                datediff(to_date(CURRENT_DATE),
                         to_date(concat(profile.birthyear,
                                        '-',profile.birthmonth,
                                        '-',profile.birthday))
                        )/365)) as age,
        min(profile.gender) as gender,
        max(datediff(to_date('{ed}'), split(created, "T")[0])) as since_creation,
        max(loginprovider) as loginprovider
    from gigya.crm_gigya_full_parquet
    Where
        round(datediff(to_date("2019-03-15"),
                         to_date(concat(profile.birthyear,
                                        '-',profile.birthmonth,
                                        '-',profile.birthday))
                        )/365)  BETWEEN 15 AND 76
        AND profile.gender <> "u"
    GROUP BY uid) as gigya_data
on gigya=uid