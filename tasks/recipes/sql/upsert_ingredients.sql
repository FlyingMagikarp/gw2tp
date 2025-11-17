INSERT INTO public.t_ingredient (
    recipe_id,
    item_id,
    count
)
VALUES %s
ON CONFLICT (recipe_id, item_id) DO UPDATE SET
    count = EXCLUDED.count;
