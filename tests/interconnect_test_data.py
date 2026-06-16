from src.datatypes import TranslationUnit, Publisher, Subscriber

# generate a mock translation unit
mock_unit_A = TranslationUnit(
    file_name="unit_A.cpp",
    main_thread=None,
    callback_threads=[Subscriber(name="callback_A", topic="example/B_to_A", cfg=None)],
    publishers=[Publisher(symbol="to_B", topic="example/A_to_B")],
)

# generate a mock translation unit
mock_unit_B = TranslationUnit(
    file_name="unit_B.cpp",
    main_thread=None,
    callback_threads=[Subscriber(name="callback_B", topic="example/A_to_B", cfg=None)],
    publishers=[Publisher(symbol="A_pub", topic="example/B_to_A")],
)
