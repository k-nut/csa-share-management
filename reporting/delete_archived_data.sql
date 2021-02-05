BEGIN;
DELETE FROM deposit where deposit.person_id in (select person.id from person join share on person.share_id = share.id where share.archived);
DELETE FROM person where person.share_id in (select id from share where share.archived);
DELETE FROM bet where bet.share_id in (select id from share where share.archived);
DELETE FROM member where member.share_id in (select id from share where share.archived);
DELETE FROM share where share.archived;
-- sanity-check the output and then:
-- COMMIT;
-- or
-- ROLLBACK;

