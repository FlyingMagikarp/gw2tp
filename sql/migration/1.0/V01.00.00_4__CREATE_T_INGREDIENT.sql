CREATE TABLE public.t_ingredient
(
    recipe_id integer NOT NULL,
    item_id   integer NOT NULL,
    count     integer NOT NULL,

    CONSTRAINT pk_t_ingredient
        PRIMARY KEY (recipe_id, item_id),

    CONSTRAINT fk_ingredient_recipe
        FOREIGN KEY (recipe_id)
        REFERENCES public.t_recipe (id)
        ON UPDATE NO ACTION
        ON DELETE CASCADE,

    CONSTRAINT fk_ingredient_item
        FOREIGN KEY (item_id)
        REFERENCES public.t_item (id)
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

ALTER TABLE IF EXISTS public.t_ingredient
    OWNER TO postgres;

CREATE INDEX idx_t_ingredient_item_id
    ON public.t_ingredient (item_id);

CREATE INDEX idx_t_ingredient_recipe_id
    ON public.t_ingredient (recipe_id);
