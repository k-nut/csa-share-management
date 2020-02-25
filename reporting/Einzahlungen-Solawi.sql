select amount as "Betrag", timestamp, title, name, is_security as "Kaution" from deposit 
join person on person.id = deposit.person_id
where timestamp > '2018-12-31'::timestamp
and timestamp < '2020-01-01'::timestamp
order by timestamp