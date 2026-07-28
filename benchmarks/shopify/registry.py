from typed_composition_search import Registry


def build_registry() -> Registry:
    reg = Registry()

    # --- Products --- GET /admin/api/products.json
    reg.register("list_products", ("Shop",), ("ProductList",), "Retrieve a list of products. GET /admin/api/products.json")
    reg.register("search_products", ("Shop",), ("ProductList",), "Search products by title, vendor, or product type. GET /admin/api/products.json?title=")
    reg.register("select_product", ("ProductList",), ("Product",), "Select a single product from a list.")
    reg.register("get_product", ("ProductId",), ("Product",), "Get a single product by ID. GET /admin/api/products/{id}.json")
    reg.register("create_product", ("ProductInput",), ("Product",), "Create a new product. POST /admin/api/products.json")
    reg.register("update_product", ("Product",), ("Product",), "Update a product. PUT /admin/api/products/{id}.json")
    reg.register("delete_product", ("Product",), ("DeletionResult",), "Delete a product. DELETE /admin/api/products/{id}.json")
    reg.register("get_product_count", ("Shop",), ("Count",), "Get a count of products. GET /admin/api/products/count.json")

    # --- Product Variants --- GET /admin/api/products/{id}/variants.json
    reg.register("list_product_variants", ("Product",), ("VariantList",), "List variants for a product. GET /admin/api/products/{id}/variants.json")
    reg.register("select_variant", ("VariantList",), ("ProductVariant",), "Select a single variant from a list.")
    reg.register("get_variant", ("VariantId",), ("ProductVariant",), "Get a single variant. GET /admin/api/variants/{id}.json")
    reg.register("create_variant", ("Product",), ("ProductVariant",), "Create a new product variant. POST /admin/api/products/{id}/variants.json")
    reg.register("update_variant", ("ProductVariant",), ("ProductVariant",), "Update a variant. PUT /admin/api/variants/{id}.json")
    reg.register("delete_variant", ("ProductVariant",), ("DeletionResult",), "Delete a variant. DELETE /admin/api/products/{id}/variants/{id}.json")
    reg.register("get_variant_count", ("Product",), ("Count",), "Get a count of variants. GET /admin/api/products/{id}/variants/count.json")

    # --- Product Images --- GET /admin/api/products/{id}/images.json
    reg.register("list_product_images", ("Product",), ("ImageList",), "List images for a product. GET /admin/api/products/{id}/images.json")
    reg.register("select_image", ("ImageList",), ("ProductImage",), "Select a single image from a list.")
    reg.register("get_product_image", ("ImageId",), ("ProductImage",), "Get a single product image. GET /admin/api/products/{id}/images/{id}.json")
    reg.register("create_product_image", ("Product",), ("ProductImage",), "Upload a product image. POST /admin/api/products/{id}/images.json")
    reg.register("delete_product_image", ("ProductImage",), ("DeletionResult",), "Delete a product image. DELETE /admin/api/products/{id}/images/{id}.json")
    reg.register("get_image_count", ("Product",), ("Count",), "Get a count of images. GET /admin/api/products/{id}/images/count.json")

    # --- Custom Collections --- GET /admin/api/custom_collections.json
    reg.register("list_custom_collections", ("Shop",), ("CustomCollectionList",), "List custom collections. GET /admin/api/custom_collections.json")
    reg.register("select_custom_collection", ("CustomCollectionList",), ("CustomCollection",), "Select a single custom collection.")
    reg.register("get_custom_collection", ("CollectionId",), ("CustomCollection",), "Get a custom collection. GET /admin/api/custom_collections/{id}.json")
    reg.register("create_custom_collection", ("CollectionInput",), ("CustomCollection",), "Create a custom collection. POST /admin/api/custom_collections.json")
    reg.register("update_custom_collection", ("CustomCollection",), ("CustomCollection",), "Update a custom collection. PUT /admin/api/custom_collections/{id}.json")
    reg.register("delete_custom_collection", ("CustomCollection",), ("DeletionResult",), "Delete a custom collection. DELETE /admin/api/custom_collections/{id}.json")
    reg.register("get_custom_collection_count", ("Shop",), ("Count",), "Get a count of custom collections. GET /admin/api/custom_collections/count.json")

    # --- Smart Collections --- GET /admin/api/smart_collections.json
    reg.register("list_smart_collections", ("Shop",), ("SmartCollectionList",), "List smart collections. GET /admin/api/smart_collections.json")
    reg.register("select_smart_collection", ("SmartCollectionList",), ("SmartCollection",), "Select a single smart collection.")
    reg.register("get_smart_collection", ("SmartCollectionId",), ("SmartCollection",), "Get a smart collection. GET /admin/api/smart_collections/{id}.json")
    reg.register("create_smart_collection", ("SmartCollectionInput",), ("SmartCollection",), "Create a smart collection. POST /admin/api/smart_collections.json")
    reg.register("update_smart_collection", ("SmartCollection",), ("SmartCollection",), "Update a smart collection. PUT /admin/api/smart_collections/{id}.json")
    reg.register("delete_smart_collection", ("SmartCollection",), ("DeletionResult",), "Delete a smart collection. DELETE /admin/api/smart_collections/{id}.json")

    # --- Collects (product-collection membership) --- GET /admin/api/collects.json
    reg.register("list_collection_products", ("CustomCollection",), ("CollectionProductList",), "List products in a custom collection. GET /admin/api/collects.json?collection_id=")
    reg.register("list_smart_collection_products", ("SmartCollection",), ("CollectionProductList",), "List products in a smart collection via product listing.")
    reg.register("select_collection_product", ("CollectionProductList",), ("Product",), "Select a product from a collection listing.")

    # --- Customers --- GET /admin/api/customers.json
    reg.register("list_customers", ("Shop",), ("CustomerList",), "List customers. GET /admin/api/customers.json")
    reg.register("search_customers", ("Shop",), ("CustomerList",), "Search customers by query. GET /admin/api/customers/search.json?query=")
    reg.register("select_customer", ("CustomerList",), ("Customer",), "Select a single customer from a list.")
    reg.register("get_customer", ("CustomerId",), ("Customer",), "Get a single customer. GET /admin/api/customers/{id}.json")
    reg.register("create_customer", ("CustomerInput",), ("Customer",), "Create a customer. POST /admin/api/customers.json")
    reg.register("update_customer", ("Customer",), ("Customer",), "Update a customer. PUT /admin/api/customers/{id}.json")
    reg.register("delete_customer", ("Customer",), ("DeletionResult",), "Delete a customer. DELETE /admin/api/customers/{id}.json")
    reg.register("get_customer_count", ("Shop",), ("Count",), "Get a count of customers. GET /admin/api/customers/count.json")

    # --- Customer Addresses --- GET /admin/api/customers/{id}/addresses.json
    reg.register("list_customer_addresses", ("Customer",), ("AddressList",), "List addresses for a customer. GET /admin/api/customers/{id}/addresses.json")
    reg.register("select_address", ("AddressList",), ("CustomerAddress",), "Select a single address from a list.")
    reg.register("get_customer_address", ("AddressId",), ("CustomerAddress",), "Get a customer address. GET /admin/api/customers/{id}/addresses/{id}.json")
    reg.register("create_customer_address", ("Customer",), ("CustomerAddress",), "Create a customer address. POST /admin/api/customers/{id}/addresses.json")
    reg.register("delete_customer_address", ("CustomerAddress",), ("DeletionResult",), "Delete a customer address. DELETE /admin/api/customers/{id}/addresses/{id}.json")

    # --- Customer Orders --- GET /admin/api/customers/{id}/orders.json
    reg.register("list_customer_orders", ("Customer",), ("CustomerOrderList",), "List orders for a customer. GET /admin/api/customers/{id}/orders.json")
    reg.register("select_customer_order", ("CustomerOrderList",), ("Order",), "Select a specific order from a customer's order list.")

    # --- Orders --- GET /admin/api/orders.json
    reg.register("list_orders", ("Shop",), ("OrderList",), "List orders. GET /admin/api/orders.json")
    reg.register("select_order", ("OrderList",), ("Order",), "Select a single order from a list.")
    reg.register("get_order", ("OrderId",), ("Order",), "Get a single order. GET /admin/api/orders/{id}.json")
    reg.register("create_order", ("OrderInput",), ("Order",), "Create an order. POST /admin/api/orders.json")
    reg.register("update_order", ("Order",), ("Order",), "Update an order. PUT /admin/api/orders/{id}.json")
    reg.register("close_order", ("Order",), ("Order",), "Close an order. POST /admin/api/orders/{id}/close.json")
    reg.register("cancel_order", ("Order",), ("Order",), "Cancel an order. POST /admin/api/orders/{id}/cancel.json")
    reg.register("get_order_count", ("Shop",), ("Count",), "Get a count of orders. GET /admin/api/orders/count.json")
    reg.register("list_order_line_items", ("Order",), ("LineItemList",), "List line items for an order (embedded in order resource).")

    # --- Draft Orders --- GET /admin/api/draft_orders.json
    reg.register("list_draft_orders", ("Shop",), ("DraftOrderList",), "List draft orders. GET /admin/api/draft_orders.json")
    reg.register("select_draft_order", ("DraftOrderList",), ("DraftOrder",), "Select a single draft order.")
    reg.register("get_draft_order", ("DraftOrderId",), ("DraftOrder",), "Get a draft order. GET /admin/api/draft_orders/{id}.json")
    reg.register("create_draft_order", ("DraftOrderInput",), ("DraftOrder",), "Create a draft order. POST /admin/api/draft_orders.json")
    reg.register("update_draft_order", ("DraftOrder",), ("DraftOrder",), "Update a draft order. PUT /admin/api/draft_orders/{id}.json")
    reg.register("delete_draft_order", ("DraftOrder",), ("DeletionResult",), "Delete a draft order. DELETE /admin/api/draft_orders/{id}.json")
    reg.register("complete_draft_order", ("DraftOrder",), ("Order",), "Complete a draft order and create an order. PUT /admin/api/draft_orders/{id}/complete.json")
    reg.register("get_draft_order_count", ("Shop",), ("Count",), "Get a count of draft orders. GET /admin/api/draft_orders/count.json")

    # --- Transactions --- GET /admin/api/orders/{id}/transactions.json
    reg.register("list_order_transactions", ("Order",), ("TransactionList",), "List transactions for an order. GET /admin/api/orders/{id}/transactions.json")
    reg.register("select_transaction", ("TransactionList",), ("Transaction",), "Select a single transaction.")
    reg.register("get_transaction", ("TransactionId",), ("Transaction",), "Get a single transaction. GET /admin/api/orders/{id}/transactions/{id}.json")
    reg.register("create_transaction", ("Order",), ("Transaction",), "Create a transaction. POST /admin/api/orders/{id}/transactions.json")
    reg.register("get_transaction_count", ("Order",), ("Count",), "Get a count of transactions. GET /admin/api/orders/{id}/transactions/count.json")

    # --- Refunds --- GET /admin/api/orders/{id}/refunds.json
    reg.register("list_order_refunds", ("Order",), ("RefundList",), "List refunds for an order. GET /admin/api/orders/{id}/refunds.json")
    reg.register("select_refund", ("RefundList",), ("Refund",), "Select a single refund.")
    reg.register("get_refund", ("RefundId",), ("Refund",), "Get a single refund. GET /admin/api/orders/{id}/refunds/{id}.json")
    reg.register("create_refund", ("Order",), ("Refund",), "Create a refund. POST /admin/api/orders/{id}/refunds.json")

    # --- Fulfillments --- GET /admin/api/orders/{id}/fulfillments.json
    reg.register("list_order_fulfillments", ("Order",), ("FulfillmentList",), "List fulfillments for an order. GET /admin/api/orders/{id}/fulfillments.json")
    reg.register("select_fulfillment", ("FulfillmentList",), ("Fulfillment",), "Select a single fulfillment.")
    reg.register("get_fulfillment", ("FulfillmentId",), ("Fulfillment",), "Get a single fulfillment. GET /admin/api/fulfillments/{id}.json")
    reg.register("create_fulfillment", ("FulfillmentOrder",), ("Fulfillment",), "Create a fulfillment. POST /admin/api/fulfillments.json")
    reg.register("cancel_fulfillment", ("Fulfillment",), ("Fulfillment",), "Cancel a fulfillment. POST /admin/api/fulfillments/{id}/cancel.json")
    reg.register("update_fulfillment_tracking", ("Fulfillment",), ("Fulfillment",), "Update tracking info. POST /admin/api/fulfillments/{id}/update_tracking.json")
    reg.register("get_fulfillment_count", ("Order",), ("Count",), "Get a count of fulfillments. GET /admin/api/orders/{id}/fulfillments/count.json")

    # --- Fulfillment Orders --- GET /admin/api/orders/{id}/fulfillment_orders.json
    reg.register("list_fulfillment_orders", ("Order",), ("FulfillmentOrderList",), "List fulfillment orders. GET /admin/api/orders/{id}/fulfillment_orders.json")
    reg.register("select_fulfillment_order", ("FulfillmentOrderList",), ("FulfillmentOrder",), "Select a single fulfillment order.")
    reg.register("get_fulfillment_order", ("FulfillmentOrderId",), ("FulfillmentOrder",), "Get a fulfillment order. GET /admin/api/fulfillment_orders/{id}.json")

    # --- Fulfillment Events --- GET /admin/api/orders/{id}/fulfillments/{id}/events.json
    reg.register("list_fulfillment_events", ("Fulfillment",), ("FulfillmentEventList",), "List tracking events for a fulfillment. GET /admin/api/orders/{id}/fulfillments/{id}/events.json")
    reg.register("select_fulfillment_event", ("FulfillmentEventList",), ("FulfillmentEvent",), "Select a single tracking event.")

    # --- Inventory Items --- GET /admin/api/inventory_items.json
    reg.register("get_variant_inventory_item", ("ProductVariant",), ("InventoryItem",), "Get the inventory item for a variant. GET /admin/api/inventory_items/{id}.json")
    reg.register("get_inventory_item", ("InventoryItemId",), ("InventoryItem",), "Get an inventory item by ID. GET /admin/api/inventory_items/{id}.json")
    reg.register("update_inventory_item", ("InventoryItem",), ("InventoryItem",), "Update an inventory item. PUT /admin/api/inventory_items/{id}.json")

    # --- Inventory Levels --- GET /admin/api/inventory_levels.json
    reg.register("list_inventory_levels", ("InventoryItem",), ("InventoryLevelList",), "List inventory levels for an item. GET /admin/api/inventory_levels.json?inventory_item_ids=")
    reg.register("select_inventory_level", ("InventoryLevelList",), ("InventoryLevel",), "Select a specific inventory level (location).")
    reg.register("set_inventory_level", ("InventoryLevel",), ("InventoryLevel",), "Set inventory level at a location. POST /admin/api/inventory_levels/set.json")
    reg.register("adjust_inventory_level", ("InventoryLevel",), ("InventoryLevel",), "Adjust inventory level. POST /admin/api/inventory_levels/adjust.json")

    # --- Locations --- GET /admin/api/locations.json
    reg.register("list_locations", ("Shop",), ("LocationList",), "List locations. GET /admin/api/locations.json")
    reg.register("select_location", ("LocationList",), ("Location",), "Select a single location.")
    reg.register("get_location", ("LocationId",), ("Location",), "Get a single location. GET /admin/api/locations/{id}.json")
    reg.register("get_location_inventory", ("Location",), ("InventoryLevelList",), "List inventory levels at a location. GET /admin/api/locations/{id}/inventory_levels.json")
    reg.register("get_location_count", ("Shop",), ("Count",), "Get a count of locations. GET /admin/api/locations/count.json")

    # --- Price Rules --- GET /admin/api/price_rules.json
    reg.register("list_price_rules", ("Shop",), ("PriceRuleList",), "List price rules. GET /admin/api/price_rules.json")
    reg.register("select_price_rule", ("PriceRuleList",), ("PriceRule",), "Select a single price rule.")
    reg.register("get_price_rule", ("PriceRuleId",), ("PriceRule",), "Get a price rule. GET /admin/api/price_rules/{id}.json")
    reg.register("create_price_rule", ("PriceRuleInput",), ("PriceRule",), "Create a price rule. POST /admin/api/price_rules.json")
    reg.register("update_price_rule", ("PriceRule",), ("PriceRule",), "Update a price rule. PUT /admin/api/price_rules/{id}.json")
    reg.register("delete_price_rule", ("PriceRule",), ("DeletionResult",), "Delete a price rule. DELETE /admin/api/price_rules/{id}.json")
    reg.register("get_price_rule_count", ("Shop",), ("Count",), "Get a count of price rules. GET /admin/api/price_rules/count.json")

    # --- Discount Codes --- GET /admin/api/price_rules/{id}/discount_codes.json
    reg.register("list_discount_codes", ("PriceRule",), ("DiscountCodeList",), "List discount codes for a price rule. GET /admin/api/price_rules/{id}/discount_codes.json")
    reg.register("select_discount_code", ("DiscountCodeList",), ("DiscountCode",), "Select a single discount code.")
    reg.register("get_discount_code", ("DiscountCodeId",), ("DiscountCode",), "Get a discount code. GET /admin/api/price_rules/{id}/discount_codes/{id}.json")
    reg.register("create_discount_code", ("PriceRule",), ("DiscountCode",), "Create a discount code. POST /admin/api/price_rules/{id}/discount_codes.json")
    reg.register("delete_discount_code", ("DiscountCode",), ("DeletionResult",), "Delete a discount code. DELETE /admin/api/price_rules/{id}/discount_codes/{id}.json")
    reg.register("get_discount_code_count", ("PriceRule",), ("Count",), "Get a count of discount codes. GET /admin/api/price_rules/{id}/discount_codes/count.json")
    reg.register("lookup_discount_code", ("Shop",), ("DiscountCode",), "Look up a discount code by code string. GET /admin/api/discount_codes/lookup.json?code=")

    # --- Blogs --- GET /admin/api/blogs.json
    reg.register("list_blogs", ("Shop",), ("BlogList",), "List blogs. GET /admin/api/blogs.json")
    reg.register("select_blog", ("BlogList",), ("Blog",), "Select a single blog.")
    reg.register("get_blog", ("BlogId",), ("Blog",), "Get a single blog. GET /admin/api/blogs/{id}.json")
    reg.register("create_blog", ("BlogInput",), ("Blog",), "Create a blog. POST /admin/api/blogs.json")
    reg.register("update_blog", ("Blog",), ("Blog",), "Update a blog. PUT /admin/api/blogs/{id}.json")
    reg.register("delete_blog", ("Blog",), ("DeletionResult",), "Delete a blog. DELETE /admin/api/blogs/{id}.json")

    # --- Articles --- GET /admin/api/blogs/{id}/articles.json
    reg.register("list_blog_articles", ("Blog",), ("ArticleList",), "List articles for a blog. GET /admin/api/blogs/{id}/articles.json")
    reg.register("select_article", ("ArticleList",), ("Article",), "Select a single article.")
    reg.register("get_article", ("ArticleId",), ("Article",), "Get a single article. GET /admin/api/blogs/{id}/articles/{id}.json")
    reg.register("create_article", ("Blog",), ("Article",), "Create an article. POST /admin/api/blogs/{id}/articles.json")
    reg.register("update_article", ("Article",), ("Article",), "Update an article. PUT /admin/api/blogs/{id}/articles/{id}.json")
    reg.register("delete_article", ("Article",), ("DeletionResult",), "Delete an article. DELETE /admin/api/blogs/{id}/articles/{id}.json")
    reg.register("get_article_count", ("Blog",), ("Count",), "Get a count of articles. GET /admin/api/blogs/{id}/articles/count.json")

    # --- Pages --- GET /admin/api/pages.json
    reg.register("list_pages", ("Shop",), ("PageList",), "List pages. GET /admin/api/pages.json")
    reg.register("select_page", ("PageList",), ("Page",), "Select a single page.")
    reg.register("get_page", ("PageId",), ("Page",), "Get a single page. GET /admin/api/pages/{id}.json")
    reg.register("create_page", ("PageInput",), ("Page",), "Create a page. POST /admin/api/pages.json")
    reg.register("update_page", ("Page",), ("Page",), "Update a page. PUT /admin/api/pages/{id}.json")
    reg.register("delete_page", ("Page",), ("DeletionResult",), "Delete a page. DELETE /admin/api/pages/{id}.json")
    reg.register("get_page_count", ("Shop",), ("Count",), "Get a count of pages. GET /admin/api/pages/count.json")

    # --- Themes --- GET /admin/api/themes.json
    reg.register("list_themes", ("Shop",), ("ThemeList",), "List themes. GET /admin/api/themes.json")
    reg.register("select_theme", ("ThemeList",), ("Theme",), "Select a single theme.")
    reg.register("get_theme", ("ThemeId",), ("Theme",), "Get a single theme. GET /admin/api/themes/{id}.json")

    # --- Theme Assets --- GET /admin/api/themes/{id}/assets.json
    reg.register("list_theme_assets", ("Theme",), ("AssetList",), "List assets for a theme. GET /admin/api/themes/{id}/assets.json")
    reg.register("select_asset", ("AssetList",), ("Asset",), "Select a single theme asset.")
    reg.register("get_theme_asset", ("AssetId",), ("Asset",), "Get a single theme asset. GET /admin/api/themes/{id}/assets.json?asset[key]=")
    reg.register("update_theme_asset", ("Asset",), ("Asset",), "Create or update a theme asset. PUT /admin/api/themes/{id}/assets.json")
    reg.register("delete_theme_asset", ("Asset",), ("DeletionResult",), "Delete a theme asset. DELETE /admin/api/themes/{id}/assets.json")

    # --- Webhooks --- GET /admin/api/webhooks.json
    reg.register("list_webhooks", ("Shop",), ("WebhookList",), "List webhooks. GET /admin/api/webhooks.json")
    reg.register("select_webhook", ("WebhookList",), ("Webhook",), "Select a single webhook.")
    reg.register("get_webhook", ("WebhookId",), ("Webhook",), "Get a single webhook. GET /admin/api/webhooks/{id}.json")
    reg.register("create_webhook", ("WebhookInput",), ("Webhook",), "Create a webhook. POST /admin/api/webhooks.json")
    reg.register("update_webhook", ("Webhook",), ("Webhook",), "Update a webhook. PUT /admin/api/webhooks/{id}.json")
    reg.register("delete_webhook", ("Webhook",), ("DeletionResult",), "Delete a webhook. DELETE /admin/api/webhooks/{id}.json")
    reg.register("get_webhook_count", ("Shop",), ("Count",), "Get a count of webhooks. GET /admin/api/webhooks/count.json")

    # --- Events --- GET /admin/api/events.json
    reg.register("list_events", ("Shop",), ("EventList",), "List events. GET /admin/api/events.json")
    reg.register("select_event", ("EventList",), ("Event",), "Select a single event.")
    reg.register("get_event", ("EventId",), ("Event",), "Get a single event. GET /admin/api/events/{id}.json")
    reg.register("get_event_count", ("Shop",), ("Count",), "Get a count of events. GET /admin/api/events/count.json")

    # --- Metafields --- GET /admin/api/metafields.json
    reg.register("list_product_metafields", ("Product",), ("MetafieldList",), "List metafields for a product. GET /admin/api/products/{id}/metafields.json")
    reg.register("list_customer_metafields", ("Customer",), ("MetafieldList",), "List metafields for a customer. GET /admin/api/customers/{id}/metafields.json")
    reg.register("list_order_metafields", ("Order",), ("MetafieldList",), "List metafields for an order. GET /admin/api/orders/{id}/metafields.json")
    reg.register("select_metafield", ("MetafieldList",), ("Metafield",), "Select a single metafield.")
    reg.register("get_metafield", ("MetafieldId",), ("Metafield",), "Get a metafield. GET /admin/api/metafields/{id}.json")
    reg.register("create_metafield", ("MetafieldInput",), ("Metafield",), "Create a metafield. POST /admin/api/metafields.json")
    reg.register("delete_metafield", ("Metafield",), ("DeletionResult",), "Delete a metafield. DELETE /admin/api/metafields/{id}.json")
    reg.register("get_metafield_count", ("Shop",), ("Count",), "Get a count of metafields. GET /admin/api/metafields/count.json")

    # --- Reports --- GET /admin/api/reports.json
    reg.register("list_reports", ("Shop",), ("ReportList",), "List reports. GET /admin/api/reports.json")
    reg.register("select_report", ("ReportList",), ("Report",), "Select a single report.")
    reg.register("get_report", ("ReportId",), ("Report",), "Get a single report. GET /admin/api/reports/{id}.json")

    # --- Carrier Services --- GET /admin/api/carrier_services.json
    reg.register("list_carrier_services", ("Shop",), ("CarrierServiceList",), "List carrier services. GET /admin/api/carrier_services.json")
    reg.register("select_carrier_service", ("CarrierServiceList",), ("CarrierService",), "Select a single carrier service.")
    reg.register("get_carrier_service", ("CarrierServiceId",), ("CarrierService",), "Get a carrier service. GET /admin/api/carrier_services/{id}.json")

    # --- Shop --- GET /admin/api/shop.json
    reg.register("get_shop", ("ShopDomain",), ("Shop",), "Get shop details. GET /admin/api/shop.json")

    return reg


ENTITY_TYPES = {
    "Shop": "The Shopify store itself",
    "ProductList": "A list of products (GET /admin/api/products.json)",
    "Product": "A product in the store",
    "VariantList": "A list of variants for a product",
    "ProductVariant": "A variant of a product (size, color, etc.)",
    "ImageList": "A list of images for a product",
    "ProductImage": "An image associated with a product",
    "CustomCollectionList": "A list of custom collections",
    "CustomCollection": "A manually curated collection of products",
    "SmartCollectionList": "A list of smart collections",
    "SmartCollection": "An automatically populated collection based on rules",
    "CollectionProductList": "Products belonging to a collection",
    "CustomerList": "A list of customers",
    "Customer": "A customer of the store",
    "AddressList": "A list of addresses for a customer",
    "CustomerAddress": "A shipping or billing address for a customer",
    "CustomerOrderList": "Orders placed by a specific customer",
    "OrderList": "A list of orders",
    "Order": "A customer order",
    "LineItemList": "Line items (individual products/quantities) in an order",
    "DraftOrderList": "A list of draft orders",
    "DraftOrder": "An order draft that can be completed into an order",
    "TransactionList": "Payment transactions for an order",
    "Transaction": "A payment transaction associated with an order",
    "RefundList": "Refunds issued for an order",
    "Refund": "A refund issued for an order",
    "FulfillmentList": "Fulfillments for an order",
    "Fulfillment": "A shipment fulfillment for an order",
    "FulfillmentOrderList": "Fulfillment orders for an order",
    "FulfillmentOrder": "A group of items to be fulfilled from one location",
    "FulfillmentEventList": "Tracking events for a fulfillment",
    "FulfillmentEvent": "A tracking event for a fulfillment (shipped, delivered, etc.)",
    "InventoryItem": "An inventory item tracked by Shopify",
    "InventoryLevelList": "Inventory levels across locations for an item",
    "InventoryLevel": "Stock quantity of an inventory item at a specific location",
    "LocationList": "A list of store locations",
    "Location": "A physical or virtual location where inventory is stocked",
    "PriceRuleList": "A list of price rules",
    "PriceRule": "A price rule that defines a discount",
    "DiscountCodeList": "Discount codes for a price rule",
    "DiscountCode": "A discount code associated with a price rule",
    "BlogList": "A list of blogs on the store",
    "Blog": "A blog on the online store",
    "ArticleList": "Articles in a blog",
    "Article": "A blog article/post",
    "PageList": "A list of pages on the store",
    "Page": "A static page on the online store",
    "ThemeList": "A list of themes",
    "Theme": "A theme for the online store",
    "AssetList": "Assets belonging to a theme",
    "Asset": "A file asset belonging to a theme (template, CSS, image)",
    "WebhookList": "A list of webhook subscriptions",
    "Webhook": "A webhook subscription for store events",
    "EventList": "A list of store events",
    "Event": "An event (action that happened in the store)",
    "MetafieldList": "Metafields attached to a resource",
    "Metafield": "Custom metadata attached to a resource",
    "ReportList": "A list of analytics reports",
    "Report": "An analytics report",
    "CarrierServiceList": "A list of carrier services",
    "CarrierService": "A third-party carrier service for shipping rates",
}
