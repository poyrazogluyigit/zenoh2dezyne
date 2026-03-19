def get_publishers(implicit cpg: Cpg) = {
    cpg.call.name("declare_publisher").l
    // Group by file name first (using headOption is safer in case a file is missing)
    .groupBy(_.file.name.headOption.getOrElse("unknown"))
    .map { case (fileName, calls) =>
        fileName -> calls.map(c => Map(
        "line"    -> c.lineNumber.getOrElse(-1),
        "code"    -> c.code,
        "keyExpr" -> c.argument(1).code
        ))
    }.toJson
}
