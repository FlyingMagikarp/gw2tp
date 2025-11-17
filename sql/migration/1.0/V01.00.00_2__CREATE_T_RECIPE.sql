CREATE TABLE public.t_recipe
(
    id                integer       NOT NULL,
    output_item_id    integer       NOT NULL,
    output_item_count integer       NOT NULL,
    disciplines       text[],
    min_rating        integer,
    auto_learned      boolean,
    learned_from_item boolean,
    time_to_craft_ms  integer,
    PRIMARY KEY (id)
);

ALTER TABLE IF EXISTS public.t_recipe
    ADD CONSTRAINT fk_recipe_output_item
    FOREIGN KEY (output_item_id)
    REFERENCES public.t_item (id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;

ALTER TABLE IF EXISTS public.t_recipe
    OWNER TO postgres;
