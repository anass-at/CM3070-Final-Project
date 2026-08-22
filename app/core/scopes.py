SCOPE_FIELDS = {
    # Context-specific name scopes — each maps to a distinct set of name fields
    "name:legal":           ["first_name", "middle_name", "last_name"],
    "name:preferred":       ["preferred_name"],
    "name:professional":    ["professional_name"],
    "name:religious":       ["religious_name"],

    # Basic profile data — grouped so one approval grants age + nationality + photo
    "profile:basic":        ["birth_date", "nationality", "profile_image"],

    # Individual profile fields (for organisations that need only one)
    "profile:location":     ["location"],
    "profile:phone":        ["phone_number"],
    "profile:education":    ["education"],

    # Account identifiers
    "account:email":        ["email"],
    "account:username":     ["username"],

    # Sensitive identity fields — require explicit justification
    "identity:national_id": ["national_id"],
    "identity:document":    ["document_path"],
}

SCOPE_DESCRIPTIONS = {
    "name:legal":           "Legal name (first, middle, last) as shown on official documents",
    "name:preferred":       "Preferred name — how the person wishes to be addressed informally",
    "name:professional":    "Professional name — used in work and business contexts",
    "name:religious":       "Religious name — used in religious or community contexts",
    "profile:basic":        "Basic profile: date of birth, nationality, and profile photo",
    "profile:location":     "City or country of residence",
    "profile:phone":        "Registered phone number",
    "profile:education":    "Education background",
    "account:email":        "Registered email address",
    "account:username":     "Username",
    "identity:national_id": "National ID number (sensitive — requires strong justification)",
    "identity:document":    "Uploaded identity document (sensitive — requires strong justification)",
}

ALL_SCOPES = list(SCOPE_FIELDS.keys())
