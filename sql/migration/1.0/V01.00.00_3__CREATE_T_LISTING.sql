CREATE TABLE public.t_listing
(
    id bigserial NOT NULL,
    item_id integer NOT NULL,
    "time" timestamp with time zone,
    buy_orders jsonb,
    sell_listings jsonb,
    PRIMARY KEY (id, item_id),
    CONSTRAINT fk_item FOREIGN KEY (item_id)
        REFERENCES public.t_item (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
);

ALTER TABLE IF EXISTS public.t_item_price
    OWNER to postgres;