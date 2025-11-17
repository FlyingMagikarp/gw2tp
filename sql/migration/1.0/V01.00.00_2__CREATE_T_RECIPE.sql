CREATE TABLE public.t_recipe
(
    id integer NOT NULL,
    output_item_id integer,
    output_item_count integer,
    disciplines text[],
    min_rating integer,
    auto_learned boolean,
    learned_from_item boolean,
    time_to_craft_ms integer,
    ingredients jsonb,
    PRIMARY KEY (id)
);

ALTER TABLE IF EXISTS public.t_recipe
    ADD CONSTRAINT fk_item FOREIGN KEY (output_item_id)
    REFERENCES public.t_item (id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;

ALTER TABLE IF EXISTS public.t_recipe
    OWNER to postgres;