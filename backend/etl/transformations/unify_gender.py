def unify_gender(value: str | None) -> str:
    if not value:
        return "No especificado"
    v = value.strip().lower()
    if v in ("m", "masculino"):
        return "Masculino"
    if v in ("f", "femenino"):
        return "Femenino"
    if v in ("x", "otro", "no especificado"):
        return "No especificado"
    return "No especificado"
