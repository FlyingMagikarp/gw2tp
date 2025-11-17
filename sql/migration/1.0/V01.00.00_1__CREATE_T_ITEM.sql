CREATE TABLE public.t_item
(
    id integer NOT NULL,
    name text,
    icon text,
    description text,
    type text,
    rarity text,
    level integer,
    vendor_value integer,
    accountbound boolean,
    soulbound boolean,
    last_update timestamp with time zone,
    PRIMARY KEY (id)
);

ALTER TABLE IF EXISTS public.t_item
    OWNER to postgres;