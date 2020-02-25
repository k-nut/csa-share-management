select amount, timestamp, title, name, ausstiegsdatum, kautionen.share_id from (
select * from deposit
join person on deposit.person_id = person.id 
where person.share_id not in (
	select distinct share_id from bet where end_date is null
) and
deposit.is_security) kautionen

join (
select max(end_date) as ausstiegsdatum, share_id from bet group by share_id
) ausstiegsdaten
on kautionen.share_id = ausstiegsdaten.share_id
order by share_id, ausstiegsdatum;