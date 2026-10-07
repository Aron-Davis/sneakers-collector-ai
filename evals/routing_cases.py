# Casi di valutazione per il routing dell'agente, raggruppati per intento.
ROUTING_CASES = [
    # Lettura della collezione.
    {
        "name": "list_all",
        "input": "Fammi vedere tutta la mia collezione",
        "expected_action": "list_collection",
    },
    {
        "name": "search_brand",
        "input": "Mostrami tutte le Nike che possiedo",
        "expected_action": "search_collection",
        "expected_arguments": {
            "query": "Nike",
        },
    },
    {
        "name": "search_model",
        "input": "Fammi vedere le Jordan che possiedo",
        "expected_action": "search_collection",
        "expected_arguments": {
            "query": "Jordan",
        },
    },
    {
        "name": "search_colorway",
        "input": "Mostrami le sneakers rosse",
        "expected_action": "search_collection",
    },
    {
        "name": "filtered_collection_not_list",
        "input": "Fammi vedere solo le Adidas della mia collezione",
        "expected_action": "search_collection",
        "expected_arguments": {
            "query": "Adidas",
        },
    },
    {
        "name": "search_style_code",
        "input": "Trova la sneaker con style code CW2288-111",
        "expected_action": "search_collection",
        "expected_arguments": {
            "query": "CW2288-111",
        },
    },
    {
        "name": "sneaker_by_id",
        "input": "Mostrami la sneaker con ID 1",
        "expected_action": "sneaker_by_id",
        "expected_arguments": {
            "sneaker_id": 1,
        },
    },
    {
        "name": "explicit_id",
        "input": "Apri la sneaker numero ID 3",
        "expected_action": "sneaker_by_id",
        "expected_arguments": {
            "sneaker_id": 3,
        },
    },

    # Statistiche della collezione.
    {
        "name": "stats_count",
        "input": "Quante sneakers ho nella mia collezione?",
        "expected_action": "collection_stats",
    },
    {
        "name": "stats_spending",
        "input": "Quanto ho speso in totale per le mie sneakers?",
        "expected_action": "collection_stats",
    },
    {
        "name": "stats_average",
        "input": "Qual è il prezzo medio delle sneakers che ho comprato?",
        "expected_action": "collection_stats",
    },

    # Mutazioni della collezione: add, update e delete.
    {
        "name": "add_sneaker",
        "input": "Aggiungi delle Adidas Samba OG taglia 43",
        "expected_action": "add_sneaker",
    },
    {
        "name": "add_duplicate_model",
        "input": (
            "Aggiungi delle Adidas Samba OG "
            "taglia 43 EU, nuove, con scatola"
        ),
        "expected_action": "add_sneaker",
        "expected_arguments": {},
    },
    {
        "name": "update_condition",
        "input": "Imposta le Nike Dunk Grey Fog come used",
        "expected_action": "update_sneaker",
        "expected_query": "Nike Dunk Grey Fog",
    },
    {
        "name": "update_box",
        "input": "Ho ritrovato la scatola delle Jordan 1 Chicago",
        "expected_action": "update_sneaker",
        "expected_query": "Jordan 1 Chicago",
    },
    {
        "name": "update_size_with_add_word",
        "input": "Aggiungi la taglia 45 EU alle Adidas Gazelle",
        "expected_action": "update_sneaker",
        "expected_query": "Adidas Gazelle",
    },
    {
        "name": "update_colorway_with_add_word",
        "input": "Aggiungi il colore nero alle Puma Test Model",
        "expected_action": "update_sneaker",
        "expected_query": "Puma Test Model",
    },
    {
        "name": "delete_sneaker",
        "input": "Elimina le Adidas Superstar dalla mia collezione",
        "expected_action": "delete_sneaker",
        "expected_query": "Adidas Superstar",
    },

    # Knowledge base RAG.
    {
        "name": "knowledge_jordan",
        "input": "Cosa sai della Jordan Chicago?",
        "expected_action": "sneaker_knowledge",
        "expected_query": "Jordan Chicago",
    },
    {
        "name": "knowledge_release",
        "input": "In che anno è uscita la Jordan Chicago?",
        "expected_action": "sneaker_knowledge",
        "expected_query": "Jordan Chicago",
    },
    {
        "name": "knowledge_vs_collection",
        "input": "Parlami delle Air Max Anniversary Red",
        "expected_action": "sneaker_knowledge",
        "expected_query": "Air Max Anniversary Red",
    },

    # Richieste in inglese.
    {
        "name": "english_list",
        "input": "Show me my entire sneaker collection",
        "expected_action": "list_collection",
    },
    {
        "name": "english_search",
        "input": "Do I own any New Balance sneakers?",
        "expected_action": "search_collection",
        "expected_arguments": {
            "query": "New Balance",
        },
    },
    {
        "name": "english_stats",
        "input": "How many pairs do I own?",
        "expected_action": "collection_stats",
    },
    {
        "name": "english_add",
        "input": "Add my Nike Air Max 90 to the collection",
        "expected_action": "add_sneaker",
    },

    # Richieste non supportate.
    {
        "name": "unsupported_question",
        "input": "Qual è la capitale del Giappone?",
        "expected_action": "unsupported",
    },
    {
        "name": "unsupported_weather",
        "input": "Che tempo fa oggi?",
        "expected_action": "unsupported",
    },
]
