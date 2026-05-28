from src.datatypes import TranslationUnit, VarPublisher, CallbackThread, SessPublisher

# generate a mock translation unit
mock_unit_A = TranslationUnit(
    file_name="unit_A.cpp",
    main_thread=None,
    callback_threads=[CallbackThread(name="callback_A", key_expr="example/B_to_A", cfg=None)],
    var_publishers=[VarPublisher(var="to_B", key_expr="example/A_to_B")],
    sess_publishers=[SessPublisher(var="session", key_exprs=["example/A_to_B"])]
)

# generate a mock translation unit
mock_unit_B = TranslationUnit(
    file_name="unit_B.cpp",
    main_thread=None,
    callback_threads=[CallbackThread(name="callback_B", key_expr="example/A_to_B", cfg=None)],
    var_publishers=[VarPublisher(var="A_pub", key_expr="example/B_to_A")],
    sess_publishers=[SessPublisher(var="session", key_exprs=["example/B_to_A"])]
)
