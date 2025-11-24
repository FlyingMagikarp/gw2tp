CREATE TABLE public.t_listing_snapshot_stats
(
    item_id integer,
    snapshot_ts_from timestamp with time zone,
    snapshot_ts_to timestamp with time zone,
    buy_qty_prev bigint,
    buy_qty_curr bigint,
    buy_qty_change bigint,
    sell_qty_prev bigint,
    sell_qty_curr bigint,
    sell_qty_change bigint,
    best_buy_prev integer,
    best_buy_curr integer,
    best_buy_change integer,
    best_sell_prev integer,
    best_sell_curr integer,
    best_sell_change integer,
    PRIMARY KEY (item_id, snapshot_ts_to)
);

ALTER TABLE IF EXISTS public.t_listing_snapshot_stats
    OWNER to postgres;