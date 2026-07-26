# Each scope controls which user fields an organisation can see.
# When admin approves a company, they grant a subset of these scopes.
# The company token then carries the approved scopes as JWT claims.

SCOPE_FIELDS = {
    "name:full":             ["first_name", "middle_name", "last_name"],
    "profile:basic":         ["birth_date", "location"],
    "profile:contact":       ["phone_number"],
    "profile:education":     ["education"],
    "identity:national_id":  ["national_id"],
    "identity:document":     ["document_path"],
}

# Human-readable descriptions shown to companies when they pick scopes
SCOPE_DESCRIPTIONS = {
    "name:full":             "User's full name (first, middle, last)",
    "profile:basic":         "User's date of birth and location",
    "profile:contact":       "User's phone number",
    "profile:education":     "User's education background",
    "identity:national_id":  "User's national ID number",
    "identity:document":     "User's uploaded identity document",
}

ALL_SCOPES = list(SCOPE_FIELDS.keys())
