// Use DBML to define your database structure
// Docs: https://dbml.dbdiagram.io/docs

Table item {
  id integer [primary key]
  name varchar
  icon varchar
  description varchar
  type varchar
  rarity varchar
  level integer
  vendor_value number
  accountbound bool
  soulbound bool
  last_update timestampz
}

Table recipe {
  id integer [primary key]
  output_item_id integer
  output_item_count integer
  disciplines varchar[]
  min_rating integer
  auto_learned bool
  learned_from_item bool
  time_to_craft_ms integer
  ingredients json[] // itemId, amount
}

Table item_price {
  id integer [primary key]
  item_id integer
  time timestampz
  buy_orders json[] //listings, unit_price, quantity
  sell_listing json[] //listings, unit_price, quantity
}

Ref: item.id < recipe.output_item_id
Ref: item.id < item_price.item_id