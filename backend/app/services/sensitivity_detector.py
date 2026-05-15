FINANCIAL_TERMS = {
    "income",
    "salary",
    "revenue",
    "profit",
    "balance",
    "asset",
    "loan",
    "debt",
}


def detect_sensitivity_tag(normalized_column_name: str) -> str:
    name = normalized_column_name
    parts = set(name.split("_"))

    if any(term in name for term in {"email", "e_mail", "mail"}):
        return "email"
    if any(term in name for term in {"phone", "mobile", "tel", "手机", "电话"}):
        return "phone"
    if (
        "name" in parts
        or any(term in name for term in {"full_name", "first_name", "last_name", "姓名"})
    ):
        return "name"
    if any(term in name for term in {"address", "location", "地址"}):
        return "address"
    if any(term in name for term in {"credit_score", "credit", "fico", "信用分"}):
        return "credit_score"
    if any(term in name for term in FINANCIAL_TERMS):
        return "financial_sensitive"
    if "id" in parts or any(term in name for term in {"user_id", "customer_id", "account_id", "ssn", "身份证"}):
        return "id"
    return "none"
