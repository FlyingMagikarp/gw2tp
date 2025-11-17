INSERT INTO public.t_recipe (
    id,
    output_item_id,
    output_item_count,
    disciplines,
    min_rating,
    auto_learned,
    learned_from_item,
    time_to_craft_ms
)
VALUES %s
ON CONFLICT (id) DO UPDATE SET
    output_item_id    = EXCLUDED.output_item_id,
    output_item_count = EXCLUDED.output_item_count,
    disciplines       = EXCLUDED.disciplines,
    min_rating        = EXCLUDED.min_rating,
    auto_learned      = EXCLUDED.auto_learned,
    learned_from_item = EXCLUDED.learned_from_item,
    time_to_craft_ms  = EXCLUDED.time_to_craft_ms;