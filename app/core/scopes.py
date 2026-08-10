SCOPE_FIELDS = {
    "account:email":        ["email"],
    "account:username":     ["username"],
    "name:full_name":       [],  # computed: first_name + middle_name + last_name joined
    "name:first_name":      ["first_name"],
    "name:middle_name":     ["middle_name"],
    "name:last_name":       ["last_name"],
    "profile:birth_date":   ["birth_date"],
    "profile:location":     ["location"],
    "profile:phone":        ["phone_number"],
    "profile:education":    ["education"],
    "profile:photo":        ["profile_image"],
    "identity:national_id": ["national_id"],
    "identity:document":    ["document_path"],
}

SCOPE_DESCRIPTIONS = {
    "account:email":        "User's registered email address",
    "account:username":     "User's username",
    "name:full_name":       "User's full name (first + middle + last) as a single combined string",
    "name:first_name":      "User's first name",
    "name:middle_name":     "User's middle name",
    "name:last_name":       "User's last name",
    "profile:birth_date":   "User's date of birth",
    "profile:location":     "User's location / city",
    "profile:phone":        "User's phone number",
    "profile:education":    "User's education background",
    "profile:photo":        "User's profile photo (URL path)",
    "identity:national_id": "User's national ID number",
    "identity:document":    "User's uploaded identity document",
}

ALL_SCOPES = list(SCOPE_FIELDS.keys())
