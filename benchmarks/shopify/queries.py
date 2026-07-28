QUERIES = [
    # ──────────────────────────────────────────────
    # Clean, well-structured queries
    # ──────────────────────────────────────────────
    {
        "id": "list_products",
        "category": "clean",
        "query": "List all products in the store",
        "source_type": "Shop",
        "target_type": "ProductList",
        "expected_tools": ["list_products"],
    },
    {
        "id": "product_variants",
        "category": "clean",
        "query": "Show me the variants for this product",
        "source_type": "Product",
        "target_type": "VariantList",
        "expected_tools": ["list_product_variants"],
    },
    {
        "id": "order_fulfillments",
        "category": "clean",
        "query": "List the fulfillments for order #1234",
        "source_type": "Order",
        "target_type": "FulfillmentList",
        "expected_tools": ["list_order_fulfillments"],
    },
    {
        "id": "order_line_items",
        "category": "clean",
        "query": "Get the line items for this order",
        "source_type": "Order",
        "target_type": "LineItemList",
        "expected_tools": ["list_order_line_items"],
    },
    {
        "id": "customer_addresses",
        "category": "clean",
        "query": "Show me the shipping addresses for this customer",
        "source_type": "Customer",
        "target_type": "AddressList",
        "expected_tools": ["list_customer_addresses"],
    },
    {
        "id": "order_transactions",
        "category": "clean",
        "query": "List the payment transactions for this order",
        "source_type": "Order",
        "target_type": "TransactionList",
        "expected_tools": ["list_order_transactions"],
    },
    {
        "id": "product_images",
        "category": "clean",
        "query": "Show me all images for this product",
        "source_type": "Product",
        "target_type": "ImageList",
        "expected_tools": ["list_product_images"],
    },
    {
        "id": "price_rule_codes",
        "category": "clean",
        "query": "List the discount codes for this price rule",
        "source_type": "PriceRule",
        "target_type": "DiscountCodeList",
        "expected_tools": ["list_discount_codes"],
    },
    {
        "id": "order_refunds",
        "category": "clean",
        "query": "Show the refunds issued for this order",
        "source_type": "Order",
        "target_type": "RefundList",
        "expected_tools": ["list_order_refunds"],
    },
    {
        "id": "theme_assets",
        "category": "clean",
        "query": "List all assets in this theme",
        "source_type": "Theme",
        "target_type": "AssetList",
        "expected_tools": ["list_theme_assets"],
    },

    # ──────────────────────────────────────────────
    # Ambiguous queries
    # ──────────────────────────────────────────────
    {
        "id": "ambiguous_order_details",
        "category": "ambiguous",
        "query": "Show me the details for this order",
        "source_type": "Order",
        "target_type": "LineItemList",
        "expected_tools": ["list_order_line_items"],
    },
    {
        "id": "ambiguous_customer_activity",
        "category": "ambiguous",
        "query": "What's the history for this customer?",
        "source_type": "Customer",
        "target_type": "CustomerOrderList",
        "expected_tools": ["list_customer_orders"],
    },
    {
        "id": "ambiguous_collection_contents",
        "category": "ambiguous",
        "query": "What's in this collection?",
        "source_type": "CustomCollection",
        "target_type": "CollectionProductList",
        "expected_tools": ["list_collection_products"],
    },

    # ──────────────────────────────────────────────
    # Multi-hop queries
    # ──────────────────────────────────────────────
    {
        "id": "multihop_customer_tracking",
        "category": "multihop",
        "query": "Show me the shipment tracking events for this customer's latest order",
        "source_type": "Customer",
        "target_type": "FulfillmentEventList",
        "expected_tools": [
            "list_customer_orders", "select_customer_order",
            "list_order_fulfillments", "select_fulfillment",
            "list_fulfillment_events",
        ],
    },
    {
        "id": "multihop_variant_stock",
        "category": "multihop",
        "query": "What are the inventory levels for each variant of this product?",
        "source_type": "Product",
        "target_type": "InventoryLevelList",
        "expected_tools": [
            "create_variant",
            "get_variant_inventory_item", "list_inventory_levels",
        ],
    },
    {
        "id": "multihop_collection_variants",
        "category": "multihop",
        "query": "List the variants for products in this collection",
        "source_type": "CustomCollection",
        "target_type": "VariantList",
        "expected_tools": [
            "list_collection_products", "select_collection_product",
            "list_product_variants",
        ],
    },
    {
        "id": "multihop_customer_transactions",
        "category": "multihop",
        "query": "Show me the payment transactions for this customer's orders",
        "source_type": "Customer",
        "target_type": "TransactionList",
        "expected_tools": [
            "list_customer_orders", "select_customer_order",
            "list_order_transactions",
        ],
    },
    {
        "id": "multihop_blog_articles",
        "category": "multihop",
        "query": "Show me all articles across the store's blogs",
        "source_type": "Shop",
        "target_type": "ArticleList",
        "expected_tools": [
            "list_blogs", "select_blog", "list_blog_articles",
        ],
    },
    {
        "id": "multihop_collection_inventory",
        "category": "multihop",
        "query": "Check the stock levels for all products in this collection",
        "source_type": "CustomCollection",
        "target_type": "InventoryLevelList",
        "expected_tools": [
            "list_collection_products", "select_collection_product",
            "create_variant",
            "get_variant_inventory_item", "list_inventory_levels",
        ],
    },

    # ──────────────────────────────────────────────
    # Synonyms and alternative wording
    # ──────────────────────────────────────────────
    {
        "id": "synonym_purchase_items",
        "category": "synonym",
        "query": "Show me the items in this purchase",
        "source_type": "Order",
        "target_type": "LineItemList",
        "expected_tools": ["list_order_line_items"],
    },
    {
        "id": "synonym_coupons",
        "category": "synonym",
        "query": "List the coupons for this promotion",
        "source_type": "PriceRule",
        "target_type": "DiscountCodeList",
        "expected_tools": ["list_discount_codes"],
    },
    {
        "id": "synonym_shipment_tracking",
        "category": "synonym",
        "query": "Where is the shipment for this purchase?",
        "source_type": "Order",
        "target_type": "FulfillmentEventList",
        "expected_tools": [
            "list_order_fulfillments", "select_fulfillment",
            "list_fulfillment_events",
        ],
    },
    {
        "id": "synonym_skus",
        "category": "synonym",
        "query": "What SKUs are available for this product?",
        "source_type": "Product",
        "target_type": "VariantList",
        "expected_tools": ["list_product_variants"],
    },

    # ──────────────────────────────────────────────
    # Noisy real-world language
    # ──────────────────────────────────────────────
    {
        "id": "noisy_stock_check",
        "category": "noisy",
        "query": "hey can u check if that tshirt product still has stock somewhere",
        "source_type": "Product",
        "target_type": "InventoryLevelList",
        "expected_tools": [
            "create_variant",
            "get_variant_inventory_item", "list_inventory_levels",
        ],
    },
    {
        "id": "noisy_order_shipped",
        "category": "noisy",
        "query": "wheres my order at, like has it shipped yet?",
        "source_type": "Order",
        "target_type": "FulfillmentEventList",
        "expected_tools": [
            "list_order_fulfillments", "select_fulfillment",
            "list_fulfillment_events",
        ],
    },
    {
        "id": "noisy_customer_charges",
        "category": "noisy",
        "query": "some customer is complaining about a charge, need to look up their transactions",
        "source_type": "Customer",
        "target_type": "TransactionList",
        "expected_tools": [
            "list_customer_orders", "select_customer_order",
            "list_order_transactions",
        ],
    },
    {
        "id": "noisy_blog_posts",
        "category": "noisy",
        "query": "yo can you pull up the blog posts real quick",
        "source_type": "Shop",
        "target_type": "ArticleList",
        "expected_tools": ["list_blogs", "select_blog", "list_blog_articles"],
    },

    # ──────────────────────────────────────────────
    # Multi-path queries (multiple valid paths)
    # ──────────────────────────────────────────────
    {
        "id": "multipath_discount_lookup",
        "category": "multipath",
        "query": "Check if the discount code SUMMER20 is valid",
        "source_type": "Shop",
        "target_type": "DiscountCode",
        "expected_tools": ["lookup_discount_code"],
    },
    {
        "id": "multipath_location_stock",
        "category": "multipath",
        "query": "What inventory is at this location?",
        "source_type": "Location",
        "target_type": "InventoryLevelList",
        "expected_tools": ["get_location_inventory"],
    },
]
