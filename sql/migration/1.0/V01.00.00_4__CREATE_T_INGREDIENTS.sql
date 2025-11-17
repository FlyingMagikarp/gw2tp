CREATE TABLE public.t_ingredients
(
    recipe_id integer NOT NULL,
    item_id   integer NOT NULL,
    count     integer NOT NULL,

    CONSTRAINT pk_t_ingredients
        PRIMARY KEY (recipe_id, item_id),

    CONSTRAINT fk_ingredients_recipe
        FOREIGN KEY (recipe_id)
        REFERENCES public.t_recipe (id)
        ON UPDATE NO ACTION
        ON DELETE CASCADE,

    CONSTRAINT fk_ingredients_item
        FOREIGN KEY (item_id)
        REFERENCES public.t_item (id)
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

ALTER TABLE IF EXISTS public.t_ingredients
    OWNER TO postgres;

CREATE INDEX idx_t_ingredients_item_id
    ON public.t_ingredients (item_id);

CREATE INDEX idx_t_ingredients_recipe_id
    ON public.t_ingredients (recipe_id);
