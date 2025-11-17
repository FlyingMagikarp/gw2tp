INSERT INTO t_item (
    id,
    name,
    icon,
    description,
    type,
    rarity,
    level,
    vendor_value,
    accountbound,
    soulbound,
    last_update
)
VALUES %s
ON CONFLICT (id) DO UPDATE SET
    name         = EXCLUDED.name,
    icon         = EXCLUDED.icon,
    description  = EXCLUDED.description,
    type         = EXCLUDED.type,
    rarity       = EXCLUDED.rarity,
    level        = EXCLUDED.level,
    vendor_value = EXCLUDED.vendor_value,
    accountbound = EXCLUDED.accountbound,
    soulbound    = EXCLUDED.soulbound,
    last_update  = EXCLUDED.last_update;