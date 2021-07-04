CREATE OR REPLACE FUNCTION get_expected_today(IN start_date date,
                                              IN end_date date,
                                              IN amount decimal,
                                              IN today date default CURRENT_DATE,
                                              OUT amount_due decimal)
AS
$$
DECLARE
    NEW_PAYMENT_REQUIRED_DAY CONSTANT integer := 27;
    bet_end CONSTANT date := LEAST(end_date, today);
    year_diff CONSTANT integer := DATE_PART('year', bet_end) - DATE_PART('year', start_date);
    month_diff CONSTANT integer :=  DATE_PART('month', bet_end) - DATE_PART('month', start_date);
    day_diff CONSTANT integer := DATE_PART('day', bet_end) - DATE_PART('day', start_date);
    months decimal := year_diff * 12 + month_diff;

BEGIN
    IF DATE_PART('day', bet_end) >= NEW_PAYMENT_REQUIRED_DAY THEN
        months = months + 1;
    END IF;

    IF CURRENT_DATE > start_date AND end_date is NULL THEN
        -- if this bet is still active, we expect them to have payed
        -- for the following month already
        months = months +1;
    END IF;

    IF DATE_PART('day', start_date) >= 15 THEN
        -- If the Bet was started at mid-month, subtract half
        -- a month from the expected amount
        months = months - 0.5;

        if day_diff > 16 THEN
            -- If the Bet started at a half month and today is a new
            -- month (but no full month in the delta yet), we need to
            -- account for one more month.
            months = months + 1;
        END IF;
    END IF;
    amount_due := months * amount;
END
$$
LANGUAGE plpgsql;